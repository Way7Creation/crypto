"""
Фабрика стратегий
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/factory.py
"""
from typing import Dict, Type
from .base import BaseStrategy
from .momentum import MomentumStrategy
from .multi_indicator import MultiIndicatorStrategy
from .scalping import ScalpingStrategy

class StrategyFactory:
    """Фабрика для создания стратегий"""
    
    _strategies: Dict[str, Type[BaseStrategy]] = {
        'momentum': MomentumStrategy,
        'multi_indicator': MultiIndicatorStrategy,
        'scalping': ScalpingStrategy,
        'safe_multi_indicator': SafeMultiIndicatorStrategy,
        'conservative': ConservativeStrategy
    }
    
    @classmethod
    def create(cls, name: str) -> BaseStrategy:
        """Создать стратегию по имени"""
        strategy_class = cls._strategies.get(name)
        if not strategy_class:
            raise ValueError(f"Неизвестная стратегия: {name}")
        return strategy_class()
    
    @classmethod
    def list_strategies(cls) -> list:
        """Список доступных стратегий"""
        return list(cls._strategies.keys())
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[BaseStrategy]):
        """Регистрация новой стратегии"""
        cls._strategies[name] = strategy_class
# В конец файла src/strategies/factory.py добавить:

# Импортируем новые стратегии
from .safe_multi_indicator import SafeMultiIndicatorStrategy
from .conservative import ConservativeStrategy

# Регистрируем новые стратегии
StrategyFactory.register_strategy('safe_multi_indicator', SafeMultiIndicatorStrategy)
StrategyFactory.register_strategy('conservative', ConservativeStrategy)
