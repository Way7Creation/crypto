#!/usr/bin/env python3
"""
ИСПРАВЛЕННЫЙ EXCHANGE CLIENT - РЕАЛЬНЫЕ ДАННЫЕ
Замените содержимое файла src/exchange/client.py
"""

import ccxt.async_support as ccxt
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

from ..core.config import config
from ..logging.smart_logger import get_logger

logger = get_logger(__name__)

class RealExchangeClient:
    """
    Клиент для работы с реальной биржей Bybit
    БЕЗ ЗАГЛУШЕК - только реальные данные!
    """
    
    def __init__(self):
        self.exchange = None
        self.is_connected = False
        self.markets = {}
        self.last_error = None
        
    async def connect(self) -> bool:
        """Подключение к бирже"""
        try:
            # API ключи из конфигурации
            api_key = os.getenv('BYBIT_API_KEY')
            api_secret = os.getenv('BYBIT_API_SECRET')
            testnet = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
            
            if not api_key or not api_secret:
                raise ValueError("❌ API ключи Bybit не настроены в .env файле!")
            
            # Конфигурация CCXT
            exchange_config = {
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'sandbox': testnet,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,
                }
            }
            
            # Testnet URLs
            if testnet:
                exchange_config['urls'] = {
                    'api': {
                        'public': 'https://api-testnet.bybit.com',
                        'private': 'https://api-testnet.bybit.com',
                    }
                }
            
            # Создаем подключение
            self.exchange = ccxt.bybit(exchange_config)
            
            # Загружаем рынки
            self.markets = await self.exchange.load_markets()
            
            # Тестируем подключение
            balance = await self.exchange.fetch_balance()
            
            self.is_connected = True
            logger.info(f"✅ Подключен к Bybit ({'testnet' if testnet else 'mainnet'})")
            logger.info(f"📊 Загружено {len(self.markets)} торговых пар")
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"❌ Ошибка подключения к бирже: {e}")
            return False
    
    async def disconnect(self):
        """Отключение от биржи"""
        if self.exchange:
            await self.exchange.close()
            self.is_connected = False
            logger.info("🔌 Отключен от биржи")
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Получение реального тикера"""
        if not self.is_connected:
            logger.error("Биржа не подключена")
            return None
            
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'percentage': ticker['percentage'],
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            logger.error(f"Ошибка получения тикера {symbol}: {e}")
            return None
    
    async def get_candles(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Получение реальных свечей OHLCV"""
        if not self.is_connected:
            logger.error("Биржа не подключена")
            return []
            
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            candles = []
            for candle in ohlcv:
                candles.append({
                    'timestamp': candle[0],
                    'datetime': datetime.fromtimestamp(candle[0] / 1000),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            logger.info(f"📈 Получено {len(candles)} свечей для {symbol} ({timeframe})")
            return candles
            
        except Exception as e:
            logger.error(f"Ошибка получения свечей {symbol}: {e}")
            return []
    
    async def get_candles_df(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Получение свечей в формате DataFrame для стратегий"""
        candles = await self.get_candles(symbol, timeframe, limit)
        
        if not candles:
            return pd.DataFrame()
        
        df = pd.DataFrame(candles)
        df.set_index('datetime', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)
        
        return df
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """Получение баланса аккаунта"""
        if not self.is_connected:
            logger.error("Биржа не подключена")
            return {}
            
        try:
            balance = await self.exchange.fetch_balance()
            
            # Форматируем для удобства
            formatted_balance = {}
            for currency, data in balance.items():
                if isinstance(data, dict) and data.get('total', 0) > 0:
                    formatted_balance[currency] = {
                        'total': data.get('total', 0),
                        'free': data.get('free', 0),
                        'used': data.get('used', 0)
                    }
            
            return formatted_balance
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {}
    
    async def get_all_markets(self) -> List[Dict]:
        """Получение всех реальных рынков (для замены random.uniform)"""
        if not self.is_connected:
            await self.connect()
        
        try:
            markets = []
            count = 0
            
            # Получаем рынки с биржи
            exchange_markets = self.exchange.markets if hasattr(self.exchange, 'markets') else {}
            
            for symbol, market in exchange_markets.items():
                if market.get('active') and market.get('spot') and 'USDT' in symbol:
                    try:
                        # Получаем РЕАЛЬНУЮ цену вместо random.uniform()
                        ticker = await self.exchange.fetch_ticker(symbol)
                        
                        market_data = {
                            'symbol': symbol,
                            'base': market['base'],
                            'quote': market['quote'],
                            'active': True,
                            'type': 'spot',
                            'spot': True,
                            'future': False,
                            'option': False,
                            # РЕАЛЬНЫЕ ДАННЫЕ (не random!):
                            'price': float(ticker['last']),
                            'volume_24h': float(ticker['baseVolume'] or 0),
                            'change_24h': float(ticker['percentage'] or 0),
                            'high_24h': float(ticker['high'] or ticker['last']),
                            'low_24h': float(ticker['low'] or ticker['last']),
                            'trades_count': int(ticker.get('count', 0))
                        }
                        
                        markets.append(market_data)
                        count += 1
                        
                        # Rate limiting
                        if count % 10 == 0:
                            await asyncio.sleep(0.2)
                            logger.info(f"📈 Загружено {count} реальных рынков...")
                        
                        # Ограничиваем для скорости
                        if count >= 200:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Пропуск {symbol}: {e}")
                        continue
            
            return markets
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения рынков: {e}")
            return []
    
    async def place_order(self, symbol: str, side: str, amount: float, 
                         price: Optional[float] = None, order_type: str = 'market') -> Optional[Dict]:
        """Размещение ордера"""
        if not self.is_connected:
            logger.error("Биржа не подключена")
            return None
        
        # ВНИМАНИЕ: Проверяем режим торговли
        if os.getenv('PAPER_TRADING', 'true').lower() == 'true':
            logger.warning("🚫 Paper trading режим - ордер не размещен!")
            return {
                'id': f'paper_{int(datetime.now().timestamp())}',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'status': 'paper_trade',
                'timestamp': datetime.now().timestamp()
            }
        
        try:
            if order_type == 'market':
                order = await self.exchange.create_market_order(symbol, side, amount)
            else:
                order = await self.exchange.create_limit_order(symbol, side, amount, price)
            
            logger.info(f"📊 Ордер размещен: {side} {amount} {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"Ошибка размещения ордера: {e}")
            return None
    
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Получение статуса ордера"""
        if not self.is_connected:
            return None
            
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Ошибка получения статуса ордера: {e}")
            return None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Получение статуса подключения"""
        return {
            'connected': self.is_connected,
            'exchange': 'bybit',
            'testnet': os.getenv('BYBIT_TESTNET', 'true').lower() == 'true',
            'markets_loaded': len(self.markets),
            'last_error': self.last_error,
            'timestamp': datetime.now().isoformat()
        }

# Создаем глобальный экземпляр
_exchange_client = None

async def get_exchange_client() -> RealExchangeClient:
    """Получение синглтона клиента биржи"""
    global _exchange_client
    
    if _exchange_client is None:
        _exchange_client = RealExchangeClient()
        await _exchange_client.connect()
    
    return _exchange_client

# Для обратной совместимости
class ExchangeClient:
    """Базовый класс для совместимости"""
    
    def __init__(self):
        self.real_client = None
    
    async def connect(self):
        self.real_client = await get_exchange_client()
        return self.real_client.is_connected
    
    async def get_ticker(self, symbol: str):
        if not self.real_client:
            await self.connect()
        return await self.real_client.get_ticker(symbol)
    
    async def get_account_balance(self):
        if not self.real_client:
            await self.connect()
        return await self.real_client.get_account_balance()
    
    async def get_candles(self, symbol: str, timeframe: str = '5m', limit: int = 100):
        if not self.real_client:
            await self.connect()
        return await self.real_client.get_candles(symbol, timeframe, limit)