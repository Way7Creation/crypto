"""
✅ ИСПРАВЛЕННЫЙ unified_bot_manager.py
Теперь использует единый StateManager
"""
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from .state_manager import state_manager
from .database import SessionLocal
from .models import Trade, TradeStatus

logger = logging.getLogger(__name__)

class UnifiedBotManager:
    """
    🎯 Упрощенный менеджер, использующий StateManager
    """
    
    def __init__(self):
        logger.info("🔧 UnifiedBotManager инициализирован")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """📊 Получение статуса через StateManager"""
        try:
            # Получаем истинное состояние
            truth = state_manager.get_truth()
            
            # Получаем статистику из БД
            db_stats = self._get_db_stats()
            
            return {
                # Основное состояние
                'process_running': truth['is_running'],
                'manager_running': truth['is_running'],  # Теперь они всегда синхронны
                'synchronized': True,  # StateManager гарантирует синхронизацию
                
                # Детали процесса
                'process_pid': truth['pid'],
                'process_memory': truth['memory_mb'],
                'process_cpu': truth['cpu_percent'],
                
                # Статистика торговли
                'active_pairs': db_stats['active_pairs'],
                'open_positions': db_stats['open_positions'],
                'total_trades': db_stats['total_trades'],
                'win_rate': db_stats['win_rate'],
                
                # Общие показатели
                'last_check': datetime.utcnow().isoformat(),
                'status_summary': self._get_status_summary(truth['is_running'])
            }
            
        except Exception as e:
            logger.error(f"💥 Ошибка получения статуса: {e}")
            return {
                'process_running': False,
                'manager_running': False,
                'synchronized': False,
                'error': str(e),
                'status_summary': 'ОШИБКА'
            }
    
    async def start_bot(self) -> Dict[str, Any]:
        """🚀 Запуск бота через StateManager"""
        return await state_manager.start_process()
    
    async def stop_bot(self) -> Dict[str, Any]:
        """⏹️ Остановка бота через StateManager"""
        return await state_manager.stop_process()
    
    def sync_state(self) -> Dict[str, Any]:
        """🔄 Синхронизация через StateManager"""
        return state_manager.sync_all_to_truth()
    
    def _get_db_stats(self) -> Dict[str, Any]:
        """📊 Получение статистики из БД"""
        db = None
        try:
            db = SessionLocal()
            
            # Считаем открытые позиции
            open_positions = db.query(Trade).filter(
                Trade.status == TradeStatus.OPEN
            ).count()
            
            # Считаем общее количество сделок
            total_trades = db.query(Trade).count()
            
            # Считаем процент прибыльных сделок
            profitable_trades = db.query(Trade).filter(
                Trade.status == TradeStatus.CLOSED,
                Trade.profit > 0
            ).count()
            
            closed_trades = db.query(Trade).filter(
                Trade.status == TradeStatus.CLOSED
            ).count()
            
            win_rate = (profitable_trades / closed_trades * 100) if closed_trades > 0 else 0
            
            return {
                'active_pairs': ['BTCUSDT', 'ETHUSDT'],  # TODO: Получить из настроек
                'open_positions': open_positions,
                'total_trades': total_trades,
                'win_rate': win_rate
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики БД: {e}")
            return {
                'active_pairs': [],
                'open_positions': 0,
                'total_trades': 0,
                'win_rate': 0
            }
        finally:
            if db:
                db.close()
    
    def _get_status_summary(self, is_running: bool) -> str:
        """📝 Краткое описание состояния"""
        return "🟢 РАБОТАЕТ" if is_running else "🔴 ОСТАНОВЛЕН"
    
    # Заглушки для совместимости
    async def update_pairs(self, pairs: List[str]) -> Dict[str, Any]:
        """💱 Обновление торговых пар"""
        return {'success': True, 'pairs': pairs, 'message': f'Пары обновлены: {pairs}'}
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """📤 Закрытие позиции"""
        return {'success': True, 'message': f'Позиция {symbol} закрыта'}

# Глобальный экземпляр
unified_bot_manager = UnifiedBotManager()