#!/usr/bin/env python3
"""
Скрипт для исправления всех критических проблем проекта
Путь: scripts/fix_all_issues.py
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

def fix_bot_manager():
    """Исправляем проблему с SQLAlchemy сессией в bot/manager.py"""
    manager_file = 'src/bot/manager.py'
    
    print(f"🔧 Исправляем {manager_file}...")
    
    with open(manager_file, 'r') as f:
        content = f.read()
    
    # Исправляем метод _save_signal
    old_save_signal = """def _save_signal(self, signal: Signal):
        \"\"\"
        Сохранение торгового сигнала в базу данных
        
        Args:
            signal: Объект сигнала для сохранения
        \"\"\"
        def _save_operation():
            db = SessionLocal()
            try:
                db.add(signal)
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"сохранение сигнала {signal.symbol}", _save_operation)"""
    
    new_save_signal = """def _save_signal(self, signal: Signal):
        \"\"\"
        Сохранение торгового сигнала в базу данных
        
        Args:
            signal: Объект сигнала для сохранения
        \"\"\"
        def _save_operation():
            db = SessionLocal()
            try:
                # Создаем новый объект Signal в контексте текущей сессии
                new_signal = Signal(
                    symbol=signal.symbol,
                    action=signal.action,
                    confidence=signal.confidence,
                    price=signal.price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    strategy=signal.strategy,
                    reason=signal.reason,
                    created_at=signal.created_at
                )
                db.add(new_signal)
                db.commit()
                # Обновляем ID в исходном объекте
                signal.id = new_signal.id
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"сохранение сигнала {signal.symbol}", _save_operation)"""
    
    content = content.replace(old_save_signal, new_save_signal)
    
    # Исправляем метод _update_signal_db
    old_update_signal = """def _update_signal_db(self, signal: Signal):
        \"\"\"
        Обновление сигнала в базе данных
        
        Args:
            signal: Объект сигнала для обновления
        \"\"\"
        def _update_operation():
            db = SessionLocal()
            try:
                db.merge(signal)
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"обновление сигнала {signal.symbol}", _update_operation)"""
    
    new_update_signal = """def _update_signal_db(self, signal: Signal):
        \"\"\"
        Обновление сигнала в базе данных
        
        Args:
            signal: Объект сигнала для обновления
        \"\"\"
        def _update_operation():
            db = SessionLocal()
            try:
                # Получаем объект из БД и обновляем его
                db_signal = db.query(Signal).filter(Signal.id == signal.id).first()
                if db_signal:
                    db_signal.executed = signal.executed
                    db_signal.executed_at = signal.executed_at
                    db_signal.trade_id = signal.trade_id
                    db.commit()
                    return True
                else:
                    logger.warning(f"Сигнал с ID {signal.id} не найден в БД")
                    return False
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"обновление сигнала {signal.symbol}", _update_operation)"""
    
    content = content.replace(old_update_signal, new_update_signal)
    
    with open(manager_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Исправлен {manager_file}")

def fix_telegram_notifications():
    """Исправляем форматирование Telegram сообщений"""
    telegram_file = 'src/notifications/telegram.py'
    
    print(f"🔧 Исправляем {telegram_file}...")
    
    with open(telegram_file, 'r') as f:
        content = f.read()
    
    # Исправляем send_error чтобы правильно экранировать HTML
    old_send_error = """async def send_error(self, error: str):
        \"\"\"Уведомление об ошибке\"\"\"
        # Ограничиваем длину сообщения
        if len(error) > 500:
            error = error[:497] + "..."
        
        text = f\"\"\"🚨 <b>Ошибка</b>
        
<code>{error}</code>
        
⏰ Время: {datetime.now().strftime('%H:%M:%S')}\"\"\"
        
        await self.send_message(text)"""
    
    new_send_error = """async def send_error(self, error: str):
        \"\"\"Уведомление об ошибке\"\"\"
        # Ограничиваем длину сообщения и экранируем HTML
        if len(error) > 500:
            error = error[:497] + "..."
        
        # Экранируем специальные символы HTML
        error = error.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        text = f\"\"\"🚨 <b>Ошибка</b>
        
