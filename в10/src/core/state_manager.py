"""
🎯 ИСПРАВЛЕННЫЙ StateManager
Убираем ошибку 'pmem' object has no attribute 'get'
"""
import logging
import psutil
import os
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class StateManager:
    """
    🔧 Исправленный менеджер состояния
    """
    
    def __init__(self):
        self.process_name = "trading_bot.py"
        self._last_check = None
        logger.info("🔧 StateManager инициализирован")
    
    def get_truth(self) -> Dict[str, Any]:
        """
        📊 Получение истинного состояния системы
        """
        try:
            bot_process = self._find_bot_process()
            
            if bot_process:
                return {
                    'is_running': True,
                    'pid': bot_process.pid,
                    'memory_mb': round(bot_process.memory_info().rss / 1024 / 1024, 2),
                    'cpu_percent': round(bot_process.cpu_percent(), 2),
                    'started_at': datetime.fromtimestamp(bot_process.create_time()),
                    'status': 'running'
                }
            else:
                return {
                    'is_running': False,
                    'pid': None,
                    'memory_mb': 0,
                    'cpu_percent': 0,
                    'started_at': None,
                    'status': 'stopped'
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения истинного состояния: {e}")
            return {
                'is_running': False,
                'pid': None,
                'memory_mb': 0,
                'cpu_percent': 0,
                'started_at': None,
                'status': 'error',
                'error': str(e)
            }
    
    def _find_bot_process(self):
        """
        🔍 ИСПРАВЛЕННЫЙ поиск процесса торгового бота
        """
        try:
            # ✅ ИСПРАВЛЕНИЕ: Правильная работа с psutil
            for proc in psutil.process_iter():
                try:
                    # Получаем информацию о процессе напрямую
                    process_name = proc.name()
                    process_cmdline = proc.cmdline()
                    
                    # Проверяем командную строку процесса
                    if process_cmdline:
                        for cmd in process_cmdline:
                            if self.process_name in cmd:
                                return proc
                    
                    # Альтернативная проверка по имени
                    if 'python' in process_name.lower():
                        if process_cmdline:
                            for cmd in process_cmdline:
                                if 'bot' in cmd.lower() or 'trading' in cmd.lower():
                                    return proc
                                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Процесс мог завершиться или нет доступа - пропускаем
                    continue
                except Exception as e:
                    # Логируем неожиданные ошибки, но продолжаем поиск
                    logger.debug(f"Ошибка при проверке процесса {proc.pid}: {e}")
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка поиска процесса: {e}")
            return None
    
    async def start_process(self) -> Dict[str, Any]:
        """
        🚀 Запуск торгового процесса
        """
        try:
            truth = self.get_truth()
            
            if truth['is_running']:
                return {
                    'success': True,
                    'message': f"✅ Процесс уже запущен (PID: {truth['pid']})",
                    'pid': truth['pid'],
                    'already_running': True,
                    'status': 'running'
                }
            
            # TODO: Здесь добавьте логику запуска вашего торгового бота
            # Пример:
            # import subprocess
            # import sys
            # subprocess.Popen([sys.executable, 'src/trading_bot.py'])
            
            logger.warning("⚠️ Функция запуска процесса не реализована")
            return {
                'success': False,
                'message': "⚠️ Функция запуска процесса не реализована. Добавьте логику в start_process()",
                'details': {
                    'info': 'Раскомментируйте и настройте subprocess.Popen()',
                    'example': 'subprocess.Popen([sys.executable, "your_trading_bot.py"])'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска процесса: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка запуска: {str(e)}",
                'error': str(e)
            }
    
    async def stop_process(self) -> Dict[str, Any]:
        """
        ⏹️ Остановка торгового процесса
        """
        try:
            bot_process = self._find_bot_process()
            
            if not bot_process:
                return {
                    'success': True,
                    'message': "✅ Процесс уже остановлен",
                    'was_running': False,
                    'status': 'stopped'
                }
            
            pid = bot_process.pid
            
            # Мягкая остановка
            bot_process.terminate()
            
            # Ждем завершения (максимум 10 секунд)
            try:
                bot_process.wait(timeout=10)
                message = f"✅ Процесс успешно остановлен (PID: {pid})"
                success = True
            except psutil.TimeoutExpired:
                # Принудительная остановка
                bot_process.kill()
                message = f"⚠️ Процесс принудительно остановлен (PID: {pid})"
                success = True
            
            return {
                'success': success,
                'message': message,
                'was_running': True,
                'status': 'stopped'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки процесса: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка остановки: {str(e)}",
                'error': str(e)
            }
    
    def sync_all_to_truth(self) -> Dict[str, Any]:
        """
        🔄 Синхронизация всех состояний с истинным
        """
        try:
            truth = self.get_truth()
            
            return {
                'success': True,
                'message': f"🔄 Синхронизация завершена. Статус: {'Запущен' if truth['is_running'] else 'Остановлен'}",
                'is_running': truth['is_running'],
                'target_state': truth,
                'changed': False,
                'changes': []
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации: {e}")
            return {
                'success': False,
                'error': f"Ошибка синхронизации: {str(e)}",
                'is_running': False
            }

# Глобальный экземпляр
state_manager = StateManager()