"""Тесты для зависимостей (dependencies) модуля пользователей и аутентификации.

Содержит тесты для всех зависимостей из src/app/api/v1/users/dependencies.py
"""

from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.v1.users.dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_user,
    get_current_user_id,
    get_current_user_username,
    get_db,
    get_optional_user,
    get_user_repository,
    require_cafe_manager,
    validate_refresh_token,
)
from src.app.core.constants import ErrorCode
from src.app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
)
from src.app.core.security import create_access_token, create_refresh_token

PATH_USER_ID = (
    'src.app.api.v1.users.dependencies.get_current_user_id_from_token'
)
PATH_USERNAME = (
    'src.app.api.v1.users.dependencies.get_current_username_from_token'
)
PATH_VERIFY_REFRESH = 'src.app.api.v1.users.dependencies.verify_refresh_token'


@pytest.mark.asyncio
class TestGetDB:
    """Тесты для зависимости get_db."""

    async def test_get_db_success(self) -> None:
        """Проверяет, что get_db возвращает асинхронный генератор."""
        db_gen = get_db()
        async for session in db_gen:
            assert session is not None
            assert isinstance(session, AsyncSession)
            break


@pytest.mark.asyncio
class TestGetUserRepository:
    """Тесты для зависимости get_user_repository."""

    def test_get_user_repository_success(self) -> None:
        """Проверяет создание экземпляра UserRepository."""
        from src.app.api.v1.users.repository import UserRepository

        repository = get_user_repository()
        assert isinstance(repository, UserRepository)


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Тесты для зависимости get_current_user."""

    async def test_get_current_user_success_by_user_id(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
        mock_credentials: Callable,
    ) -> None:
        """Успешное получение пользователя по user_id из токена."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')

        token_data = {'sub': user.username, 'user_id': user.id}
        token = create_access_token(data=token_data)
        credentials = mock_credentials()
        credentials.credentials = token

        repository.get.return_value = user

        result = await get_current_user(credentials, test_db, repository)

        assert result == user
        repository.get.assert_called_once_with(
            test_db, user.id, active_only=True
        )

    async def test_get_current_user_success_by_username(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
        mock_credentials: Callable,
    ) -> None:
        """Успешное получение пользователя по username из токена."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')

        token_data = {'sub': user.username}
        token = create_access_token(data=token_data)
        credentials = mock_credentials()
        credentials.credentials = token

        with (
            patch(
                PATH_USER_ID,
                return_value=None,
            ),
            patch(
                PATH_USERNAME,
                return_value=user.username,
            ),
        ):
            repository.get_by_username.return_value = user
            result = await get_current_user(credentials, test_db, repository)

            assert result == user
            repository.get_by_username.assert_called_once_with(
                test_db, user.username, active_only=True
            )

    async def test_get_current_user_no_credentials(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Проверяет обработку отсутствия credentials."""
        repository = MagicMock()

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_user(None, test_db, repository)

        assert exc_info.value.error_code == ErrorCode.AUTHENTICATION_REQUIRED

    async def test_get_current_user_invalid_token(
        self,
        test_db: AsyncSession,
        mock_credentials: Callable,
    ) -> None:
        """Проверяет обработку невалидного токена."""
        repository = MagicMock()
        credentials = mock_credentials()
        credentials.credentials = 'invalid_token'

        with (
            patch(
                PATH_USER_ID,
                return_value=None,
            ),
            patch(
                PATH_USERNAME,
                return_value=None,
            ),
        ):
            with pytest.raises(AuthenticationException) as exc_info:
                await get_current_user(credentials, test_db, repository)

            assert exc_info.value.error_code == ErrorCode.INVALID_TOKEN

    async def test_get_current_user_not_found(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
        mock_credentials: Callable,
    ) -> None:
        """Проверяет обработку отсутствия пользователя."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')

        token_data = {'sub': user.username, 'user_id': user.id}
        token = create_access_token(data=token_data)
        credentials = mock_credentials()
        credentials.credentials = token

        repository.get.return_value = None

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_user(credentials, test_db, repository)

        assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND

    async def test_get_current_user_blocked(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
        mock_credentials: Callable,
    ) -> None:
        """Проверяет обработку заблокированного пользователя."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')
        user.is_blocked = True

        token_data = {'sub': user.username, 'user_id': user.id}
        token = create_access_token(data=token_data)
        credentials = mock_credentials()
        credentials.credentials = token

        repository.get.return_value = user

        with pytest.raises(AuthorizationException) as exc_info:
            await get_current_user(credentials, test_db, repository)

        assert exc_info.value.error_code == ErrorCode.USER_BLOCKED


