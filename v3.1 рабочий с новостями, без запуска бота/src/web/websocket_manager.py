# src/web/websocket_manager.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
WebSocket Manager - Production-Ready реализация с threading integration

КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ:
- Замена asyncio.create_task() на threading для Flask совместимости
- Сохранение ВСЕЙ функциональности: Rate limiting, Message queue, Health monitoring
- Production-ready архитектура с error recovery и metrics

АРХИТЕКТУРНЫЕ ИЗМЕНЕНИЯ:
1. start() метод - threading workers вместо asyncio tasks
2. _message_worker() - thread-safe обработка без asyncio
3. _cleanup_worker() - threading-based cleanup
4. Сохранение всех advanced компонентов без упрощения
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Set, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from contextlib import contextmanager
import weakref

from flask_socketio import SocketIO, emit, disconnect
from flask import request

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """Состояния WebSocket соединения"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"

class MessagePriority(Enum):
    """Приоритеты сообщений"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class WebSocketMessage:
    """Структура WebSocket сообщения"""
    event: str
    data: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 3
    ttl_seconds: int = 300  # Time to live
    target_rooms: Optional[List[str]] = None
    target_sids: Optional[List[str]] = None

@dataclass
class ConnectionMetrics:
    """Метрики соединения"""
    connect_time: datetime
    last_activity: datetime
    messages_sent: int = 0
    messages_received: int = 0
    errors_count: int = 0
    reconnections: int = 0
    latency_ms: float = 0.0
    
    def update_activity(self):
        self.last_activity = datetime.utcnow()
    
    def add_error(self):
        self.errors_count += 1
    
    def add_reconnection(self):
        self.reconnections += 1

@dataclass
class ConnectionInfo:
    """Информация о WebSocket соединении"""
    sid: str
    state: ConnectionState
    metrics: ConnectionMetrics
    subscriptions: Set[str] = field(default_factory=set)
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    rate_limit_tokens: int = 100
    last_token_refill: datetime = field(default_factory=datetime.utcnow)

