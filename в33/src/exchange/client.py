"""
Клиент для работы с биржей Bybit
Путь: src/exchange/client.py

Обеспечивает взаимодействие с Bybit API:
- Получение рыночных данных
- Размещение и отмена ордеров
- Управление позициями
- Получение баланса
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hmac
import hashlib
import time
import json

import aiohttp
import pandas as pd
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError, FailedRequestError

from ..core.config import config
from ..core.exceptions import ExchangeError

logger = logging.getLogger(__name__)


class ExchangeClient:
    """
    Унифицированный клиент для работы с Bybit
    
    Поддерживает:
    - Spot и Futures торговлю
    - Testnet и Mainnet
    - Синхронные и асинхронные вызовы
    """
    
    def __init__(self):
        """Инициализация клиента"""
        self.api_key = config.BYBIT_API_KEY
        self.api_secret = config.BYBIT_API_SECRET
        self.testnet = config.BYBIT_TESTNET
        
        # Базовые URL
        if self.testnet:
            self.base_url = "https://api-testnet.bybit.com"
            self.ws_url = "wss://stream-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
            self.ws_url = "wss://stream.bybit.com"
        
        # Создаем HTTP клиент pybit
        try:
            self.client = HTTP(
                testnet=self.testnet,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            logger.info(f"✅ Bybit клиент инициализирован ({'TESTNET' if self.testnet else 'MAINNET'})")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Bybit клиента: {e}")
            raise ExchangeError(f"Failed to initialize Bybit client: {e}")
        
        # Кэш для часто используемых данных
        self._symbol_info_cache = {}
        self._balance_cache = {}
        self._cache_ttl = 60  # секунд
        
        # Лимиты API
        self.rate_limits = {
            'orders': 10,      # ордеров в секунду
            'data': 50,        # запросов данных в секунду
            'account': 5       # запросов аккаунта в секунду
        }
        
        # Счетчики для rate limiting
        self._request_counters = {}
    
    async def test_connection(self) -> bool:
        """
        Тест подключения к бирже
        
        Returns:
            bool: True если подключение успешно
        """
        try:
            # Пробуем получить серверное время
            response = self.client.get_server_time()
            
            if response['retCode'] == 0:
                server_time = datetime.fromtimestamp(int(response['result']['timeSecond']))
                logger.info(f"✅ Подключение к Bybit успешно. Серверное время: {server_time}")
                return True
            else:
                logger.error(f"❌ Ошибка подключения: {response['retMsg']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к Bybit: {e}")
            return False
    
    async def fetch_balance(self, coin: str = "USDT") -> Dict[str, float]:
        """
        Получение баланса
        
        Args:
            coin: Валюта для получения баланса
            
        Returns:
            Dict с балансами {total, free, locked}
        """
        try:
            # Проверяем кэш
            cache_key = f"balance_{coin}"
            if self._is_cache_valid(cache_key):
                return self._balance_cache[cache_key]
            
            # Получаем баланс
            response = self.client.get_wallet_balance(
                accountType="UNIFIED",
                coin=coin
            )
            
            if response['retCode'] != 0:
                raise ExchangeError(f"Failed to fetch balance: {response['retMsg']}")
            
            # Парсим результат
            coin_data = None
            for account in response['result']['list']:
                for coin_info in account['coin']:
                    if coin_info['coin'] == coin:
                        coin_data = coin_info
                        break
            
            if not coin_data:
                return {'total': 0.0, 'free': 0.0, 'locked': 0.0}
            
            balance = {
                'total': float(coin_data.get('walletBalance', 0)),
                'free': float(coin_data.get('availableToWithdraw', 0)),
                'locked': float(coin_data.get('locked', 0))
            }
            
            # Сохраняем в кэш
            self._balance_cache[cache_key] = balance
            self._balance_cache[f"{cache_key}_timestamp"] = time.time()
            
            logger.debug(f"💰 Баланс {coin}: {balance}")
            return balance
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
            raise ExchangeError(f"Failed to fetch balance: {e}")
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, float]:
        """
        Получение текущей цены и тикера
        
        Args:
            symbol: Торговая пара (например, BTCUSDT)
            
        Returns:
            Dict с ценами {last, bid, ask, volume}
        """
        try:
            response = self.client.get_tickers(
                category="spot",
                symbol=symbol
            )
            
            if response['retCode'] != 0:
                raise ExchangeError(f"Failed to fetch ticker: {response['retMsg']}")
            
            if not response['result']['list']:
                raise ExchangeError(f"No ticker data for {symbol}")
            
            ticker_data = response['result']['list'][0]
            
            ticker = {
                'symbol': symbol,
                'last': float(ticker_data['lastPrice']),
                'bid': float(ticker_data['bid1Price']),
                'ask': float(ticker_data['ask1Price']),
                'volume': float(ticker_data['volume24h']),
                'high': float(ticker_data['highPrice24h']),
                'low': float(ticker_data['lowPrice24h']),
                'change': float(ticker_data['price24hPcnt']) * 100  # в процентах
            }
            
            logger.debug(f"📊 Тикер {symbol}: ${ticker['last']:.2f}")
            return ticker
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения тикера {symbol}: {e}")
            raise ExchangeError(f"Failed to fetch ticker: {e}")
    
    async def fetch_ohlcv(self, symbol: str, interval: str = "5", limit: int = 200) -> List[List]:
        """
        Получение исторических свечей OHLCV
        
        Args:
            symbol: Торговая пара
            interval: Интервал свечей (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            limit: Количество свечей
            
        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        try:
            response = self.client.get_kline(
                category="spot",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if response['retCode'] != 0:
                raise ExchangeError(f"Failed to fetch OHLCV: {response['retMsg']}")
            
            # Преобразуем в стандартный формат
            ohlcv = []
            for candle in response['result']['list']:
                ohlcv.append([
                    int(candle[0]),      # timestamp
                    float(candle[1]),    # open
                    float(candle[2]),    # high
                    float(candle[3]),    # low
                    float(candle[4]),    # close
                    float(candle[5])     # volume
                ])
            
            # Сортируем по времени (Bybit возвращает в обратном порядке)
            ohlcv.sort(key=lambda x: x[0])
            
            logger.debug(f"📈 Получено {len(ohlcv)} свечей для {symbol}")
            return ohlcv
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения OHLCV для {symbol}: {e}")
            raise ExchangeError(f"Failed to fetch OHLCV: {e}")
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """
        Размещение ордера
        
        Args:
            symbol: Торговая пара
            side: Buy или Sell
            order_type: Market или Limit
            amount: Количество
            price: Цена для лимитного ордера
            stop_loss: Уровень стоп-лосса
            take_profit: Уровень тейк-профита
            time_in_force: GTC, IOC, FOK
            
        Returns:
            Dict с информацией об ордере
        """
        try:
            # Проверяем rate limits
            if not await self._check_rate_limit('orders'):
                await asyncio.sleep(0.5)
            
            # Получаем информацию о символе для округления
            symbol_info = await self.get_symbol_info(symbol)
            
            # Округляем количество
            amount = self._round_quantity(amount, symbol_info)
            
            # Базовые параметры ордера
            order_params = {
                "category": "spot",
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(amount),
                "timeInForce": time_in_force
            }
            
            # Добавляем цену для лимитного ордера
            if order_type.upper() == "LIMIT" and price:
                price = self._round_price(price, symbol_info)
                order_params["price"] = str(price)
            
            # Размещаем ордер
            response = self.client.place_order(**order_params)
            
            if response['retCode'] != 0:
                raise ExchangeError(f"Failed to place order: {response['retMsg']}")
            
            order_info = response['result']
            
            logger.info(f"✅ Ордер размещен: {side} {amount} {symbol} @ "
                       f"{'MARKET' if order_type == 'Market' else price}")
            
            # Если указаны SL/TP, размещаем их отдельно
            if stop_loss or take_profit:
                await self._place_sl_tp_orders(
                    symbol, side, amount, stop_loss, take_profit, order_info['orderId']
                )
            
            return {
                'order_id': order_info['orderId'],
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'amount': amount,
                'price': price,
                'status': order_info['orderStatus'],
                'created_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка размещения ордера: {e}")
            raise ExchangeError(f"Failed to place order: {e}")
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Отмена ордера
        
        Args:
            symbol: Торговая пара
            order_id: ID ордера
            
        Returns:
            bool: True если успешно отменен
        """
        try:
            response = self.client.cancel_order(
                category="spot",
                symbol=symbol,
                orderId=order_id
            )
            
            if response['retCode'] == 0:
                logger.info(f"✅ Ордер {order_id} отменен")
                return True
            else:
                logger.error(f"❌ Не удалось отменить ордер: {response['retMsg']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка отмены ордера: {e}")
            return False
    
    async def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Получение статуса ордера
        
        Args:
            symbol: Торговая пара
            order_id: ID ордера
            
        Returns:
            Dict с информацией об ордере
        """
        try:
            response = self.client.get_open_orders(
                category="spot",
                symbol=symbol,
                orderId=order_id
            )
            
            if response['retCode'] != 0:
                raise ExchangeError(f"Failed to get order status: {response['retMsg']}")
            
            if not response['result']['list']:
                # Проверяем в истории
                response = self.client.get_order_history(
                    category="spot",
                    symbol=symbol,
                    orderId=order_id,
                    limit=1
                )
                
                if not response['result']['list']:
                    raise ExchangeError(f"Order {order_id} not found")
            
            order_data = response['result']['list'][0]
            
            return {
                'order_id': order_data['orderId'],
                'status': order_data['orderStatus'],
                'filled': float(order_data.get('cumExecQty', 0)),
                'remaining': float(order_data.get('leavesQty', 0)),
                'average_price': float(order_data.get('avgPrice', 0)),
                'created_at': datetime.fromtimestamp(int(order_data['createdTime']) / 1000)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса ордера: {e}")
            raise ExchangeError(f"Failed to get order status: {e}")
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Получение открытых позиций
        
        Returns:
            List позиций
        """
        try:
            # Для spot торговли позиции определяются балансом
            response = self.client.get_wallet_balance(
                accountType="UNIFIED"
            )
            
            if response['retCode'] != 0:
                raise ExchangeError(f"Failed to get positions: {response['retMsg']}")
            
            positions = []
            
            for account in response['result']['list']:
                for coin_info in account['coin']:
                    balance = float(coin_info.get('walletBalance', 0))
                    
                    # Пропускаем стейблкоины и малые балансы
                    if coin_info['coin'] in ['USDT', 'USDC', 'BUSD'] or balance < 0.00001:
                        continue
                    
                    positions.append({
                        'symbol': f"{coin_info['coin']}USDT",
                        'amount': balance,
                        'value': float(coin_info.get('usdValue', 0)),
                        'pnl': float(coin_info.get('unrealisedPnl', 0))
                    })
            
            return positions
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения позиций: {e}")
            raise ExchangeError(f"Failed to get positions: {e}")
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Получение информации о торговой паре
        
        Args:
            symbol: Торговая пара
            
        Returns:
            Dict с информацией о паре
        """
        try:
            # Проверяем кэш
            if symbol in self._symbol_info_cache:
                return self._symbol_info_cache[symbol]
            
            response = self.client.get_instruments_info(
                category="spot",
                symbol=symbol
            )
            
            if response['retCode'] != 0:
                raise ExchangeError(f"Failed to get symbol info: {response['retMsg']}")
            
            if not response['result']['list']:
                raise ExchangeError(f"Symbol {symbol} not found")
            
            info_data = response['result']['list'][0]
            
            symbol_info = {
                'symbol': symbol,
                'base_asset': info_data['baseCoin'],
                'quote_asset': info_data['quoteCoin'],
                'min_qty': float(info_data['lotSizeFilter']['minOrderQty']),
                'max_qty': float(info_data['lotSizeFilter']['maxOrderQty']),
                'qty_step': float(info_data['lotSizeFilter']['basePrecision']),
                'min_price': float(info_data['priceFilter']['minPrice']),
                'max_price': float(info_data['priceFilter']['maxPrice']),
                'price_step': float(info_data['priceFilter']['tickSize']),
                'min_notional': float(info_data.get('minNotional', 10))  # минимальная сумма ордера
            }
            
            # Сохраняем в кэш
            self._symbol_info_cache[symbol] = symbol_info
            
            return symbol_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о {symbol}: {e}")
            raise ExchangeError(f"Failed to get symbol info: {e}")
    
    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====
    
    def _round_quantity(self, quantity: float, symbol_info: Dict) -> float:
        """Округление количества по правилам биржи"""
        step = symbol_info['qty_step']
        return round(quantity / step) * step
    
    def _round_price(self, price: float, symbol_info: Dict) -> float:
        """Округление цены по правилам биржи"""
        step = symbol_info['price_step']
        return round(price / step) * step
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Проверка валидности кэша"""
        timestamp_key = f"{cache_key}_timestamp"
        if timestamp_key in self._balance_cache:
            age = time.time() - self._balance_cache[timestamp_key]
            return age < self._cache_ttl
        return False
    
    async def _check_rate_limit(self, category: str) -> bool:
        """Проверка rate limit"""
        now = time.time()
        key = f"{category}_{int(now)}"
        
        if key not in self._request_counters:
            self._request_counters[key] = 0
        
        self._request_counters[key] += 1
        
        # Очищаем старые счетчики
        old_keys = [k for k in self._request_counters if int(k.split('_')[1]) < now - 60]
        for k in old_keys:
            del self._request_counters[k]
        
        return self._request_counters[key] <= self.rate_limits.get(category, 10)
    
    async def _place_sl_tp_orders(
        self, 
        symbol: str, 
        side: str, 
        amount: float,
        stop_loss: Optional[float], 
        take_profit: Optional[float],
        parent_order_id: str
    ):
        """Размещение ордеров стоп-лосс и тейк-профит"""
        try:
            # Для spot торговли SL/TP реализуются через условные ордера
            # Это упрощенная реализация
            
            if stop_loss:
                logger.info(f"⚠️ Stop-loss для spot пока не реализован")
            
            if take_profit:
                logger.info(f"⚠️ Take-profit для spot пока не реализован")
                
        except Exception as e:
            logger.error(f"❌ Ошибка установки SL/TP: {e}")


# Создаем глобальный экземпляр клиента
exchange_client = ExchangeClient()

# Экспортируем
__all__ = ['ExchangeClient', 'exchange_client']