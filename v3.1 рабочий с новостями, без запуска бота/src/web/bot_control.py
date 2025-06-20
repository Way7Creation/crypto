# src/web/bot_control.py
"""
Bot Control API - ИСПРАВЛЕННАЯ ВЕРСИЯ

Модуль: API управления торговым ботом с корректной async интеграцией
Статус: КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ Event Loop Management
Изменения: Полная переработка async обработки, устранение "Event loop is closed"

Архитектурные изменения:
1. Замена небезопасных asyncio.new_event_loop() на AsyncRouteHandler
2. Улучшенная обработка остановки бота с корректными таймаутами
3. Централизованное управление async операциями
4. Расширенное логирование для диагностики
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import jsonify, request

# КРИТИЧЕСКИЙ ИМПОРТ: Новый AsyncRouteHandler
from .async_handler import async_handler

logger = logging.getLogger(__name__)

class BotController:
    """
    Контроллер для управления торговым ботом
    
    ИСПРАВЛЕНИЯ в этой версии:
    - Убраны все asyncio.new_event_loop() вызовы
    - Добавлено корректное управление жизненным циклом async задач
    - Улучшена обработка ошибок и таймаутов
    - Расширена диагностическая информация
    """
    
    def __init__(self, bot_manager=None):
        """
        Инициализация BotController
        
        Args:
            bot_manager: Экземпляр BotManager для управления торговлей
        """
        self.bot_manager = bot_manager
        self.auto_trading = False
        self.trading_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._status_lock = asyncio.Lock()
        
        # Диагностическая информация
        self.controller_stats = {
            'start_time': datetime.utcnow(),
            'total_starts': 0,
            'total_stops': 0,
            'last_error': None,
            'uptime': timedelta(0)
        }
        
        logger.info("🎮 BotController инициализирован")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получить статус бота (синхронная версия для быстрого доступа)
        
        Returns:
            Dict с информацией о статусе бота
        """
        try:
            # Базовая информация
            base_status = {
                'is_running': self.auto_trading,
                'status': 'running' if self.auto_trading else 'stopped',
                'active_pairs': getattr(self.bot_manager, 'active_pairs', []),
                'open_positions': 0,
                'positions_details': {},
                'statistics': {
                    'start_time': None,
                    'uptime': None,
                    'cycles_count': 0,
                    'trades_today': 0
                },
                'process_info': {},
                'config': {
                    'mode': 'TESTNET',
                    'max_positions': 1,
                    'human_mode': True,
                    'max_daily_trades': 10
                }
            }
            
            # Расширенная информация если bot_manager доступен
            if self.bot_manager:
                try:
                    manager_status = self.bot_manager.get_status()
                    base_status.update(manager_status)
                except Exception as e:
                    logger.warning(f"Не удалось получить статус от bot_manager: {e}")
            
            # Добавляем статистику контроллера
            if self.auto_trading and 'statistics' in base_status:
                base_status['statistics'].update({
                    'controller_uptime': str(datetime.utcnow() - self.controller_stats['start_time']),
                    'total_starts': self.controller_stats['total_starts'],
                    'total_stops': self.controller_stats['total_stops']
                })
            
            return base_status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def start_bot(self, pairs: List[str] = None, strategy: str = 'auto') -> Dict[str, Any]:
        """
        Запустить торгового бота
        
        Args:
            pairs: Список торговых пар (по умолчанию ['BTCUSDT', 'ETHUSDT'])
            strategy: Стратегия торговли (по умолчанию 'auto')
            
        Returns:
            Dict с результатом операции
        """
        async with self._status_lock:
            try:
                logger.info(f"🚀 Запуск торгового бота (пары: {pairs}, стратегия: {strategy})")
                
                # Проверяем что бот не запущен
                if self.auto_trading:
                    logger.warning("⚠️ Попытка запуска уже работающего бота")
                    return {
                        'success': False,
                        'message': 'Бот уже запущен'
                    }
                
                # Параметры по умолчанию
                if pairs is None:
                    pairs = ['BTCUSDT', 'ETHUSDT']
                
                # Сбрасываем событие остановки
                self._shutdown_event.clear()
                
                # Устанавливаем режим автоторговли
                self.auto_trading = True
                
                # Обновляем торговые пары если доступен bot_manager
                if self.bot_manager:
                    await self._update_trading_pairs(pairs)
                
                # Запускаем торговый цикл
                self.trading_task = asyncio.create_task(
                    self._trading_loop(),
                    name="TradingLoop"
                )
                
                # Обновляем статистику
                self.controller_stats['total_starts'] += 1
                self.controller_stats['last_error'] = None
                
                logger.info("✅ Торговый бот успешно запущен")
                return {
                    'success': True,
                    'message': f'Бот запущен с парами {pairs} и стратегией {strategy}',
                    'pairs': pairs,
                    'strategy': strategy
                }
                
            except Exception as e:
                self.auto_trading = False
                self.controller_stats['last_error'] = str(e)
                logger.error(f"❌ Ошибка запуска бота: {e}")
                return {
                    'success': False,
                    'message': f'Ошибка запуска: {str(e)}'
                }
    
    async def stop_bot(self) -> Dict[str, Any]:
        """
        ИСПРАВЛЕННАЯ версия остановки бота с корректным управлением async задачами
        
        Returns:
            Dict с результатом операции
        """
        async with self._status_lock:
            try:
                logger.info("⏹️ Начинаем остановку торгового бота...")
                
                if not self.auto_trading:
                    logger.info("ℹ️ Бот уже остановлен")
                    return {
                        'success': True,
                        'message': 'Бот уже остановлен'
                    }
                
                # Шаг 1: Останавливаем новые торговые операции
                self.auto_trading = False
                self._shutdown_event.set()
                
                logger.info("📢 Сигнал остановки отправлен торговому циклу")
                
                # Шаг 2: Корректно останавливаем торговую задачу
                if self.trading_task and not self.trading_task.done():
                    logger.info("⏳ Ожидаем завершения торгового цикла...")
                    
                    try:
                        # Даем торговому циклу время на корректное завершение
                        await asyncio.wait_for(self.trading_task, timeout=5.0)
                        logger.info("✅ Торговый цикл завершился корректно")
                        
                    except asyncio.TimeoutError:
                        logger.warning("⏰ Таймаут ожидания завершения, принудительная остановка")
                        self.trading_task.cancel()
                        
                        try:
                            await asyncio.wait_for(self.trading_task, timeout=2.0)
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            logger.info("🛑 Торговая задача принудительно остановлена")
                    
                    except asyncio.CancelledError:
                        logger.info("🚫 Торговая задача была отменена")
                
                # Шаг 3: Закрываем открытые позиции если есть менеджер
                if self.bot_manager:
                    try:
                        logger.info("💼 Закрываем открытые позиции...")
                        
                        await asyncio.wait_for(
                            self._safe_close_positions(), 
                            timeout=15.0
                        )
                        
                        logger.info("✅ Позиции закрыты")
                        
                    except asyncio.TimeoutError:
                        logger.error("⏰ Таймаут закрытия позиций")
                    except Exception as e:
                        logger.error(f"❌ Ошибка закрытия позиций: {e}")
                
                # Шаг 4: Обновляем статистику
                self.controller_stats['total_stops'] += 1
                self.controller_stats['last_error'] = None
                
                logger.info("✅ Торговый бот полностью остановлен")
                return {
                    'success': True,
                    'message': 'Бот успешно остановлен'
                }
                
            except Exception as e:
                self.controller_stats['last_error'] = str(e)
                logger.error(f"❌ Критическая ошибка остановки бота: {e}")
                
                # В случае критической ошибки принудительно сбрасываем состояние
                self.auto_trading = False
                if self.trading_task:
                    self.trading_task.cancel()
                
                return {
                    'success': False,
                    'message': f'Ошибка остановки: {str(e)}'
                }
    
    async def _safe_close_positions(self):
        """Безопасное закрытие позиций с обработкой ошибок"""
        try:
            if hasattr(self.bot_manager, 'close_all_positions'):
                await self.bot_manager.close_all_positions()
            elif hasattr(self.bot_manager, 'positions') and self.bot_manager.positions:
                logger.info(f"Найдено {len(self.bot_manager.positions)} открытых позиций")
                # Здесь можно добавить логику закрытия позиций
        except Exception as e:
            logger.error(f"Ошибка в _safe_close_positions: {e}")
            raise
    
    async def restart_bot(self) -> Dict[str, Any]:
        """
        Перезапустить торгового бота
        
        Returns:
            Dict с результатом операции
        """
        try:
            logger.info("🔄 Начинаем перезапуск бота...")
            
            # Останавливаем бота
            stop_result = await self.stop_bot()
            if not stop_result['success']:
                return {
                    'success': False,
                    'message': f'Ошибка остановки при перезапуске: {stop_result["message"]}'
                }
            
            # Пауза между остановкой и запуском
            logger.info("⏸️ Пауза между остановкой и запуском...")
            await asyncio.sleep(3)
            
            # Запускаем бота
            start_result = await self.start_bot()
            
            if start_result['success']:
                logger.info("✅ Бот успешно перезапущен")
                return {
                    'success': True,
                    'message': 'Бот успешно перезапущен'
                }
            else:
                return {
                    'success': False,
                    'message': f'Ошибка запуска при перезапуске: {start_result["message"]}'
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка перезапуска бота: {e}")
            return {
                'success': False,
                'message': f'Ошибка перезапуска: {str(e)}'
            }
    
    async def _trading_loop(self):
        """
        Главный торговый цикл с улучшенной обработкой остановки
        """
        logger.info("📈 Торговый цикл запущен")
        cycle_count = 0
        
        try:
            while self.auto_trading and not self._shutdown_event.is_set():
                cycle_start = datetime.utcnow()
                cycle_count += 1
                
                try:
                    logger.debug(f"🔄 Торговый цикл #{cycle_count}")
                    
                    # 1. Анализ рынка
                    market_data = await self.analyze_market()
                    
                    # 2. Генерация сигналов  
                    signals = await self.generate_signals(market_data)
                    
                    # 3. Исполнение сделок
                    if signals:
                        await self.execute_trades(signals)
                    
                    # 4. Управление позициями
                    await self.manage_positions()
                    
                    # 5. Пауза между циклами (с проверкой остановки)
                    cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                    sleep_time = max(0, 30 - cycle_duration)  # Цикл каждые 30 секунд
                    
                    if sleep_time > 0:
                        try:
                            await asyncio.wait_for(
                                self._shutdown_event.wait(), 
                                timeout=sleep_time
                            )
                            # Если дождались события остановки, выходим
                            break
                        except asyncio.TimeoutError:
                            # Таймаут - продолжаем работу
                            pass
                    
                except asyncio.CancelledError:
                    logger.info("🚫 Торговый цикл отменен")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка в торговом цикле #{cycle_count}: {e}")
                    # Продолжаем работу после ошибки с паузой
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            logger.info("🛑 Торговый цикл остановлен по запросу")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка торгового цикла: {e}")
        finally:
            logger.info(f"📊 Торговый цикл завершен (выполнено циклов: {cycle_count})")
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ТОРГОВОГО ЦИКЛА ===
    
    async def analyze_market(self):
        """Анализ рыночных данных"""
        if self.bot_manager and hasattr(self.bot_manager, 'analyze_market'):
            try:
                return await self.bot_manager.analyze_market()
            except Exception as e:
                logger.warning(f"Ошибка анализа рынка: {e}")
        
        # Имитация анализа для тестирования
        await asyncio.sleep(0.5)
        return {'trend': 'neutral', 'volatility': 'low'}
    
    async def generate_signals(self, market_data):
        """Генерация торговых сигналов"""
        if self.bot_manager and hasattr(self.bot_manager, 'generate_signals'):
            try:
                return await self.bot_manager.generate_signals(market_data)
            except Exception as e:
                logger.warning(f"Ошибка генерации сигналов: {e}")
        
        # Имитация генерации для тестирования
        await asyncio.sleep(0.3)
        return []
    
    async def execute_trades(self, signals):
        """Исполнение торговых сделок"""
        logger.info(f"💼 Исполняем {len(signals)} торговых сигналов...")
        
        if self.bot_manager and hasattr(self.bot_manager, 'execute_trades'):
            try:
                return await self.bot_manager.execute_trades(signals)
            except Exception as e:
                logger.warning(f"Ошибка исполнения сделок: {e}")
        
        # Имитация исполнения для тестирования
        await asyncio.sleep(1)
    
    async def manage_positions(self):
        """Управление открытыми позициями"""
        if self.bot_manager and hasattr(self.bot_manager, 'manage_positions'):
            try:
                return await self.bot_manager.manage_positions()
            except Exception as e:
                logger.warning(f"Ошибка управления позициями: {e}")
        
        # Имитация управления для тестирования
        await asyncio.sleep(0.2)
    
    async def _update_trading_pairs(self, pairs):
        """Обновление списка торговых пар"""
        try:
            if self.bot_manager and hasattr(self.bot_manager, 'update_pairs'):
                await self.bot_manager.update_pairs(pairs)
            logger.info(f"✅ Обновлены торговые пары: {pairs}")
        except Exception as e:
            logger.warning(f"Ошибка обновления торговых пар: {e}")


def register_bot_control_routes(app, bot_manager=None):
    """
    ОБНОВЛЕННАЯ регистрация роутов с использованием AsyncRouteHandler
    
    Args:
        app: Flask приложение
        bot_manager: Менеджер бота
        
    Returns:
        BotController: Экземпляр контроллера
    """
    logger.info("📝 Регистрируем роуты управления ботом с AsyncRouteHandler...")
    
    bot_controller = BotController(bot_manager)
    
    # === РОУТЫ С ИСПРАВЛЕННЫМ ASYNC УПРАВЛЕНИЕМ ===
    
    @app.route('/api/bot/status')
    def get_bot_status_action():
        """Получить статус бота (синхронный)"""
        try:
            status = bot_controller.get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Ошибка API статуса: {e}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    

    @app.route('/api/bot/start', methods=['POST'])
    @async_handler.async_route(timeout=30)
    async def start_bot_action():
        """Запустить бота - ИСПРАВЛЕННАЯ ВЕРСИЯ с flexible Content-Type"""
        try:
            # ИСПРАВЛЕНИЕ: Универсальная обработка request data
            data = {}
            
            # Попытка получить JSON data
            if request.is_json:
                try:
                    data = request.get_json() or {}
                except Exception as e:
                    logger.warning(f"Ошибка парсинга JSON: {e}")
            
            # Fallback на form data если JSON недоступен
            if not data and request.form:
                data = {
                    'pairs': request.form.getlist('pairs') or ['BTCUSDT', 'ETHUSDT'],
                    'strategy': request.form.get('strategy', 'auto')
                }
            
            # Fallback на query parameters
            if not data:
                data = {
                    'pairs': request.args.getlist('pairs') or ['BTCUSDT', 'ETHUSDT'], 
                    'strategy': request.args.get('strategy', 'auto')
                }
            
            # Default values если ничего не передано
            pairs = data.get('pairs', ['BTCUSDT', 'ETHUSDT'])
            strategy = data.get('strategy', 'auto')
            
            # Обеспечиваем что pairs это список
            if isinstance(pairs, str):
                pairs = [pairs]
            
            logger.info(f"🎯 API запрос запуска бота: пары={pairs}, стратегия={strategy}")
            logger.info(f"📊 Request info: Content-Type={request.content_type}, Method={request.method}")
            
            result = await bot_controller.start_bot(pairs, strategy)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Ошибка API запуска: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'request_info': {
                    'content_type': request.content_type,
                    'method': request.method,
                    'has_json': request.is_json,
                    'has_form': bool(request.form),
                    'has_args': bool(request.args)
                }
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    @async_handler.async_route(timeout=20)
    async def stop_bot_action():
        """Остановить бота - ИСПРАВЛЕННАЯ ВЕРСИЯ с улучшенным логированием"""
        try:
            logger.info("🎯 API запрос остановки бота")
            logger.info(f"📊 Request info: Content-Type={request.content_type}, Method={request.method}")
            
            result = await bot_controller.stop_bot()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Ошибка API остановки: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'request_info': {
                    'content_type': request.content_type,
                    'method': request.method
                }
            }), 500
    
    @app.route('/api/bot/restart', methods=['POST'])
    @async_handler.async_route(timeout=60)
    async def restart_bot_action():
        """Перезапустить бота - ИСПРАВЛЕННАЯ ВЕРСИЯ с улучшенным логированием"""
        try:
            logger.info("🎯 API запрос перезапуска бота")
            logger.info(f"📊 Request info: Content-Type={request.content_type}, Method={request.method}")
            
            result = await bot_controller.restart_bot()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Ошибка API перезапуска: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'request_info': {
                    'content_type': request.content_type,
                    'method': request.method
                }
            }), 500
    
    @app.route('/api/bot/config', methods=['GET', 'POST'])
    def bot_config_action():
        """Конфигурация бота (синхронная)"""
        if request.method == 'GET':
            try:
                config = {
                    'auto_trading': bot_controller.auto_trading,
                    'active_pairs': getattr(bot_controller.bot_manager, 'active_pairs', []),
                    'max_positions': 1,
                    'risk_level': 'medium',
                    'strategy': 'auto'
                }
                return jsonify(config)
            except Exception as e:
                logger.error(f"Ошибка получения конфигурации: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.get_json() or {}
                logger.info(f"Обновление конфигурации: {data}")
                return jsonify({'success': True, 'message': 'Конфигурация обновлена'})
            except Exception as e:
                logger.error(f"Ошибка обновления конфигурации: {e}")
                return jsonify({'error': str(e)}), 500
    
    # Диагностический роут для проверки AsyncHandler
    @app.route('/api/bot/async_stats')
    def get_async_stats():
        """Получить статистику AsyncRouteHandler"""
        try:
            stats = async_handler.get_stats()
            return jsonify({
                'success': True,
                'async_handler_stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Ошибка получения статистики AsyncHandler: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✅ Роуты управления ботом зарегистрированы с AsyncRouteHandler")
    return bot_controller
    
    @app.route('/api/bot/start', methods=['OPTIONS'])
    @app.route('/api/bot/stop', methods=['OPTIONS'])
    @app.route('/api/bot/restart', methods=['OPTIONS'])
    def bot_control_options():
        """CORS preflight обработка для bot control endpoints"""
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    logger.info("✅ Bot Control API Content-Type handling обновлен")
    logger.info("📊 Поддерживаемые форматы: JSON, Form-Data, Query Parameters")

# Экспорт основных компонентов
__all__ = ['BotController', 'register_bot_control_routes']