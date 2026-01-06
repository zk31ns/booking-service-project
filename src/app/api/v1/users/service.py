"""Сервисный слой для модуля пользователей.

Содержит бизнес-логику, валидации и обработку ошибок.
Использует Repository для доступа к данным и возвращает Pydantic схемы.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.users.repository import UserRepository
from app.api.v1.users.schemas import (
    UserCreate,
    UserInfo,
    UserShortInfo,
    UserUpdate,
)
from app.core.constants import ErrorCode, Limits
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    InternalServerException,
    NotFoundException,
    ValidationException,
)
from app.core.security import create_tokens_pair, verify_password
from app.models.models import User


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self) -> None:
        """Инициализирует сервис."""
        self.repository_class = UserRepository

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: int,
        current_user: Optional[User] = None,
    ) -> UserInfo:
        """Получает пользователя по ID.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя
            current_user: Текущий аутентифицированный пользователь
                        (для проверки прав доступа)

        Returns:
            UserInfo: Информация о пользователе

        """
        repository = self.repository_class(session)
        user = await repository.get_user(user_id, active_only=True)
        if not user:
            raise NotFoundException(
                ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
            )

        await self._check_user_access(user, current_user, 'просмотр')

        return UserInfo.from_orm(user)

    async def get_users_list(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = Limits.DEFAULT_PAGE_SIZE,
        active_only: bool = True,
        current_user: Optional[User] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[UserInfo]:
        """Получает список пользователей.

        Args:
            session: Асинхронная сессия БД
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            active_only: Если True, возвращает только активных пользователей
            current_user: Текущий аутентифицированный пользователь
                        (для проверки прав доступа)
            filters: Дополнительные фильтры

        Returns:
            List[UserInfo]: Список пользователей

        """
        if not self._is_superuser_or_none(current_user):
            raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)

        repository = self.repository_class(session)
        users = await repository.get_multi(
            skip=skip,
            limit=limit,
            active_only=active_only,
            filters=filters,
        )

        return [UserInfo.from_orm(user) for user in users]

    async def create_user(
        self,
        session: AsyncSession,
        user_create: UserCreate,
        current_user: Optional[User] = None,
    ) -> UserInfo:
        """Создаёт нового пользователя.

        Args:
            session: Асинхронная сессия БД
            user_create: Данные для создания пользователя
            current_user: Текущий аутентифицированный пользователь
                        (если создаёт администратор)

        Returns:
            UserInfo: Созданный пользователь

        """
        repository = self.repository_class(session)

        if await repository.get_by_username(
            user_create.username,
            active_only=False,
        ):
            raise ConflictException(
                ErrorCode.USER_ALREADY_EXISTS,
                extra={'username': user_create.username},
            )

        if user_create.email and await repository.get_by_email(
            user_create.email,
            active_only=False,
        ):
            raise ConflictException(
                ErrorCode.USER_ALREADY_EXISTS,
                extra={'email': user_create.email},
            )

        if user_create.phone and await repository.get_by_phone(
            user_create.phone,
            active_only=False,
        ):
            raise ConflictException(
                ErrorCode.PHONE_ALREADY_REGISTERED,
                extra={'phone': user_create.phone},
            )

        try:
            user_data = user_create.model_dump()
            user = await repository.create_user(user_data)
            return UserInfo.from_orm(user)
        except Exception as e:
            raise InternalServerException(
                ErrorCode.INTERNAL_SERVER_ERROR,
                extra={'original_error': str(e)},
            )

    async def update_user(
        self,
        session: AsyncSession,
        user_id: int,
        user_update: UserUpdate,
        current_user: Optional[User] = None,
    ) -> UserInfo:
        """Обновляет информацию о пользователе."""
        from sqlalchemy.exc import IntegrityError

        try:
            repository = self.repository_class(session)
            user = await repository.get_user(user_id, active_only=False)
            if not user:
                raise NotFoundException(
                    ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
                )

            await self._check_user_access(user, current_user, 'обновление')
            await self._validate_update_uniqueness(
                repository, user, user_update
            )
            update_data = user_update.model_dump(exclude_unset=True)

            if 'password' in update_data:
                if verify_password(
                    update_data['password'], user.password_hash
                ):
                    raise ValidationException(ErrorCode.PASSWORD_SAME_AS_OLD)

            updated_user = await repository.update_user(user, update_data)
            return UserInfo.from_orm(updated_user)
        except IntegrityError as e:
            raise ConflictException(
                ErrorCode.USER_ALREADY_EXISTS,
                extra={'original_error': str(e)},
            )
        except Exception as e:
            raise InternalServerException(
                ErrorCode.INTERNAL_SERVER_ERROR,
                extra={'original_error': str(e)},
            )

    async def delete_user(
        self,
        session: AsyncSession,
        user_id: int,
        current_user: Optional[User] = None,
    ) -> UserInfo:
        """Деактивирует пользователя (логическое удаление).

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя для деактивации
            current_user: Текущий аутентифицированный пользователь

        Returns:
            UserInfo: Деактивированный пользователь

        """
        from sqlalchemy.exc import IntegrityError

        try:
            repository = self.repository_class(session)
            user = await repository.get_user(user_id, active_only=False)
            if not user:
                raise NotFoundException(
                    ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
                )
            await self._check_user_access(user, current_user, 'удаление')
            if current_user and user.id == current_user.id:
                raise ValidationException(ErrorCode.CANNOT_DELETE_OWN_ACCOUNT)
            deleted_user = await repository.delete_user(user_id)
            return UserInfo.from_orm(deleted_user)
        except IntegrityError as e:
            raise ConflictException(
                ErrorCode.USER_ALREADY_EXISTS,
                extra={'original_error': str(e)},
            )
        except Exception as e:
            raise InternalServerException(
                ErrorCode.INTERNAL_SERVER_ERROR,
                extra={'original_error': str(e)},
            )

    async def authenticate_user(
        self,
        session: AsyncSession,
        login: str,
        password: str,
    ) -> Dict[str, Any]:
        """Аутентифицирует пользователя.

        Args:
            session: Асинхронная сессия БД
            login: Имя пользователя, email или телефон
            password: Пароль

        Returns:
            Dict[str, Any]: Словарь с пользователем и токенами

        """
        repository = self.repository_class(session)
        user = await repository.authenticate(login, password)

        if not user:
            raise AuthenticationException(ErrorCode.INVALID_CREDENTIALS)

        if not user.active:
            raise AuthorizationException(ErrorCode.USER_DEACTIVATED)

        if user.is_blocked:
            raise AuthorizationException(ErrorCode.USER_BLOCKED)

        tokens = create_tokens_pair(user.id, user.username)

        return {
            'user': UserInfo.from_orm(user),
            'tokens': tokens,
        }

    async def refresh_tokens(
        self,
        session: AsyncSession,
        refresh_token: str,
    ) -> Dict[str, Any]:
        """Обновляет access токен с помощью refresh токена.

        Args:
            session: Асинхронная сессия БД
            refresh_token: Refresh токен

        Returns:
            Dict[str, Any]: Новые токены и информация о пользователе

        """
        from app.core.security import verify_refresh_token

        token_data = verify_refresh_token(refresh_token)
        if not token_data or not token_data.user_id:
            raise AuthenticationException(ErrorCode.INVALID_REFRESH_TOKEN)

        repository = self.repository_class(session)
        user = await repository.get_user(
            token_data.user_id,
            active_only=True,
        )
        if not user:
            raise AuthenticationException(ErrorCode.USER_NOT_FOUND)

        if user.is_blocked:
            raise AuthorizationException(ErrorCode.USER_BLOCKED)

        tokens = create_tokens_pair(user.id, user.username)

        return {
            'user': UserInfo.from_orm(user),
            'tokens': tokens,
        }

    async def update_user_password(
        self,
        session: AsyncSession,
        user_id: int,
        current_password: str,
        new_password: str,
        current_user: Optional[User] = None,
    ) -> UserInfo:
        """Обновляет пароль пользователя.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя
            current_password: Текущий пароль (для проверки)
            new_password: Новый пароль
            current_user: Текущий аутентифицированный пользователь

        Returns:
            UserInfo: Пользователь с обновлённым паролем

        """
        repository = self.repository_class(session)
        user = await repository.get_user(user_id, active_only=True)
        if not user:
            raise NotFoundException(
                ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
            )

        await self._check_user_access(user, current_user, 'изменение пароля')

        if not verify_password(current_password, user.password_hash):
            raise AuthenticationException(ErrorCode.INCORRECT_CURRENT_PASSWORD)

        if verify_password(new_password, user.password_hash):
            raise ValidationException(ErrorCode.PASSWORD_SAME_AS_OLD)

        updated_user = await repository.update_password(
            user,
            new_password,
        )

        return UserInfo.from_orm(updated_user)

    async def search_users(
        self,
        session: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = Limits.DEFAULT_PAGE_SIZE,
        current_user: Optional[User] = None,
    ) -> List[UserInfo]:
        """Ищет пользователей по строке запроса.

        Args:
            session: Асинхронная сессия БД
            query: Строка поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            current_user: Текущий аутентифицированный пользователь

        Returns:
            List[UserInfo]: Найденные пользователи

        """
        if not self._is_superuser_or_none(current_user):
            raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)

        repository = self.repository_class(session)
        users = await repository.search(
            query,
            skip=skip,
            limit=limit,
            active_only=True,
        )

        return [UserInfo.from_orm(user) for user in users]

    async def get_user_short_info(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Optional[UserShortInfo]:
        """Получает краткую информацию о пользователе.

        Используется для вложенных объектов в других схемах.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя

        Returns:
            UserShortInfo: Краткая информация о пользователе или None

        """
        repository = self.repository_class(session)
        user = await repository.get_user(user_id, active_only=True)
        if not user:
            return None

        return UserShortInfo.from_orm(user)

    def _is_superuser_or_none(self, user: Optional[User]) -> bool:
        """Проверяет, является ли пользователь суперпользователем или None.

        Args:
            user: Пользователь или None

        Returns:
            bool: True если пользователь суперпользователь или None

        """
        if user is None:
            return False
        return user.is_superuser

    async def _check_user_access(
        self,
        target_user: User,
        current_user: Optional[User],
        action: str,
    ) -> None:
        """Проверяет права доступа к пользователю.

        Args:
            target_user: Пользователь, к которому нужен доступ
            current_user: Текущий аутентифицированный пользователь
            action: Действие (просмотр, обновление, удаление)

        """
        if current_user is None:
            raise AuthenticationException(
                ErrorCode.AUTHENTICATION_REQUIRED, extra={'action': action}
            )

        if current_user.is_superuser:
            return

        if current_user.id != target_user.id:
            raise AuthorizationException(
                ErrorCode.INSUFFICIENT_PERMISSIONS,
                extra={'action': action, 'target_user_id': target_user.id},
            )

    async def _validate_update_uniqueness(
        self,
        repository: UserRepository,
        user: User,
        user_update: UserUpdate,
    ) -> None:
        """Проверяет уникальность обновляемых данных.

        Args:
            repository: Репозиторий пользователей
            user: Текущий пользователь
            user_update: Данные для обновления

        """
        update_data = user_update.model_dump(exclude_unset=True)

        if 'username' in update_data:
            existing = await repository.get_by_username(
                update_data['username'],
                active_only=False,
            )
            if existing and existing.id != user.id:
                raise ConflictException(
                    ErrorCode.USER_ALREADY_EXISTS,
                    extra={'username': update_data['username']},
                )

        if 'email' in update_data and update_data['email']:
            existing = await repository.get_by_email(
                update_data['email'],
                active_only=False,
            )
            if existing and existing.id != user.id:
                raise ConflictException(
                    ErrorCode.USER_ALREADY_EXISTS,
                    extra={'email': update_data['email']},
                )

        if 'phone' in update_data and update_data['phone']:
            existing = await repository.get_by_phone(
                update_data['phone'],
                active_only=False,
            )
            if existing and existing.id != user.id:
                raise ConflictException(
                    ErrorCode.PHONE_ALREADY_REGISTERED,
                    extra={'phone': update_data['phone']},
                )


def get_user_service() -> UserService:
    """Создаёт экземпляр UserService.

    Returns:
        UserService: Экземпляр сервиса пользователей

    """
    return UserService()
