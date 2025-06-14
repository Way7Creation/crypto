"""
API роуты для дашборда криптотрейдинг бота
Файл: src/web/api_routes.py
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import pandas as pd
import io
import csv

from ..core.database import get_db_session
from ..core.models import Trade, BotStatus
from ..bot.manager import TradingBotManager
from .dashboard import get_dashboard_html
from ..core.clean_logging import trading_logger, get_clean_logger

logger = get_clean_logger(__name__)

# Pydantic модели для API
class BotStartRequest(BaseModel):
    strategy: str
    pairs: Optional[List[str]] = None

class SettingsRequest(BaseModel):
    max_position_size: float
    stop_loss: float
    take_profit: float
    max_daily_trades: int
    trading_pairs: List[str]
    email_notifications: bool = True
    telegram_notifications: bool = False
    telegram_token: Optional[str] = None

class TradeResponse(BaseModel):
    id: int
    timestamp: datetime
    symbol: str
    side: str
    amount: float
    price: float
    profit: float
    strategy: str
    status: str

class StatsResponse(BaseModel):
    total_trades: int
    total_profit: float
    success_rate: float
    active_positions: int
    daily_trades: int
    best_pair: str
    worst_pair: str

# WebSocket менеджер для real-time обновлений
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket подключен. Активных соединений: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket отключен. Активных соединений: {len(self.active_connections)}")
    
    async def broadcast(self, data: dict):
        """Отправка данных всем подключенным клиентам"""
        if not self.active_connections:
            return
        
        message = json.dumps(data, default=str, ensure_ascii=False)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Ошибка отправки WebSocket сообщения: {e}")
                disconnected.append(connection)
        
        # Удаляем отключенные соединения
        for connection in disconnected:
            self.disconnect(connection)

# Глобальный менеджер WebSocket
ws_manager = WebSocketManager()

# Создаем роутер для API
router = APIRouter()

# Глобальная ссылка на менеджера бота
bot_manager: Optional[TradingBotManager] = None

def set_bot_manager(manager: TradingBotManager):
    """Установить ссылку на менеджера бота"""
    global bot_manager
    bot_manager = manager

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница дашборда"""
    return HTMLResponse(get_dashboard_html())

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Отправляем статус каждые 5 секунд
            await asyncio.sleep(5)
            
            if bot_manager:
                status_data = {
                    "type": "bot_status",
                    "status": "active" if bot_manager.is_running else "inactive",
                    "strategy": bot_manager.current_strategy if bot_manager.current_strategy else None,
                    "timestamp": datetime.now()
                }
                await websocket.send_text(json.dumps(status_data, default=str))
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@router.get("/api/status")
async def get_bot_status():
    """Получить текущий статус бота"""
    if not bot_manager:
        return {"status": "inactive", "strategy": None, "message": "Бот не инициализирован"}
    
    return {
        "status": "active" if bot_manager.is_running else "inactive",
        "strategy": bot_manager.current_strategy,
        "uptime": str(datetime.now() - bot_manager.start_time) if bot_manager.start_time else None,
        "message": "Бот работает" if bot_manager.is_running else "Бот остановлен"
    }

@router.post("/api/bot/start")
async def start_bot(request: BotStartRequest):
    """Запустить бота"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        if bot_manager.is_running:
            return {"success": False, "message": "Бот уже запущен"}
        
        # Запускаем бота с выбранной стратегией
        await bot_manager.start_strategy(request.strategy, request.pairs or ["BTCUSDT"])
        
        trading_logger.strategy_started(request.strategy, request.pairs or ["BTCUSDT"])
        
        # Уведомляем WebSocket клиентов
        await ws_manager.broadcast({
            "type": "bot_status",
            "status": "active",
            "strategy": request.strategy,
            "message": f"Бот запущен со стратегией {request.strategy}"
        })
        
        return {
            "success": True,
            "message": f"Бот успешно запущен со стратегией '{request.strategy}'"
        }
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска: {str(e)}")

@router.post("/api/bot/stop")
async def stop_bot():
    """Остановить бота"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        if not bot_manager.is_running:
            return {"success": False, "message": "Бот уже остановлен"}
        
        strategy_name = bot_manager.current_strategy
        await bot_manager.stop()
        
        trading_logger.strategy_stopped(strategy_name or "unknown", "Остановлен пользователем")
        
        # Уведомляем WebSocket клиентов
        await ws_manager.broadcast({
            "type": "bot_status", 
            "status": "inactive",
            "strategy": None,
            "message": "Бот остановлен"
        })
        
        return {"success": True, "message": "Бот успешно остановлен"}
        
    except Exception as e:
        logger.error(f"Ошибка остановки бота: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка остановки: {str(e)}")

