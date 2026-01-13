"""Роутер для работы с пользователями и аутентификацией.

Реализует все эндпоинты из OpenAPI спецификации для модуля Users/Auth.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_current_manager_or_superuser,
    get_current_user,
    get_optional_user,
)
from app.core.constants import API, ErrorCode
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models import User
from app.schemas.auth import AuthData
from app.schemas.types import AuthResponseDict
from app.schemas.users import (
    UserCreate,
    UserInfo,
    UserUpdate,
)
from app.services.users import UserService, get_user_service

auth_router = APIRouter(tags=API.AUTH)
router = APIRouter(tags=API.USERS)


@auth_router.post(
    '/auth/login',
    response_model=AuthResponseDict,
    summary='Получение токена авторизации',
    description='Возвращает токен для последующей авторизации пользователя.',
)
async def login(
    auth_data: AuthData,
    service: Annotated[UserService, Depends(get_user_service)],
) -> AuthResponseDict:
    """Аутентификация пользователя и получение JWT токенов.

    Поддерживает вход по username, email или phone.
    """
    try:
        result = await service.authenticate_user(
            login=auth_data.login,
            password=auth_data.password,
        )
        return {
            'access_token': result['tokens']['access_token'],
            'token_type': 'bearer',
        }
    except (AuthenticationException, AuthorizationException) as e:
        if (
            isinstance(e, AuthenticationException)
            and e.error_code == ErrorCode.INVALID_CREDENTIALS
        ):
            raise ValidationException(ErrorCode.INVALID_CREDENTIALS) from e
        raise e


@router.get(
    '/users',
    response_model=list[UserInfo],
    summary='Получение списка пользователей',
    description='Возвращает информацию о всех пользователях. '
    'Только для администраторов или менеджеров.',
)
async def get_users(
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_manager_or_superuser)],
) -> list[UserInfo]:
    """Получает список пользователей."""
    try:
        return await service.get_users_list(
            current_user=current_user,
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
    '- email или phone\n\n'
    '**Ограничения:**\n'
    '- Поле `role` доступно только администраторам',
)
async def create_user(
    user_create: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> UserInfo:
    """Создаёт нового пользователя.

    Если создаёт администратор, пользователь создаётся
    без дополнительных проверок.
    """
    try:
        if not current_user or not current_user.is_superuser:
            create_data = user_create.model_dump(exclude={'is_superuser'})
            user_create = UserCreate(**create_data)

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
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfo:
    """Получает информацию о текущем пользователе."""
    return UserInfo.from_orm(current_user)


@router.patch(
    '/users/me',
    response_model=UserInfo,
    summary='Обновление информации о текущем пользователе',
    description='Обновляет информацию о текущем пользователе.\n\n'
    '**Ограничения:**\n'
    '- Нельзя изменить поля `role`, `is_active`\n'
    '- Нельзя изменить поле `managed_cafes`',
)
async def update_current_user(
    user_update: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfo:
    """Обновляет информацию о текущем пользователе."""
    try:
        update_data = user_update.model_dump(exclude_unset=True)

        protected_fields = [
            'active',
            'role',
            'managed_cafes',
        ]
        for field in protected_fields:
            if field in update_data:
                raise ValidationException(
                    ErrorCode.CANNOT_CHANGE_PRIVILEGES, extra={'field': field}
                )

        safe_update_data = {
            k: v for k, v in update_data.items() if k not in protected_fields
        }
        safe_user_update = UserUpdate(**safe_update_data)

        return await service.update_user(
            user_id=current_user.id,
            user_update=safe_user_update,
            current_user=current_user,
        )
    except (
        AuthorizationException,
        ValidationException,
        ConflictException,
    ) as e:
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
    description='Обновляет информацию о пользователе по его ID.\n\n'
    '**Разрешения:**\n'
    '- Администраторы: могут изменять все поля\n'
    '- Обычные пользователи: могут изменять только свои данные',
)
async def update_user(
    user_id: Annotated[int, ...],
    user_update: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfo:
    """Обновляет информацию о пользователе."""
    try:
        update_data = user_update.model_dump(exclude_unset=True)

        privileged_fields = [
            'active',
            'role',
            'managed_cafes',
        ]

        if not current_user.is_superuser:
            for field in privileged_fields:
                if field in update_data:
                    raise AuthorizationException(
                        ErrorCode.INSUFFICIENT_PERMISSIONS,
                        extra={'field': field},
                    )

            if current_user.id != user_id:
                raise AuthorizationException(
                    ErrorCode.INSUFFICIENT_PERMISSIONS,
                    extra={'message': 'Можно изменять только свой профиль'},
                )

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
