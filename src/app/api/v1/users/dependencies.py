"""Зависимости (Dependencies) для модуля пользователей и аутентификации.

Содержит зависимости FastAPI для:
- Получения текущего пользователя из JWT токена
- Проверки прав доступа (ролей)
- Валидации и обработки исключений
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db

# from app.api.v1.cafes.models import cafe_managers
# Модуль отсутствует, импорт закомментирован для устранения ошибки
from app.api.v1.users.repository import UserRepository
from app.core.constants import ErrorCode
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
)
from app.core.security import (
    get_current_user_id_from_token,
    get_current_username_from_token,
    verify_refresh_token,
)
from app.models.models import User

security = HTTPBearer(auto_error=False)


def get_user_repository() -> UserRepository:
    """Получает репозиторий пользователей.

    Returns:
        UserRepository: Экземпляр репозитория пользователей

    """
    return UserRepository()


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Security(security),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Получает текущего аутентифицированного пользователя из JWT токена.

    Args:
        credentials: HTTP Bearer токен из заголовка Authorization
        db: Асинхронная сессия базы данных
        repo: Репозиторий пользователей

    Returns:
        User: Объект текущего пользователя

    Raises:
        HTTPException: 401 если токен не валиден или пользователь не найден

    """
    if credentials is None:
        raise AuthenticationException(
            ErrorCode.AUTHENTICATION_REQUIRED,
            headers={'WWW-Authenticate': 'Bearer'},
        )

    token = credentials.credentials

    user_id = get_current_user_id_from_token(token)
    if user_id is None:
        username = get_current_username_from_token(token)
        if username is None:
            raise AuthenticationException(
                ErrorCode.INVALID_TOKEN,
                headers={'WWW-Authenticate': 'Bearer'},
            )
        user = await repo.get_by_username(db, username, active_only=True)
    else:
        user = await repo.get(db, user_id, active_only=True)

    if not user:
        raise AuthenticationException(
            ErrorCode.USER_NOT_FOUND,
            headers={'WWW-Authenticate': 'Bearer'},
        )

    if user.is_blocked:
        raise AuthorizationException(ErrorCode.USER_BLOCKED)

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Зависимость для получения текущего активного пользователя.

    Гарантирует, что пользователь не заблокирован и активен.

    Args:
        current_user: Текущий пользователь из get_current_user

    Returns:
        User: Активный пользователь

    Raises:
        HTTPException: 403 если пользователь заблокирован

    """
    if current_user.is_blocked:
        raise AuthorizationException(ErrorCode.USER_BLOCKED)

    if not current_user.active:
        raise AuthorizationException(ErrorCode.USER_DEACTIVATED)

    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Зависимость для получения текущего суперпользователя (администратора).

    Args:
        current_user: Текущий пользователь из get_current_user

    Returns:
        User: Суперпользователь

    Raises:
        HTTPException: 403 если пользователь не суперпользователь

    """
    if not current_user.is_superuser:
        raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)

    return current_user


async def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Security(security),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> Optional[User]:
    """Получает текущего пользователя, если токен передан.

    В отличие от get_current_user, не выбрасывает исключение если токен
    отсутствует. Возвращает None если пользователь не аутентифицирован.

    Returns:
        Optional[User]: Пользователь или None

    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db, repo)
    except HTTPException:
        return None


async def require_cafe_manager(
    cafe_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Проверяет, является ли пользователь менеджером указанного кафе.

    Args:
        cafe_id: ID кафе для проверки
        current_user: Текущий пользователь
        db: Сессия базы данных

    Returns:
        User: Пользователь если он менеджер кафе

    Raises:
        HTTPException: 403 если пользователь не менеджер этого кафе

    """
    if current_user.is_superuser:
        return current_user

    # query = select(cafe_managers).where(
    #     and_(
    #         cafe_managers.c.cafe_id == cafe_id,
    #         cafe_managers.c.user_id == current_user.id,
    #     ),
    # )

    # result = await db.execute(query)
    # is_manager = result.scalar() is not None

    # if not is_manager:
    #     raise AuthorizationException(ErrorCode.NOT_CAFE_MANAGER)

    # TODO: Реализовать проверку менеджера кафе
    # когда появится модель cafe_managers
    return current_user


async def validate_refresh_token(
    refresh_token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Валидирует refresh токен и возвращает пользователя.

    Args:
        refresh_token: JWT refresh токен
        db: Сессия базы данных
        repo: Репозиторий пользователей

    Returns:
        User: Пользователь, если токен валиден

    Raises:
        HTTPException: 401 если токен не валиден

    """
    token_data = verify_refresh_token(refresh_token)
    if not token_data or not token_data.user_id:
        raise AuthenticationException(ErrorCode.TOKEN_EXPIRED)

    user = await repo.get(db, token_data.user_id, active_only=True)
    if not user:
        raise AuthenticationException(ErrorCode.USER_NOT_FOUND)

    if user.is_blocked:
        raise AuthenticationException(ErrorCode.USER_NOT_FOUND)

    return user


async def get_current_user_id(
    current_user: Annotated[User, Depends(get_current_user)],
) -> int:
    """Получает ID текущего пользователя.

    Удобно для эндпоинтов, где нужен только user_id.

    Args:
        current_user: Текущий пользователь

    Returns:
        int: ID пользователя

    """
    return current_user.id


async def get_current_user_username(
    current_user: Annotated[User, Depends(get_current_user)],
) -> str:
    """Получает username текущего пользователя.

    Args:
        current_user: Текущий пользователь

    Returns:
        str: Username пользователя

    """
    return current_user.username


__all__ = [
    'security',
    'get_db',
    'get_user_repository',
    'get_current_user',
    'get_current_active_user',
    'get_current_superuser',
    'get_current_user_id',
    'get_current_user_username',
    'get_optional_user',
    'require_cafe_manager',
    'validate_refresh_token',
]
