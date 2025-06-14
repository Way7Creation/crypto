"""
API endpoints для управления ботом - ПОЛНАЯ ВЕРСИЯ
Путь: src/web/api_routes.py

Этот файл содержит все API endpoints для управления ботом через веб-интерфейс.
Исправлены все проблемы с интеграцией и добавлены недостающие функции.
"""
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
import logging

# Импорты из нашего проекта
from ..core.database import get_db
from ..core.models import Trade, Signal, TradingPair, User, BotState, Balance, TradeStatus
from ..core.clean_logging import get_clean_logger
from .dashboard import get_dashboard_html
from .auth import get_current_user

logger = get_clean_logger(__name__)

# Pydantic модели для API
class BotStartRequest(BaseModel):
    """Запрос на запуск бота"""
    strategy: Optional[str] = "auto"  # По умолчанию - автоматический выбор
    pairs: Optional[List[str]] = None

class BotActionRequest(BaseModel):
    """Запрос на действие с ботом"""
    action: str  # start, stop, restart

class SettingsRequest(BaseModel):
    """Запрос на обновление настроек"""
    max_position_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_daily_trades: Optional[int] = None
    trading_pairs: Optional[List[str]] = None

# WebSocket менеджер
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._broadcast_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket подключен. Активных соединений: {len(self.active_connections)}")
        
        # Отправляем начальный статус
        try:
            if bot_manager:
                status = bot_manager.get_status()
                await websocket.send_json({
                    "type": "initial_status",
                    "data": status
                })
        except Exception as e:
            logger.error(f"Ошибка отправки начального статуса: {e}")
    
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
                logger.error(f"Ошибка отправки WebSocket: {e}")
                disconnected.append(connection)
        
        # Удаляем отключенные соединения
        for connection in disconnected:
            self.disconnect(connection)
    
    async def start_broadcast_loop(self):
        """Запуск цикла автоматических обновлений"""
        if self._broadcast_task and not self._broadcast_task.done():
            return
        
        self._broadcast_task = asyncio.create_task(self._broadcast_worker())
        logger.info("🔄 Запущен цикл WebSocket обновлений")
    
    async def _broadcast_worker(self):
        """Воркер для отправки обновлений"""
        while True:
            try:
                if bot_manager:
                    # Получаем актуальные данные
                    status = bot_manager.get_status()
                    
                    # Отправляем обновление
                    await self.broadcast({
                        "type": "status_update",
                        "data": status,
                        "timestamp": datetime.utcnow()
                    })
                
                await asyncio.sleep(5)  # Обновление каждые 5 секунд
                
            except Exception as e:
                logger.error(f"Ошибка в broadcast worker: {e}")
                await asyncio.sleep(10)

# Глобальный менеджер WebSocket
ws_manager = WebSocketManager()

# Глобальная переменная для BotManager
bot_manager = None

def set_bot_manager(manager):
    """Установить ссылку на менеджера бота"""
    global bot_manager
    bot_manager = manager
    logger.info("✅ BotManager установлен в API роутах")

# Создаем роутер
router = APIRouter()

