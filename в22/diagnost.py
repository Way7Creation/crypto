#!/usr/bin/env python3
"""
Диагностика проблем в Crypto Trading Bot
"""
import os
import sys
from pathlib import Path

def check_file_structure():
    """Проверяет структуру файлов"""
    print("📁 Проверка структуры проекта:")
    
    required_files = [
        "main.py",
        "src/__init__.py",
        "src/strategies/__init__.py", 
        "src/strategies/factory.py",
        "src/strategies/base.py",
        "src/strategies/momentum.py",
        "src/strategies/multi_indicator.py",
        "src/strategies/scalping.py",
        "src/bot/__init__.py",
        "src/bot/manager.py",
        "src/core/__init__.py",
        "src/core/config.py",
        "src/core/database.py",
        "src/core/models.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)
    
    return missing_files

def check_python_path():
    """Проверяет Python path"""
    print("\n🐍 Python информация:")
    print(f"  Python версия: {sys.version}")
    print(f"  Исполняемый файл: {sys.executable}")
    print(f"  Текущая директория: {os.getcwd()}")

def check_imports():
    """Проверяет критические импорты"""
    print("\n📦 Проверка импортов:")
    
    # Проверяем основные пакеты
    packages = ['pandas', 'numpy', 'fastapi', 'sqlalchemy', 'ccxt']
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
    
    # Проверяем наши модули
    print("\n📋 Проверка внутренних модулей:")
    
    try:
        sys.path.insert(0, '.')
        from src.core.config import config
        print("  ✅ src.core.config")
    except Exception as e:
        print(f"  ❌ src.core.config: {e}")
    
    try:
        from src.strategies.base import BaseStrategy
        print("  ✅ src.strategies.base")
    except Exception as e:
        print(f"  ❌ src.strategies.base: {e}")
    
    try:
        from src.strategies.factory import StrategyFactory
        print("  ✅ src.strategies.factory")
    except Exception as e:
        print(f"  ❌ src.strategies.factory: {e}")

def check_factory_content():
    """Проверяет содержимое factory.py"""
    print("\n🏭 Анализ factory.py:")
    
    factory_path = "src/strategies/factory.py"
    if not os.path.exists(factory_path):
        print("  ❌ Файл не существует")
        return
    
    with open(factory_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    if 'SafeMultiIndicatorStrategy' in content and 'from .safe_multi_indicator import' not in content:
        issues.append("SafeMultiIndicatorStrategy используется без импорта")
    
    if 'ConservativeStrategy' in content and 'from .conservative import' not in content:
        issues.append("ConservativeStrategy используется без импорта")
    
    if 'class StrategyFactory' not in content:
        issues.append("Класс StrategyFactory не найден")
    
    if issues:
        print("  ❌ Найдены проблемы:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✅ Базовая структура корректна")

def show_factory_fix():
    """Показывает как исправить factory.py"""
    print("\n🔧 Рекомендуемое исправление factory.py:")
    print("""
Замените содержимое src/strategies/factory.py на:

```python
from typing import Dict, Type
from .base import BaseStrategy
from .momentum import MomentumStrategy
from .multi_indicator import MultiIndicatorStrategy
from .scalping import ScalpingStrategy

class StrategyFactory:
    def __init__(self):
        self._strategies: Dict[str, Type[BaseStrategy]] = {
            'momentum': MomentumStrategy,
            'multi_indicator': MultiIndicatorStrategy, 
            'scalping': ScalpingStrategy
        }
    
    def create(self, name: str) -> BaseStrategy:
        if name not in self._strategies:
            available = ', '.join(self._strategies.keys())
            raise ValueError(f"Неизвестная стратегия: '{name}'. Доступные: {available}")
        return self._strategies[name]()
    
    def list_strategies(self) -> list:
        return list(self._strategies.keys())

strategy_factory = StrategyFactory()
```
""")

def main():
    """Главная функция диагностики"""
    print("🔍 ДИАГНОСТИКА CRYPTO TRADING BOT")
    print("=" * 50)
    
    # Проверки
    missing_files = check_file_structure()
    check_python_path()
    check_imports()
    check_factory_content()
    
    print("\n" + "=" * 50)
    print("📋 РЕЗЮМЕ:")
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {len(missing_files)}")
        for file in missing_files[:5]:  # Показываем первые 5
            print(f"  - {file}")
    
    # Основная проблема
    if os.path.exists("src/strategies/factory.py"):
        with open("src/strategies/factory.py", 'r') as f:
            content = f.read()
        
        if 'SafeMultiIndicatorStrategy' in content and 'try:' not in content:
            print("\n🎯 ОСНОВНАЯ ПРОБЛЕМА:")
            print("   factory.py пытается использовать SafeMultiIndicatorStrategy")
            print("   без условного импорта")
            print("\n💡 РЕШЕНИЕ:")
            print("   Выполните: python quick_fix.py")
    
    show_factory_fix()

if __name__ == "__main__":
    main()