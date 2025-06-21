"""
ORDER EXECUTION ENGINE - Центральный торговый движок
Файл: src/exchange/execution_engine.py

🎯 ИНТЕГРИРУЕТ ВСЕ КОМПОНЕНТЫ:
✅ Стратегии → Риск-менеджмент → Исполнение → Мониторинг
✅ Валидация сигналов через риск-менеджер
✅ Расчет оптимального размера позиций
✅ Проверка ликвидности и проскальзывания
✅ Создание записей в БД и мониторинг
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from ..core.database import SessionLocal
from ..models.trade import Trade, TradeStatus, OrderSide
from ..models.signal import Signal, SignalType
from ..strategies.base import TradingSignal
from ..risk.enhanced_risk_manager import get_risk_manager
from ..logging.smart_logger import get_logger
from .real_client import get_real_exchange_client
from .position_manager import get_position_manager, PositionInfo

logger = get_logger(__name__)

class ExecutionStatus(Enum):
    """Статусы исполнения"""
    PENDING = "pending"
    VALIDATING = "validating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

@dataclass
class ExecutionRequest:
    """Запрос на исполнение торговой операции"""
    signal: TradingSignal
    strategy_name: str
    confidence: float
    market_conditions: Dict[str, Any]
    risk_params: Dict[str, Any]
    
    # Рассчитываемые поля
    quantity: Optional[float] = None
    expected_slippage: Optional[float] = None
    execution_priority: int = 1  # 1-низкий, 5-высокий
    
@dataclass
class ExecutionResult:
    """Результат исполнения"""
    request: ExecutionRequest
    status: ExecutionStatus
    order_id: Optional[str] = None
    trade_id: Optional[int] = None
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    slippage: Optional[float] = None
    error_message: Optional[str] = None
    execution_time: Optional[datetime] = None

class OrderExecutionEngine:
    """
    Центральный движок исполнения торговых операций
    
    🔥 ПОЛНАЯ АВТОМАТИЗАЦИЯ ТОРГОВЛИ:
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   СИГНАЛ ОТ     │───▶│  ВАЛИДАЦИЯ       │───▶│   ИСПОЛНЕНИЕ    │
    │   СТРАТЕГИИ     │    │  РИСК-МЕНЕДЖЕР   │    │   НА БИРЖЕ      │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
             │                        │                        │
             ▼                        ▼                        ▼
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   РАСЧЕТ        │    │   ПРОВЕРКА       │    │   МОНИТОРИНГ    │
    │   ПОЗИЦИИ       │    │   ЛИКВИДНОСТИ    │    │   ПОЗИЦИИ       │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
    """
    
    def __init__(self, max_concurrent_executions: int = 3):
        """
        Инициализация движка исполнения
        
        Args:
            max_concurrent_executions: Максимум одновременных исполнений
        """
        self.exchange = get_real_exchange_client()
        self.risk_manager = get_risk_manager()
        self.position_manager = get_position_manager()
        
        self.max_concurrent_executions = max_concurrent_executions
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.active_executions: Dict[str, ExecutionRequest] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # Статистика
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.rejected_executions = 0
        
        # Состояние
        self.is_running = False
        self.emergency_stop = False
        
        logger.info(
            "Order Execution Engine инициализирован",
            category='execution',
            max_concurrent=max_concurrent_executions
        )
    
    # =================================================================
    # ОСНОВНЫЕ МЕТОДЫ ИСПОЛНЕНИЯ
    # =================================================================
    
    async def execute_signal(self, signal: TradingSignal, strategy_name: str,
                           confidence: float, market_conditions: Dict[str, Any]) -> ExecutionResult:
        """
        🔥 ГЛАВНЫЙ МЕТОД ИСПОЛНЕНИЯ ТОРГОВОГО СИГНАЛА
        
        Полный цикл: Сигнал → Валидация → Расчеты → Исполнение → Мониторинг
        
        Args:
            signal: Торговый сигнал от стратегии
            strategy_name: Название стратегии
            confidence: Уверенность в сигнале (0-1)
            market_conditions: Рыночные условия
            
        Returns:
            ExecutionResult: Результат исполнения
        """
        start_time = datetime.utcnow()
        
        # Создаем запрос на исполнение
        request = ExecutionRequest(
            signal=signal,
            strategy_name=strategy_name,
            confidence=confidence,
            market_conditions=market_conditions,
            risk_params={}
        )
        
        logger.info(
            f"🎯 Новый сигнал для исполнения",
            category='execution',
            symbol=signal.symbol,
            action=signal.action,
            strategy=strategy_name,
            confidence=confidence,
            price=signal.price
        )
        
        try:
            # 1. Валидация через риск-менеджмент
            result = await self._validate_execution_request(request)
            if result.status == ExecutionStatus.REJECTED:
                return result
            
            # 2. Расчет размера позиции
            result = await self._calculate_position_size(request)
            if result.status == ExecutionStatus.FAILED:
                return result
            
            # 3. Проверка ликвидности и проскальзывания
            result = await self._check_liquidity_and_slippage(request)
            if result.status == ExecutionStatus.FAILED:
                return result
            
            # 4. Исполнение ордера на бирже
            result = await self._execute_order(request)
            if result.status == ExecutionStatus.FAILED:
                return result
            
            # 5. Создание записи в БД
            if result.status == ExecutionStatus.COMPLETED:
                await self._create_trade_record(request, result)
            
            # 6. Обновление статистики
            self._update_execution_stats(result)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = start_time
            
            logger.info(
                f"✅ Исполнение завершено: {result.status.value}",
                category='execution',
                symbol=signal.symbol,
                status=result.status.value,
                execution_time=execution_time,
                order_id=result.order_id,
                trade_id=result.trade_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"❌ Критическая ошибка исполнения: {e}",
                category='execution',
                symbol=signal.symbol,
                strategy=strategy_name,
                error=str(e)
            )
            
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.FAILED,
                error_message=f"Критическая ошибка: {e}",
                execution_time=start_time
            )
    
    async def _validate_execution_request(self, request: ExecutionRequest) -> ExecutionResult:
        """Валидация запроса через риск-менеджмент"""
        try:
            # Проверка экстренной остановки
            if self.emergency_stop:
                return ExecutionResult(
                    request=request,
                    status=ExecutionStatus.REJECTED,
                    error_message="Активна экстренная остановка"
                )
            
            # Валидация через риск-менеджер
            risk_check, risk_reason = await self.risk_manager.validate_position(
                symbol=request.signal.symbol,
                side=request.signal.action.lower(),
                quantity=1.0,  # Пока примерное значение
                price=request.signal.price,
                market_data=request.market_conditions
            )
            
            if not risk_check:
                logger.warning(
                    f"⚠️ Сигнал отклонен риск-менеджером",
                    category='execution',
                    symbol=request.signal.symbol,
                    reason=risk_reason
                )
                
                self.rejected_executions += 1
                
                return ExecutionResult(
                    request=request,
                    status=ExecutionStatus.REJECTED,
                    error_message=f"Риск-менеджмент: {risk_reason}"
                )
            
            logger.debug(
                f"✅ Валидация пройдена",
                category='execution',
                symbol=request.signal.symbol
            )
            
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.VALIDATING
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации: {e}")
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.FAILED,
                error_message=f"Ошибка валидации: {e}"
            )
    
    async def _calculate_position_size(self, request: ExecutionRequest) -> ExecutionResult:
        """Расчет размера позиции"""
        try:
            # Получаем баланс
            balance = await self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if usdt_balance < 10:  # Минимум $10
                return ExecutionResult(
                    request=request,
                    status=ExecutionStatus.REJECTED,
                    error_message="Недостаточно средств для торговли"
                )
            
            # Рассчитываем размер позиции через биржевой клиент
            risk_percent = self.risk_manager.risk_params.position_size_percent
            quantity = self.exchange.calculate_position_size(
                symbol=request.signal.symbol,
                balance=usdt_balance,
                risk_percent=risk_percent
            )
            
            if quantity <= 0:
                return ExecutionResult(
                    request=request,
                    status=ExecutionStatus.REJECTED,
                    error_message="Рассчитанный размер позиции слишком мал"
                )
            
            # Сохраняем в запросе
            request.quantity = quantity
            
            logger.debug(
                f"📊 Размер позиции рассчитан",
                category='execution',
                symbol=request.signal.symbol,
                quantity=quantity,
                balance=usdt_balance,
                risk_percent=risk_percent
            )
            
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.VALIDATING
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета размера позиции: {e}")
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.FAILED,
                error_message=f"Ошибка расчета позиции: {e}"
            )
    
    async def _check_liquidity_and_slippage(self, request: ExecutionRequest) -> ExecutionResult:
        """Проверка ликвидности и ожидаемого проскальзывания"""
        try:
            symbol = request.signal.symbol
            
            # Получаем стакан заявок
            order_book = await self.exchange.fetch_order_book(symbol, limit=20)
            
            # Рассчитываем ожидаемое проскальзывание
            side = request.signal.action.lower()
            quantity = request.quantity
            
            if side == 'buy':
                # Для покупки смотрим asks
                asks = order_book['asks']
                total_quantity = 0
                weighted_price = 0
                
                for price, size in asks:
                    if total_quantity >= quantity:
                        break
                    
                    take_quantity = min(size, quantity - total_quantity)
                    weighted_price += price * take_quantity
                    total_quantity += take_quantity
                
                if total_quantity < quantity:
                    return ExecutionResult(
                        request=request,
                        status=ExecutionStatus.REJECTED,
                        error_message="Недостаточно ликвидности для исполнения"
                    )
                
                avg_execution_price = weighted_price / total_quantity
                
            else:
                # Для продажи смотрим bids
                bids = order_book['bids']
                total_quantity = 0
                weighted_price = 0
                
                for price, size in bids:
                    if total_quantity >= quantity:
                        break
                    
                    take_quantity = min(size, quantity - total_quantity)
                    weighted_price += price * take_quantity
                    total_quantity += take_quantity
                
                if total_quantity < quantity:
                    return ExecutionResult(
                        request=request,
                        status=ExecutionStatus.REJECTED,
                        error_message="Недостаточно ликвидности для исполнения"
                    )
                
                avg_execution_price = weighted_price / total_quantity
            
            # Рассчитываем проскальзывание
            expected_price = request.signal.price
            slippage_percent = abs(avg_execution_price - expected_price) / expected_price * 100
            
            # Проверяем допустимое проскальзывание
            max_slippage = 0.5  # 0.5%
            if slippage_percent > max_slippage:
                return ExecutionResult(
                    request=request,
                    status=ExecutionStatus.REJECTED,
                    error_message=f"Слишком большое проскальзывание: {slippage_percent:.2f}%"
                )
            
            request.expected_slippage = slippage_percent
            
            logger.debug(
                f"📈 Ликвидность проверена",
                category='execution',
                symbol=symbol,
                expected_slippage=slippage_percent,
                avg_execution_price=avg_execution_price
            )
            
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.VALIDATING
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки ликвидности: {e}")
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.FAILED,
                error_message=f"Ошибка проверки ликвидности: {e}"
            )
    
    async def _execute_order(self, request: ExecutionRequest) -> ExecutionResult:
        """Исполнение ордера на бирже"""
        try:
            signal = request.signal
            
            # Исполняем ордер через реальный клиент
            order = await self.exchange.create_order(
                symbol=signal.symbol,
                order_type='market',  # Пока только рыночные ордера
                side=signal.action.lower(),
                amount=request.quantity,
                price=None,  # Рыночная цена
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            
            if not order.success:
                return ExecutionResult(
                    request=request,
                    status=ExecutionStatus.FAILED,
                    error_message=order.error_message or "Ордер не был создан"
                )
            
            # Успешное исполнение
            logger.info(
                f"✅ Ордер успешно исполнен",
                category='execution',
                symbol=signal.symbol,
                order_id=order.order_id,
                executed_price=order.average_price,
                executed_quantity=order.filled_quantity,
                slippage=order.slippage
            )
            
            self.successful_executions += 1
            
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.COMPLETED,
                order_id=order.order_id,
                executed_price=order.average_price,
                executed_quantity=order.filled_quantity,
                slippage=order.slippage
            )
                
        except Exception as e:
            logger.error(f"❌ Ошибка исполнения ордера: {e}")
            self.failed_executions += 1
            
            return ExecutionResult(
                request=request,
                status=ExecutionStatus.FAILED,
                error_message=f"Ошибка исполнения: {e}"
            )
    
    async def _create_trade_record(self, request: ExecutionRequest, 
                                 result: ExecutionResult) -> Optional[int]:
        """Создание записи сделки в БД"""
        db = SessionLocal()
        try:
            trade = Trade(
                symbol=request.signal.symbol,
                side=OrderSide.BUY if request.signal.action == 'BUY' else OrderSide.SELL,
                quantity=result.executed_quantity,
                entry_price=result.executed_price,
                stop_loss=request.signal.stop_loss,
                take_profit=request.signal.take_profit,
                strategy=request.strategy_name,
                confidence=request.confidence,
                status=TradeStatus.OPEN,
                order_id=result.order_id,
                slippage=result.slippage,
                market_conditions=request.market_conditions,
                created_at=datetime.utcnow()
            )
            
            db.add(trade)
            db.commit()
            db.refresh(trade)
            
            result.trade_id = trade.id
            
            logger.info(
                f"✅ Сделка сохранена в БД",
                category='execution',
                trade_id=trade.id,
                symbol=request.signal.symbol
            )
            
            return trade.id
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сделки: {e}")
            return None
        finally:
            db.close()
    
    def _update_execution_stats(self, result: ExecutionResult):
        """Обновление статистики исполнений"""
        self.total_executions += 1
        self.execution_history.append(result)
        
        # Ограничиваем историю последними 1000 исполнениями
        if len(self.execution_history) > 1000:
            self.execution_history.pop(0)
    
    # =================================================================
    # УПРАВЛЕНИЕ И МОНИТОРИНГ
    # =================================================================
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Получение статистики исполнений"""
        success_rate = 0
        if self.total_executions > 0:
            success_rate = self.successful_executions / self.total_executions * 100
        
        # Средняя скорость исполнения
        avg_execution_time = 0
        if self.execution_history:
            execution_times = [
                (r.execution_time - r.request.signal.timestamp).total_seconds()
                for r in self.execution_history
                if r.execution_time and hasattr(r.request.signal, 'timestamp')
            ]
            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)
        
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'rejected_executions': self.rejected_executions,
            'success_rate_percent': success_rate,
            'avg_execution_time_seconds': avg_execution_time,
            'emergency_stop': self.emergency_stop
        }
    
    def activate_emergency_stop(self, reason: str = "Manual activation"):
        """Активация экстренной остановки"""
        self.emergency_stop = True
        
        logger.critical(
            f"🚨 ЭКСТРЕННАЯ ОСТАНОВКА АКТИВИРОВАНА: {reason}",
            category='execution'
        )
    
    def deactivate_emergency_stop(self):
        """Деактивация экстренной остановки"""
        self.emergency_stop = False
        
        logger.info(
            "✅ Экстренная остановка деактивирована",
            category='execution'
        )
    
    async def close_all_positions_emergency(self) -> bool:
        """Экстренное закрытие всех позиций"""
        try:
            self.activate_emergency_stop("Emergency close all positions")
            
            # Закрываем через Position Manager
            success = await self.position_manager.emergency_close_all()
            
            if success:
                logger.critical(
                    "🚨 Все позиции экстренно закрыты",
                    category='execution'
                )
            else:
                logger.error(
                    "❌ Ошибка экстренного закрытия позиций",
                    category='execution'
                )
            
            return success
            
        except Exception as e:
            logger.critical(f"🚨 КРИТИЧЕСКАЯ ОШИБКА ЭКСТРЕННОГО ЗАКРЫТИЯ: {e}")
            return False

# =================================================================
# ГЛОБАЛЬНЫЕ ФУНКЦИИ
# =================================================================

# Глобальный экземпляр
execution_engine = None

def get_execution_engine() -> OrderExecutionEngine:
    """Получить глобальный экземпляр движка исполнения"""
    global execution_engine
    
    if execution_engine is None:
        execution_engine = OrderExecutionEngine()
    
    return execution_engine

def create_execution_engine(**kwargs) -> OrderExecutionEngine:
    """Создать новый экземпляр движка исполнения"""
    return OrderExecutionEngine(**kwargs)

# Экспорты
__all__ = [
    'OrderExecutionEngine',
    'ExecutionRequest',
    'ExecutionResult', 
    'ExecutionStatus',
    'get_execution_engine',
    'create_execution_engine'
]