"""
Обновленный главный файл с интеграцией полного дашборда
Файл: main.py
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорты нашего проекта
from src.core.config import Config
from src.core.clean_logging import init_logging_system, get_clean_logger, trading_logger
from src.bot.manager import TradingBotManager
from src.web.api_routes import router as api_router, set_bot_manager, ws_manager
from src.core.database import init_database

# Глобальные переменные
config = Config()
bot_manager: Optional[TradingBotManager] = None
web_app: Optional[FastAPI] = None
shutdown_event = asyncio.Event()

# Инициализируем логгер после настройки системы логирования
logger = None

def setup_signal_handlers():
    """Настройка обработчиков сигналов для graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"🛑 Получен сигнал {signum}, начинаем завершение...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def create_web_app() -> FastAPI:
    """Создание FastAPI приложения"""
    app = FastAPI(
        title="🚀 Crypto Trading Bot Dashboard",
        description="Полная панель управления криптотрейдинг ботом",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware для фронтенда
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключаем роуты дашборда
    app.include_router(api_router)
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("🌐 Веб-приложение запускается...")
        
        # Инициализируем базу данных
        try:
            await init_database()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🌐 Веб-приложение завершается...")
    
    return app

async def run_bot_only():
    """Запуск только торгового бота без веб-интерфейса"""
    global bot_manager
    
    logger.info("🤖 Запуск торгового бота...")
    
    try:
        # Создаем менеджера бота
        bot_manager = TradingBotManager(config)
        
        # Запускаем бота с базовой стратегией
        await bot_manager.start_strategy("momentum", ["BTCUSDT"])
        
        # Ждем сигнала завершения
        await shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"💥 Ошибка в торговом боте: {e}", exc_info=True)
        raise
    finally:
        if bot_manager:
            await bot_manager.stop()
            logger.info("✅ Торговый бот остановлен")

