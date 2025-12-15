"""Модуль безопасности: JWT, хеширование паролей, валидация.

Использует настройки из config.py с константами из constants.py.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from src.app.core.config import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class TokenData(BaseModel):
    """Данные токена."""

    username: Optional[str] = None
    user_id: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля его хешу.

    Args:
        plain_password: Обычный пароль
        hashed_password: Хешированный пароль

    Returns:
        True если пароль совпадает, иначе False

    Raises:
        ValueError: Если хеш имеет неверный формат

    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Генерирует хеш пароля с использованием bcrypt.

    Args:
        password: Пароль для хеширования

    Returns:
        Хешированный пароль

    Raises:
        ValueError: Если пароль пустой

    """
    if not password:
        raise ValueError('Пароль не может быть пустым')

    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Создаёт JWT access token с сроком действия 1 час.

    Args:
        data: Данные для кодирования в токен
        expires_delta: Время жизни токена (по умолчанию 1 час)

    Returns:
        JWT токен

    Raises:
        ValueError: Если не удалось создать токен

    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    to_encode.update({'exp': expire, 'type': 'access'})

    try:
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
    except JWTError as e:
        raise ValueError(f'Ошибка создания токена: {e}') from e


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Декодирует JWT access token.

    Args:
        token: JWT токен

    Returns:
        Декодированные данные или None при ошибке

    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get('type') != 'access':
            return None

        return payload
    except JWTError:
        return None


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Создаёт JWT refresh token с сроком действия 7 дней.

    Args:
        data: Данные для кодирования в токен
        expires_delta: Время жизни токена (по умолчанию 7 дней)

    Returns:
        JWT refresh токен

    Raises:
        ValueError: Если не удалось создать токен

    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )

    to_encode.update({'exp': expire, 'type': 'refresh'})

    try:
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
    except JWTError as e:
        raise ValueError(f'Ошибка создания refresh токена: {e}') from e


def decode_refresh_token(token: str) -> Optional[dict[str, Any]]:
    """Декодирует JWT refresh token.

    Args:
        token: JWT refresh токен

    Returns:
        Декодированные данные или None при ошибке

    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get('type') != 'refresh':
            return None

        return payload
    except JWTError:
        return None


def create_tokens_pair(
    user_id: int,
    username: str,
) -> dict[str, str]:
    """Создаёт пару access и refresh токенов.

    Args:
        user_id: ID пользователя
        username: Имя пользователя

    Returns:
        Словарь с access и refresh токенами

    """
    token_data = {
        'sub': username,
        'user_id': user_id,
    }

    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
    }


def verify_refresh_token(token: str) -> Optional[TokenData]:
    """Проверяет refresh token и возвращает данные пользователя.

    Args:
        token: Refresh token

    Returns:
        Данные пользователя или None

    """
    payload = decode_refresh_token(token)
    if not payload:
        return None

    username = payload.get('sub')
    user_id = payload.get('user_id')

    if not username or not user_id:
        return None

    return TokenData(username=username, user_id=user_id)


def get_current_user_id_from_token(token: str) -> Optional[int]:
    """Получает ID пользователя из access token.

    Args:
        token: Access token

    Returns:
        ID пользователя или None

    """
    payload = decode_access_token(token)
    if not payload:
        return None

    return payload.get('user_id')


def get_current_username_from_token(token: str) -> Optional[str]:
    """Получает username из access token.

    Args:
        token: Access token

    Returns:
        Username или None

    """
    payload = decode_access_token(token)
    if not payload:
        return None

    return payload.get('sub')