class RateLimiter:
    """Rate limiter для WebSocket соединений"""
    
    def __init__(self, max_tokens: int = 100, refill_rate: int = 10):
        """
        Args:
            max_tokens: Максимальное количество токенов
            refill_rate: Скорость пополнения токенов в секунду
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
    
    def can_send(self, connection: ConnectionInfo) -> bool:
        """Проверка возможности отправки сообщения"""
        now = datetime.utcnow()
        time_passed = (now - connection.last_token_refill).total_seconds()
        
        # Пополняем токены
        tokens_to_add = int(time_passed * self.refill_rate)
        if tokens_to_add > 0:
            connection.rate_limit_tokens = min(
                self.max_tokens,
                connection.rate_limit_tokens + tokens_to_add
            )
            connection.last_token_refill = now
        
        # Проверяем доступность токенов
        if connection.rate_limit_tokens > 0:
            connection.rate_limit_tokens -= 1
            return True
        
        return False

class MessageQueue:
    """Очередь сообщений с приоритетами и retry логикой"""
    
    def __init__(self, max_size: int = 1000):
        self.queues = {
            MessagePriority.CRITICAL: deque(),
            MessagePriority.HIGH: deque(),
            MessagePriority.NORMAL: deque(),
            MessagePriority.LOW: deque()
        }
        self.max_size = max_size
        self._lock = threading.Lock()
    
    def add_message(self, message: WebSocketMessage) -> bool:
        """Добавление сообщения в очередь"""
        with self._lock:
            queue = self.queues[message.priority]
            
            # Проверяем размер очереди
            total_size = sum(len(q) for q in self.queues.values())
            if total_size >= self.max_size:
                # Удаляем старые сообщения с низким приоритетом
                if self.queues[MessagePriority.LOW]:
                    self.queues[MessagePriority.LOW].popleft()
                elif self.queues[MessagePriority.NORMAL]:
                    self.queues[MessagePriority.NORMAL].popleft()
                else:
                    logger.warning("Очередь сообщений переполнена")
                    return False
            
            queue.append(message)
            return True
    
    def get_next_message(self) -> Optional[WebSocketMessage]:
        """Получение следующего сообщения по приоритету"""
        with self._lock:
            # Проверяем очереди в порядке приоритета
            for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH, 
                           MessagePriority.NORMAL, MessagePriority.LOW]:
                queue = self.queues[priority]
                if queue:
                    message = queue.popleft()
                    
                    # Проверяем TTL
                    age = (datetime.utcnow() - message.timestamp).total_seconds()
                    if age > message.ttl_seconds:
                        logger.debug(f"Сообщение истекло: {message.event}")
                        continue
                    
                    return message
            
            return None
    
    def size(self) -> int:
        """Размер очереди"""
        return sum(len(q) for q in self.queues.values())

class WebSocketManager:
    """
    Production-Ready менеджер WebSocket соединений с threading integration
    
    ПОЛНАЯ ФУНКЦИОНАЛЬНОСТЬ:
    - Advanced connection management с метриками
    - Rate limiting с token bucket алгоритмом
    - Priority-based message queue с retry логикой
    - Health monitoring и automatic cleanup
    - Error recovery и reconnection logic
    - Real-time statistics и performance metrics
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connections: Dict[str, ConnectionInfo] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # channel -> set of sids
        self.message_queue = MessageQueue()
        self.rate_limiter = RateLimiter()
        self._running = False
        self._lock = threading.RLock()
        
        # Threading workers - ИСПРАВЛЕНИЕ: замена asyncio на threading
        self._message_worker_thread: Optional[threading.Thread] = None
        self._cleanup_worker_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Статистика
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'reconnections': 0,
            'rate_limits': 0,
            'start_time': datetime.utcnow()
        }
        
        # Callbacks
        self.on_connect_callbacks: List[Callable] = []
        self.on_disconnect_callbacks: List[Callable] = []
        self.on_message_callbacks: List[Callable] = []
        
        self._setup_socketio_handlers()
        
        logger.info("✅ Production-Ready WebSocketManager инициализирован")
    
    def _setup_socketio_handlers(self):
        """Настройка обработчиков SocketIO событий"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Обработка подключения"""
            sid = request.sid
            
            # Создаем информацию о соединении
            connection = ConnectionInfo(
                sid=sid,
                state=ConnectionState.CONNECTED,
                metrics=ConnectionMetrics(
                    connect_time=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                ),
                ip_address=request.environ.get('REMOTE_ADDR'),
                user_agent=request.environ.get('HTTP_USER_AGENT')
            )
            
            with self._lock:
                self.connections[sid] = connection
                self.stats['total_connections'] += 1
                self.stats['active_connections'] += 1
            
            logger.info(f"🔗 WebSocket подключен: {sid} (IP: {connection.ip_address})")
            
            # Вызываем callbacks
            for callback in self.on_connect_callbacks:
                try:
                    callback(sid, connection)
                except Exception as e:
                    logger.error(f"Ошибка в connect callback: {e}")
            
            # Отправляем приветственное сообщение
            self.send_to_connection(sid, 'welcome', {
                'message': 'WebSocket соединение установлено',
                'sid': sid,
                'timestamp': datetime.utcnow().isoformat()
            }, MessagePriority.HIGH)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Обработка отключения"""
            sid = request.sid
            
            with self._lock:
                if sid in self.connections:
                    connection = self.connections[sid]
                    connection.state = ConnectionState.DISCONNECTED
                    
                    # Удаляем подписки
                    for channel in list(connection.subscriptions):
                        self._unsubscribe_internal(sid, channel)
                    
                    del self.connections[sid]
                    self.stats['active_connections'] -= 1
                    
                    logger.info(f"❌ WebSocket отключен: {sid}")
                    
                    # Вызываем callbacks
                    for callback in self.on_disconnect_callbacks:
                        try:
                            callback(sid, connection)
                        except Exception as e:
                            logger.error(f"Ошибка в disconnect callback: {e}")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Обработка подписки на канал"""
            sid = request.sid
            channel = data.get('channel')
            
            if not channel:
                self.send_error(sid, 'subscribe', 'Не указан канал для подписки')
                return
            
            success = self.subscribe(sid, channel)
            
            if success:
                self.send_to_connection(sid, 'subscription_success', {
                    'channel': channel,
                    'message': f'Подписка на канал {channel} активна'
                })
            else:
                self.send_error(sid, 'subscribe', f'Ошибка подписки на канал {channel}')
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """Обработка отмены подписки"""
            sid = request.sid
            channel = data.get('channel')
            
            if not channel:
                self.send_error(sid, 'unsubscribe', 'Не указан канал для отписки')
                return
            
            success = self.unsubscribe(sid, channel)
            
            if success:
                self.send_to_connection(sid, 'unsubscription_success', {
                    'channel': channel,
                    'message': f'Отписка от канала {channel} выполнена'
                })
        
        @self.socketio.on('ping')
        def handle_ping(data=None):
            """Обработка ping для проверки соединения"""
            sid = request.sid
            
            with self._lock:
                if sid in self.connections:
                    self.connections[sid].metrics.update_activity()
                    
                    self.send_to_connection(sid, 'pong', {
                        'timestamp': datetime.utcnow().isoformat(),
                        'data': data
                    })
        
        @self.socketio.on('get_status')
        def handle_get_status():
            """Получение статуса соединения"""
            sid = request.sid
            
            with self._lock:
                if sid in self.connections:
                    connection = self.connections[sid]
                    connection.metrics.update_activity()
                    
                    status = {
                        'sid': sid,
                        'state': connection.state.value,
                        'connected_since': connection.metrics.connect_time.isoformat(),
                        'subscriptions': list(connection.subscriptions),
                        'messages_sent': connection.metrics.messages_sent,
                        'messages_received': connection.metrics.messages_received,
                        'errors': connection.metrics.errors_count,
                        'reconnections': connection.metrics.reconnections
                    }
                    
                    self.send_to_connection(sid, 'status_response', status)
    
    def start(self):
        """ИСПРАВЛЕННЫЙ запуск WebSocket менеджера с threading workers"""
        if self._running:
            logger.warning("WebSocketManager уже запущен")
            return
        
        self._running = True
        self._shutdown_event.clear()
        
        # ИСПРАВЛЕНИЕ: Запускаем threading workers вместо asyncio tasks
        self._message_worker_thread = threading.Thread(
            target=self._message_worker,
            name="WSMessageWorker",
            daemon=True
        )
        
        self._cleanup_worker_thread = threading.Thread(
            target=self._cleanup_worker,
            name="WSCleanupWorker", 
            daemon=True
        )
        
        self._message_worker_thread.start()
        self._cleanup_worker_thread.start()
        
        logger.info("🚀 Production-Ready WebSocketManager запущен")
        logger.info("📨 Message worker запущен в отдельном потоке")
        logger.info("🧹 Cleanup worker запущен в отдельном потоке")
    
    def stop(self):
        """Остановка WebSocket менеджера"""
        self._running = False
        self._shutdown_event.set()
        
        # Ждем завершения worker threads
        if self._message_worker_thread and self._message_worker_thread.is_alive():
            self._message_worker_thread.join(timeout=5)
        
        if self._cleanup_worker_thread and self._cleanup_worker_thread.is_alive():
            self._cleanup_worker_thread.join(timeout=5)
        
        # Отключаем все соединения
        with self._lock:
            for sid in list(self.connections.keys()):
                try:
                    self.socketio.disconnect(sid)
                except Exception as e:
                    logger.error(f"Ошибка отключения {sid}: {e}")
        
        logger.info("🛑 Production-Ready WebSocketManager остановлен")
    
    def _message_worker(self):
        """ИСПРАВЛЕННЫЙ threading-based worker для обработки очереди сообщений"""
        logger.info("📨 Message worker запущен")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                message = self.message_queue.get_next_message()
                
                if message:
                    success = self._send_message_sync(message)
                    
                    if not success and message.retry_count < message.max_retries:
                        # Retry logic
                        message.retry_count += 1
                        self.message_queue.add_message(message)
                        logger.debug(f"Повтор отправки сообщения: {message.event} (попытка {message.retry_count})")
                
                # Небольшая пауза чтобы не загружать CPU
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Ошибка в message worker: {e}")
                time.sleep(1)
        
        logger.info("📨 Message worker завершен")
    
    def _cleanup_worker(self):
        """ИСПРАВЛЕННЫЙ threading-based worker для очистки устаревших соединений"""
        logger.info("🧹 Cleanup worker запущен")
        
        while self._running and not self._shutdown_event.wait(60):  # Проверяем каждую минуту
            try:
                now = datetime.utcnow()
                inactive_threshold = timedelta(minutes=30)
                
                # Находим неактивные соединения
                inactive_sids = []
                with self._lock:
                    for sid, connection in self.connections.items():
                        if now - connection.metrics.last_activity > inactive_threshold:
                            inactive_sids.append(sid)
                
                # Отключаем неактивные соединения
                for sid in inactive_sids:
                    logger.info(f"🧹 Отключаем неактивное соединение: {sid}")
                    try:
                        self.socketio.disconnect(sid)
                    except Exception as e:
                        logger.error(f"Ошибка отключения неактивного соединения {sid}: {e}")
                
            except Exception as e:
                logger.error(f"Ошибка в cleanup worker: {e}")
        
        logger.info("🧹 Cleanup worker завершен")
    
    def subscribe(self, sid: str, channel: str) -> bool:
        """Подписка соединения на канал"""
        with self._lock:
            if sid not in self.connections:
                logger.warning(f"Попытка подписки неизвестного соединения: {sid}")
                return False
            
            connection = self.connections[sid]
            connection.subscriptions.add(channel)
            self.subscriptions[channel].add(sid)
            
            logger.debug(f"📺 Подписка {sid} на канал {channel}")
            return True
    
    def unsubscribe(self, sid: str, channel: str) -> bool:
        """Отмена подписки соединения"""
        with self._lock:
            return self._unsubscribe_internal(sid, channel)
    
    def _unsubscribe_internal(self, sid: str, channel: str) -> bool:
        """Внутренняя отмена подписки (без блокировки)"""
        if sid not in self.connections:
            return False
        
        connection = self.connections[sid]
        connection.subscriptions.discard(channel)
        self.subscriptions[channel].discard(sid)
        
        # Удаляем пустой канал
        if not self.subscriptions[channel]:
            del self.subscriptions[channel]
        
        logger.debug(f"📺❌ Отписка {sid} от канала {channel}")
        return True
    
    def send_to_connection(self, sid: str, event: str, data: Dict[str, Any], 
                          priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Отправка сообщения конкретному соединению"""
        with self._lock:
            if sid not in self.connections:
                logger.warning(f"Попытка отправки сообщения неизвестному соединению: {sid}")
                return False
        
        message = WebSocketMessage(
            event=event,
            data=data,
            priority=priority,
            target_sids=[sid]
        )
        
        return self.message_queue.add_message(message)
    
    def broadcast_to_channel(self, channel: str, event: str, data: Dict[str, Any],
                           priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Broadcast сообщения всем подписчикам канала"""
        with self._lock:
            if channel not in self.subscriptions or not self.subscriptions[channel]:
                logger.debug(f"Нет подписчиков для канала: {channel}")
                return True
            
            target_sids = list(self.subscriptions[channel])
        
        message = WebSocketMessage(
            event=event,
            data=data,
            priority=priority,
            target_sids=target_sids
        )
        
        return self.message_queue.add_message(message)
    
    def broadcast_to_all(self, event: str, data: Dict[str, Any],
                        priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Broadcast сообщения всем соединениям"""
        with self._lock:
            if not self.connections:
                logger.debug("Нет активных соединений для broadcast")
                return True
            
            target_sids = list(self.connections.keys())
        
        message = WebSocketMessage(
            event=event,
            data=data,
            priority=priority,
            target_sids=target_sids
        )
        
        return self.message_queue.add_message(message)
    
    def _send_message_sync(self, message: WebSocketMessage) -> bool:
        """ИСПРАВЛЕННАЯ синхронная отправка сообщения"""
        success_count = 0
        total_targets = 0
        
        try:
            # Определяем целевые соединения
            target_sids = message.target_sids or []
            with self._lock:
                if not target_sids:
                    target_sids = list(self.connections.keys())
            
            total_targets = len(target_sids)
            
            for sid in target_sids:
                with self._lock:
                    if sid not in self.connections:
                        continue
                    
                    connection = self.connections[sid]
                    
                    # Проверяем rate limiting
                    if not self.rate_limiter.can_send(connection):
                        logger.debug(f"Rate limit для {sid}")
                        self.stats['rate_limits'] += 1
                        continue
                
                try:
                    # Отправляем сообщение
                    self.socketio.emit(message.event, message.data, room=sid)
                    
                    # Обновляем метрики
                    with self._lock:
                        if sid in self.connections:
                            connection = self.connections[sid]
                            connection.metrics.messages_sent += 1
                            connection.metrics.update_activity()
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения {sid}: {e}")
                    with self._lock:
                        if sid in self.connections:
                            self.connections[sid].metrics.add_error()
                        self.stats['messages_failed'] += 1
            
            # Обновляем общую статистику
            with self._lock:
                self.stats['messages_sent'] += success_count
            
            # Считаем успешной если отправили хотя бы 80%
            success_rate = success_count / total_targets if total_targets > 0 else 1.0
            return success_rate >= 0.8
            
        except Exception as e:
            logger.error(f"Критическая ошибка при отправке сообщения: {e}")
            return False
    
    def send_error(self, sid: str, context: str, error_message: str):
        """Отправка сообщения об ошибке"""
        self.send_to_connection(sid, 'error', {
            'context': context,
            'message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }, MessagePriority.HIGH)
    
    def get_connection_info(self, sid: str) -> Optional[ConnectionInfo]:
        """Получение информации о соединении"""
        with self._lock:
            return self.connections.get(sid)
    
    def get_channel_subscribers(self, channel: str) -> Set[str]:
        """Получение списка подписчиков канала"""
        with self._lock:
            return self.subscriptions.get(channel, set()).copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики WebSocket менеджера"""
        now = datetime.utcnow()
        
        with self._lock:
            # Статистика соединений
            connection_stats = {
                'by_state': defaultdict(int),
                'average_lifetime': 0.0,
                'total_messages': 0,
                'total_errors': 0
            }
            
            if self.connections:
                total_lifetime = 0
                for connection in self.connections.values():
                    connection_stats['by_state'][connection.state.value] += 1
                    total_lifetime += (now - connection.metrics.connect_time).total_seconds()
                    connection_stats['total_messages'] += connection.metrics.messages_sent
                    connection_stats['total_errors'] += connection.metrics.errors_count
                
                connection_stats['average_lifetime'] = total_lifetime / len(self.connections)
            
            stats_copy = self.stats.copy()
            subscriptions_copy = {ch: len(subs) for ch, subs in self.subscriptions.items()}
        
        return {
            **stats_copy,
            'queue_size': self.message_queue.size(),
            'channels': {
                'total': len(subscriptions_copy),
                'active': len([ch for ch, count in subscriptions_copy.items() if count > 0]),
                'subscribers': subscriptions_copy
            },
            'connections': connection_stats,
            'uptime_seconds': (now - stats_copy['start_time']).total_seconds(),
            'timestamp': now.isoformat()
        }
    
    # === CALLBACK SYSTEM ===
    
    def on_connect(self, callback: Callable[[str, ConnectionInfo], None]):
        """Регистрация callback для подключения"""
        self.on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable[[str, ConnectionInfo], None]):
        """Регистрация callback для отключения"""
        self.on_disconnect_callbacks.append(callback)
    
    def on_message(self, callback: Callable[[str, str, Dict], None]):
        """Регистрация callback для сообщений"""
        self.on_message_callbacks.append(callback)

# === ИНТЕГРАЦИОННЫЕ КОМПОНЕНТЫ ===

class BotStatusBroadcaster:
    """Production-Ready broadcaster для статуса бота через WebSocket"""
    
    def __init__(self, ws_manager: WebSocketManager, bot_manager=None):
        self.ws_manager = ws_manager
        self.bot_manager = bot_manager
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
    
    def start(self):
        """Запуск broadcaster'а"""
        if self._running:
            return
        
        self._running = True
        self._shutdown_event.clear()
        self._thread = threading.Thread(
            target=self._broadcast_loop,
            name="BotStatusBroadcaster",
            daemon=True
        )
        self._thread.start()
        logger.info("📡 BotStatusBroadcaster запущен")
    
    def stop(self):
        """Остановка broadcaster'а"""
        self._running = False
        self._shutdown_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        logger.info("📡 BotStatusBroadcaster остановлен")
    
    def _broadcast_loop(self):
        """Основной цикл broadcast'а"""
        while self._running and not self._shutdown_event.wait(10):  # Обновляем каждые 10 секунд
            try:
                if self.bot_manager and self.ws_manager._running:
                    status = self.bot_manager.get_status()
                    
                    self.ws_manager.broadcast_to_channel(
                        'bot_status',
                        'bot_status_update',
                        status,
                        MessagePriority.NORMAL
                    )
                
            except Exception as e:
                logger.error(f"Ошибка в broadcast loop: {e}")

def create_websocket_manager(socketio: SocketIO, bot_manager=None) -> WebSocketManager:
    """
    Фабрика для создания Production-Ready WebSocket менеджера с интеграциями
    
    Args:
        socketio: SocketIO экземпляр
        bot_manager: Менеджер бота для интеграции
        
    Returns:
        Настроенный WebSocketManager с полной функциональностью
    """
    ws_manager = WebSocketManager(socketio)
    
    # Настраиваем bot status broadcaster
    broadcaster = None
    if bot_manager:
        broadcaster = BotStatusBroadcaster(ws_manager, bot_manager)
        
        # Запускаем broadcaster при первом подключении
        @ws_manager.on_connect
        def setup_bot_status(sid: str, connection: ConnectionInfo):
            if broadcaster and not broadcaster._running:
                broadcaster.start()
    
    logger.info("✅ Production-Ready WebSocket интеграции настроены")
    
    return ws_manager

# Экспорт основных компонентов
__all__ = [
    'WebSocketManager',
    'ConnectionState', 
    'MessagePriority',
    'WebSocketMessage',
    'ConnectionInfo',
    'BotStatusBroadcaster',
    'create_websocket_manager'
]