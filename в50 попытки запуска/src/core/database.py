"""
Модуль для работы с базой данных
Путь: src/core/database.py

Этот файл управляет подключением к базе данных и сессиями.
Использует паттерн Singleton для единого подключения.
"""
import os
import logging
from typing import Generator, Optional
from contextlib import contextmanager
from dotenv import load_dotenv

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

# Загружаем переменные окружения
load_dotenv('/etc/crypto/config/.env')

logger = logging.getLogger(__name__)

class Database:
    """
    Класс для управления подключением к базе данных
    Реализует паттерн Singleton
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация подключения к БД"""
        if not self._initialized:
            self.database_url = os.getenv('DATABASE_URL')
            if not self.database_url:
                raise ValueError("DATABASE_URL не установлен в переменных окружения")
            
            # Создаем движок с пулом соединений
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Проверка соединения перед использованием
                pool_recycle=3600,   # Переподключение каждый час
                echo=False,          # Отключаем логирование SQL (включить для отладки)
                connect_args={
                    'connect_timeout': 30,
                }
            )
            
            # Настройка событий для логирования
            @event.listens_for(self.engine, "connect")
            def receive_connect(dbapi_connection, connection_record):
                connection_record.info['pid'] = os.getpid()
            
            @event.listens_for(self.engine, "checkout")
            def receive_checkout(dbapi_connection, connection_record, connection_proxy):
                pid = os.getpid()
                if connection_record.info['pid'] != pid:
                    connection_record.connection = connection_proxy.connection = None
                    raise SQLAlchemyError(
                        f"Connection record belongs to pid {connection_record.info['pid']}, "
                        f"attempting to check out in pid {pid}"
                    )
            
            # Создаем фабрику сессий
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine,
                    expire_on_commit=False
                )
            )
            
            self._initialized = True
            logger.info("База данных успешно инициализирована")
    
    def create_tables(self):
        """Создание всех таблиц в БД"""
        try:
            # Импортируем Base здесь, чтобы избежать циклических импортов
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Таблицы базы данных созданы/обновлены")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Контекстный менеджер для безопасной работы с сессией
        
        Пример использования:
            with db.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Ошибка БД в транзакции: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Неожиданная ошибка в транзакции: {e}")
            raise
        finally:
            session.close()
    
    def get_db(self) -> Generator[Session, None, None]:
        """
        Генератор сессий для FastAPI зависимостей
        
        Используется в FastAPI endpoints:
            @app.get("/users")
            def get_users(db: Session = Depends(get_db)):
                return db.query(User).all()
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def close(self):
        """Закрытие всех соединений"""
        try:
            self.SessionLocal.remove()
            self.engine.dispose()
            logger.info("Соединения с БД закрыты")
        except Exception as e:
            logger.error(f"Ошибка закрытия соединений: {e}")
    
    def test_connection(self) -> bool:
        """Проверка соединения с БД"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Ошибка проверки соединения с БД: {e}")
            return False
    
    def get_table_info(self) -> dict:
        """Получение информации о таблицах"""
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            
            tables_info = {}
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                tables_info[table_name] = {
                    'columns': [col['name'] for col in columns],
                    'indexes': [idx['name'] for idx in inspector.get_indexes(table_name)]
                }
            
            return tables_info
        except Exception as e:
            logger.error(f"Ошибка получения информации о таблицах: {e}")
            return {}

# Создаем единственный экземпляр базы данных
db = Database()

# Экспортируем для обратной совместимости
engine = db.engine
SessionLocal = db.SessionLocal
get_db = db.get_db

# Функция для получения сессии (для обратной совместимости)
def get_session() -> Session:
    """Получить новую сессию БД"""
    return SessionLocal()

# Контекстный менеджер для транзакций
@contextmanager
def transaction():
    """
    Контекстный менеджер для транзакций
    
    Пример:
        with transaction() as session:
            user = User(name="Test")
            session.add(user)
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

# Экспорт всех необходимых компонентов
__all__ = [
    'Database',
    'db',
    'engine',
    'SessionLocal',
    'get_db',
    'get_session',
    'transaction'
]