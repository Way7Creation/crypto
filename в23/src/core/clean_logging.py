"""
Чистая конфигурация логирования для криптобота
Убирает избыточные логи, оставляет только важные события
Файл: src/core/clean_logging.py
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами для консоли"""
    
    # Цветовые коды ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Добавляем цвет к уровню логирования
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class TradingLogFilter(logging.Filter):
    """Фильтр для торговых логов - показывает только важные события"""
    
    IMPORTANT_KEYWORDS = [
        'trade', 'сделка', 'позиция', 'прибыль', 'убыток',
        'buy', 'sell', 'покупка', 'продажа',
        'stop', 'loss', 'profit', 'стоп', 'лосс',
        'signal', 'сигнал', 'strategy', 'стратегия',
        'error', 'ошибка', 'warning', 'предупреждение',
        'start', 'stop', 'запуск', 'остановка',
        'balance', 'баланс', 'portfolio', 'портфель'
    ]
    
    EXCLUDE_PATTERNS = [
        'heartbeat', 'ping', 'pong',
        'websocket', 'ws',
        'checking', 'проверка',
        'fetching', 'получение',
        'updating', 'обновление',
        'debug', 'отладка'
    ]
    
    def filter(self, record):
        message = record.getMessage().lower()
        
        # Всегда показываем ERROR и CRITICAL
        if record.levelno >= logging.ERROR:
            return True
        
        # Исключаем DEBUG сообщения
        if record.levelno == logging.DEBUG:
            return False
        
        # Проверяем исключения
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern in message:
                return False
        
        # Проверяем важные ключевые слова
        for keyword in self.IMPORTANT_KEYWORDS:
            if keyword in message:
                return True
        
        # Для WARNING показываем всегда
        if record.levelno == logging.WARNING:
            return True
        
        # Остальные INFO сообщения фильтруем
        return False