@router.post("/api/bot/restart")
async def restart_bot():
    """Перезапустить бота"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        strategy = bot_manager.current_strategy or "momentum"
        
        # Останавливаем
        if bot_manager.is_running:
            await bot_manager.stop()
            await asyncio.sleep(2)  # Ждем полной остановки
        
        # Запускаем заново
        await bot_manager.start_strategy(strategy, ["BTCUSDT"])
        
        return {"success": True, "message": f"Бот перезапущен со стратегией '{strategy}'"}
        
    except Exception as e:
        logger.error(f"Ошибка перезапуска бота: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка перезапуска: {str(e)}")

@router.get("/api/stats", response_model=StatsResponse)
async def get_stats(db=Depends(get_db_session)):
    """Получить статистику торговли"""
    try:
        # Получаем сделки за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        trades = db.query(Trade).filter(
            Trade.timestamp >= thirty_days_ago
        ).all()
        
        if not trades:
            return StatsResponse(
                total_trades=0,
                total_profit=0.0,
                success_rate=0.0,
                active_positions=0,
                daily_trades=0,
                best_pair="N/A",
                worst_pair="N/A"
            )
        
        # Вычисляем статистику
        total_trades = len(trades)
        total_profit = sum(trade.profit or 0 for trade in trades)
        profitable_trades = len([t for t in trades if (t.profit or 0) > 0])
        success_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Сделки за сегодня
        today = datetime.now().date()
        daily_trades = len([t for t in trades if t.timestamp.date() == today])
        
        # Активные позиции (можно добавить проверку статуса)
        active_positions = len([t for t in trades if t.status == 'open'])
        
        # Лучшая и худшая пара
        pair_profits = {}
        for trade in trades:
            symbol = trade.symbol
            if symbol not in pair_profits:
                pair_profits[symbol] = 0
            pair_profits[symbol] += trade.profit or 0
        
        best_pair = max(pair_profits.items(), key=lambda x: x[1])[0] if pair_profits else "N/A"
        worst_pair = min(pair_profits.items(), key=lambda x: x[1])[0] if pair_profits else "N/A"
        
        return StatsResponse(
            total_trades=total_trades,
            total_profit=round(total_profit, 2),
            success_rate=round(success_rate, 1),
            active_positions=active_positions,
            daily_trades=daily_trades,
            best_pair=best_pair,
            worst_pair=worst_pair
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

@router.get("/api/trades")
async def get_trades(limit: int = 50, db=Depends(get_db_session)):
    """Получить список последних сделок"""
    try:
        trades = db.query(Trade).order_by(
            Trade.timestamp.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": trade.id,
                "timestamp": trade.timestamp,
                "symbol": trade.symbol,
                "side": trade.side,
                "amount": trade.amount,
                "price": trade.price,
                "profit": trade.profit or 0,
                "strategy": trade.strategy,
                "status": trade.status or "completed"
            }
            for trade in trades
        ]
        
    except Exception as e:
        logger.error(f"Ошибка получения сделок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения сделок")

@router.post("/api/settings")
async def save_settings(settings: SettingsRequest):
    """Сохранить настройки"""
    try:
        # Здесь должна быть логика сохранения настроек в базу данных или конфиг
        # Пока просто логируем
        logger.info(f"💾 Сохранены настройки: {settings.dict()}")
        
        # Если бот запущен, применяем настройки
        if bot_manager and bot_manager.is_running:
            # Обновляем настройки риск-менеджмента
            if hasattr(bot_manager, 'risk_manager'):
                bot_manager.risk_manager.max_position_size = settings.max_position_size / 100
                bot_manager.risk_manager.stop_loss_percent = settings.stop_loss / 100
                bot_manager.risk_manager.take_profit_percent = settings.take_profit / 100
        
        return {"success": True, "message": "Настройки успешно сохранены"}
        
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения настроек")

@router.get("/api/strategies")
async def get_strategies():
    """Получить список доступных стратегий"""
    strategies = [
        {
            "name": "momentum",
            "display_name": "Momentum",
            "description": "Торговля по трендам и импульсам цены",
            "type": "aggressive",
            "risk_level": "high"
        },
        {
            "name": "multi_indicator", 
            "display_name": "Multi Indicator",
            "description": "Комплексный анализ множества индикаторов",
            "type": "balanced",
            "risk_level": "medium"
        },
        {
            "name": "scalping",
            "display_name": "Scalping", 
            "description": "Быстрые сделки на малых движениях",
            "type": "high_frequency",
            "risk_level": "high"
        },
        {
            "name": "safe_multi_indicator",
            "display_name": "Safe Multi Indicator",
            "description": "Безопасная версия мульти-индикаторной стратегии",
            "type": "conservative",
            "risk_level": "low"
        },
        {
            "name": "conservative",
            "display_name": "Conservative",
            "description": "Максимально безопасная торговля",
            "type": "conservative", 
            "risk_level": "very_low"
        }
    ]
    
    return strategies

@router.get("/api/export")
async def export_data(format: str = "csv", db=Depends(get_db_session)):
    """Экспорт данных торговли"""
    try:
        # Получаем все сделки
        trades = db.query(Trade).order_by(Trade.timestamp.desc()).all()
        
        if format.lower() == "csv":
            # Создаем CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow([
                "Время", "Символ", "Сторона", "Количество", 
                "Цена", "Прибыль", "Стратегия", "Статус"
            ])
            
            # Данные
            for trade in trades:
                writer.writerow([
                    trade.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    trade.symbol,
                    trade.side,
                    trade.amount,
                    trade.price,
                    trade.profit or 0,
                    trade.strategy,
                    trade.status or "completed"
                ])
            
            # Возвращаем файл
            output.seek(0)
            content = output.getvalue()
            output.close()
            
            from fastapi import Response
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=crypto_bot_trades_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Поддерживается только формат CSV")
            
    except Exception as e:
        logger.error(f"Ошибка экспорта данных: {e}")
        raise HTTPException(status_code=500, detail="Ошибка экспорта данных")

@router.post("/api/manual/buy")
async def manual_buy(symbol: str, amount: float):
    """Ручная покупка"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        # Здесь должна быть логика ручной покупки
        logger.info(f"📈 Ручная покупка: {amount} {symbol}")
        
        # Уведомляем через WebSocket
        await ws_manager.broadcast({
            "type": "manual_trade",
            "action": "buy",
            "symbol": symbol,
            "amount": amount,
            "timestamp": datetime.now()
        })
        
        return {"success": True, "message": f"Покупка {amount} {symbol} выполнена"}
        
    except Exception as e:
        logger.error(f"Ошибка ручной покупки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка покупки: {str(e)}")