async def run_web_only():
    """Запуск только веб-интерфейса"""
    global web_app
    
    logger.info("🌐 Запуск веб-интерфейса...")
    
    try:
        # Создаем FastAPI приложение
        web_app = create_web_app()
        
        # Настройки сервера
        config_uvicorn = uvicorn.Config(
            app=web_app,
            host="0.0.0.0",
            port=8000,
            log_level="warning",  # Убираем лишние логи uvicorn
            access_log=False,     # Отключаем access логи
            ws_ping_interval=20,
            ws_ping_timeout=10
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        logger.info("🚀 Веб-интерфейс запущен на http://0.0.0.0:8000")
        logger.info("📊 Дашборд доступен по адресу: http://localhost:8000")
        
        # Запускаем сервер
        await server.serve()
        
    except Exception as e:
        logger.error(f"💥 Ошибка веб-интерфейса: {e}", exc_info=True)
        raise

async def run_bot_with_web():
    """Запуск бота и веб-интерфейса одновременно"""
    global bot_manager, web_app
    
    logger.info("🚀 Запуск полной системы (бот + веб)...")
    
    try:
        # Создаем менеджера бота
        bot_manager = TradingBotManager(config)
        
        # Связываем бота с API
        set_bot_manager(bot_manager)
        
        # Создаем веб-приложение
        web_app = create_web_app()
        
        # Настройки сервера
        config_uvicorn = uvicorn.Config(
            app=web_app,
            host="0.0.0.0", 
            port=8000,
            log_level="warning",
            access_log=False,
            ws_ping_interval=20,
            ws_ping_timeout=10
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        logger.info("🌐 Веб-сервер настроен")
        logger.info("🚀 Система готова к запуску")
        logger.info("📊 Дашборд: http://localhost:8000")
        logger.info("📖 API документация: http://localhost:8000/docs")
        
        # Запускаем сервер и ждем завершения
        await server.serve()
        
    except Exception as e:
        logger.error(f"💥 Ошибка системы: {e}", exc_info=True)
        raise
    finally:
        # Останавливаем бота при завершении
        if bot_manager:
            await bot_manager.stop()
            logger.info("✅ Торговый бот остановлен")

async def check_system():
    """Проверка системы"""
    logger.info("🔍 Проверка системы...")
    
    try:
        # Проверяем конфигурацию
        if not config.BYBIT_API_KEY or config.BYBIT_API_KEY == 'your_testnet_api_key_here':
            logger.error("❌ API ключи не настроены!")
            return False
        
        # Проверяем стратегии
        from src.strategies.factory import strategy_factory
        strategies = strategy_factory.list_strategies()
        logger.info(f"✅ Доступно стратегий: {len(strategies)}")
        for strategy in strategies:
            logger.info(f"  📊 {strategy}")
        
        # Проверяем базу данных
        try:
            await init_database()
            logger.info("✅ База данных доступна")
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")
            return False
        
        # Проверяем биржу (тестовое подключение)
        try:
            from src.exchange.bybit_client import BybitClient
            client = BybitClient(config)
            balance = await client.get_balance()
            logger.info(f"✅ Подключение к бирже: баланс {balance} USDT")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к бирже: {e}")
            return False
        
        logger.info("✅ Все проверки пройдены успешно!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Ошибка проверки системы: {e}")
        return False

def print_startup_banner():
    """Печать приветственного баннера"""
    banner = """
    
🚀 =============================================== 🚀
    
     CRYPTO TRADING BOT v3.0
     Полная система автоматической торговли
    
📊 Возможности:
   • Автоматическая торговля криптовалютами
   • 5 продвинутых торговых стратегий  
   • Веб-дашборд с полным управлением
   • Real-time мониторинг и аналитика
   • Риск-менеджмент и уведомления
   • Чистое логирование важных событий
    
🎯 Стратегии: Momentum, Multi-Indicator, Scalping,
              Safe Multi-Indicator, Conservative
    
🌐 Дашборд: http://localhost:8000
📖 API Docs: http://localhost:8000/docs
    
🚀 =============================================== 🚀
"""
    print(banner)

def main():
    """Главная функция"""
    global logger
    
    # Создаем необходимые директории
    for directory in ['logs', 'data/cache', 'data/backups']:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(
        description="🚀 Crypto Trading Bot v3.0 - Полная система автоматической торговли",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py              # Полная система (бот + веб-дашборд)
  python main.py --bot        # Только торговый бот
  python main.py --web        # Только веб-дашборд  
  python main.py --check      # Проверка системы
        """
    )
    
    parser.add_argument('--bot', action='store_true', help='Запустить только торгового бота')
    parser.add_argument('--web', action='store_true', help='Запустить только веб-дашборд')
    parser.add_argument('--check', action='store_true', help='Проверить систему')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Уровень логирования')
    
    args = parser.parse_args()
    
    # Инициализируем систему логирования
    init_logging_system(args.log_level)
    logger = get_clean_logger("main")
    
    # Печатаем баннер
    print_startup_banner()
    
    # Настраиваем обработчики сигналов
    setup_signal_handlers()
    
    # Проверка API ключей
    if not config.BYBIT_API_KEY or config.BYBIT_API_KEY == 'your_testnet_api_key_here':
        logger.error("❌ API ключи не настроены!")
        logger.info("📝 Настройте BYBIT_API_KEY в файле .env")
        sys.exit(1)
    
    if not config.BYBIT_API_SECRET or config.BYBIT_API_SECRET == 'your_testnet_secret_here':
        logger.error("❌ Secret ключ не настроен!")
        logger.info("📝 Настройте BYBIT_API_SECRET в файле .env")
        sys.exit(1)
    
    # Проверяем конфликты аргументов
    if sum([args.bot, args.web, args.check]) > 1:
        logger.error("❌ Можно указать только один режим работы")
        sys.exit(1)
    
    try:
        if args.check:
            # Проверка системы
            result = asyncio.run(check_system())
            sys.exit(0 if result else 1)
            
        elif args.bot:
            # Только торговый бот
            logger.info("🤖 Режим: Только торговый бот")
            asyncio.run(run_bot_only())
            
        elif args.web:
            # Только веб-интерфейс  
            logger.info("🌐 Режим: Только веб-дашборд")
            asyncio.run(run_web_only())
            
        else:
            # Полная система (по умолчанию)
            logger.info("🚀 Режим: Полная система")
            asyncio.run(run_bot_with_web())
            
    except KeyboardInterrupt:
        logger.info("⌨️ Прервано пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("🏁 Программа завершена")

if __name__ == "__main__":
    main()