def setup_clean_logging(log_level: str = "INFO", enable_file_logging: bool = True) -> logging.Logger:
    """
    Настройка чистого логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        enable_file_logging: Включить логирование в файл
    
    Returns:
        Настроенный логгер
    """
    
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Очищаем старые логи при запуске
    clear_old_logs(log_dir)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие обработчики
    root_logger.handlers.clear()
    
    # Консольный обработчик с цветами
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Простой формат для консоли
    console_format = ColoredFormatter(
        fmt='%(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # Добавляем фильтр для торговых логов
    console_handler.addFilter(TradingLogFilter())
    
    root_logger.addHandler(console_handler)
    
    # Файловый обработчик для важных событий
    if enable_file_logging:
        # Главный лог файл
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "crypto_bot.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        file_format = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        file_handler.addFilter(TradingLogFilter())
        
        root_logger.addHandler(file_handler)
        
        # Отдельный файл для торговых событий
        trade_handler = logging.handlers.RotatingFileHandler(
            log_dir / "trades.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        trade_handler.setLevel(logging.INFO)
        trade_handler.setFormatter(file_format)
        
        # Фильтр только для торговых событий
        class TradeOnlyFilter(logging.Filter):
            def filter(self, record):
                message = record.getMessage().lower()
                trade_keywords = ['trade', 'сделка', 'buy', 'sell', 'покупка', 'продажа', 'profit', 'loss']
                return any(keyword in message for keyword in trade_keywords)
        
        trade_handler.addFilter(TradeOnlyFilter())
        root_logger.addHandler(trade_handler)
        
        # Ошибки в отдельный файл
        error_handler = logging.FileHandler(
            log_dir / "errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        
        root_logger.addHandler(error_handler)
    
    # Отключаем логирование для шумных модулей
    disable_noisy_loggers()
    
    # Получаем основной логгер приложения
    app_logger = logging.getLogger("crypto_bot")
    
    return app_logger


def clear_old_logs(log_dir: Path, max_age_days: int = 7):
    """Очищает старые лог файлы"""
    if not log_dir.exists():
        return
    
    now = datetime.now()
    for log_file in log_dir.glob("*.log*"):
        try:
            file_age = now - datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_age.days > max_age_days:
                log_file.unlink()
        except Exception:
            pass  # Игнорируем ошибки при удалении


def disable_noisy_loggers():
    """Отключает логирование для шумных модулей"""
    noisy_loggers = [
        'asyncio',
        'websockets', 
        'websockets.protocol',
        'websockets.server',
        'ccxt',
        'ccxt.base',
        'urllib3',
        'urllib3.connectionpool',
        'requests',
        'uvicorn',
        'uvicorn.access',
        'fastapi',
        'sqlalchemy.engine',
        'sqlalchemy.pool'
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


class TradingLogger:
    """Специальный логгер для торговых событий"""
    
    def __init__(self, name: str = "trading"):
        self.logger = logging.getLogger(name)
    
    def trade_opened(self, symbol: str, side: str, amount: float, price: float, strategy: str):
        """Лог открытия позиции"""
        self.logger.info(
            f"🔄 Открыта позиция: {side.upper()} {amount} {symbol} @ {price} | Стратегия: {strategy}"
        )
    
    def trade_closed(self, symbol: str, side: str, amount: float, price: float, profit: float):
        """Лог закрытия позиции"""
        profit_emoji = "📈" if profit > 0 else "📉" if profit < 0 else "➖"
        self.logger.info(
            f"{profit_emoji} Закрыта позиция: {side.upper()} {amount} {symbol} @ {price} | Прибыль: {profit:.2f} USDT"
        )
    
    def signal_generated(self, symbol: str, signal: str, strength: float, strategy: str):
        """Лог сигнала"""
        self.logger.info(
            f"🎯 Сигнал {signal.upper()} для {symbol} | Сила: {strength:.2f} | {strategy}"
        )
    
    def strategy_started(self, strategy: str, pairs: list):
        """Лог запуска стратегии"""
        self.logger.info(
            f"🚀 Запущена стратегия: {strategy} | Пары: {', '.join(pairs)}"
        )
    
    def strategy_stopped(self, strategy: str, reason: str = ""):
        """Лог остановки стратегии"""
        reason_text = f" | Причина: {reason}" if reason else ""
        self.logger.info(
            f"⏹️ Остановлена стратегия: {strategy}{reason_text}"
        )
    
    def error_occurred(self, error: str, context: str = ""):
        """Лог ошибки"""
        context_text = f" | Контекст: {context}" if context else ""
        self.logger.error(f"❌ Ошибка: {error}{context_text}")
    
    def balance_update(self, total_balance: float, available: float, currency: str = "USDT"):
        """Лог обновления баланса"""
        self.logger.info(
            f"💰 Баланс: {total_balance:.2f} {currency} | Доступно: {available:.2f} {currency}"
        )


# Глобальный экземпляр торгового логгера
trading_logger = TradingLogger()


def get_clean_logger(name: str) -> logging.Logger:
    """Получить чистый логгер для модуля"""
    return logging.getLogger(name)


# Функция для инициализации в main.py
def init_logging_system(log_level: str = "INFO") -> None:
    """Инициализация системы логирования"""
    
    print("🧹 Инициализация чистой системы логирования...")
    
    # Настраиваем чистое логирование
    setup_clean_logging(log_level)
    
    # Стартовое сообщение
    logger = get_clean_logger("startup")
    logger.info("✅ Система логирования настроена")
    logger.info(f"📊 Уровень логирования: {log_level}")
    logger.info("📁 Логи сохраняются в директории: logs/")
    
    # Информация о файлах логов
    log_files = {
        "crypto_bot.log": "Основные события",
        "trades.log": "Торговые операции", 
        "errors.log": "Ошибки системы"
    }
    
    for file, description in log_files.items():
        logger.info(f"📝 {file}: {description}")


if __name__ == "__main__":
    # Тест системы логирования
    init_logging_system("INFO")
    
    # Тестируем разные типы логов
    test_logger = get_clean_logger("test")
    test_logger.info("Это важное информационное сообщение")
    test_logger.debug("Это отладочное сообщение (не показывается)")
    test_logger.warning("Это предупреждение")
    test_logger.error("Это ошибка")
    
    # Тестируем торговый логгер
    trading_logger.strategy_started("momentum", ["BTCUSDT", "ETHUSDT"])
    trading_logger.signal_generated("BTCUSDT", "buy", 0.85, "momentum")
    trading_logger.trade_opened("BTCUSDT", "buy", 0.001, 45000, "momentum")
    trading_logger.trade_closed("BTCUSDT", "buy", 0.001, 45100, 0.1)
    trading_logger.balance_update(1000.50, 950.25)