<code>{error}</code>
        
⏰ Время: {datetime.now().strftime('%H:%M:%S')}\"\"\"
        
        await self.send_message(text)"""
    
    content = content.replace(old_send_error, new_send_error)
    
    with open(telegram_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Исправлен {telegram_file}")

def create_safe_strategies():
    """Создаем безопасные версии стратегий"""
    
    # 1. Безопасная версия multi_indicator стратегии
    safe_multi_indicator = '''"""
Безопасная версия мульти-индикаторной стратегии
Путь: src/strategies/safe_multi_indicator.py
"""
import pandas as pd
import numpy as np
import ta
from typing import Dict, Any
import logging
import warnings

from .base import BaseStrategy, TradingSignal

# Подавляем предупреждения NumPy
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)

class SafeMultiIndicatorStrategy(BaseStrategy):
    """
    Безопасная мульти-индикаторная стратегия с защитой от ошибок
    """
    
    def __init__(self):
        super().__init__("safe_multi_indicator")
        self.min_confidence = 0.65
        self.min_indicators_confirm = 3
    
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Безопасный анализ с обработкой всех исключений"""
        
        if not self.validate_dataframe(df):
            return TradingSignal('WAIT', 0, 0, reason='Недостаточно данных')
        
        try:
            # Очищаем данные от NaN и inf
            df = self._clean_dataframe(df)
            
            # Рассчитываем индикаторы с защитой
            indicators = self._safe_calculate_indicators(df)
            
            if not indicators:
                return TradingSignal('WAIT', 0, 0, reason='Ошибка расчета индикаторов')
            
            # Анализируем сигналы
            signals = self._analyze_signals(indicators, df)
            
            # Принимаем решение
            return self._make_decision(signals, indicators, df)
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason='Ошибка анализа')
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Очистка данных от некорректных значений"""
        df = df.copy()
        
        # Заменяем inf на NaN
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Заполняем NaN методом forward fill
        df.fillna(method='ffill', inplace=True)
        
        # Если остались NaN, заполняем средними значениями
        df.fillna(df.mean(), inplace=True)
        
        return df
    
    def _safe_calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Безопасный расчет индикаторов"""
        indicators = {}
        
        try:
            # Подавляем предупреждения для этого блока
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # RSI
                try:
                    indicators['rsi'] = ta.momentum.rsi(df['close'], window=14).iloc[-1]
                    if pd.isna(indicators['rsi']):
                        indicators['rsi'] = 50.0
                except:
                    indicators['rsi'] = 50.0
                
                # MACD
                try:
                    macd = ta.trend.MACD(df['close'])
                    indicators['macd'] = macd.macd().iloc[-1]
                    indicators['macd_signal'] = macd.macd_signal().iloc[-1]
                    indicators['macd_diff'] = macd.macd_diff().iloc[-1]
                    
                    # Проверка на NaN
                    for key in ['macd', 'macd_signal', 'macd_diff']:
                        if pd.isna(indicators[key]):
                            indicators[key] = 0.0
                except:
                    indicators['macd'] = 0.0
                    indicators['macd_signal'] = 0.0
                    indicators['macd_diff'] = 0.0
                
                # Bollinger Bands
                try:
                    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
                    indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
                    indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
                    indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
                    indicators['bb_percent'] = bb.bollinger_pband().iloc[-1]
                    
                    # Проверка на NaN
                    current_price = df['close'].iloc[-1]
                    for key in ['bb_upper', 'bb_lower', 'bb_middle']:
                        if pd.isna(indicators[key]):
                            indicators[key] = current_price
                    if pd.isna(indicators['bb_percent']):
                        indicators['bb_percent'] = 0.5
                except:
                    current_price = df['close'].iloc[-1]
                    indicators['bb_upper'] = current_price * 1.02
                    indicators['bb_lower'] = current_price * 0.98
                    indicators['bb_middle'] = current_price
                    indicators['bb_percent'] = 0.5
                
                # EMA
                try:
                    indicators['ema_9'] = ta.trend.ema_indicator(df['close'], window=9).iloc[-1]
                    indicators['ema_21'] = ta.trend.ema_indicator(df['close'], window=21).iloc[-1]
                    indicators['ema_50'] = ta.trend.ema_indicator(df['close'], window=50).iloc[-1]
                except:
                    current_price = df['close'].iloc[-1]
                    indicators['ema_9'] = current_price
                    indicators['ema_21'] = current_price
                    indicators['ema_50'] = current_price
                
                # ADX (с защитой от деления на ноль)
                try:
                    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
                    indicators['adx'] = adx.adx().iloc[-1]
                    indicators['adx_pos'] = adx.adx_pos().iloc[-1]
                    indicators['adx_neg'] = adx.adx_neg().iloc[-1]
                    
                    # Проверка на NaN
                    for key in ['adx', 'adx_pos', 'adx_neg']:
                        if pd.isna(indicators[key]):
                            indicators[key] = 0.0
                except:
                    indicators['adx'] = 0.0
                    indicators['adx_pos'] = 0.0
                    indicators['adx_neg'] = 0.0
                
                # ATR
                try:
                    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'])
                    indicators['atr'] = atr.average_true_range().iloc[-1]
                    if pd.isna(indicators['atr']):
                        indicators['atr'] = df['close'].iloc[-1] * 0.02
                except:
                    indicators['atr'] = df['close'].iloc[-1] * 0.02
                
                # Volume
                try:
                    indicators['volume_sma'] = df['volume'].rolling(window=20).mean().iloc[-1]
                    indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
                    if pd.isna(indicators['volume_ratio']):
                        indicators['volume_ratio'] = 1.0
                except:
                    indicators['volume_sma'] = df['volume'].mean()
                    indicators['volume_ratio'] = 1.0
                
                # Текущая цена
                indicators['current_price'] = df['close'].iloc[-1]
                
                return indicators
                
        except Exception as e:
            logger.error(f"Критическая ошибка расчета индикаторов: {e}")
            return {}
    
    def _analyze_signals(self, indicators: Dict, df: pd.DataFrame) -> Dict:
        """Анализ сигналов с защитой от ошибок"""
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }
        
        try:
            # RSI сигналы
            if indicators['rsi'] < 30:
                signals['buy_signals'].append(('RSI', 'Перепроданность', 0.8))
            elif indicators['rsi'] > 70:
                signals['sell_signals'].append(('RSI', 'Перекупленность', 0.8))
            
            # MACD сигналы
            if indicators['macd'] > indicators['macd_signal'] and indicators['macd_diff'] > 0:
                signals['buy_signals'].append(('MACD', 'Бычье пересечение', 0.7))
            elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_diff'] < 0:
                signals['sell_signals'].append(('MACD', 'Медвежье пересечение', 0.7))
            
            # Bollinger Bands сигналы
            if indicators['bb_percent'] < 0.2:
                signals['buy_signals'].append(('BB', 'Цена у нижней границы', 0.6))
            elif indicators['bb_percent'] > 0.8:
                signals['sell_signals'].append(('BB', 'Цена у верхней границы', 0.6))
            
            # EMA тренд
            if (indicators['ema_9'] > indicators['ema_21'] > indicators['ema_50'] and 
                indicators['current_price'] > indicators['ema_9']):
                signals['buy_signals'].append(('EMA', 'Восходящий тренд', 0.7))
            elif (indicators['ema_9'] < indicators['ema_21'] < indicators['ema_50'] and 
                  indicators['current_price'] < indicators['ema_9']):
                signals['sell_signals'].append(('EMA', 'Нисходящий тренд', 0.7))
            
            # ADX сила тренда
            if indicators['adx'] > 25:
                if indicators['adx_pos'] > indicators['adx_neg']:
                    signals['buy_signals'].append(('ADX', 'Сильный восходящий тренд', 0.6))
                else:
                    signals['sell_signals'].append(('ADX', 'Сильный нисходящий тренд', 0.6))
            
            # Volume подтверждение
            if indicators['volume_ratio'] > 1.5:
                signals['neutral_signals'].append(('Volume', 'Высокий объем', 0.5))
            
            return signals
            
        except Exception as e:
            logger.error(f"Ошибка анализа сигналов: {e}")
            return signals
    
    def _make_decision(self, signals: Dict, indicators: Dict, df: pd.DataFrame) -> TradingSignal:
        """Принятие решения с защитой от ошибок"""
        try:
            buy_score = sum(signal[2] for signal in signals['buy_signals'])
            sell_score = sum(signal[2] for signal in signals['sell_signals'])
            
            buy_count = len(signals['buy_signals'])
            sell_count = len(signals['sell_signals'])
            
            current_price = indicators['current_price']
            atr = indicators['atr']
            
            # Проверяем минимальное количество подтверждений
            if buy_count >= self.min_indicators_confirm and buy_score > sell_score:
                # Безопасный расчет уровней
                stop_loss = max(current_price * 0.95, current_price - 2 * atr)
                take_profit = min(current_price * 1.1, current_price + 3 * atr)
                
                # Проверка risk/reward
                risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
                if risk_reward < 1.5:
                    take_profit = current_price + (current_price - stop_loss) * 2
                
                confidence = min(0.95, buy_score / (buy_count * 0.8))
                
                reasons = [f"{sig[0]}: {sig[1]}" for sig in signals['buy_signals']]
                reason = "; ".join(reasons[:3])
                
                return TradingSignal(
                    action='BUY',
                    confidence=confidence,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=reason,
                    risk_reward_ratio=risk_reward,
                    indicators=indicators
                )
                
            elif sell_count >= self.min_indicators_confirm and sell_score > buy_score:
                # Безопасный расчет уровней
                stop_loss = min(current_price * 1.05, current_price + 2 * atr)
                take_profit = max(current_price * 0.9, current_price - 3 * atr)
                
                # Проверка risk/reward
                risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
                if risk_reward < 1.5:
                    take_profit = current_price - (stop_loss - current_price) * 2
                
                confidence = min(0.95, sell_score / (sell_count * 0.8))
                
                reasons = [f"{sig[0]}: {sig[1]}" for sig in signals['sell_signals']]
                reason = "; ".join(reasons[:3])
                
                return TradingSignal(
                    action='SELL',
                    confidence=confidence,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=reason,
                    risk_reward_ratio=risk_reward,
                    indicators=indicators
                )
            
            else:
                reason = f"Недостаточно подтверждений (BUY: {buy_count}, SELL: {sell_count})"
                return TradingSignal(
                    action='WAIT',
                    confidence=0,
                    price=current_price,
                    reason=reason,
                    indicators=indicators
                )
                
        except Exception as e:
            logger.error(f"Ошибка принятия решения: {e}")
            return TradingSignal(
                action='WAIT',
                confidence=0,
                price=df['close'].iloc[-1],
                reason='Ошибка принятия решения'
            )
