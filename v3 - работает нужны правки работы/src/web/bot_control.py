#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система управления торговым ботом через веб-интерфейс
Файл: src/web/bot_control.py

СОЗДАЙТЕ ЭТОТ ФАЙЛ: src/web/bot_control.py
"""

from flask import jsonify, request
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BotController:
    """Контроллер для управления ботом"""
    
    def __init__(self, bot_manager=None):
        self.bot_manager = bot_manager
        self.auto_trading = False
        self.trading_task = None
        logger.info("🤖 BotController инициализирован")
    
    def get_status(self) -> Dict[str, Any]:
        """Получить полный статус бота"""
        try:
            if not self.bot_manager:
                return {
                    'status': 'error',
                    'is_running': False,
                    'message': 'Bot manager не инициализирован',
                    'active_pairs': [],
                    'open_positions': 0,
                    'trades_today': 0,
                    'cycles_count': 0,
                    'uptime': 0,
                    'auto_trading': self.auto_trading,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Получаем статус от менеджера
            if hasattr(self.bot_manager, 'get_status'):
                try:
                    status = self.bot_manager.get_status()
                    if isinstance(status, dict):
                        # Дополняем статус нашими данными
                        status.update({
                            'auto_trading': self.auto_trading,
                            'trading_task_active': self.trading_task is not None and not self.trading_task.done(),
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        return status
                except Exception as e:
                    logger.warning(f"Ошибка получения статуса от менеджера: {e}")
            
            # Базовый статус если менеджер не отвечает
            return {
                'status': 'stopped',
                'is_running': False,
                'message': 'Менеджер не отвечает',
                'active_pairs': [],
                'open_positions': 0,
                'trades_today': 0,
                'cycles_count': 0,
                'uptime': 0,
                'auto_trading': self.auto_trading,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {
                'status': 'error',
                'is_running': False,
                'message': f'Ошибка: {str(e)}',
                'active_pairs': [],
                'open_positions': 0,
                'trades_today': 0,
                'cycles_count': 0,
                'uptime': 0,
                'auto_trading': self.auto_trading,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def start_bot(self, pairs: list = None, strategy: str = 'auto') -> Dict[str, Any]:
        """Запустить бота"""
        try:
            logger.info(f"🚀 Запуск бота. Пары: {pairs}, Стратегия: {strategy}")
            
            if not self.bot_manager:
                return {'success': False, 'message': 'Bot manager не инициализирован'}
            
            # Проверяем, не запущен ли уже
            if self.auto_trading and self.trading_task and not self.trading_task.done():
                return {'success': False, 'message': 'Бот уже запущен'}
            
            # Обновляем пары если указаны
            if pairs:
                await self._update_trading_pairs(pairs)
            
            # Запускаем торговую задачу
            self.auto_trading = True
            self.trading_task = asyncio.create_task(self._trading_loop())
            
            logger.info("✅ Бот запущен")
            return {'success': True, 'message': 'Бот успешно запущен'}
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            self.auto_trading = False
            return {'success': False, 'message': f'Ошибка запуска: {str(e)}'}
    
    async def stop_bot(self) -> Dict[str, Any]:
        """Остановить бота"""
        try:
            logger.info("⏹️ Остановка бота...")
            
            self.auto_trading = False
            
            # Останавливаем торговую задачу
            if self.trading_task and not self.trading_task.done():
                self.trading_task.cancel()
                try:
                    await self.trading_task
                except asyncio.CancelledError:
                    pass
            
            # Закрываем позиции если есть менеджер
            if self.bot_manager and hasattr(self.bot_manager, 'close_all_positions'):
                try:
                    await self.bot_manager.close_all_positions()
                except Exception as e:
                    logger.warning(f"Ошибка закрытия позиций: {e}")
            
            logger.info("✅ Бот остановлен")
            return {'success': True, 'message': 'Бот успешно остановлен'}
            
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            return {'success': False, 'message': f'Ошибка остановки: {str(e)}'}
    
    async def restart_bot(self) -> Dict[str, Any]:
        """Перезапустить бота"""
        try:
            logger.info("🔄 Перезапуск бота...")
            
            # Останавливаем
            await self.stop_bot()
            await asyncio.sleep(2)  # Пауза между остановкой и запуском
            
            # Запускаем
            result = await self.start_bot()
            
            if result['success']:
                return {'success': True, 'message': 'Бот успешно перезапущен'}
            else:
                return {'success': False, 'message': f'Ошибка перезапуска: {result["message"]}'}
                
        except Exception as e:
            logger.error(f"Ошибка перезапуска бота: {e}")
            return {'success': False, 'message': f'Ошибка перезапуска: {str(e)}'}
    
    async def _trading_loop(self):
        """Основной торговый цикл"""
        logger.info("📈 Торговый цикл запущен")
        
        try:
            while self.auto_trading:
                try:
                    # 1. Анализ рынка
                    market_data = await self.analyze_market()
                    
                    # 2. Генерация сигналов
                    signals = await self.generate_signals(market_data)
                    
                    # 3. Исполнение сделок
                    if signals:
                        await self.execute_trades(signals)
                    
                    # 4. Управление позициями
                    await self.manage_positions()
                    
                    # Пауза между циклами
                    await asyncio.sleep(60)  # 1 минута
                    
                except asyncio.CancelledError:
                    logger.info("Торговый цикл отменен")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в торговом цикле: {e}")
                    await asyncio.sleep(30)  # Пауза при ошибке
                    
        except asyncio.CancelledError:
            logger.info("Торговый цикл завершен")
        except Exception as e:
            logger.error(f"Критическая ошибка торгового цикла: {e}")
        finally:
            self.auto_trading = False
            logger.info("📈 Торговый цикл завершен")
    
    async def analyze_market(self):
        """Анализ рынка"""
        logger.info("📊 Анализируем рынок...")
        
        if self.bot_manager and hasattr(self.bot_manager, 'analyze_market'):
            try:
                return await self.bot_manager.analyze_market()
            except Exception as e:
                logger.warning(f"Ошибка анализа рынка: {e}")
        
        # Базовая имитация анализа
        await asyncio.sleep(1)
        return {'trend': 'neutral', 'volatility': 'medium', 'signals': []}
    
    async def generate_signals(self, market_data):
        """Генерация торговых сигналов"""
        logger.info("🎯 Генерируем сигналы...")
        
        if self.bot_manager and hasattr(self.bot_manager, 'generate_signals'):
            try:
                return await self.bot_manager.generate_signals(market_data)
            except Exception as e:
                logger.warning(f"Ошибка генерации сигналов: {e}")
        
        # Имитация генерации сигналов
        await asyncio.sleep(1)
        return []
    
    async def execute_trades(self, signals):
        """Исполнение сделок"""
        logger.info(f"💼 Исполняем {len(signals)} сделок...")
        
        if self.bot_manager and hasattr(self.bot_manager, 'execute_trades'):
            try:
                return await self.bot_manager.execute_trades(signals)
            except Exception as e:
                logger.warning(f"Ошибка исполнения сделок: {e}")
        
        # Имитация исполнения
        await asyncio.sleep(1)
    
    async def manage_positions(self):
        """Управление позициями"""
        logger.info("⚖️ Управляем позициями...")
        
        if self.bot_manager and hasattr(self.bot_manager, 'manage_positions'):
            try:
                return await self.bot_manager.manage_positions()
            except Exception as e:
                logger.warning(f"Ошибка управления позициями: {e}")
        
        # Имитация управления
        await asyncio.sleep(1)
    
    async def _update_trading_pairs(self, pairs):
        """Обновление торговых пар"""
        try:
            if self.bot_manager and hasattr(self.bot_manager, 'update_pairs'):
                await self.bot_manager.update_pairs(pairs)
            logger.info(f"✅ Обновлены торговые пары: {pairs}")
        except Exception as e:
            logger.warning(f"Ошибка обновления пар: {e}")


def register_bot_control_routes(app, bot_manager=None):
    """
    Регистрирует роуты для управления ботом
    """
    logger.info("📝 Регистрируем роуты управления ботом...")
    
    bot_controller = BotController(bot_manager)
    
    @app.route('/api/bot/status')
    def get_bot_status_action():
        """Получить статус бота"""
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
    def start_bot_action():
        """Запустить бота"""
        try:
            data = request.get_json() or {}
            pairs = data.get('pairs', ['BTCUSDT', 'ETHUSDT'])
            strategy = data.get('strategy', 'auto')
            
            # Запускаем асинхронно
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    bot_controller.start_bot(pairs, strategy)
                )
                return jsonify(result)
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Ошибка API запуска: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    def stop_bot_action():
        """Остановить бота"""
        try:
            # Запускаем асинхронно
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    bot_controller.stop_bot()
                )
                return jsonify(result)
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Ошибка API остановки: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/restart', methods=['POST'])
    def restart_bot_action():
        """Перезапустить бота"""
        try:
            # Запускаем асинхронно
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    bot_controller.restart_bot()
                )
                return jsonify(result)
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Ошибка API перезапуска: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/config', methods=['GET', 'POST'])
    def bot_config_action():
        """Получить/обновить конфигурацию бота"""
        if request.method == 'GET':
            try:
                config = {
                    'auto_trading': bot_controller.auto_trading,
                    'active_pairs': getattr(bot_controller.bot_manager, 'active_pairs', []),
                    'max_positions': 1,  # Из конфигурации
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
                # Здесь можно добавить логику обновления конфигурации
                logger.info(f"Обновление конфигурации: {data}")
                return jsonify({'success': True, 'message': 'Конфигурация обновлена'})
            except Exception as e:
                logger.error(f"Ошибка обновления конфигурации: {e}")
                return jsonify({'error': str(e)}), 500
    
    logger.info("✅ Роуты управления ботом зарегистрированы")
    return bot_controller


# Экспортируем основные функции
__all__ = ['BotController', 'register_bot_control_routes']