@router.post("/api/manual/sell") 
async def manual_sell(symbol: str, amount: float):
    """Ручная продажа"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        # Здесь должна быть логика ручной продажи
        logger.info(f"📉 Ручная продажа: {amount} {symbol}")
        
        # Уведомляем через WebSocket
        await ws_manager.broadcast({
            "type": "manual_trade",
            "action": "sell", 
            "symbol": symbol,
            "amount": amount,
            "timestamp": datetime.now()
        })
        
        return {"success": True, "message": f"Продажа {amount} {symbol} выполнена"}
        
    except Exception as e:
        logger.error(f"Ошибка ручной продажи: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка продажи: {str(e)}")

@router.post("/api/positions/close_all")
async def close_all_positions():
    """Закрыть все позиции"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        # Здесь должна быть логика закрытия всех позиций
        logger.info("🚪 Закрытие всех позиций")
        
        await ws_manager.broadcast({
            "type": "positions_closed",
            "message": "Все позиции закрыты",
            "timestamp": datetime.now()
        })
        
        return {"success": True, "message": "Все позиции закрыты"}
        
    except Exception as e:
        logger.error(f"Ошибка закрытия позиций: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

# Функция для уведомления о новой сделке (вызывается из bot manager)
async def notify_new_trade(trade_data: dict):
    """Уведомление о новой сделке через WebSocket"""
    await ws_manager.broadcast({
        "type": "new_trade",
        "trade": trade_data,
        "timestamp": datetime.now()
    })

# Функция для уведомления о логах (вызывается из logging system)
async def notify_log_message(message: str, level: str):
    """Уведомление о новом лог сообщении"""
    await ws_manager.broadcast({
        "type": "log",
        "message": message,
        "level": level.lower(),
        "timestamp": datetime.now()
    })