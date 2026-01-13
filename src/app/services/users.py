"""Сервисный слой для модуля пользователей.

Содержит бизнес-логику, валидации и обработку ошибок.
Использует Repository для доступа к данным и возвращает Pydantic схемы.
"""

from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode, Limits, UserRole
from app.core.database import get_session
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    InternalServerException,
    NotFoundException,
    ValidationException,
)
from app.core.security import create_tokens_pair, verify_password
from app.models.cafes import Cafe
from app.models.users import User
from app.repositories.users import UserRepository
from app.schemas.users import (
    UserCreate,
    UserInfo,
    UserShortInfo,
    UserUpdate,
)


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис."""
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_user_by_id(
        self,
        user_id: int,
        current_user: User | None = None,
    ) -> UserInfo:
        """Получает пользователя по ID.

        Args:
            user_id: ID пользователя
            current_user: Текущий аутентифицированный пользователь
                        (для проверки прав доступа)

        Returns:
            UserInfo: Информация о пользователе

        """
        if current_user is None:
            raise AuthenticationException(
                ErrorCode.AUTHENTICATION_REQUIRED,
                extra={'action': 'просмотр'},
            )

        if not current_user.is_superuser and current_user.id != user_id:
            raise AuthorizationException(
                ErrorCode.INSUFFICIENT_PERMISSIONS,
                extra={'action': 'просмотр', 'target_user_id': user_id},
            )

        user = await self.user_repo.get(user_id, active_only=True)
        if not user:
            raise NotFoundException(
                ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
            )
        return UserInfo.from_orm(user)

    async def get_users_list(
        self,
        skip: int = 0,
        limit: int = Limits.DEFAULT_PAGE_SIZE,
        active_only: bool = True,
        current_user: User | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[UserInfo]:
        """Получает список пользователей.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            active_only: Если True, возвращает только активных пользователей
            current_user: Текущий аутентифицированный пользователь
                        (для проверки прав доступа)
            filters: Дополнительные фильтры

        Returns:
            List[UserInfo]: Список пользователей

        """
        # Проверка прав уже выполнена в зависимости
        # get_current_manager_or_superuser
        users = await self.user_repo.get_multi(
            skip=skip,
            limit=limit,
            active_only=active_only,
            filters=filters,
        )
        return [UserInfo.from_orm(user) for user in users]

    async def create_user(
        self,
        user_create: UserCreate,
        current_user: User | None = None,
    ) -> UserInfo:
        """Создаёт нового пользователя.

        Args:
            user_create: Данные для создания пользователя
            current_user: Текущий аутентифицированный пользователь
                        (если создаёт администратор)

        Returns:
            UserInfo: Созданный пользователь

        """
        if await self.user_repo.get_by_username(
            user_create.username,
            active_only=False,
        ):
            raise ConflictException(
                ErrorCode.USER_ALREADY_EXISTS,
                extra={'username': user_create.username},
            )
        if user_create.email and await self.user_repo.get_by_email(
            user_create.email,
            active_only=False,
        ):
            raise ConflictException(
                ErrorCode.USER_ALREADY_EXISTS,
                extra={'email': user_create.email},
            )
        if user_create.phone and await self.user_repo.get_by_phone(
            user_create.phone,
            active_only=False,
        ):
            raise ConflictException(
                ErrorCode.PHONE_ALREADY_REGISTERED,
                extra={'phone': user_create.phone},
            )
        try:
            user_data = user_create.model_dump()
            user = await self.user_repo.create_user(user_data)
            return UserInfo.from_orm(user)
        except Exception as e:
            raise InternalServerException(
                ErrorCode.INTERNAL_SERVER_ERROR,
                extra={'original_error': str(e)},
            )

    async def update_user(  # noqa: C901
        self,
        user_id: int,
        user_update: UserUpdate,
        current_user: User | None = None,
    ) -> UserInfo:
        """Обновляет информацию о пользователе."""
        from sqlalchemy.exc import IntegrityError

        try:
            self._check_user_access_by_id(
                user_id=user_id,
                current_user=current_user,
                action='обновление',
            )
            user = await self.user_repo.get(user_id, active_only=False)
            if not user:
                raise NotFoundException(
                    ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
                )

            await self._validate_update_uniqueness(
                self.user_repo, user, user_update
            )
            update_data = user_update.model_dump(exclude_unset=True)
            role = update_data.pop('role', None)
            managed_cafe_ids = update_data.pop('managed_cafes', None)

            if 'password' in update_data:
                if verify_password(
                    update_data['password'], user.password_hash
                ):
                    raise ValidationException(ErrorCode.PASSWORD_SAME_AS_OLD)

            if role is not None:
                if current_user is None or not current_user.is_superuser:
                    raise AuthorizationException(
                        ErrorCode.INSUFFICIENT_PERMISSIONS,
                        extra={'field': 'role'},
                    )
                update_data['is_superuser'] = role == UserRole.ADMIN
                if role == UserRole.USER and managed_cafe_ids is None:
                    managed_cafe_ids = []

            if managed_cafe_ids is not None:
                if current_user is None or not current_user.is_superuser:
                    raise AuthorizationException(
                        ErrorCode.INSUFFICIENT_PERMISSIONS,
                        extra={'field': 'managed_cafes'},
                    )

                cafes: list[Cafe] = []
                if managed_cafe_ids:
                    result = await self.session.execute(
                        select(Cafe).where(Cafe.id.in_(managed_cafe_ids))
                    )
                    cafes = list(result.scalars().all())

                    missing_ids = set(managed_cafe_ids) - {
                        cafe.id for cafe in cafes
                    }
                    if missing_ids:
                        raise NotFoundException(
                            ErrorCode.CAFE_NOT_FOUND,
                            extra={
                                'cafe_ids': sorted(missing_ids),
                                'user_id': user_id,
                            },
                        )

                await self.session.refresh(
                    user, attribute_names=['managed_cafes']
                )
                user.managed_cafes = cafes

            updated_user = await self.user_repo.update_user(user, update_data)
            return UserInfo.from_orm(updated_user)
        except (
            AuthorizationException,
            ValidationException,
            NotFoundException,
            ConflictException,
        ) as e:
            raise e
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
        user_id: int,
        current_user: User | None = None,
    ) -> UserInfo:
        """Деактивирует пользователя (логическое удаление).

        Args:
            user_id: ID пользователя для деактивации
            current_user: Текущий аутентифицированный пользователь

        Returns:
            UserInfo: Деактивированный пользователь

        """
        from sqlalchemy.exc import IntegrityError

        try:
            self._check_user_access_by_id(
                user_id=user_id,
                current_user=current_user,
                action='удаление',
            )
            user = await self.user_repo.get(user_id, active_only=False)
            if not user:
                raise NotFoundException(
                    ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
                )
            if current_user and user.id == current_user.id:
                raise ValidationException(ErrorCode.CANNOT_DELETE_OWN_ACCOUNT)
            deleted_user = await self.user_repo.delete_user(user_id)
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
        login: str,
        password: str,
    ) -> dict[str, Any]:
        """Аутентифицирует пользователя.

        Args:
            login: Имя пользователя, email или телефон
            password: Пароль

        Returns:
            Dict[str, Any]: Словарь с пользователем и токенами

        """
        user = await self.user_repo.authenticate(login, password)
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
        refresh_token: str,
    ) -> dict[str, Any]:
        """Обновляет access токен с помощью refresh токена.

        Args:
            refresh_token: Refresh токен

        Returns:
            Dict[str, Any]: Новые токены и информация о пользователе

        """
        from app.core.security import verify_refresh_token

        token_data = verify_refresh_token(refresh_token)
        if not token_data or not token_data.user_id:
            raise AuthenticationException(ErrorCode.INVALID_REFRESH_TOKEN)
        user = await self.user_repo.get(
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
        user_id: int,
        current_password: str,
        new_password: str,
        current_user: User | None = None,
    ) -> UserInfo:
        """Обновляет пароль пользователя.

        Args:
            user_id: ID пользователя
            current_password: Текущий пароль (для проверки)
            new_password: Новый пароль
            current_user: Текущий аутентифицированный пользователь

        Returns:
            UserInfo: Пользователь с обновлённым паролем

        """
        user = await self.user_repo.get(user_id, active_only=True)
        if not user:
            raise NotFoundException(
                ErrorCode.USER_NOT_FOUND, extra={'user_id': user_id}
            )
        await self._check_user_access(user, current_user, 'изменение пароля')
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationException(ErrorCode.INCORRECT_CURRENT_PASSWORD)

        if verify_password(new_password, user.password_hash):
            raise ValidationException(ErrorCode.PASSWORD_SAME_AS_OLD)
        updated_user = await self.user_repo.update_password(
            user,
            new_password,
        )
        return UserInfo.from_orm(updated_user)

    async def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = Limits.DEFAULT_PAGE_SIZE,
        current_user: User | None = None,
    ) -> list[UserInfo]:
        """Ищет пользователей по строке запроса.

        Args:
            query: Строка поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            current_user: Текущий аутентифицированный пользователь

        Returns:
            List[UserInfo]: Найденные пользователи

        """
        if not self._is_superuser_or_none(current_user):
            raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)
        users = await self.user_repo.search(
            query,
            skip=skip,
            limit=limit,
            active_only=True,
        )
        return [UserInfo.from_orm(user) for user in users]

    async def get_user_short_info(
        self,
        user_id: int,
    ) -> UserShortInfo | None:
        """Получает краткую информацию о пользователе.

        Используется для вложенных объектов в других схемах.

        Args:
            user_id: ID пользователя

        Returns:
            UserShortInfo: Краткая информация о пользователе или None

        """
        user = await self.user_repo.get(user_id, active_only=True)
        if not user:
            return None
        return UserShortInfo.from_orm(user)

    def _is_superuser_or_none(self, user: User | None) -> bool:
        """Проверяет, является ли пользователь суперпользователем или None.

        Args:
            user: Пользователь или None

        Returns:
            bool: True если пользователь суперпользователь или None

        """
        if user is None:
            return False
        return user.is_superuser

    @staticmethod
    def _check_user_access_by_id(
        user_id: int,
        current_user: User | None,
        action: str,
    ) -> None:
        """Проверяет доступ по ID пользователя без обращения к БД."""
        if current_user is None:
            raise AuthenticationException(
                ErrorCode.AUTHENTICATION_REQUIRED, extra={'action': action}
            )

        if current_user.is_superuser:
            return

        if current_user.id != user_id:
            raise AuthorizationException(
                ErrorCode.INSUFFICIENT_PERMISSIONS,
                extra={'action': action, 'target_user_id': user_id},
            )

    async def _check_user_access(
        self,
        target_user: User,
        current_user: User | None,
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


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserService:
    """Создаёт экземпляр UserService.

    Returns:
        UserService: Экземпляр сервиса пользователей

    """
    return UserService(session)
