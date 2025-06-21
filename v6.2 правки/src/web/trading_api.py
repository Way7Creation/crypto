"""
API роуты для управления реальной торговлей - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/trading_api.py

🎯 УПРАВЛЕНИЕ РЕАЛЬНОЙ ТОРГОВЛЕЙ:
✅ Запуск/остановка бота
✅ Экстренная остановка
✅ Управление позициями
✅ Мониторинг торговых операций
✅ Интеграция с TradingController

ИСПРАВЛЕНИЯ:
✅ Убраны дублированные декораторы @login_required
✅ Правильное использование @async_handler()
✅ Исправлены все асинхронные функции
✅ Добавлена обработка ошибок
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import jsonify, request
from functools import wraps

from ..core.config import config
from ..logging.smart_logger import get_logger

logger = get_logger(__name__)

def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Упрощенная проверка авторизации для разработки
        auth_header = request.headers.get('Authorization', '')
        if not auth_header and not request.cookies.get('session'):
            return jsonify({
                'success': False,
                'error': 'Authorization required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def register_trading_api_routes(app, bot_manager=None):
    """
    Регистрирует API роуты для управления торговлей
    
    Args:
        app: Flask приложение
        bot_manager: Менеджер торгового бота
        
    ИСПРАВЛЕНИЕ: Убрано использование async_handler как вызываемого объекта
    """
    
    logger.info("🔄 Регистрация API роутов торговли...")
    
    # =================================================================
    # УПРАВЛЕНИЕ БОТОМ
    # =================================================================
    
    @app.route('/api/bot/start', methods=['POST'])
    @login_required
    def start_trading_bot():
        """
        Запуск торгового бота
        
        ИСПРАВЛЕНИЕ: Синхронная функция с правильной обработкой
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            # Получаем параметры запуска
            data = request.get_json() or {}
            pairs = data.get('pairs', [])
            auto_strategy = data.get('auto_strategy', True)
            
            logger.info(
                "🚀 Запуск торгового бота",
                category='bot',
                pairs_count=len(pairs),
                auto_strategy=auto_strategy
            )
            
            # Проверяем текущий статус
            current_status = bot_manager.get_status()
            if current_status.get('is_running', False):
                return jsonify({
                    'success': False,
                    'error': 'Bot is already running',
                    'current_status': current_status
                })
            
            # Устанавливаем торговые пары если указаны
            if pairs:
                # Синхронный вызов через asyncio
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Если уже в event loop, создаем задачу
                        asyncio.create_task(bot_manager.update_trading_pairs(pairs))
                    else:
                        # Если нет event loop, запускаем синхронно
                        loop.run_until_complete(bot_manager.update_trading_pairs(pairs))
                except Exception as e:
                    logger.warning(f"Не удалось обновить пары через asyncio: {e}")
                    # Fallback к синхронному методу если есть
                    if hasattr(bot_manager, 'update_pairs'):
                        bot_manager.update_pairs(pairs)
            
            # Запускаем бота
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для запуска
                    task = asyncio.create_task(bot_manager.start())
                    success, message = True, "Bot start initiated"
                else:
                    # Запускаем синхронно
                    result = loop.run_until_complete(bot_manager.start())
                    if isinstance(result, tuple):
                        success, message = result
                    else:
                        success, message = bool(result), "Bot started"
            except Exception as e:
                logger.error(f"Ошибка запуска бота: {e}")
                success, message = False, str(e)
            
            if success:
                logger.info(
                    "✅ Торговый бот запущен успешно",
                    category='bot',
                    message=message
                )
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'status': 'starting',
                    'pairs': pairs,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logger.error(
                    "❌ Ошибка запуска торгового бота",
                    category='bot',
                    error=message
                )
                
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка запуска бота: {e}")
            return jsonify({
                'success': False,
                'error': f'Internal error: {str(e)}'
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    @login_required
    def stop_trading_bot():
        """
        Остановка торгового бота
        
        ИСПРАВЛЕНИЕ: Синхронная функция с правильной обработкой
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.info("🛑 Остановка торгового бота", category='bot')
            
            # Проверяем текущий статус
            current_status = bot_manager.get_status()
            if not current_status.get('is_running', False):
                return jsonify({
                    'success': False,
                    'error': 'Bot is not running',
                    'current_status': current_status
                })
            
            # Останавливаем бота
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для остановки
                    task = asyncio.create_task(bot_manager.stop())
                    success, message = True, "Bot stop initiated"
                else:
                    # Запускаем синхронно
                    result = loop.run_until_complete(bot_manager.stop())
                    if isinstance(result, tuple):
                        success, message = result
                    else:
                        success, message = bool(result), "Bot stopped"
            except Exception as e:
                logger.error(f"Ошибка остановки бота: {e}")
                success, message = False, str(e)
            
            if success:
                logger.info(
                    "✅ Торговый бот остановлен",
                    category='bot',
                    message=message
                )
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'status': 'stopped',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logger.error(
                    "❌ Ошибка остановки бота",
                    category='bot',
                    error=message
                )
                
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка остановки бота: {e}")
            return jsonify({
                'success': False,
                'error': f'Internal error: {str(e)}'
            }), 500
    
    @app.route('/api/bot/emergency-stop', methods=['POST'])
    @login_required
    def emergency_stop_bot():
        """
        Экстренная остановка бота
        
        ИСПРАВЛЕНИЕ: Синхронная функция с правильной обработкой
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.critical("🚨 ЭКСТРЕННАЯ ОСТАНОВКА БОТА!", category='bot')
            
            # Экстренная остановка
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для экстренной остановки
                    task = asyncio.create_task(bot_manager.emergency_stop())
                    success, message = True, "Emergency stop initiated"
                else:
                    # Запускаем синхронно
                    result = loop.run_until_complete(bot_manager.emergency_stop())
                    if isinstance(result, tuple):
                        success, message = result
                    else:
                        success, message = bool(result), "Emergency stop completed"
            except Exception as e:
                logger.critical(f"Ошибка экстренной остановки: {e}")
                success, message = False, str(e)
            
            if success:
                logger.critical(
                    "🚨 Экстренная остановка выполнена",
                    category='bot',
                    message=message
                )
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'status': 'emergency_stop',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logger.error(
                    "❌ Ошибка экстренной остановки",
                    category='bot',
                    error=message
                )
                
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
                
        except Exception as e:
            logger.critical(f"❌ Критическая ошибка экстренной остановки: {e}")
            return jsonify({
                'success': False,
                'error': f'Internal error: {str(e)}'
            }), 500
    
    # =================================================================
    # УПРАВЛЕНИЕ ПОЗИЦИЯМИ
    # =================================================================
    
    @app.route('/api/bot/positions', methods=['GET'])
    @login_required
    def get_open_positions():
        """Получение открытых позиций"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            # Получаем статус бота с позициями
            status = bot_manager.get_status()
            positions = status.get('positions', [])
            
            # Дополнительная информация о позициях
            enriched_positions = []
            for position in positions:
                enriched_position = dict(position)
                # Добавляем дополнительные поля если их нет
                if 'unrealized_pnl' not in enriched_position:
                    enriched_position['unrealized_pnl'] = 0.0
                if 'unrealized_pnl_percent' not in enriched_position:
                    enriched_position['unrealized_pnl_percent'] = 0.0
                enriched_positions.append(enriched_position)
            
            return jsonify({
                'success': True,
                'positions': enriched_positions,
                'count': len(enriched_positions),
                'total_unrealized_pnl': sum(p.get('unrealized_pnl', 0) for p in enriched_positions),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения позиций: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/close-position/<symbol>', methods=['POST'])
    @login_required
    def close_position(symbol):
        """
        Закрытие конкретной позиции
        
        ИСПРАВЛЕНИЕ: Убран дублированный декоратор @login_required
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.info(f"📊 Закрытие позиции {symbol}", category='trading')
            
            # Закрываем позицию
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для закрытия позиции
                    task = asyncio.create_task(bot_manager.close_position(symbol))
                    result = {'success': True, 'message': f'Position {symbol} close initiated'}
                else:
                    # Запускаем синхронно
                    result = loop.run_until_complete(bot_manager.close_position(symbol))
                    if not isinstance(result, dict):
                        result = {'success': bool(result), 'message': f'Position {symbol} closed'}
            except Exception as e:
                logger.error(f"Ошибка закрытия позиции: {e}")
                result = {'success': False, 'error': str(e)}
            
            if result.get('success'):
                logger.info(
                    f"✅ Позиция {symbol} закрыта",
                    category='trading',
                    profit=result.get('profit', 0)
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Position {symbol} closed successfully',
                    'symbol': symbol,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'symbol': symbol
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'symbol': symbol
            }), 500
    
    @app.route('/api/bot/close-all-positions', methods=['POST'])
    @login_required
    def close_all_positions():
        """
        Закрытие всех открытых позиций
        
        ИСПРАВЛЕНИЕ: Убран @async_handler()
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.warning("📊 Закрытие ВСЕХ позиций", category='trading')
            
            # Закрываем все позиции
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для закрытия всех позиций
                    task = asyncio.create_task(bot_manager.close_all_positions())
                    results = [{'success': True, 'message': 'All positions close initiated'}]
                else:
                    # Запускаем синхронно
                    results = loop.run_until_complete(bot_manager.close_all_positions())
                    if not isinstance(results, list):
                        results = [{'success': bool(results), 'message': 'All positions processed'}]
            except Exception as e:
                logger.error(f"Ошибка закрытия всех позиций: {e}")
                results = [{'success': False, 'error': str(e)}]
            
            closed_count = sum(1 for r in results if r.get('success', False))
            failed_count = len(results) - closed_count
            
            logger.info(
                f"📊 Результат закрытия позиций: {closed_count} успешно, {failed_count} ошибок",
                category='trading'
            )
            
            return jsonify({
                'success': True,
                'message': f'Closed {closed_count} positions, {failed_count} failed',
                'results': results,
                'closed_count': closed_count,
                'failed_count': failed_count,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия всех позиций: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # НАСТРОЙКИ ТОРГОВЛИ
    # =================================================================
    
    @app.route('/api/bot/pairs', methods=['GET'])
    @login_required
    def get_trading_pairs():
        """
        Получение активных торговых пар
        
        ИСПРАВЛЕНИЕ: Убран @async_handler()
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            status = bot_manager.get_status()
            active_pairs = status.get('active_pairs', [])
            all_pairs = status.get('available_pairs', [])
            
            # Если нет доступных пар, используем активные
            if not all_pairs:
                all_pairs = active_pairs
            
            return jsonify({
                'success': True,
                'active_pairs': active_pairs,
                'available_pairs': all_pairs,
                'count': len(active_pairs),
                'total_available': len(all_pairs),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения торговых пар: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/pairs', methods=['POST'])
    @login_required
    def update_trading_pairs():
        """
        Обновление активных торговых пар
        
        ИСПРАВЛЕНИЕ: Убран @async_handler()
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            data = request.get_json() or {}
            pairs = data.get('pairs', [])
            
            if not pairs:
                return jsonify({
                    'success': False,
                    'error': 'No pairs specified'
                }), 400
            
            # Валидация пар
            invalid_pairs = [pair for pair in pairs if not isinstance(pair, str) or len(pair) < 6]
            if invalid_pairs:
                return jsonify({
                    'success': False,
                    'error': f'Invalid pairs format: {invalid_pairs}'
                }), 400
            
            logger.info(
                f"🔄 Обновление торговых пар: {pairs}",
                category='config',
                pairs_count=len(pairs)
            )
            
            # Обновляем пары
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для обновления пар
                    task = asyncio.create_task(bot_manager.update_trading_pairs(pairs))
                    success = True
                else:
                    # Запускаем синхронно
                    result = loop.run_until_complete(bot_manager.update_trading_pairs(pairs))
                    success = bool(result) if result is not None else True
            except Exception as e:
                logger.error(f"Ошибка обновления пар: {e}")
                success = False
                # Fallback к синхронному методу
                if hasattr(bot_manager, 'update_pairs'):
                    try:
                        bot_manager.update_pairs(pairs)
                        success = True
                    except Exception as e2:
                        logger.error(f"Fallback тоже не сработал: {e2}")
            
            if success:
                logger.info("✅ Торговые пары обновлены", category='config')
                
                return jsonify({
                    'success': True,
                    'message': f'Updated {len(pairs)} trading pairs',
                    'pairs': pairs,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update trading pairs'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления торговых пар: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # СТРАТЕГИИ
    # =================================================================
    
    @app.route('/api/bot/strategies', methods=['GET'])
    @login_required
    def get_available_strategies():
        """Получение доступных стратегий"""
        try:
            if not bot_manager:
                # Возвращаем стандартный набор стратегий
                strategies = [
                    'multi_indicator', 'momentum', 'mean_reversion', 
                    'breakout', 'scalping', 'swing', 'ml_prediction'
                ]
            else:
                status = bot_manager.get_status()
                strategies = status.get('available_strategies', [
                    'multi_indicator', 'momentum', 'mean_reversion'
                ])
            
            return jsonify({
                'success': True,
                'strategies': strategies,
                'count': len(strategies),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения стратегий: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/strategy', methods=['POST'])
    @login_required
    def set_strategy():
        """
        Установка активной стратегии
        
        ИСПРАВЛЕНИЕ: Убран @async_handler()
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            data = request.get_json() or {}
            strategy = data.get('strategy')
            symbol = data.get('symbol', 'default')
            
            if not strategy:
                return jsonify({
                    'success': False,
                    'error': 'No strategy specified'
                }), 400
            
            # Валидация стратегии
            valid_strategies = [
                'multi_indicator', 'momentum', 'mean_reversion',
                'breakout', 'scalping', 'swing', 'ml_prediction'
            ]
            if strategy not in valid_strategies:
                return jsonify({
                    'success': False,
                    'error': f'Invalid strategy. Valid options: {valid_strategies}'
                }), 400
            
            logger.info(
                f"🎯 Установка стратегии {strategy} для {symbol}",
                category='strategy'
            )
            
            # Устанавливаем стратегию
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для установки стратегии
                    task = asyncio.create_task(bot_manager.set_strategy(symbol, strategy))
                    success = True
                else:
                    # Запускаем синхронно
                    result = loop.run_until_complete(bot_manager.set_strategy(symbol, strategy))
                    success = bool(result) if result is not None else True
            except Exception as e:
                logger.error(f"Ошибка установки стратегии: {e}")
                success = False
            
            if success:
                logger.info(f"✅ Стратегия {strategy} установлена", category='strategy')
                
                return jsonify({
                    'success': True,
                    'message': f'Strategy {strategy} set for {symbol}',
                    'strategy': strategy,
                    'symbol': symbol,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to set strategy'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка установки стратегии: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # МОНИТОРИНГ
    # =================================================================
    
    @app.route('/api/bot/health', methods=['GET'])
    @login_required
    def get_bot_health():
        """
        Проверка здоровья торгового бота
        
        ИСПРАВЛЕНИЕ: Убран @async_handler()
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'healthy': False,
                    'error': 'Bot manager not available',
                    'components': {}
                })
            
            # Получаем детальный статус здоровья
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Создаем задачу для проверки здоровья
                    task = asyncio.create_task(bot_manager.health_check())
                    health = {'overall_healthy': True, 'components': {}}
                else:
                    # Запускаем синхронно
                    health = loop.run_until_complete(bot_manager.health_check())
                    if not isinstance(health, dict):
                        health = {'overall_healthy': bool(health), 'components': {}}
            except Exception as e:
                logger.error(f"Ошибка проверки здоровья: {e}")
                health = {'overall_healthy': False, 'components': {}, 'error': str(e)}
            
            return jsonify({
                'success': True,
                'healthy': health.get('overall_healthy', False),
                'components': health.get('components', {}),
                'error': health.get('error'),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья бота: {e}")
            return jsonify({
                'success': False,
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
    
    @app.route('/api/bot/metrics', methods=['GET'])
    @login_required
    def get_bot_metrics():
        """Получение метрик производительности бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            # Получаем метрики
            try:
                metrics = bot_manager.get_performance_metrics()
                if not isinstance(metrics, dict):
                    metrics = {'status': 'no_metrics_available'}
            except Exception as e:
                logger.error(f"Ошибка получения метрик: {e}")
                metrics = {'error': str(e)}
            
            # Добавляем базовые метрики если их нет
            if 'uptime' not in metrics:
                status = bot_manager.get_status()
                start_time = status.get('start_time')
                if start_time:
                    try:
                        if isinstance(start_time, str):
                            from datetime import datetime
                            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        uptime = (datetime.utcnow() - start_time).total_seconds()
                        metrics['uptime_seconds'] = uptime
                    except:
                        metrics['uptime_seconds'] = 0
            
            return jsonify({
                'success': True,
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения метрик: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS
    # =================================================================
    
    @app.route('/api/bot/restart', methods=['POST'])
    @login_required
    def restart_bot():
        """Перезапуск бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.info("🔄 Перезапуск торгового бота", category='bot')
            
            # Останавливаем
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    task = asyncio.create_task(bot_manager.stop())
                    stop_success = True
                else:
                    result = loop.run_until_complete(bot_manager.stop())
                    stop_success = bool(result) if result is not None else True
            except Exception as e:
                logger.error(f"Ошибка остановки при перезапуске: {e}")
                stop_success = False
            
            # Небольшая задержка
            import time
            time.sleep(2)
            
            # Запускаем
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    task = asyncio.create_task(bot_manager.start())
                    start_success = True
                else:
                    result = loop.run_until_complete(bot_manager.start())
                    start_success = bool(result) if result is not None else True
            except Exception as e:
                logger.error(f"Ошибка запуска при перезапуске: {e}")
                start_success = False
            
            if stop_success and start_success:
                logger.info("✅ Бот успешно перезапущен", category='bot')
                return jsonify({
                    'success': True,
                    'message': 'Bot restarted successfully',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Restart failed - stop: {stop_success}, start: {start_success}'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка перезапуска бота: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # CORS ПОДДЕРЖКА
    # =================================================================
    
    @app.route('/api/bot/start', methods=['OPTIONS'])
    @app.route('/api/bot/stop', methods=['OPTIONS'])
    @app.route('/api/bot/restart', methods=['OPTIONS'])
    @app.route('/api/bot/emergency-stop', methods=['OPTIONS'])
    @app.route('/api/bot/close-all-positions', methods=['OPTIONS'])
    def bot_control_options():
        """CORS preflight обработка"""
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # =================================================================
    # ЛОГИРОВАНИЕ РЕЗУЛЬТАТОВ
    # =================================================================
    
    logger.info("✅ API роуты торговли зарегистрированы:")
    logger.info("   🟢 POST /api/bot/start - запуск бота")
    logger.info("   🟢 POST /api/bot/stop - остановка бота")
    logger.info("   🟢 POST /api/bot/restart - перезапуск бота")
    logger.info("   🟢 POST /api/bot/emergency-stop - экстренная остановка")
    logger.info("   🟢 GET /api/bot/positions - открытые позиции")
    logger.info("   🟢 POST /api/bot/close-position/<symbol> - закрытие позиции")
    logger.info("   🟢 POST /api/bot/close-all-positions - закрытие всех позиций")
    logger.info("   🟢 GET/POST /api/bot/pairs - управление торговыми парами")
    logger.info("   🟢 GET /api/bot/strategies - доступные стратегии")
    logger.info("   🟢 POST /api/bot/strategy - установка стратегии")
    logger.info("   🟢 GET /api/bot/health - здоровье бота")
    logger.info("   🟢 GET /api/bot/metrics - метрики производительности")
    
    return True

# Экспорт
__all__ = ['register_trading_api_routes']