#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система управления торговым ботом через веб-интерфейс
Файл: src/web/bot_control.py

ИНСТРУКЦИЯ: 
1. Создайте файл src/web/bot_control.py
2. Скопируйте туда ВСЁ содержимое этого артефакта
3. Сохраните файл
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
                    logger.warning(f"Ошибка получения статуса от bot_manager: {e}")
            
            # Простой статус
            return {
                'status': 'stopped',
                'is_running': False,
                'auto_trading': self.auto_trading,
                'active_pairs': ['BTCUSDT', 'ETHUSDT'],
                'open_positions': 0,
                'trades_today': 0,
                'cycles_count': 0,
                'uptime': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Ошибка получения статуса бота: {e}")
            return {
                'status': 'error',
                'is_running': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def start_bot(self, pairs=None, strategy='auto') -> Dict[str, Any]:
        """Запустить бота"""
        try:
            logger.info(f"🚀 Запуск бота с парами: {pairs}, стратегия: {strategy}")
            
            if not self.bot_manager:
                logger.warning("Bot manager недоступен, запускаем демо-режим")
                # Запускаем демо-режим
                self.auto_trading = True
                self.trading_task = asyncio.create_task(self.demo_trading_loop())
                
                return {
                    'success': True,
                    'message': 'Демо-режим запущен',
                    'strategy': strategy,
                    'pairs': pairs or ['BTCUSDT', 'ETHUSDT']
                }
            
            # Обновляем пары если переданы
            if pairs:
                if hasattr(self.bot_manager, 'update_pairs'):
                    try:
                        if asyncio.iscoroutinefunction(self.bot_manager.update_pairs):
                            await self.bot_manager.update_pairs(pairs)
                        else:
                            self.bot_manager.update_pairs(pairs)
                    except Exception as e:
                        logger.warning(f"Не удалось обновить пары: {e}")
                else:
                    logger.info(f"Установлены торговые пары: {pairs}")
            
            # Запускаем бота
            if hasattr(self.bot_manager, 'start'):
                try:
                    if asyncio.iscoroutinefunction(self.bot_manager.start):
                        result = await self.bot_manager.start()
                    else:
                        result = self.bot_manager.start()
                    
                    if result:
                        self.auto_trading = True
                        # Запускаем торговый цикл
                        self.trading_task = asyncio.create_task(self.trading_loop())
                        
                        return {
                            'success': True,
                            'message': 'Бот успешно запущен',
                            'strategy': strategy,
                            'pairs': pairs or ['BTCUSDT', 'ETHUSDT']
                        }
                    else:
                        return {
                            'success': False,
                            'message': 'Не удалось запустить бота'
                        }
                except Exception as e:
                    logger.error(f"Ошибка запуска bot_manager: {e}")
                    return {
                        'success': False,
                        'message': f'Ошибка запуска: {str(e)}'
                    }
            else:
                # Имитация запуска
                self.auto_trading = True
                self.trading_task = asyncio.create_task(self.demo_trading_loop())
                
                return {
                    'success': True,
                    'message': 'Демо-режим запущен',
                    'strategy': strategy,
                    'pairs': pairs or ['BTCUSDT', 'ETHUSDT']
                }
                
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            return {
                'success': False,
                'message': f'Ошибка запуска: {str(e)}'
            }
    
    async def stop_bot(self) -> Dict[str, Any]:
        """Остановить бота"""
        try:
            logger.info("🛑 Останавливаем бота...")
            
            # Останавливаем торговый цикл
            self.auto_trading = False
            
            if self.trading_task and not self.trading_task.done():
                self.trading_task.cancel()
                try:
                    await self.trading_task
                except asyncio.CancelledError:
                    logger.info("Торговый цикл остановлен")
            
            # Останавливаем менеджер бота
            if self.bot_manager and hasattr(self.bot_manager, 'stop'):
                try:
                    if asyncio.iscoroutinefunction(self.bot_manager.stop):
                        await self.bot_manager.stop()
                    else:
                        self.bot_manager.stop()
                except Exception as e:
                    logger.warning(f"Ошибка остановки bot_manager: {e}")
            
            return {
                'success': True,
                'message': 'Бот успешно остановлен'
            }
            
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            return {
                'success': False,
                'message': f'Ошибка остановки: {str(e)}'
            }
    
    async def trading_loop(self):
        """Основной торговый цикл"""
        logger.info("🤖 Запущен торговый цикл")
        
        cycle_count = 0
        
        try:
            while self.auto_trading:
                cycle_count += 1
                logger.info(f"🔄 Торговый цикл #{cycle_count}")
                
                # Основной торговый алгоритм
                await self.execute_trading_cycle()
                
                # Пауза между циклами (60 секунд)
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info("Торговый цикл отменен")
        except Exception as e:
            logger.error(f"Ошибка в торговом цикле: {e}")
        finally:
            logger.info(f"Торговый цикл завершен после {cycle_count} циклов")
    
    async def demo_trading_loop(self):
        """Демо торговый цикл для тестирования"""
        logger.info("🎮 Запущен демо торговый цикл")
        
        cycle_count = 0
        
        try:
            while self.auto_trading:
                cycle_count += 1
                logger.info(f"🎮 Демо цикл #{cycle_count}")
                
                # Имитируем анализ рынка
                await self.simulate_market_analysis()
                
                # Имитируем принятие торговых решений
                if cycle_count % 5 == 0:  # Каждый 5-й цикл
                    await self.simulate_trade()
                
                # Пауза (30 секунд для демо)
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            logger.info("Демо торговый цикл отменен")
        except Exception as e:
            logger.error(f"Ошибка в демо цикле: {e}")
    
    async def execute_trading_cycle(self):
        """Выполнить один торговый цикл"""
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
            
        except Exception as e:
            logger.error(f"Ошибка в торговом цикле: {e}")
    
    async def analyze_market(self):
        """Анализ рынка"""
        logger.info("📊 Анализируем рынок...")
        await asyncio.sleep(1)  # Имитация анализа
        return {'trend': 'neutral', 'volatility': 'medium'}
    
    async def generate_signals(self, market_data):
        """Генерация торговых сигналов"""
        logger.info("🎯 Генерируем сигналы...")
        await asyncio.sleep(1)  # Имитация генерации
        return []
    
    async def execute_trades(self, signals):
        """Исполнение сделок"""
        logger.info(f"💼 Исполняем {len(signals)} сделок...")
        await asyncio.sleep(1)  # Имитация исполнения
    
    async def manage_positions(self):
        """Управление позициями"""
        logger.info("⚖️ Управляем позициями...")
        await asyncio.sleep(1)  # Имитация управления
    
    async def simulate_market_analysis(self):
        """Имитация анализа рынка"""
        logger.info("📊 [ДЕМО] Анализируем рынок...")
        await asyncio.sleep(2)
    
    async def simulate_trade(self):
        """Имитация сделки"""
        logger.info("💰 [ДЕМО] Открываем позицию BTCUSDT")
        await asyncio.sleep(1)


def register_bot_control_routes(app, bot_manager=None):
    """
    Регистрирует роуты для управления ботом
    """
    logger.info("📝 Регистрируем роуты управления ботом...")
    
    bot_controller = BotController(bot_manager)
    
    @app.route('/api/bot/status')
    def get_bot_status():
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
    def start_bot():
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
            finally:
                loop.close()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    def stop_bot():
        """Остановить бота"""
        try:
            # Останавливаем асинхронно
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    bot_controller.stop_bot()
                )
            finally:
                loop.close()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    logger.info("✅ API управления ботом зарегистрированы:")
    logger.info("   🤖 GET /api/bot/status - статус бота")
    logger.info("   ▶️ POST /api/bot/start - запуск бота")
    logger.info("   ⏹️ POST /api/bot/stop - остановка бота")
    
    return bot_controller