'''
    
    # Сохраняем безопасную версию
    with open('src/strategies/safe_multi_indicator.py', 'w', encoding='utf-8') as f:
        f.write(safe_multi_indicator)
    
    print("✅ Создана безопасная версия multi_indicator стратегии")
    
    # 2. Консервативная стратегия
    conservative_strategy = '''"""
Консервативная стратегия для безопасной торговли
Путь: src/strategies/conservative.py
"""
import pandas as pd
import numpy as np
import ta
from typing import Dict
import logging

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class ConservativeStrategy(BaseStrategy):
    """
    Консервативная стратегия с жесткими критериями входа
    Минимизирует риски за счет снижения количества сделок
    """
    
    def __init__(self):
        super().__init__("conservative")
        self.min_confidence = 0.75  # Высокий порог уверенности
        self.min_risk_reward = 2.5  # Минимум 1:2.5
        self.max_risk_percent = 1.0  # Максимум 1% риска на сделку
    
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Консервативный анализ с множественными подтверждениями"""
        
        if not self.validate_dataframe(df) or len(df) < 200:
            return TradingSignal('WAIT', 0, 0, reason='Недостаточно данных')
        
        try:
            # Рассчитываем индикаторы
            indicators = self._calculate_indicators(df)
            
            # Проверяем рыночные условия
            market_condition = self._check_market_conditions(indicators, df)
            
            if market_condition == 'UNSUITABLE':
                return TradingSignal('WAIT', 0, 0, reason='Неподходящие рыночные условия')
            
            # Ищем сигналы входа
            entry_signal = self._find_entry_signal(indicators, market_condition)
            
            return entry_signal
            
        except Exception as e:
            logger.error(f"Ошибка консервативного анализа {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason='Ошибка анализа')
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет надежных индикаторов"""
        indicators = {}
        
        # Скользящие средние для определения тренда
        indicators['sma_50'] = df['close'].rolling(window=50).mean().iloc[-1]
        indicators['sma_200'] = df['close'].rolling(window=200).mean().iloc[-1]
        
        # RSI для определения перекупленности/перепроданности
        indicators['rsi'] = ta.momentum.rsi(df['close'], window=14).iloc[-1]
        
        # ATR для волатильности
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'])
        indicators['atr'] = atr.average_true_range().iloc[-1]
        indicators['atr_percent'] = (indicators['atr'] / df['close'].iloc[-1]) * 100
        
        # Объемный анализ
        indicators['volume_sma'] = df['volume'].rolling(window=50).mean().iloc[-1]
        indicators['volume_trend'] = df['volume'].rolling(window=10).mean().iloc[-1] / indicators['volume_sma']
        
        # Поддержка и сопротивление
        indicators['resistance'] = df['high'].rolling(window=20).max().iloc[-1]
        indicators['support'] = df['low'].rolling(window=20).min().iloc[-1]
        
        # Текущая цена
        indicators['current_price'] = df['close'].iloc[-1]
        
        return indicators
    
    def _check_market_conditions(self, indicators: Dict, df: pd.DataFrame) -> str:
        """Проверка рыночных условий"""
        
        # 1. Проверяем волатильность - не торгуем при экстремальной волатильности
        if indicators['atr_percent'] > 5:  # Волатильность > 5%
            return 'UNSUITABLE'
        
        # 2. Проверяем объем - должен быть стабильный
        if indicators['volume_trend'] < 0.5 or indicators['volume_trend'] > 3:
            return 'UNSUITABLE'
        
        # 3. Определяем тренд
        if indicators['current_price'] > indicators['sma_50'] > indicators['sma_200']:
            return 'UPTREND'
        elif indicators['current_price'] < indicators['sma_50'] < indicators['sma_200']:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def _find_entry_signal(self, indicators: Dict, market_condition: str) -> TradingSignal:
        """Поиск консервативных точек входа"""
        
        current_price = indicators['current_price']
        atr = indicators['atr']
        
        # Сигнал покупки только в восходящем тренде
        if market_condition == 'UPTREND':
            # Условия для покупки:
            # 1. RSI вышел из зоны перепроданности (30-40)
            # 2. Цена выше SMA50
            # 3. Откат к поддержке завершен
            
            if (30 < indicators['rsi'] < 40 and
                current_price > indicators['sma_50'] and
                current_price < indicators['sma_50'] * 1.02):  # Близко к SMA50
                
                # Консервативные уровни
                stop_loss = indicators['support']  # Стоп под уровнем поддержки
                take_profit = current_price + (current_price - stop_loss) * 3  # R:R = 1:3
                
                # Проверка риска
                risk_percent = ((current_price - stop_loss) / current_price) * 100
                if risk_percent > self.max_risk_percent:
                    stop_loss = current_price * (1 - self.max_risk_percent / 100)
                
                risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
                
                if risk_reward >= self.min_risk_reward:
                    return TradingSignal(
                        action='BUY',
                        confidence=0.8,
                        price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        reason='Консервативная покупка: откат в восходящем тренде',
                        risk_reward_ratio=risk_reward,
                        indicators=indicators
                    )
        
        # Сигнал продажи только в нисходящем тренде
        elif market_condition == 'DOWNTREND':
            if (60 < indicators['rsi'] < 70 and
                current_price < indicators['sma_50'] and
                current_price > indicators['sma_50'] * 0.98):  # Близко к SMA50
                
                stop_loss = indicators['resistance']
                take_profit = current_price - (stop_loss - current_price) * 3
                
                risk_percent = ((stop_loss - current_price) / current_price) * 100
                if risk_percent > self.max_risk_percent:
                    stop_loss = current_price * (1 + self.max_risk_percent / 100)
                
                risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
                
                if risk_reward >= self.min_risk_reward:
                    return TradingSignal(
                        action='SELL',
                        confidence=0.8,
                        price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        reason='Консервативная продажа: откат в нисходящем тренде',
                        risk_reward_ratio=risk_reward,
                        indicators=indicators
                    )
        
        return TradingSignal(
            action='WAIT',
            confidence=0,
            price=current_price,
            reason=f'Ждем подходящих условий в {market_condition}'
        )
