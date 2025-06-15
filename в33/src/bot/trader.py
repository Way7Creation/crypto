"""
Исполнитель торговых операций
Путь: src/bot/trader.py

Отвечает за:
- Исполнение торговых сигналов
- Размещение ордеров на бирже
- Управление позициями
- Расчет размера позиции
"""

import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
import asyncio

from ..core.exceptions import ExchangeError, InsufficientBalanceError
from ..core.models import Trade, TradeStatus, OrderSide
from ..exchange.client import ExchangeClient

logger = logging.getLogger(__name__)


class Trader:
    """
    Класс для исполнения торговых операций
    
    Обеспечивает безопасное исполнение сделок с:
    - Проверкой баланса
    - Расчетом размера позиции
    - Установкой защитных ордеров
    - Обработкой ошибок
    """
    
    def __init__(self, exchange: ExchangeClient):
        """
        Инициализация трейдера
        
        Args:
            exchange: Клиент биржи
        """
        self.exchange = exchange
        
        # Параметры по умолчанию
        self.min_order_value = 10.0  # Минимальная сумма ордера в USDT
        self.max_slippage = 0.5      # Максимальное проскальзывание в %
        self.order_timeout = 30       # Таймаут ордера в секундах
        
        logger.info("✅ Trader инициализирован")
    
    async def execute_buy(
        self,
        symbol: str,
        amount: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """
        Исполнение покупки
        
        Args:
            symbol: Торговая пара
            amount: Количество для покупки
            price: Цена для лимитного ордера
            stop_loss: Уровень стоп-лосса
            take_profit: Уровень тейк-профита
            order_type: Тип ордера (MARKET/LIMIT)
            
        Returns:
            Dict с информацией об ордере
            
        Raises:
            ExchangeError: При ошибке исполнения
            InsufficientBalanceError: При недостатке средств
        """
        try:
            logger.info(f"🛒 Исполняем покупку {amount} {symbol}")
            
            # Проверяем баланс
            balance_check = await self._check_balance_for_buy(symbol, amount, price)
            if not balance_check[0]:
                raise InsufficientBalanceError(balance_check[1])
            
            # Проверяем минимальный размер ордера
            order_value = amount * (price if price else await self._get_current_price(symbol))
            if order_value < self.min_order_value:
                raise ExchangeError(f"Order value {order_value:.2f} USDT is below minimum {self.min_order_value}")
            
            # Размещаем ордер
            order_result = await self.exchange.place_order(
                symbol=symbol,
                side="Buy",
                order_type=order_type,
                amount=amount,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Ждем исполнения если market ордер
            if order_type == "MARKET":
                await self._wait_for_order_fill(symbol, order_result['order_id'])
            
            logger.info(f"✅ Покупка исполнена: {order_result['order_id']}")
            return order_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка исполнения покупки {symbol}: {e}")
            raise
    
    async def execute_sell(
        self,
        symbol: str,
        amount: float,
        price: Optional[float] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """
        Исполнение продажи
        
        Args:
            symbol: Торговая пара
            amount: Количество для продажи
            price: Цена для лимитного ордера
            order_type: Тип ордера (MARKET/LIMIT)
            
        Returns:
            Dict с информацией об ордере
            
        Raises:
            ExchangeError: При ошибке исполнения
        """
        try:
            logger.info(f"💰 Исполняем продажу {amount} {symbol}")
            
            # Проверяем наличие позиции
            position_check = await self._check_position_for_sell(symbol, amount)
            if not position_check[0]:
                raise ExchangeError(position_check[1])
            
            # Размещаем ордер
            order_result = await self.exchange.place_order(
                symbol=symbol,
                side="Sell",
                order_type=order_type,
                amount=amount,
                price=price
            )
            
            # Ждем исполнения если market ордер
            if order_type == "MARKET":
                await self._wait_for_order_fill(symbol, order_result['order_id'])
            
            logger.info(f"✅ Продажа исполнена: {order_result['order_id']}")
            return order_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка исполнения продажи {symbol}: {e}")
            raise
    
    async def close_position(
        self,
        trade: Trade,
        reason: str = "Manual close"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Закрытие позиции
        
        Args:
            trade: Объект сделки
            reason: Причина закрытия
            
        Returns:
            Tuple[успех, результат]
        """
        try:
            logger.info(f"🔄 Закрываем позицию {trade.symbol}: {reason}")
            
            # Определяем направление закрытия
            close_side = "Sell" if trade.side == OrderSide.BUY else "Buy"
            
            # Получаем текущую цену
            current_price = await self._get_current_price(trade.symbol)
            
            # Размещаем market ордер для закрытия
            order_result = await self.exchange.place_order(
                symbol=trade.symbol,
                side=close_side,
                order_type="MARKET",
                amount=trade.quantity
            )
            
            # Ждем исполнения
            filled_order = await self._wait_for_order_fill(
                trade.symbol, 
                order_result['order_id']
            )
            
            # Рассчитываем прибыль
            exit_price = filled_order.get('average_price', current_price)
            
            if trade.side == OrderSide.BUY:
                profit = (exit_price - trade.entry_price) * trade.quantity
            else:
                profit = (trade.entry_price - exit_price) * trade.quantity
            
            # Учитываем комиссию (примерно 0.1%)
            commission = trade.quantity * exit_price * 0.001
            profit -= commission
            
            result = {
                'order_id': order_result['order_id'],
                'exit_price': exit_price,
                'profit': profit,
                'profit_percent': (profit / (trade.entry_price * trade.quantity)) * 100,
                'commission': commission,
                'reason': reason
            }
            
            logger.info(f"✅ Позиция закрыта с прибылью: ${profit:.2f} ({result['profit_percent']:.2f}%)")
            return True, result
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции: {e}")
            return False, {'error': str(e)}
    
    async def calculate_position_size(
        self,
        symbol: str,
        capital: float,
        risk_percent: float = 1.0,
        stop_loss_price: Optional[float] = None,
        entry_price: Optional[float] = None
    ) -> float:
        """
        Расчет размера позиции
        
        Args:
            symbol: Торговая пара
            capital: Доступный капитал
            risk_percent: Процент риска на сделку
            stop_loss_price: Цена стоп-лосса
            entry_price: Цена входа
            
        Returns:
            float: Размер позиции
        """
        try:
            # Получаем информацию о символе
            symbol_info = await self.exchange.get_symbol_info(symbol)
            
            # Если не указана цена входа, берем текущую
            if not entry_price:
                entry_price = await self._get_current_price(symbol)
            
            # Метод 1: Фиксированный процент от капитала
            if not stop_loss_price:
                # Простой расчет - используем процент от капитала
                position_value = capital * (risk_percent / 100)
                position_size = position_value / entry_price
            else:
                # Метод 2: На основе риска на сделку
                # Риск = (Entry - StopLoss) * Количество
                risk_per_unit = abs(entry_price - stop_loss_price)
                max_risk = capital * (risk_percent / 100)
                position_size = max_risk / risk_per_unit
            
            # Применяем ограничения
            # 1. Минимальный размер
            min_size = symbol_info['min_qty']
            if position_size < min_size:
                logger.warning(f"Размер позиции {position_size} меньше минимального {min_size}")
                return 0.0
            
            # 2. Максимальный размер
            max_size = symbol_info['max_qty']
            if position_size > max_size:
                position_size = max_size
            
            # 3. Проверяем минимальную стоимость ордера
            order_value = position_size * entry_price
            if order_value < self.min_order_value:
                position_size = self.min_order_value / entry_price
            
            # 4. Округляем по правилам биржи
            step = symbol_info['qty_step']
            position_size = round(position_size / step) * step
            
            logger.debug(f"📏 Рассчитан размер позиции: {position_size} {symbol} "
                        f"(${position_size * entry_price:.2f})")
            
            return position_size
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета размера позиции: {e}")
            return 0.0
    
    async def update_stop_loss(
        self,
        trade: Trade,
        new_stop_loss: float
    ) -> bool:
        """
        Обновление стоп-лосса (trailing stop)
        
        Args:
            trade: Сделка
            new_stop_loss: Новый уровень стоп-лосса
            
        Returns:
            bool: Успешность обновления
        """
        try:
            logger.info(f"📈 Обновляем стоп-лосс для {trade.symbol}: "
                       f"{trade.stop_loss:.2f} -> {new_stop_loss:.2f}")
            
            # В spot торговле нет встроенного trailing stop
            # Нужно реализовать через мониторинг цены
            # Это заглушка для будущей реализации
            
            logger.warning("⚠️ Trailing stop для spot торговли пока не реализован")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления стоп-лосса: {e}")
            return False
    
    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====
    
    async def _get_current_price(self, symbol: str) -> float:
        """Получение текущей цены"""
        ticker = await self.exchange.fetch_ticker(symbol)
        return ticker['last']
    
    async def _check_balance_for_buy(
        self, 
        symbol: str, 
        amount: float,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """Проверка баланса для покупки"""
        try:
            # Получаем баланс USDT
            balance = await self.exchange.fetch_balance("USDT")
            available = balance['free']
            
            # Получаем цену если не указана
            if not price:
                price = await self._get_current_price(symbol)
            
            # Считаем необходимую сумму с учетом комиссии
            required = amount * price * 1.002  # +0.2% на комиссию и проскальзывание
            
            if available >= required:
                return True, f"Balance OK: {available:.2f} USDT available"
            else:
                return False, f"Insufficient balance: need {required:.2f} USDT, have {available:.2f}"
                
        except Exception as e:
            return False, f"Balance check error: {e}"
    
    async def _check_position_for_sell(
        self, 
        symbol: str, 
        amount: float
    ) -> Tuple[bool, str]:
        """Проверка позиции для продажи"""
        try:
            # Получаем базовую валюту
            symbol_info = await self.exchange.get_symbol_info(symbol)
            base_asset = symbol_info['base_asset']
            
            # Проверяем баланс базовой валюты
            balance = await self.exchange.fetch_balance(base_asset)
            available = balance['free']
            
            if available >= amount:
                return True, f"Position OK: {available:.8f} {base_asset} available"
            else:
                return False, f"Insufficient position: need {amount:.8f} {base_asset}, have {available:.8f}"
                
        except Exception as e:
            return False, f"Position check error: {e}"
    
    async def _wait_for_order_fill(
        self, 
        symbol: str, 
        order_id: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Ожидание исполнения ордера"""
        timeout = timeout or self.order_timeout
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                # Проверяем статус ордера
                order_status = await self.exchange.get_order_status(symbol, order_id)
                
                if order_status['status'] in ['Filled', 'PartiallyFilled']:
                    return order_status
                
                if order_status['status'] in ['Cancelled', 'Rejected']:
                    raise ExchangeError(f"Order {order_id} was {order_status['status']}")
                
                # Проверяем таймаут
                if asyncio.get_event_loop().time() - start_time > timeout:
                    # Пытаемся отменить ордер
                    await self.exchange.cancel_order(symbol, order_id)
                    raise ExchangeError(f"Order {order_id} timeout")
                
                # Ждем перед следующей проверкой
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error waiting for order fill: {e}")
                raise


# Экспортируем
__all__ = ['Trader']