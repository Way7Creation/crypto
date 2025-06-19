#!/usr/bin/env python3
"""
Модуль исправления компонентов - временное решение для совместимости
Файл: src/core/component_fix.py

ВАЖНО: Этот файл создан для исправления ошибки импорта.
В будущем рекомендуется полностью перейти на component_system.py
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from .component_system import component_manager, ComponentStatus

logger = logging.getLogger(__name__)

def patch_component_manager():
    """
    Функция патча для совместимости со старым кодом
    
    Эта функция вызывается из manager.py для инициализации
    системы компонентов.
    """
    logger.info("🔧 Применяем патч для системы компонентов...")
    
    try:
        # Проверяем что система компонентов доступна
        if component_manager is None:
            logger.error("❌ ComponentManager не доступен")
            return False
            
        logger.info("✅ Система компонентов готова к использованию")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка патча компонентов: {e}")
        return False

def get_component_status() -> Dict[str, Any]:
    """
    Получение статуса всех компонентов
    
    Returns:
        Dict: Статус компонентов
    """
    try:
        return component_manager.get_status()
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса: {e}")
        return {}

def initialize_component_system() -> bool:
    """
    Инициализация системы компонентов
    
    Returns:
        bool: Успешность инициализации
    """
    try:
        logger.info("🚀 Инициализируем систему компонентов...")
        
        # Применяем патч
        patch_result = patch_component_manager()
        
        if patch_result:
            logger.info("✅ Система компонентов успешно инициализирована")
            return True
        else:
            logger.error("❌ Не удалось инициализировать систему компонентов")
            return False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка инициализации: {e}")
        return False

# Функции для обратной совместимости
def ensure_component_ready(component_name: str) -> bool:
    """Проверка готовности компонента"""
    try:
        return component_manager.is_ready(component_name)
    except:
        return False

def get_component_instance(component_name: str) -> Optional[Any]:
    """Получение экземпляра компонента"""
    try:
        return component_manager.get_component(component_name)
    except:
        return None

# Экспорт основных функций
__all__ = [
    'patch_component_manager',
    'get_component_status', 
    'initialize_component_system',
    'ensure_component_ready',
    'get_component_instance'
]