@pytest.mark.asyncio
class TestGetCurrentActiveUser:
    """Тесты для зависимости get_current_active_user."""

    async def test_get_current_active_user_success(
        self,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение активного пользователя."""
        user = await create_test_user(username='testuser')
        user.is_blocked = False
        user.active = True

        result = await get_current_active_user(user)
        assert result == user

    async def test_get_current_active_user_blocked(
        self,
        create_test_user: Callable,
    ) -> None:
        """Проверяет заблокированного пользователя."""
        user = await create_test_user(username='testuser')
        user.is_blocked = True

        with pytest.raises(AuthorizationException) as exc_info:
            await get_current_active_user(user)

        assert exc_info.value.error_code == ErrorCode.USER_BLOCKED

    async def test_get_current_active_user_deactivated(
        self,
        create_test_user: Callable,
    ) -> None:
        """Проверяет неактивного пользователя."""
        user = await create_test_user(username='testuser')
        user.is_blocked = False
        user.active = False

        with pytest.raises(AuthorizationException) as exc_info:
            await get_current_active_user(user)

        assert exc_info.value.error_code == ErrorCode.USER_DEACTIVATED


@pytest.mark.asyncio
class TestGetCurrentSuperuser:
    """Тесты для зависимости get_current_superuser."""

    async def test_get_current_superuser_success(
        self,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение суперпользователя."""
        user = await create_test_user(username='admin')
        user.is_superuser = True

        result = await get_current_superuser(user)
        assert result == user

    async def test_get_current_superuser_not_superuser(
        self,
        create_test_user: Callable,
    ) -> None:
        """Проверяет обычного пользователя."""
        user = await create_test_user(username='regular')
        user.is_superuser = False

        with pytest.raises(AuthorizationException) as exc_info:
            await get_current_superuser(user)

        assert exc_info.value.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS


@pytest.mark.asyncio
class TestGetOptionalUser:
    """Тесты для зависимости get_optional_user."""

    async def test_get_optional_user_with_credentials(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
        mock_credentials: Callable,
    ) -> None:
        """Успешное получение пользователя при наличии credentials."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')
        credentials = mock_credentials()
        credentials.credentials = 'valid_token'

        with patch(
            'src.app.api.v1.users.dependencies.get_current_user',
            AsyncMock(return_value=user),
        ):
            result = await get_optional_user(credentials, test_db, repository)
            assert result == user

    async def test_get_optional_user_no_credentials(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Возвращает None при отсутствии credentials."""
        repository = MagicMock()
        result = await get_optional_user(None, test_db, repository)
        assert result is None

    async def test_get_optional_user_invalid_token(
        self,
        test_db: AsyncSession,
        mock_credentials: Callable,
    ) -> None:
        """Возвращает None при невалидном токене."""
        repository = MagicMock()
        credentials = mock_credentials()
        credentials.credentials = 'invalid_token'

        with patch(
            'src.app.api.v1.users.dependencies.get_current_user',
            AsyncMock(
                side_effect=AuthenticationException(ErrorCode.INVALID_TOKEN)
            ),
        ):
            result = await get_optional_user(credentials, test_db, repository)
            assert result is None


@pytest.mark.asyncio
class TestRequireCafeManager:
    """Тесты для зависимости require_cafe_manager."""

    async def test_require_cafe_manager_superuser(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Суперпользователь всегда проходит проверку."""
        user = await create_test_user(username='admin')
        user.is_superuser = True

        result = await require_cafe_manager(1, user, test_db)
        assert result == user

    async def test_require_cafe_manager_not_implemented(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Для обычного пользователя проверка пока не реализована."""
        user = await create_test_user(username='regular')
        user.is_superuser = False

        result = await require_cafe_manager(1, user, test_db)
        assert result == user


@pytest.mark.asyncio
class TestValidateRefreshToken:
    """Тесты для зависимости validate_refresh_token."""

    async def test_validate_refresh_token_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешная валидация refresh токена."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')

        refresh_token = create_refresh_token({
            'sub': user.username,
            'user_id': user.id,
        })

        mock_token_data = MagicMock()
        mock_token_data.user_id = user.id

        with patch(
            PATH_VERIFY_REFRESH,
            return_value=mock_token_data,
        ):
            repository.get.return_value = user
            result = await validate_refresh_token(
                refresh_token, test_db, repository
            )

            assert result == user
            repository.get.assert_called_once_with(
                test_db, user.id, active_only=True
            )

    async def test_validate_refresh_token_expired(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Проверяет обработку просроченного токена."""
        repository = MagicMock()

        with patch(
            PATH_VERIFY_REFRESH,
            return_value=None,
        ):
            with pytest.raises(AuthenticationException) as exc_info:
                await validate_refresh_token(
                    'expired_token', test_db, repository
                )

            assert exc_info.value.error_code == ErrorCode.TOKEN_EXPIRED

    async def test_validate_refresh_token_user_not_found(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверяет отсутствие пользователя."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')

        refresh_token = create_refresh_token({
            'sub': user.username,
            'user_id': user.id,
        })

        mock_token_data = MagicMock()
        mock_token_data.user_id = user.id

        with patch(
            PATH_VERIFY_REFRESH,
            return_value=mock_token_data,
        ):
            repository.get.return_value = None

            with pytest.raises(AuthenticationException) as exc_info:
                await validate_refresh_token(
                    refresh_token, test_db, repository
                )

            assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND

    async def test_validate_refresh_token_user_blocked(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверяет заблокированного пользователя."""
        repository = MagicMock()
        user = await create_test_user(username='testuser')
        user.is_blocked = True

        refresh_token = create_refresh_token({
            'sub': user.username,
            'user_id': user.id,
        })

        mock_token_data = MagicMock()
        mock_token_data.user_id = user.id

        with patch(
            PATH_VERIFY_REFRESH,
            return_value=mock_token_data,
        ):
            repository.get.return_value = user

            with pytest.raises(AuthenticationException) as exc_info:
                await validate_refresh_token(
                    refresh_token, test_db, repository
                )

            assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND


@pytest.mark.asyncio
class TestCurrentUserHelpers:
    """Тесты вспомогательных зависимостей."""

    async def test_get_current_user_id_success(
        self,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение ID пользователя."""
        user = await create_test_user(username='testuser')

        result = await get_current_user_id(user)
        assert result == user.id

    async def test_get_current_user_username_success(
        self,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение username пользователя."""
        user = await create_test_user(username='testuser')

        result = await get_current_user_username(user)
        assert result == user.username


@pytest.fixture
def mock_credentials() -> Callable:
    """Создает мок HTTP авторизационных данных."""

    def _mock_credentials() -> MagicMock:
        return MagicMock()

    return _mock_credentials


@pytest.mark.asyncio
class TestIntegrationDependencies:
    """Интеграционные тесты для зависимостей."""

    async def test_imports_work_correctly(self) -> None:
        """Проверяет что все зависимости импортируются корректно."""
        from src.app.api.v1.users.dependencies import (
            get_current_active_user,
            get_current_superuser,
            get_current_user,
        )

        assert callable(get_current_user)
        assert callable(get_current_active_user)
        assert callable(get_current_superuser)
