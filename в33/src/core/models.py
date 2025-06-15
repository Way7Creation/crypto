"""
SQLAlchemy модели для криптотрейдинг бота
Путь: src/core/models.py

Определяет структуру базы данных:
- Пользователи и авторизация
- Торговые сделки и история
- Сигналы и стратегии
- Состояние бота и настройки
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
import json

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from .database import Base


# ===== ENUMS =====

class OrderSide(PyEnum):
    """Направление ордера"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(PyEnum):
    """Тип ордера"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class TradeStatus(PyEnum):
    """Статус сделки"""
    PENDING = "PENDING"      # Ожидает исполнения
    OPEN = "OPEN"           # Открытая позиция
    CLOSED = "CLOSED"       # Закрытая позиция
    CANCELLED = "CANCELLED"  # Отменена
    ERROR = "ERROR"         # Ошибка исполнения


class SignalStatus(PyEnum):
    """Статус торгового сигнала"""
    PENDING = "PENDING"      # Ожидает обработки
    EXECUTED = "EXECUTED"    # Исполнен
    CANCELLED = "CANCELLED"  # Отменен
    EXPIRED = "EXPIRED"      # Истек


# ===== МОДЕЛИ =====

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Настройки пользователя
    settings = Column(JSON, default=dict)
    
    # Отношения
    trades = relationship("Trade", back_populates="user", lazy="dynamic")
    signals = relationship("Signal", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class TradingPair(Base):
    """Торговые пары и их настройки"""
    __tablename__ = "trading_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Настройки для пары
    strategy = Column(String(50), default="multi_indicator")
    stop_loss_percent = Column(Float, default=2.0)
    take_profit_percent = Column(Float, default=4.0)
    max_position_size = Column(Float, nullable=True)
    
    # Статистика
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    trades = relationship("Trade", back_populates="pair", lazy="dynamic")
    signals = relationship("Signal", back_populates="pair", lazy="dynamic")
    
    def __repr__(self):
        return f"<TradingPair(symbol='{self.symbol}', active={self.is_active})>"


class Trade(Base):
    """Модель торговой сделки"""
    __tablename__ = "trades"
    __table_args__ = (
        Index('idx_trade_status_symbol', 'status', 'symbol'),
        Index('idx_trade_created_at', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Основная информация
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    
    # Цены и объемы
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    
    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Результаты
    profit = Column(Float, default=0.0)
    profit_percent = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    
    # Идентификаторы биржи
    exchange_order_id = Column(String(100), nullable=True, unique=True)
    
    # Метаданные
    strategy = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    opened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pair_id = Column(Integer, ForeignKey("trading_pairs.id"), nullable=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    
    # Отношения
    user = relationship("User", back_populates="trades")
    pair = relationship("TradingPair", back_populates="trades")
    signal = relationship("Signal", back_populates="trade", uselist=False)
    
    def __repr__(self):
        return f"<Trade(symbol='{self.symbol}', side={self.side.value}, status={self.status.value})>"
    
    @validates('profit')
    def update_profit_percent(self, key, value):
        """Автоматически обновляем процент прибыли"""
        if self.entry_price and self.entry_price > 0:
            self.profit_percent = (value / (self.entry_price * self.quantity)) * 100
        return value


class Signal(Base):
    """Торговые сигналы от стратегий"""
    __tablename__ = "signals"
    __table_args__ = (
        Index('idx_signal_created_at', 'created_at'),
        Index('idx_signal_symbol_status', 'symbol', 'status'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Информация о сигнале
    symbol = Column(String(20), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL, WAIT
    confidence = Column(Float, nullable=False)
    
    # Рекомендуемые параметры
    price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Стратегия и причина
    strategy = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    
    # Статус исполнения
    status = Column(Enum(SignalStatus), default=SignalStatus.PENDING)
    executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pair_id = Column(Integer, ForeignKey("trading_pairs.id"), nullable=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    
    # Отношения
    user = relationship("User", back_populates="signals")
    pair = relationship("TradingPair", back_populates="signals")
    trade = relationship("Trade", back_populates="signal", uselist=False)
    
    def __repr__(self):
        return f"<Signal(symbol='{self.symbol}', action='{self.action}', confidence={self.confidence})>"


class Balance(Base):
    """История баланса"""
    __tablename__ = "balances"
    __table_args__ = (
        Index('idx_balance_timestamp', 'timestamp'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Балансы
    total_balance = Column(Float, nullable=False)
    free_balance = Column(Float, nullable=False)
    locked_balance = Column(Float, default=0.0)
    
    # В разрезе валют
    balances_snapshot = Column(JSON, default=dict)  # {"BTC": 0.5, "USDT": 1000}
    
    # Временная метка
    timestamp = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Balance(total={self.total_balance}, free={self.free_balance})>"


class BotState(Base):
    """Состояние бота"""
    __tablename__ = "bot_state"
    
    id = Column(Integer, primary_key=True)
    
    # Статус
    is_running = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime, nullable=True)
    
    # Временные метки
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    
    # Статистика текущей сессии
    current_session_trades = Column(Integer, default=0)
    current_session_profit = Column(Float, default=0.0)
    
    # Настройки
    settings = Column(JSON, default=dict)
    
    # Информация о процессе
    process_info = Column(JSON, default=dict)
    
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BotState(running={self.is_running})>"


class PerformanceMetric(Base):
    """Метрики производительности стратегий"""
    __tablename__ = "performance_metrics"
    __table_args__ = (
        UniqueConstraint('strategy', 'symbol', 'timeframe', 'date'),
        Index('idx_performance_date', 'date'),
    )
    
    id = Column(Integer, primary_key=True)
    
    # Идентификаторы
    strategy = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), default='daily')
    
    # Метрики
    trades_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    total_profit = Column(Float, default=0.0)
    total_loss = Column(Float, default=0.0)
    
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, default=0.0)
    
    # Временная метка
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<PerformanceMetric(strategy='{self.strategy}', symbol='{self.symbol}', win_rate={self.win_rate})>"


class LoginAttempt(Base):
    """Попытки входа для защиты от брутфорса"""
    __tablename__ = "login_attempts"
    __table_args__ = (
        Index('idx_login_username_timestamp', 'username', 'timestamp'),
    )
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<LoginAttempt(username='{self.username}', success={self.success})>"


# ===== HELPER FUNCTIONS =====

def get_active_bot_state(db_session: Any) -> Optional[BotState]:
    """Получить текущее состояние бота"""
    return db_session.query(BotState).first()


def get_active_trades(db_session: Any) -> list:
    """Получить все активные сделки"""
    return db_session.query(Trade).filter(
        Trade.status == TradeStatus.OPEN
    ).all()


def get_today_trades_count(db_session: Any) -> int:
    """Получить количество сделок за сегодня"""
    from datetime import datetime, time
    
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    
    return db_session.query(Trade).filter(
        Trade.created_at >= today_start
    ).count()


# Экспортируем все модели и enums
__all__ = [
    # Enums
    'OrderSide',
    'OrderType',
    'TradeStatus',
    'SignalStatus',
    # Models
    'User',
    'TradingPair',
    'Trade',
    'Signal',
    'Balance',
    'BotState',
    'PerformanceMetric',
    'LoginAttempt',
    # Helpers
    'get_active_bot_state',
    'get_active_trades',
    'get_today_trades_count'
]