'''
    
    with open('src/strategies/conservative.py', 'w', encoding='utf-8') as f:
        f.write(conservative_strategy)
    
    print("✅ Создана консервативная стратегия")

def update_factory():
    """Обновляем фабрику стратегий"""
    factory_file = 'src/strategies/factory.py'
    
    # Читаем текущий файл
    with open(factory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем импорты новых стратегий
    if 'from .safe_multi_indicator import SafeMultiIndicatorStrategy' not in content:
        # Добавляем после последнего импорта
        import_line = "from .scalping import ScalpingStrategy"
        if import_line in content:
            content = content.replace(
                import_line,
                import_line + "\nfrom .safe_multi_indicator import SafeMultiIndicatorStrategy\nfrom .conservative import ConservativeStrategy"
            )
    
    # Регистрируем новые стратегии
    if "'safe_multi_indicator': SafeMultiIndicatorStrategy" not in content:
        # Добавляем в словарь стратегий
        strategies_dict_end = "'scalping': ScalpingStrategy"
        if strategies_dict_end in content:
            content = content.replace(
                strategies_dict_end,
                strategies_dict_end + ",\n        'safe_multi_indicator': SafeMultiIndicatorStrategy,\n        'conservative': ConservativeStrategy"
            )
    
    with open(factory_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Обновлена фабрика стратегий")

def create_update_sql():
    """Создаем SQL для обновления БД"""
    update_sql = """-- Обновляем стратегию на безопасную версию
UPDATE trading_pairs 
SET strategy = 'safe_multi_indicator',
    stop_loss_percent = 1.5,
    take_profit_percent = 3.0
WHERE strategy = 'multi_indicator';

-- Для консервативной торговли можно выбрать определенные пары
UPDATE trading_pairs 
SET strategy = 'conservative',
    stop_loss_percent = 1.0,
    take_profit_percent = 3.0
WHERE symbol IN ('BTCUSDT', 'ETHUSDT');
"""
    
    with open('update_strategies.sql', 'w') as f:
        f.write(update_sql)
    
    print("✅ Создан SQL скрипт для обновления стратегий")

def main():
    print("🔧 ИСПРАВЛЕНИЕ ВСЕХ КРИТИЧЕСКИХ ПРОБЛЕМ")
    print("=" * 50)
    
    # 1. Исправляем проблемы с БД
    fix_bot_manager()
    
    # 2. Исправляем Telegram уведомления
    fix_telegram_notifications()
    
    # 3. Создаем безопасные стратегии
    create_safe_strategies()
    
    # 4. Обновляем фабрику
    update_factory()
    
    # 5. Создаем SQL для обновления БД
    create_update_sql()
    
    print("\n✅ Все исправления применены!")
    print("\n📋 Следующие шаги:")
    print("1. Выполните SQL скрипт: mysql crypto_top_bd_mysql < update_strategies.sql")
    print("2. Запустите скрипт создания расширенной аналитики")
    print("3. Запустите скрипт создания нового дашборда")

if __name__ == "__main__":
    main()