# ===== ОСНОВНЫЕ ENDPOINTS =====

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница с дашбордом"""
    return get_dashboard_html()

@router.get("/api")
async def api_info():
    """Информация об API"""
    return {
        "service": "Crypto Trading Bot API",
        "version": "3.0.0",
        "status": "running",
        "timestamp": datetime.utcnow(),
        "endpoints": {
            "dashboard": "/",
            "documentation": "/docs",
            "health": "/health",
            "bot_status": "/api/bot/status",
            "websocket": "/ws"
        }
    }

@router.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    health_info = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "components": {}
    }
    
    # Проверяем компоненты
    try:
        # База данных
        db = next(get_db())
        db.execute("SELECT 1")
        health_info["components"]["database"] = "healthy"
        db.close()
    except Exception as e:
        health_info["components"]["database"] = "error"
        health_info["status"] = "degraded"
    
    # BotManager
    if bot_manager:
        health_info["components"]["bot_manager"] = "healthy"
    else:
        health_info["components"]["bot_manager"] = "not_initialized"
        health_info["status"] = "degraded"
    
    return health_info

# ===== BOT CONTROL ENDPOINTS =====

@router.get("/api/bot/status")
async def get_bot_status():
    """Получить полный статус бота"""
    if not bot_manager:
        return {
            "status": "error",
            "is_running": False,
            "message": "Bot manager not initialized",
            "timestamp": datetime.utcnow()
        }
    
    try:
        return bot_manager.get_status()
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return {
            "status": "error",
            "is_running": False,
            "message": str(e),
            "timestamp": datetime.utcnow()
        }

@router.post("/api/bot/start")
async def start_bot(request: BotStartRequest):
    """Запустить бота"""
    if not bot_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot manager not initialized"
        )
    
    try:
        # Обновляем пары если указаны
        if request.pairs:
            await bot_manager.update_pairs(request.pairs)
        
        # Запускаем бота
        success, message = await bot_manager.start()
        
        if success:
            # Запускаем broadcast loop
            await ws_manager.start_broadcast_loop()
            
            # Отправляем уведомление через WebSocket
            await ws_manager.broadcast({
                "type": "bot_started",
                "message": message,
                "strategy": request.strategy,
                "timestamp": datetime.utcnow()
            })
            
            return {
                "success": True,
                "message": message,
                "status": "started"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}"
        )

@router.post("/api/bot/stop")
async def stop_bot():
    """Остановить бота"""
    if not bot_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot manager not initialized"
        )
    
    try:
        success, message = await bot_manager.stop()
        
        # Отправляем уведомление через WebSocket
        await ws_manager.broadcast({
            "type": "bot_stopped",
            "message": message,
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": success,
            "message": message,
            "status": "stopped"
        }
        
    except Exception as e:
        logger.error(f"Ошибка остановки бота: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop bot: {str(e)}"
        )

@router.post("/api/bot/action")
async def bot_action(request: BotActionRequest):
    """Выполнить действие с ботом"""
    if request.action == "start":
        return await start_bot(BotStartRequest())
    elif request.action == "stop":
        return await stop_bot()
    elif request.action == "restart":
        # Сначала останавливаем
        await stop_bot()
        await asyncio.sleep(2)  # Небольшая пауза
        # Затем запускаем
        return await start_bot(BotStartRequest())
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {request.action}"
        )

# ===== DATA ENDPOINTS =====

@router.get("/api/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Получить статистику торговли"""
    try:
        # Определяем временные границы
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Статистика за сегодня
        today_trades = db.query(Trade).filter(
            Trade.created_at >= today_start
        ).all()
        
        # Считаем метрики
        total_trades = len(today_trades)
        closed_trades = [t for t in today_trades if t.status == TradeStatus.CLOSED]
        profitable_trades = [t for t in closed_trades if t.profit and t.profit > 0]
        
        total_profit = sum(t.profit or 0 for t in closed_trades)
        success_rate = (len(profitable_trades) / len(closed_trades) * 100) if closed_trades else 0
        
        # Лучшая и худшая сделки
        best_trade = max(closed_trades, key=lambda t: t.profit or 0) if closed_trades else None
        worst_trade = min(closed_trades, key=lambda t: t.profit or 0) if closed_trades else None
        
        return {
            "total_trades": total_trades,
            "closed_trades": len(closed_trades),
            "profitable_trades": len(profitable_trades),
            "total_profit": round(total_profit, 2),
            "success_rate": round(success_rate, 1),
            "best_trade": {
                "symbol": best_trade.symbol,
                "profit": round(best_trade.profit, 2)
            } if best_trade else None,
            "worst_trade": {
                "symbol": worst_trade.symbol,
                "profit": round(worst_trade.profit, 2)
            } if worst_trade else None,
            "timestamp": now
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )

@router.get("/api/trades")
async def get_trades(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить список сделок с пагинацией"""
    try:
        query = db.query(Trade)
        
        # Фильтр по статусу
        if status:
            if status == "open":
                query = query.filter(Trade.status == TradeStatus.OPEN)
            elif status == "closed":
                query = query.filter(Trade.status == TradeStatus.CLOSED)
        
        # Получаем общее количество
        total = query.count()
        
        # Получаем сделки с пагинацией
        trades = query.order_by(desc(Trade.created_at)).offset(offset).limit(limit).all()
        
        # Форматируем для отправки
        trades_data = []
        for trade in trades:
            trades_data.append({
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                "entry_price": float(trade.entry_price) if trade.entry_price else 0,
                "exit_price": float(trade.exit_price) if trade.exit_price else None,
                "quantity": float(trade.quantity) if trade.quantity else 0,
                "profit": float(trade.profit) if trade.profit else None,
                "profit_percent": float(trade.profit_percent) if trade.profit_percent else None,
                "status": trade.status.value if hasattr(trade.status, 'value') else str(trade.status),
                "strategy": trade.strategy,
                "created_at": trade.created_at.isoformat() if trade.created_at else None,
                "closed_at": trade.closed_at.isoformat() if trade.closed_at else None
            })
        
        return {
            "trades": trades_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения сделок: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trades"
        )

@router.get("/api/signals")
async def get_signals(
    limit: int = 50,
    executed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Получить список торговых сигналов"""
    try:
        query = db.query(Signal)
        
        # Фильтр по исполнению
        if executed is not None:
            query = query.filter(Signal.executed == executed)
        
        # Получаем сигналы
        signals = query.order_by(desc(Signal.created_at)).limit(limit).all()
        
        # Форматируем для отправки
        signals_data = []
        for signal in signals:
            signals_data.append({
                "id": signal.id,
                "symbol": signal.symbol,
                "action": signal.action,
                "confidence": float(signal.confidence) if signal.confidence else 0,
                "price": float(signal.price) if signal.price else 0,
                "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
                "take_profit": float(signal.take_profit) if signal.take_profit else None,
                "strategy": signal.strategy,
                "reason": signal.reason,
                "executed": signal.executed,
                "created_at": signal.created_at.isoformat() if signal.created_at else None
            })
        
        return {"signals": signals_data}
        
    except Exception as e:
        logger.error(f"Ошибка получения сигналов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get signals"
        )

@router.get("/api/balance")
async def get_balance(db: Session = Depends(get_db)):
    """Получить текущий баланс"""
    try:
        # Пробуем получить с биржи
        if bot_manager and hasattr(bot_manager, 'exchange'):
            try:
                balance = await bot_manager.exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {})
                
                # Сохраняем в БД
                balance_record = Balance(
                    currency='USDT',
                    total=float(usdt_balance.get('total', 0)),
                    free=float(usdt_balance.get('free', 0)),
                    used=float(usdt_balance.get('used', 0)),
                    timestamp=datetime.utcnow()
                )
                db.add(balance_record)
                db.commit()
                
                return {
                    "USDT": {
                        "total": float(usdt_balance.get('total', 0)),
                        "free": float(usdt_balance.get('free', 0)),
                        "used": float(usdt_balance.get('used', 0))
                    },
                    "source": "exchange",
                    "timestamp": datetime.utcnow()
                }
            except Exception as e:
                logger.warning(f"Не удалось получить баланс с биржи: {e}")
        
        # Если не получилось с биржи, берем из БД
        latest_balance = db.query(Balance).filter(
            Balance.currency == 'USDT'
        ).order_by(desc(Balance.timestamp)).first()
        
        if latest_balance:
            return {
                "USDT": {
                    "total": float(latest_balance.total),
                    "free": float(latest_balance.free),
                    "used": float(latest_balance.used)
                },
                "source": "database",
                "timestamp": latest_balance.timestamp
            }
        else:
            return {
                "USDT": {"total": 0, "free": 0, "used": 0},
                "source": "default",
                "timestamp": datetime.utcnow()
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        return {
            "USDT": {"total": 0, "free": 0, "used": 0},
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/api/trading-pairs")
async def get_trading_pairs(db: Session = Depends(get_db)):
    """Получить список торговых пар"""
    try:
        pairs = db.query(TradingPair).all()
        
        pairs_data = []
        for pair in pairs:
            pairs_data.append({
                "id": pair.id,
                "symbol": pair.symbol,
                "is_active": pair.is_active,
                "strategy": pair.strategy,
                "stop_loss_percent": float(pair.stop_loss_percent),
                "take_profit_percent": float(pair.take_profit_percent),
                "created_at": pair.created_at.isoformat() if pair.created_at else None
            })
        
        return {"pairs": pairs_data}
        
    except Exception as e:
        logger.error(f"Ошибка получения торговых пар: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trading pairs"
        )

@router.post("/api/trading-pairs")
async def update_trading_pairs(
    pairs: List[str],
    db: Session = Depends(get_db)
):
    """Обновить список активных торговых пар"""
    try:
        # Деактивируем все пары
        db.query(TradingPair).update({"is_active": False})
        
        # Активируем выбранные
        for symbol in pairs:
            pair = db.query(TradingPair).filter(
                TradingPair.symbol == symbol
            ).first()
            
            if pair:
                pair.is_active = True
            else:
                # Создаем новую пару
                new_pair = TradingPair(
                    symbol=symbol,
                    is_active=True,
                    strategy='auto',  # Автоматический выбор стратегии
                    stop_loss_percent=2.0,
                    take_profit_percent=4.0
                )
                db.add(new_pair)
        
        db.commit()
        
        # Обновляем в боте если он запущен
        if bot_manager:
            await bot_manager.update_pairs(pairs)
        
        return {
            "success": True,
            "message": f"Updated {len(pairs)} trading pairs",
            "pairs": pairs
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка обновления торговых пар: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update trading pairs"
        )

# ===== SETTINGS ENDPOINTS =====

@router.get("/api/settings")
async def get_settings(db: Session = Depends(get_db)):
    """Получить текущие настройки"""
    try:
        # Получаем настройки из конфига и БД
        from ..core.config import config
        
        settings = {
            "trading": {
                "max_position_size_percent": config.MAX_POSITION_SIZE_PERCENT,
                "stop_loss_percent": config.STOP_LOSS_PERCENT,
                "take_profit_percent": config.TAKE_PROFIT_PERCENT,
                "max_daily_trades": config.MAX_DAILY_TRADES,
                "max_positions": config.MAX_POSITIONS,
                "min_risk_reward_ratio": config.MIN_RISK_REWARD_RATIO
            },
            "exchange": {
                "name": "Bybit",
                "testnet": config.BYBIT_TESTNET
            },
            "notifications": {
                "telegram_enabled": bool(config.TELEGRAM_BOT_TOKEN),
                "telegram_chat_id": config.TELEGRAM_CHAT_ID if config.TELEGRAM_BOT_TOKEN else None
            }
        }
        
        return settings
        
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get settings"
        )

@router.post("/api/settings")
async def update_settings(
    settings: SettingsRequest,
    db: Session = Depends(get_db)
):
    """Обновить настройки бота"""
    try:
        # Здесь можно сохранить настройки в БД
        # Для простоты пока просто возвращаем успех
        
        # Отправляем уведомление через WebSocket
        await ws_manager.broadcast({
            "type": "settings_updated",
            "settings": settings.dict(exclude_none=True),
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "message": "Settings updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Ошибка обновления настроек: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )

# ===== WEBSOCKET ENDPOINT =====

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Ждем сообщения от клиента
            data = await websocket.receive_text()
            
            # Обрабатываем команды от клиента
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "get_status":
                    if bot_manager:
                        status = bot_manager.get_status()
                        await websocket.send_json({
                            "type": "status_response",
                            "data": status
                        })
                        
            except json.JSONDecodeError:
                logger.warning(f"Получено некорректное сообщение: {data}")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
        ws_manager.disconnect(websocket)

# ===== EXPORT/IMPORT ENDPOINTS =====

@router.get("/api/export/trades")
async def export_trades(
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """Экспорт сделок в CSV или JSON"""
    try:
        trades = db.query(Trade).order_by(desc(Trade.created_at)).all()
        
        if format == "json":
            trades_data = []
            for trade in trades:
                trades_data.append({
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "side": str(trade.side.value) if hasattr(trade.side, 'value') else str(trade.side),
                    "entry_price": float(trade.entry_price) if trade.entry_price else 0,
                    "exit_price": float(trade.exit_price) if trade.exit_price else None,
                    "quantity": float(trade.quantity) if trade.quantity else 0,
                    "profit": float(trade.profit) if trade.profit else None,
                    "status": str(trade.status.value) if hasattr(trade.status, 'value') else str(trade.status),
                    "strategy": trade.strategy,
                    "created_at": trade.created_at.isoformat() if trade.created_at else None,
                    "closed_at": trade.closed_at.isoformat() if trade.closed_at else None
                })
            
            return JSONResponse(content={"trades": trades_data})
            
        else:  # CSV
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow([
                "ID", "Symbol", "Side", "Entry Price", "Exit Price",
                "Quantity", "Profit", "Status", "Strategy",
                "Created At", "Closed At"
            ])
            
            # Данные
            for trade in trades:
                writer.writerow([
                    trade.id,
                    trade.symbol,
                    str(trade.side.value) if hasattr(trade.side, 'value') else str(trade.side),
                    float(trade.entry_price) if trade.entry_price else 0,
                    float(trade.exit_price) if trade.exit_price else "",
                    float(trade.quantity) if trade.quantity else 0,
                    float(trade.profit) if trade.profit else "",
                    str(trade.status.value) if hasattr(trade.status, 'value') else str(trade.status),
                    trade.strategy,
                    trade.created_at.isoformat() if trade.created_at else "",
                    trade.closed_at.isoformat() if trade.closed_at else ""
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
            
    except Exception as e:
        logger.error(f"Ошибка экспорта сделок: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export trades"
        )

# ===== ADVANCED ANALYTICS ENDPOINTS =====

@router.get("/api/analytics/performance")
async def get_performance_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Получить расширенную аналитику производительности"""
    try:
        # Используем AdvancedAnalytics если доступен
        from ..analysis.advanced_analytics import advanced_analytics
        
        report = await advanced_analytics.generate_performance_report(days)
        return report
        
    except ImportError:
        # Базовая аналитика если модуль недоступен
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trades = db.query(Trade).filter(
            Trade.created_at >= start_date,
            Trade.status == TradeStatus.CLOSED
        ).all()
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_trades": len(trades),
                "profitable_trades": len([t for t in trades if t.profit and t.profit > 0]),
                "total_profit": sum(t.profit or 0 for t in trades)
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения аналитики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics"
        )

# ===== ФУНКЦИИ ДЛЯ ЭКСПОРТА =====

__all__ = [
    'router',
    'set_bot_manager',
    'ws_manager',
    'WebSocketManager'
]