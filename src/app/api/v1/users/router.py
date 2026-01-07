"""Роутер для работы с пользователями и аутентификацией.

Реализует все эндпоинты из OpenAPI спецификации для модуля Users/Auth.
"""

from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_user,
    get_optional_user,
)
from app.core.constants import API, ErrorCode, Limits
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ServiceUnavailableException,
    ValidationException,
)

from src.app.models import User
from src.app.schemas.users import (
    UserCreate,
    UserInfo,
    UserUpdate,
)
from src.app.services.users import UserService, get_user_service

router = APIRouter(tags=API.USERS)


@router.post(
    '/auth/login',
    response_model=dict,
    summary='Получение токена авторизации',
    description='Возвращает токен для последующей авторизации пользователя.',
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> dict:
    """Аутентификация пользователя и получение JWT токенов.

    Поддерживает вход по username, email или phone.
    """
    try:
        result = await service.authenticate_user(
            login=form_data.username,
            password=form_data.password,
        )
        return {
            'access_token': result['tokens']['access_token'],
            'refresh_token': result['tokens']['refresh_token'],
            'token_type': 'bearer',
            'user': result['user'],
        }
    except (AuthenticationException, AuthorizationException) as e:
        raise e


@router.post(
    '/auth/refresh',
    response_model=dict,
    summary='Обновление access токена',
    description='Обновляет access токен с помощью refresh токена.',
)
async def refresh_tokens(
    refresh_token: Annotated[
        str,
        Body(..., embed=True, description='Refresh токен'),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> dict:
    """Обновляет access токен."""
    try:
        result = await service.refresh_tokens(
            refresh_token=refresh_token,
        )
        return {
            'access_token': result['tokens']['access_token'],
            'refresh_token': result['tokens']['refresh_token'],
            'token_type': 'bearer',
            'user': result['user'],
        }
    except (AuthenticationException, AuthorizationException) as e:
        raise e


@router.get(
    '/users',
    response_model=List[UserInfo],
    summary='Получение списка пользователей',
    description='Возвращает информацию о всех пользователях. '
    'Только для администраторов или менеджеров.',
)
async def get_users(
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_superuser)],
    skip: Annotated[
        int,
        Query(ge=0, description='Сколько записей пропустить'),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=Limits.MAX_PAGE_SIZE,
            description='Максимальное количество записей',
        ),
    ] = Limits.DEFAULT_PAGE_SIZE,
    active_only: Annotated[
        bool,
        Query(description='Показывать только активных пользователей'),
    ] = True,
    username: Annotated[
        Optional[str],
        Query(description='Фильтр по username'),
    ] = None,
    email: Annotated[
        Optional[str],
        Query(description='Фильтр по email'),
    ] = None,
    is_blocked: Annotated[
        Optional[bool],
        Query(description='Фильтр по статусу блокировки'),
    ] = None,
) -> List[UserInfo]:
    """Получает список пользователей."""
    try:
        filters: Dict[str, Any] = {}
        if username:
            filters['username'] = username
        if email:
            filters['email'] = email
        if is_blocked is not None:
            filters['is_blocked'] = is_blocked
        return await service.get_users_list(
            skip=skip,
            limit=limit,
            active_only=active_only,
            current_user=current_user,
            filters=filters if filters else None,
        )
    except (AuthorizationException, ValidationException):
        raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)


@router.post(
    '/users',
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
    description='Создает нового пользователя с указанными данными.\n\n'
    '**Обязательные поля:**\n'
    '- username\n'
    '- password\n'
    '- email или phone',
)
async def create_user(
    user_create: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[Optional[User], Depends(get_optional_user)],
) -> UserInfo:
    """Создаёт нового пользователя.

    Если создаёт администратор, пользователь создаётся
    без дополнительных проверок.
    """
    try:
        return await service.create_user(
            user_create=user_create,
            current_user=current_user,
        )

    except (ConflictException, ValidationException) as e:
        raise e


