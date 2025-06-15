"""
Конфигурация базы данных для криптотрейдинг бота
Путь: src/core/database.py

Этот модуль отвечает за:
- Создание подключения к MySQL
- Инициализацию таблиц
- Управление сессиями
- Миграции базы данных
"""

import asyncio
import logging
from typing import Optional
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from sqlalchemy.exc import SQLAlchemyError
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .config import config

logger = logging.getLogger(__name__)

# Создаем базовый класс для моделей
Base = declarative_base()

# Строка подключения к БД
DATABASE_URL = (
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@"
    f"{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
)

# Асинхронная версия URL для aiomysql
ASYNC_DATABASE_URL = (
    f"mysql+aiomysql://{config.DB_USER}:{config.DB_PASSWORD}@"
    f"{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
)

# Создаем синхронный движок
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=10,        # Размер пула соединений
    max_overflow=20,     # Максимум дополнительных соединений
    pool_recycle=3600,   # Переподключение каждый час
    echo=False           # Отключаем SQL логи (включить для отладки)
)

# Создаем асинхронный движок
async_engine = None
AsyncSessionLocal = None

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_database():
    """
    Синхронная инициализация базы данных
    
    Создает все таблицы если их нет
    """
    try:
        logger.info("🔧 Инициализируем базу данных...")
        
        # Импортируем модели чтобы они зарегистрировались
        from . import models  # noqa
        
        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        
        # Проверяем подключение
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("✅ База данных инициализирована успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return False


async def init_database_async():
    """
    Асинхронная инициализация базы данных
    
    Создает асинхронный движок и сессии
    """
    global async_engine, AsyncSessionLocal
    
    try:
        logger.info("🔧 Инициализируем асинхронную базу данных...")
        
        # Создаем асинхронный движок
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        
        # Создаем фабрику асинхронных сессий
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Проверяем подключение
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        logger.info("✅ Асинхронная база данных инициализирована")
        
        # Также инициализируем синхронную БД
        init_database()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка асинхронной инициализации БД: {e}")
        # Fallback на синхронную версию
        return init_database()


def get_db():
    """
    Dependency для получения сессии БД в FastAPI
    
    Yields:
        Session: Сессия базы данных
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """
    Dependency для получения асинхронной сессии БД
    
    Yields:
        AsyncSession: Асинхронная сессия базы данных
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Асинхронная БД не инициализирована")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def db_session():
    """
    Контекстный менеджер для работы с БД
    
    Example:
        with db_session() as db:
            user = db.query(User).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def async_db_session():
    """
    Асинхронный контекстный менеджер для работы с БД
    
    Example:
        async with async_db_session() as db:
            result = await db.execute(select(User))
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Асинхронная БД не инициализирована")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def check_database_connection() -> bool:
    """
    Проверка подключения к базе данных
    
    Returns:
        bool: True если подключение успешно
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"❌ Нет подключения к БД: {e}")
        return False


async def check_async_database_connection() -> bool:
    """
    Асинхронная проверка подключения к БД
    
    Returns:
        bool: True если подключение успешно
    """
    if async_engine is None:
        return False
    
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"❌ Нет асинхронного подключения к БД: {e}")
        return False


def create_initial_data():
    """
    Создание начальных данных в БД
    
    Создает пользователя по умолчанию и начальные настройки
    """
    from .models import User, BotState
    from ..web.auth import get_password_hash
    
    try:
        with db_session() as db:
            # Проверяем есть ли пользователи
            user_count = db.query(User).count()
            
            if user_count == 0:
                # Создаем пользователя по умолчанию
                default_user = User(
                    username="admin",
                    email="admin@localhost",
                    hashed_password=get_password_hash("admin123"),
                    is_active=True
                )
                db.add(default_user)
                logger.info("✅ Создан пользователь по умолчанию: admin/admin123")
            
            # Проверяем состояние бота
            bot_state = db.query(BotState).first()
            if not bot_state:
                bot_state = BotState(
                    is_running=False,
                    started_at=None,
                    settings={}
                )
                db.add(bot_state)
                logger.info("✅ Создано начальное состояние бота")
            
            db.commit()
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания начальных данных: {e}")


# Event listeners для пула соединений
@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Настройка соединения при подключении"""
    # Для MySQL можно добавить SET команды если нужно
    pass


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """Проверка соединения перед использованием"""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # Соединение не работает, пересоздаем
        raise exc.DisconnectionError()
    cursor.close()


# Экспортируем все необходимое
__all__ = [
    'Base',
    'engine',
    'async_engine',
    'SessionLocal',
    'AsyncSessionLocal',
    'get_db',
    'get_async_db',
    'db_session',
    'async_db_session',
    'init_database',
    'init_database_async',
    'check_database_connection',
    'check_async_database_connection',
    'create_initial_data'
]