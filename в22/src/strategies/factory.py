"""
Фабрика стратегий - ИСПРАВЛЕННАЯ ВЕРСИЯ
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/factory.py
"""
from typing import Dict, Type

# Импорт базового класса
from .base import BaseStrategy

# Импорт всех доступных стратегий
from .momentum import MomentumStrategy
from .multi_indicator import MultiIndicatorStrategy
from .scalping import ScalpingStrategy

# Условные импорты для дополнительных стратегий
try:
    from .safe_multi_indicator import SafeMultiIndicatorStrategy
    SAFE_MULTI_INDICATOR_AVAILABLE = True
except ImportError:
    SAFE_MULTI_INDICATOR_AVAILABLE = False
    print("⚠️ SafeMultiIndicatorStrategy не найден")

try:
    from .conservative import ConservativeStrategy
    CONSERVATIVE_AVAILABLE = True
except ImportError:
    CONSERVATIVE_AVAILABLE = False
    print("⚠️ ConservativeStrategy не найден")

class StrategyFactory:
    """Фабрика для создания торговых стратегий"""
    
    def __init__(self):
        # Базовые стратегии (всегда доступны)
        self._strategies: Dict[str, Type[BaseStrategy]] = {
            'momentum': MomentumStrategy,
            'multi_indicator': MultiIndicatorStrategy, 
            'scalping': ScalpingStrategy
        }
        
        # Добавляем дополнительные стратегии если они доступны
        if SAFE_MULTI_INDICATOR_AVAILABLE:
            self._strategies['safe_multi_indicator'] = SafeMultiIndicatorStrategy
            
        if CONSERVATIVE_AVAILABLE:
            self._strategies['conservative'] = ConservativeStrategy
    
    def create(self, name: str) -> BaseStrategy:
        """Создать стратегию по имени"""
        if name not in self._strategies:
            available = ', '.join(self._strategies.keys())
            raise ValueError(
                f"Неизвестная стратегия: '{name}'. "
                f"Доступные стратегии: {available}"
            )
        
        strategy_class = self._strategies[name]
        return strategy_class()
    
    def list_strategies(self) -> list:
        """Получить список доступных стратегий"""
        return list(self._strategies.keys())
    
    def register_strategy(self, name: str, strategy_class: Type[BaseStrategy]):
        """Зарегистрировать новую стратегию"""
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(
                f"Стратегия {strategy_class.__name__} должна наследовать BaseStrategy"
            )
        
        self._strategies[name] = strategy_class
        print(f"✅ Зарегистрирована стратегия: {name}")

# Создаем глобальный экземпляр фабрики
strategy_factory = StrategyFactory()

# Выводим информацию о загруженных стратегиях
print(f"📋 Загружено стратегий: {len(strategy_factory.list_strategies())}")
for strategy_name in strategy_factory.list_strategies():
    print(f"  ✅ {strategy_name}")