@router.get(
    '/users/me',
    response_model=UserInfo,
    summary='Получение информации о текущем пользователе',
    description='Возвращает информацию о текущем пользователе. '
    'Только для авторизированных пользователей.',
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserInfo:
    """Получает информацию о текущем пользователе."""
    return UserInfo.from_orm(current_user)


@router.patch(
    '/users/me',
    response_model=UserInfo,
    summary='Обновление информации о текущем пользователе',
    description='Возвращает обновленную информацию о пользователе. '
    'Только для авторизированных пользователей.',
)
async def update_current_user(
    user_update: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserInfo:
    """Обновляет информацию о текущем пользователе."""
    try:
        return await service.update_user(
            user_id=current_user.id,
            user_update=user_update,
            current_user=current_user,
        )
    except (
        AuthorizationException,
        ValidationException,
        ConflictException,
    ) as e:
        raise e


@router.post(
    '/users/me/password',
    response_model=UserInfo,
    summary='Смена пароля текущего пользователя',
    description='Изменяет пароль текущего пользователя.',
)
async def change_password(
    current_password: Annotated[str, Body(..., description='Текущий пароль')],
    new_password: Annotated[str, Body(..., description='Новый пароль')],
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserInfo:
    """Изменяет пароль текущего пользователя."""
    try:
        return await service.update_user_password(
            user_id=current_user.id,
            current_password=current_password,
            new_password=new_password,
            current_user=current_user,
        )
    except (
        NotFoundException,
        AuthenticationException,
        AuthorizationException,
        ValidationException,
    ) as e:
        raise e


@router.delete(
    '/users/me',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Деактивация своего аккаунта',
    description='Деактивирует аккаунт текущего пользователя.',
)
async def delete_current_user(
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    confirm: Annotated[
        bool,
        Body(..., description='Подтверждение удаления аккаунта'),
    ] = False,
) -> None:
    """Деактивирует аккаунт текущего пользователя."""
    if not confirm:
        raise ValidationException(ErrorCode.CONFIRMATION_REQUIRED)
    await service.delete_user(current_user.id, current_user)


@router.get(
    '/users/search',
    response_model=List[UserInfo],
    summary='Поиск пользователей',
    description='Ищет пользователей по строке запроса. '
    'Только для администраторов.',
)
async def search_users(
    query: Annotated[
        str,
        Query(
            ...,
            min_length=Limits.MIN_SEARCH_QUERY_LENGTH,
            description='Строка поиска',
        ),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_superuser)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[
        int, Query(ge=1, le=Limits.MAX_PAGE_SIZE)
    ] = Limits.DEFAULT_PAGE_SIZE,
) -> List[UserInfo]:
    """Ищет пользователей по строке запроса."""
    try:
        return await service.search_users(
            query=query,
            skip=skip,
            limit=limit,
            current_user=current_user,
        )
    except AuthorizationException as e:
        raise e


@router.get(
    '/users/{user_id}',
    response_model=UserInfo,
    summary='Получение информации о пользователе по его ID',
    description='Возвращает информацию о пользователе по его ID. '
    'Только для администраторов или менеджеров.',
)
async def get_user_by_id(
    user_id: Annotated[int, ...],
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfo:
    """Получает пользователя по ID."""
    try:
        return await service.get_user_by_id(
            user_id=user_id,
            current_user=current_user,
        )

    except (NotFoundException, AuthorizationException) as e:
        raise e


@router.patch(
    '/users/{user_id}',
    response_model=UserInfo,
    summary='Обновление информации о пользователе по его ID',
    description='Возвращает обновленную информацию о пользователе по его ID. '
    'Только для администраторов или менеджеров.',
)
async def update_user(
    user_id: Annotated[int, ...],
    user_update: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfo:
    """Обновляет информацию о пользователе."""
    try:
        return await service.update_user(
            user_id=user_id,
            user_update=user_update,
            current_user=current_user,
        )
    except (
        NotFoundException,
        AuthorizationException,
        ValidationException,
        ConflictException,
    ) as e:
        raise e


@router.delete(
    '/users/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Деактивация пользователя',
    description='Деактивирует пользователя (логическое удаление). '
    'Только для администраторов.',
)
async def delete_user(
    user_id: Annotated[int, ...],
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_superuser)],
) -> None:
    """Деактивирует пользователя."""
    try:
        await service.delete_user(
            user_id=user_id,
            current_user=current_user,
        )
    except (
        NotFoundException,
        AuthorizationException,
        ValidationException,
    ) as e:
        raise e


@router.get(
    '/health',
    summary='Проверка здоровья сервиса',
    description='Проверяет работоспособность сервиса пользователей.',
)
async def health_check(
    service: Annotated[UserService, Depends(get_user_service)],
) -> dict:
    """Проверка здоровья сервиса."""
    try:
        count = await service.user_repo.count()
        return {
            'status': 'healthy',
            'database': 'connected',
            'users_count': count,
            'timestamp': '2024-01-01T00:00:00Z',
        }
    except Exception:
        raise ServiceUnavailableException(ErrorCode.SERVICE_UNAVAILABLE)
