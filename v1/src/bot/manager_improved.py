# ========================================
# ФАЙЛ: src/bot/manager_improved.py
# Улучшенная версия BotManager с надежной инициализацией
# ========================================

"""
Улучшенный менеджер торгового бота с надежной системой инициализации
Файл: src/bot/manager_improved.py
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Импорт базовой системы
from ..core.component_system import component_manager, ComponentStatus

logger = logging.getLogger(__name__)

class ImprovedBotManager:
    """
    Улучшенный менеджер бота с надежной инициализацией
    
    Основные улучшения:
    - Система управления зависимостями
    - Graceful degradation при ошибках
    - Централизованное управление компонентами
    - Возможность перезапуска отдельных модулей
    """
    
    def __init__(self):
        """Инициализация менеджера"""
        self.status = "stopped"
        self.start_time = None
        self.active_pairs = []
        self.positions = {}
        self.cycles_count = 0
        self.trades_today = 0
        
        # Регистрируем все компоненты
        self._register_components()
        
        logger.info("🤖 Улучшенный BotManager инициализирован")
    
    def _register_components(self):
        """
        Регистрация всех компонентов системы с указанием зависимостей
        """
        logger.info("📝 Регистрируем компоненты системы...")
        
        # 1. База данных (критичный, без зависимостей)
        component_manager.register_component(
            name="database",
            initializer=self._init_database,
            dependencies=[],
            is_critical=True,
            max_retries=3
        )
        
        # 2. Конфигурация (критичный, без зависимостей)
        component_manager.register_component(
            name="config",
            initializer=self._init_config,
            dependencies=[],
            is_critical=True,
            max_retries=1
        )
        
        # 3. Exchange клиент (критичный, зависит от конфигурации)
        component_manager.register_component(
            name="exchange",
            initializer=self._init_exchange,
            dependencies=["config"],
            is_critical=True,
            max_retries=5
        )
        
        # 4. Логирование (не критичный, зависит от конфигурации)
        component_manager.register_component(
            name="logging",
            initializer=self._init_logging,
            dependencies=["config"],
            is_critical=False,
            max_retries=2
        )
        
        # 5. Уведомления (не критичный, зависит от конфигурации)
        component_manager.register_component(
            name="notifications",
            initializer=self._init_notifications,
            dependencies=["config"],
            is_critical=False,
            max_retries=3
        )
        
        # 6. Market Analyzer (критичный, зависит от Exchange)
        component_manager.register_component(
            name="market_analyzer",
            initializer=self._init_market_analyzer,
            dependencies=["exchange"],
            is_critical=True,
            max_retries=3
        )
        
        # 7. Risk Manager (критичный, зависит от конфигурации)
        component_manager.register_component(
            name="risk_manager",
            initializer=self._init_risk_manager,
            dependencies=["config"],
            is_critical=True,
            max_retries=2
        )
        
        # 8. Trader (критичный, зависит от Exchange и Risk Manager)
        component_manager.register_component(
            name="trader",
            initializer=self._init_trader,
            dependencies=["exchange", "risk_manager"],
            is_critical=True,
            max_retries=3
        )
        
        # 9. Strategy Factory (критичный, зависит от конфигурации)
        component_manager.register_component(
            name="strategy_factory",
            initializer=self._init_strategy_factory,
            dependencies=["config"],
            is_critical=True,
            max_retries=2
        )
        
        # 10. ML компоненты (не критичные, зависят от базы данных)
        component_manager.register_component(
            name="ml_components",
            initializer=self._init_ml_components,
            dependencies=["database", "config"],
            is_critical=False,
            max_retries=2
        )
        
        logger.info("✅ Все компоненты зарегистрированы")
    
    # =========================================================================
    # === ИНИЦИАЛИЗАТОРЫ КОМПОНЕНТОВ ===
    # =========================================================================
    
    async def _init_database(self):
        """Инициализация базы данных"""
        logger.info("💾 Инициализируем базу данных...")
        
        try:
            from ..core.database import SessionLocal
            from sqlalchemy import text
            
            # Проверяем подключение
            db = SessionLocal()
            try:
                result = db.execute(text("SELECT 1")).scalar()
                if result != 1:
                    raise Exception("Неожиданный результат запроса")
                
                logger.info("✅ База данных доступна")
                return db
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    def _init_config(self):
        """Инициализация конфигурации"""
        logger.info("⚙️ Инициализируем конфигурацию...")
        
        try:
            from ..core.config import config
            
            # Проверяем критичные настройки
            if not hasattr(config, 'BYBIT_API_KEY') or not config.BYBIT_API_KEY:
                raise ValueError("API ключ не настроен")
            
            if not hasattr(config, 'BYBIT_API_SECRET') or not config.BYBIT_API_SECRET:
                raise ValueError("Secret ключ не настроен")
            
            logger.info("✅ Конфигурация загружена")
            return config
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации конфигурации: {e}")
            raise
    
    async def _init_exchange(self):
        """Инициализация Exchange клиента"""
        logger.info("🌐 Инициализируем Exchange клиент...")
        
        try:
            from ..exchange.client import get_exchange_client
            
            # Получаем клиент
            exchange = get_exchange_client()
            
            # Тестируем подключение
            connection_test = await exchange.test_connection()
            if not connection_test:
                raise Exception("Не удалось подключиться к бирже")
            
            logger.info("✅ Exchange клиент готов")
            return exchange
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Exchange: {e}")
            raise
    
    def _init_logging(self):
        """Инициализация системы логирования"""
        logger.info("📝 Инициализируем систему логирования...")
        
        try:
            # Пытаемся инициализировать SmartLogger
            try:
                from ..logging.smart_logger import SmartLogger
                smart_logger = SmartLogger(__name__)
                logger.info("✅ SmartLogger инициализирован")
                return smart_logger
            except ImportError:
                # Используем стандартный логгер
                logger.info("✅ Используем стандартное логирование")
                return logging.getLogger(__name__)
                
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации логирования: {e}")
            # Возвращаем базовый логгер
            return logging.getLogger(__name__)
    
    def _init_notifications(self):
        """Инициализация уведомлений"""
        logger.info("📱 Инициализируем уведомления...")
        
        try:
            from ..notifications.telegram import telegram_notifier
            
            # Проверяем настройки Telegram
            config = component_manager.get_component("config")
            if hasattr(config, 'TELEGRAM_BOT_TOKEN') and config.TELEGRAM_BOT_TOKEN:
                logger.info("✅ Telegram уведомления готовы")
                return telegram_notifier
            else:
                logger.warning("⚠️ Telegram не настроен, уведомления отключены")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации уведомлений: {e}")
            return None
    
    async def _init_market_analyzer(self):
        """Инициализация анализатора рынка"""
        logger.info("📊 Инициализируем Market Analyzer...")
        
        try:
            from ..analysis.market_analyzer import MarketAnalyzer
            
            # Создаем анализатор
            analyzer = MarketAnalyzer()
            
            logger.info("✅ Market Analyzer готов")
            return analyzer
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Market Analyzer: {e}")
            raise
    
    def _init_risk_manager(self):
        """Инициализация риск-менеджера"""
        logger.info("⚖️ Инициализируем Risk Manager...")
        
        try:
            # Пытаемся загрузить основной риск-менеджер
            try:
                from ..bot.risk_manager import RiskManager
                risk_manager = RiskManager()
                logger.info("✅ Основной Risk Manager инициализирован")
                return risk_manager
            except ImportError:
                # Используем простой риск-менеджер
                from ..risk.simple_risk_manager import SimpleRiskManager
                risk_manager = SimpleRiskManager()
                logger.info("✅ Простой Risk Manager инициализирован")
                return risk_manager
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Risk Manager: {e}")
            raise
    
    async def _init_trader(self):
        """Инициализация трейдера"""
        logger.info("💼 Инициализируем Trader...")
        
        try:
            from ..bot.trader import Trader
            
            # Получаем Exchange из компонентов
            exchange = component_manager.get_component("exchange")
            if not exchange:
                raise Exception("Exchange клиент не доступен")
            
            # Создаем трейдера с Exchange
            trader = Trader(exchange=exchange)
            
            logger.info("✅ Trader готов")
            return trader
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Trader: {e}")
            raise
    
    def _init_strategy_factory(self):
        """Инициализация фабрики стратегий"""
        logger.info("🏭 Инициализируем Strategy Factory...")
        
        try:
            from ..strategies import strategy_factory
            
            logger.info("✅ Strategy Factory готова")
            return strategy_factory
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Strategy Factory: {e}")
            raise
    
    def _init_ml_components(self):
        """Инициализация ML компонентов"""
        logger.info("🤖 Инициализируем ML компоненты...")
        
        ml_components = {}
        
        # Strategy Selector (не критичный)
        try:
            from ..strategies.auto_strategy_selector import auto_strategy_selector
            ml_components['strategy_selector'] = auto_strategy_selector
            logger.info("✅ Strategy Selector готов")
        except ImportError:
            logger.info("📦 Strategy Selector недоступен (не критично)")
        
        # Feature Engineering (не критичный)
        try:
            from ..ml.features import FeatureEngineering
            if FeatureEngineering:
                ml_components['feature_engineering'] = FeatureEngineering()
                logger.info("✅ Feature Engineering готов")
        except ImportError:
            logger.info("📦 Feature Engineering недоступен (не критично)")
        
        # ML Models (не критичные)
        try:
            from ..ml.models import DirectionClassifier, PriceLevelRegressor
            if DirectionClassifier:
                ml_components['classifier'] = DirectionClassifier()
            if PriceLevelRegressor:
                ml_components['regressor'] = PriceLevelRegressor()
            logger.info("✅ ML модели готовы")
        except ImportError:
            logger.info("📦 ML модели недоступны (не критично)")
        
        return ml_components
    
    # =========================================================================
    # === ПУБЛИЧНЫЕ МЕТОДЫ ===
    # =========================================================================
    
    async def initialize(self) -> bool:
        """
        Инициализация всей системы
        
        Returns:
            bool: Успешность инициализации критичных компонентов
        """
        logger.info("🚀 Начинаем инициализацию системы...")
        
        try:
            # Инициализируем все компоненты
            results = await component_manager.initialize_all()
            
            # Проверяем критичные компоненты
            critical_components = ['database', 'config', 'exchange', 'market_analyzer', 'risk_manager', 'trader', 'strategy_factory']
            critical_failed = []
            
            for comp in critical_components:
                if not results.get(comp, False):
                    critical_failed.append(comp)
            
            if critical_failed:
                logger.error(f"❌ Критичные компоненты не инициализированы: {critical_failed}")
                return False
            
            logger.info("✅ Система успешно инициализирована")
            return True
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка инициализации: {e}")
            return False
    
    def get_component(self, name: str) -> Any:
        """Получение компонента"""
        return component_manager.get_component(name)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Получение статуса всей системы
        
        Returns:
            Dict: Полная информация о статусе системы
        """
        component_status = component_manager.get_status()
        
        # Подсчитываем статистику
        total = len(component_status)
        ready = sum(1 for comp in component_status.values() if comp['status'] == 'ready')
        failed = sum(1 for comp in component_status.values() if comp['status'] == 'failed')
        critical_failed = sum(1 for comp in component_status.values() 
                             if comp['status'] == 'failed' and comp['is_critical'])
        
        return {
            'overall_status': 'healthy' if critical_failed == 0 else 'degraded' if ready > failed else 'unhealthy',
            'components': component_status,
            'statistics': {
                'total_components': total,
                'ready_components': ready,
                'failed_components': failed,
                'critical_failed': critical_failed
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def restart_component(self, name: str) -> bool:
        """
        Перезапуск компонента
        
        Args:
            name: Имя компонента
            
        Returns:
            bool: Успешность перезапуска
        """
        return await component_manager.restart_component(name)
    
    async def graceful_shutdown(self):
        """Graceful завершение работы"""
        logger.info("🛑 Начинаем graceful shutdown...")
        
        # Здесь можно добавить логику корректного завершения
        # например, закрытие позиций, сохранение состояния и т.д.
        
        logger.info("✅ Graceful shutdown завершен")

# Пример интеграции с существующим BotManager
def integrate_with_existing_manager():
    """
    Функция для интеграции улучшенной системы с существующим BotManager
    """
    # Добавить в существующий _init_components метод BotManager:
    
    improved_init_code = '''
    def _init_components(self):
        """Улучшенная инициализация компонентов"""
        
        # Создаем улучшенный менеджер
        self.improved_manager = ImprovedBotManager()
        
        # Инициализируем все компоненты
        success = asyncio.run(self.improved_manager.initialize())
        
        if success:
            # Получаем инициализированные компоненты
            self.exchange = self.improved_manager.get_component("exchange")
            self.analyzer = self.improved_manager.get_component("market_analyzer")
            self.trader = self.improved_manager.get_component("trader")
            self.risk_manager = self.improved_manager.get_component("risk_manager")
            self.notifier = self.improved_manager.get_component("notifications")
            self.strategy_factory = self.improved_manager.get_component("strategy_factory")
            
            logger.info("✅ Все компоненты инициализированы через улучшенную систему")
        else:
            logger.error("❌ Ошибка инициализации через улучшенную систему")
            # Откат к старой системе инициализации
            self._init_components_fallback()
    '''
    
    return improved_init_code