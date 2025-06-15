"""
Система авторизации и аутентификации
Путь: src/web/auth.py

Обеспечивает:
- Хеширование паролей
- Создание и проверка JWT токенов
- Защиту от брутфорса
- Middleware для защищенных эндпоинтов
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..core.config import config
from ..core.database import get_db
from ..core.models import User, LoginAttempt

logger = logging.getLogger(__name__)

# ===== КОНСТАНТЫ =====

# Алгоритм для JWT
ALGORITHM = "HS256"

# Время жизни токенов
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Защита от брутфорса
MAX_LOGIN_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 30
LOGIN_ATTEMPT_WINDOW_MINUTES = 15

# ===== НАСТРОЙКА БЕЗОПАСНОСТИ =====

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ПАРОЛЯМИ =====

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль
        
    Returns:
        bool: True если пароль верный
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Ошибка проверки пароля: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Хеширование пароля
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        str: Хешированный пароль
    """
    return pwd_context.hash(password)


# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С JWT =====

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT access токена
    
    Args:
        data: Данные для включения в токен
        expires_delta: Время жизни токена
        
    Returns:
        str: JWT токен
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Создание JWT refresh токена
    
    Args:
        data: Данные для включения в токен
        
    Returns:
        str: JWT refresh токен
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Декодирование JWT токена
    
    Args:
        token: JWT токен
        
    Returns:
        Dict: Декодированные данные
        
    Raises:
        HTTPException: Если токен невалидный
    """
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Ошибка декодирования токена: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ =====

def get_user(db: Session, username: str) -> Optional[User]:
    """
    Получение пользователя по username
    
    Args:
        db: Сессия БД
        username: Имя пользователя
        
    Returns:
        User или None
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Получение пользователя по email
    
    Args:
        db: Сессия БД
        email: Email пользователя
        
    Returns:
        User или None
    """
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Аутентификация пользователя
    
    Args:
        db: Сессия БД
        username: Имя пользователя
        password: Пароль
        
    Returns:
        User если аутентификация успешна, иначе None
    """
    user = get_user(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# ===== ЗАЩИТА ОТ БРУТФОРСА =====

def check_login_attempts(db: Session, username: str, ip_address: Optional[str] = None) -> bool:
    """
    Проверка количества попыток входа
    
    Args:
        db: Сессия БД
        username: Имя пользователя
        ip_address: IP адрес
        
    Returns:
        bool: True если вход разрешен, False если заблокирован
    """
    # Временное окно для подсчета попыток
    time_window = datetime.utcnow() - timedelta(minutes=LOGIN_ATTEMPT_WINDOW_MINUTES)
    
    # Считаем неудачные попытки
    attempts_query = db.query(LoginAttempt).filter(
        and_(
            LoginAttempt.username == username,
            LoginAttempt.timestamp >= time_window,
            LoginAttempt.success == False
        )
    )
    
    # Если есть IP, учитываем и его
    if ip_address:
        attempts_query = attempts_query.filter(
            LoginAttempt.ip_address == ip_address
        )
    
    failed_attempts = attempts_query.count()
    
    if failed_attempts >= MAX_LOGIN_ATTEMPTS:
        logger.warning(f"🚫 Превышен лимит попыток входа для {username} (IP: {ip_address})")
        return False
    
    return True


def record_login_attempt(
    db: Session, 
    username: str, 
    success: bool, 
    ip_address: Optional[str] = None
) -> None:
    """
    Запись попытки входа
    
    Args:
        db: Сессия БД
        username: Имя пользователя
        success: Успешная попытка или нет
        ip_address: IP адрес
    """
    try:
        attempt = LoginAttempt(
            username=username,
            success=success,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        db.add(attempt)
        db.commit()
        
        # Если успешный вход, очищаем старые неудачные попытки
        if success:
            old_attempts = db.query(LoginAttempt).filter(
                and_(
                    LoginAttempt.username == username,
                    LoginAttempt.success == False,
                    LoginAttempt.timestamp < datetime.utcnow() - timedelta(hours=1)
                )
            ).delete()
            db.commit()
            
    except Exception as e:
        logger.error(f"Ошибка записи попытки входа: {e}")
        db.rollback()


# ===== DEPENDENCIES ДЛЯ FASTAPI =====

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя из токена
    
    Args:
        token: JWT токен
        db: Сессия БД
        
    Returns:
        User: Текущий пользователь
        
    Raises:
        HTTPException: Если токен невалидный или пользователь не найден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодируем токен
        payload = decode_token(token)
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "access":
            raise credentials_exception
            
    except HTTPException:
        raise credentials_exception
    
    # Получаем пользователя
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    
    # Проверяем что пользователь активен
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Обновляем время последнего входа
    try:
        user.last_login = datetime.utcnow()
        db.commit()
    except:
        db.rollback()
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Проверка что пользователь активен
    
    Args:
        current_user: Текущий пользователь
        
    Returns:
        User: Активный пользователь
        
    Raises:
        HTTPException: Если пользователь не активен
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Проверка что пользователь является администратором
    
    Args:
        current_user: Текущий пользователь
        
    Returns:
        User: Пользователь-администратор
        
    Raises:
        HTTPException: Если пользователь не администратор
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_client_ip(request: Request) -> Optional[str]:
    """
    Получение IP адреса клиента
    
    Args:
        request: FastAPI Request объект
        
    Returns:
        str: IP адрес или None
    """
    # Проверяем заголовки прокси
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Берем первый IP из списка
        return forwarded_for.split(",")[0].strip()
    
    # Проверяем другие заголовки
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Используем IP из соединения
    if request.client:
        return request.client.host
    
    return None


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    is_admin: bool = False
) -> User:
    """
    Создание нового пользователя
    
    Args:
        db: Сессия БД
        username: Имя пользователя
        email: Email
        password: Пароль в открытом виде
        is_admin: Является ли администратором
        
    Returns:
        User: Созданный пользователь
    """
    hashed_password = get_password_hash(password)
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=is_admin,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ Создан пользователь: {username}")
    return user


def update_user_password(db: Session, user: User, new_password: str) -> None:
    """
    Обновление пароля пользователя
    
    Args:
        db: Сессия БД
        user: Пользователь
        new_password: Новый пароль
    """
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    logger.info(f"✅ Обновлен пароль для пользователя: {user.username}")


# Экспортируем все необходимое
__all__ = [
    # Функции для паролей
    'verify_password',
    'get_password_hash',
    # Функции для токенов
    'create_access_token',
    'create_refresh_token',
    'decode_token',
    # Функции для пользователей
    'get_user',
    'get_user_by_email',
    'authenticate_user',
    'create_user',
    'update_user_password',
    # Защита от брутфорса
    'check_login_attempts',
    'record_login_attempt',
    # Dependencies
    'get_current_user',
    'get_current_active_user',
    'get_admin_user',
    # Утилиты
    'get_client_ip',
    # Схемы
    'oauth2_scheme'
]