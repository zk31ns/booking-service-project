"""Тесты для UserService.

Тестирует бизнес-логику, валидации и обработку ошибок
в сервисном слое пользователей.
"""

from typing import Callable

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.v1.users.repository import UserRepository
from src.app.api.v1.users.schemas import UserCreate, UserInfo, UserUpdate
from src.app.api.v1.users.service import UserService
from src.app.core.constants import ErrorCode
from src.app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    InternalServerException,
    NotFoundException,
    ValidationException,
)


class TestUserService:
    """Тесты для методов UserService."""

    # ===================== Тесты get_user_by_id =====================

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение пользователя по ID."""
        repository = UserRepository()
        service = UserService(repository)
        created_user = await create_test_user(username='testuser1')

        result = await service.get_user_by_id(
            session=test_db,
            user_id=created_user.id,
            current_user=created_user,
        )

        assert isinstance(result, UserInfo)
        assert result.id == created_user.id
        assert result.username == 'testuser1'
        assert result.active is True

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка получить несуществующего пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        current_user = await create_test_user()

        with pytest.raises(NotFoundException) as exc_info:
            await service.get_user_by_id(
                session=test_db,
                user_id=999,
                current_user=current_user,
            )

        assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND
        assert exc_info.value.extra['user_id'] == 999

    @pytest.mark.asyncio
    async def test_get_user_by_id_unauthorized(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка получить другого пользователя без прав."""
        repository = UserRepository()
        service = UserService(repository)
        user1 = await create_test_user(username='user1')
        user2 = await create_test_user(username='user2')

        with pytest.raises(AuthorizationException) as exc_info:
            await service.get_user_by_id(
                session=test_db,
                user_id=user1.id,
                current_user=user2,
            )

        assert exc_info.value.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS

    @pytest.mark.asyncio
    async def test_get_user_by_id_requires_auth(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка получить пользователя без аутентификации."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user()

        with pytest.raises(AuthenticationException) as exc_info:
            await service.get_user_by_id(
                session=test_db,
                user_id=user.id,
                current_user=None,
            )

        assert exc_info.value.error_code == ErrorCode.AUTHENTICATION_REQUIRED

    @pytest.mark.asyncio
    async def test_get_user_by_id_admin_access(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Администратор может получить любого пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)
        regular_user = await create_test_user(username='regular')

        result = await service.get_user_by_id(
            session=test_db,
            user_id=regular_user.id,
            current_user=admin,
        )

        assert result.id == regular_user.id
        assert result.username == 'regular'

    # ===================== Тесты get_users_list =====================

    @pytest.mark.asyncio
    async def test_get_users_list_success_admin(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Администратор может получить список пользователей."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)

        for i in range(5):
            await create_test_user(username=f'user{i}')

        users = await service.get_users_list(
            session=test_db,
            current_user=admin,
        )

        assert len(users) == 6
        assert all(isinstance(user, UserInfo) for user in users)

    @pytest.mark.asyncio
    async def test_get_users_list_pagination(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка пагинации в списке пользователей."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)

        for i in range(15):
            await create_test_user(username=f'user{i}')

        users_page1 = await service.get_users_list(
            session=test_db,
            skip=0,
            limit=5,
            current_user=admin,
        )

        users_page2 = await service.get_users_list(
            session=test_db,
            skip=5,
            limit=5,
            current_user=admin,
        )

        assert len(users_page1) == 5
        assert len(users_page2) == 5

        user_ids_page1 = {user.id for user in users_page1}
        user_ids_page2 = {user.id for user in users_page2}
        assert user_ids_page1.isdisjoint(user_ids_page2)

    @pytest.mark.asyncio
    async def test_get_users_list_regular_user_denied(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Обычный пользователь не может получить список пользователей."""
        repository = UserRepository()
        service = UserService(repository)
        regular_user = await create_test_user(username='regular')

        with pytest.raises(AuthorizationException) as exc_info:
            await service.get_users_list(
                session=test_db,
                current_user=regular_user,
            )

        assert exc_info.value.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS

    @pytest.mark.asyncio
    async def test_get_users_list_with_filters(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Фильтрация списка пользователей."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)

        await create_test_user(username='active', is_blocked=False)
        await create_test_user(username='blocked', is_blocked=True)
        await create_test_user(username='deactivated', active=False)

        active_users = await service.get_users_list(
            session=test_db,
            active_only=True,
            current_user=admin,
        )

        all_users = await service.get_users_list(
            session=test_db,
            active_only=False,
            current_user=admin,
        )

        blocked_users = await service.get_users_list(
            session=test_db,
            filters={'is_blocked': True},
            current_user=admin,
        )

        assert len(active_users) >= 2
        assert len(all_users) >= 4
        assert len(blocked_users) == 1
        assert blocked_users[0].username == 'blocked'

    # ===================== Тесты create_user =====================

    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное создание пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        user_data = UserCreate(
            username='newuser',
            email='new@example.com',
            phone='+79161234567',
            tg_id=None,
            password='Password123!',
        )

        result = await service.create_user(
            session=test_db,
            user_create=user_data,
            current_user=None,
        )

        assert isinstance(result, UserInfo)
        assert result.username == 'newuser'
        assert result.email == 'new@example.com'
        assert result.phone == '+79161234567'
        assert result.active is True
        assert result.is_superuser is False
        assert result.is_blocked is False

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка создать пользователя с существующим username."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(
            username='existing', email='existing@example.com'
        )

        user_data = UserCreate(
            username='existing',
            email='new@example.com',
            phone=None,
            tg_id=None,
            password='Password123!',
        )

        with pytest.raises(ConflictException) as exc_info:
            await service.create_user(
                session=test_db,
                user_create=user_data,
            )

        assert exc_info.value.error_code == ErrorCode.USER_ALREADY_EXISTS
        assert exc_info.value.extra['username'] == 'existing'

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка создать пользователя с существующим email."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(username='user1', email='existing@example.com')

        user_data = UserCreate(
            username='user2',
            email='existing@example.com',
            phone=None,
            tg_id=None,
            password='Password123!',
        )

        with pytest.raises(ConflictException) as exc_info:
            await service.create_user(
                session=test_db,
                user_create=user_data,
            )

        assert exc_info.value.error_code == ErrorCode.USER_ALREADY_EXISTS
        assert exc_info.value.extra['email'] == 'existing@example.com'

    @pytest.mark.asyncio
    async def test_create_user_duplicate_phone(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка создать пользователя с существующим телефоном."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(username='user1', phone='+79161234567')

        user_data = UserCreate(
            username='user2',
            email='new@example.com',
            phone='+79161234567',
            tg_id=None,
            password='Password123!',
        )

        with pytest.raises(ConflictException) as exc_info:
            await service.create_user(
                session=test_db,
                user_create=user_data,
            )

        assert exc_info.value.error_code == ErrorCode.PHONE_ALREADY_REGISTERED
        assert exc_info.value.extra['phone'] == '+79161234567'

    @pytest.mark.asyncio
    async def test_create_user_admin_creation(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Администратор создает пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)

        user_data = UserCreate(
            username='admin_created',
            email='admin_created@example.com',
            phone=None,
            tg_id=None,
            password='Password123!',
        )

        result = await service.create_user(
            session=test_db,
            user_create=user_data,
            current_user=admin,
        )

        assert result.username == 'admin_created'

    # ===================== Тесты update_user =====================

    @pytest.mark.asyncio
    async def test_update_user_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное обновление пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(username='original')

        update_data = UserUpdate(
            username='updated',
            email='updated@example.com',
            phone=None,
            tg_id=None,
            password=None,
            is_blocked=None,
            is_superuser=None,
            active=None,
        )

        result = await service.update_user(
            session=test_db,
            user_id=user.id,
            user_update=update_data,
            current_user=user,
        )

        assert result.username == 'updated'
        assert result.email == 'updated@example.com'

    @pytest.mark.asyncio
    async def test_update_user_partial_update(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Частичное обновление пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(
            username='original',
            email='original@example.com',
            phone='+79160000000',
        )

        update_data = UserUpdate(
            email='updated@example.com',
            username=None,
            phone=None,
            tg_id=None,
            password=None,
            is_blocked=None,
            is_superuser=None,
            active=None,
        )

        result = await service.update_user(
            session=test_db,
            user_id=user.id,
            user_update=update_data,
            current_user=user,
        )

        assert result.username == 'original'
        assert result.email == 'updated@example.com'
        assert result.phone == '+79160000000'

    @pytest.mark.asyncio
    async def test_update_user_password_same_as_old_in_update(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка установить тот же пароль при обновлении пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(
            username='testuser',
            password='OldPassword123!',
        )

        update_data = UserUpdate(
            password='OldPassword123!',
            username=None,
            email=None,
            phone=None,
            tg_id=None,
            is_blocked=None,
            is_superuser=None,
            active=None,
        )

        with pytest.raises(ValidationException) as exc_info:
            await service.update_user(
                session=test_db,
                user_id=user.id,
                user_update=update_data,
                current_user=user,
            )

        assert exc_info.value.error_code == ErrorCode.PASSWORD_SAME_AS_OLD

    @pytest.mark.asyncio
    async def test_update_user_duplicate_username(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка установить username другого пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(username='user1')
        user2 = await create_test_user(username='user2')

        update_data = UserUpdate(
            username='user1',
            email=None,
            phone=None,
            tg_id=None,
            password=None,
            is_blocked=None,
            is_superuser=None,
            active=None,
        )

        with pytest.raises(ConflictException) as exc_info:
            await service.update_user(
                session=test_db,
                user_id=user2.id,
                user_update=update_data,
                current_user=user2,
            )

        assert exc_info.value.error_code == ErrorCode.USER_ALREADY_EXISTS
        assert exc_info.value.extra['username'] == 'user1'

    @pytest.mark.asyncio
    async def test_update_user_admin_updates_other_user(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Администратор обновляет другого пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)
        regular_user = await create_test_user(username='regular')

        update_data = UserUpdate(
            is_blocked=True,
            username=None,
            email=None,
            phone=None,
            tg_id=None,
            password=None,
            is_superuser=None,
            active=None,
        )

        result = await service.update_user(
            session=test_db,
            user_id=regular_user.id,
            user_update=update_data,
            current_user=admin,
        )

        assert result.is_blocked is True

    # ===================== Тесты delete_user =====================

    @pytest.mark.asyncio
    async def test_delete_user_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное удаление (деактивация) пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)
        user_to_delete = await create_test_user(username='todelete')

        result = await service.delete_user(
            session=test_db,
            user_id=user_to_delete.id,
            current_user=admin,
        )

        assert result.active is False

        with pytest.raises(NotFoundException):
            await service.get_user_by_id(
                session=test_db,
                user_id=user_to_delete.id,
                current_user=admin,
            )

    @pytest.mark.asyncio
    async def test_delete_user_cannot_delete_self(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Пользователь не может удалить свой аккаунт через этот метод."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user()

        with pytest.raises(ValidationException) as exc_info:
            await service.delete_user(
                session=test_db,
                user_id=user.id,
                current_user=user,
            )

        assert exc_info.value.error_code == ErrorCode.CANNOT_DELETE_OWN_ACCOUNT

    @pytest.mark.asyncio
    async def test_delete_user_regular_user_cannot_delete(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Обычный пользователь не может удалять других."""
        repository = UserRepository()
        service = UserService(repository)
        user1 = await create_test_user(username='user1')
        user2 = await create_test_user(username='user2')

        with pytest.raises(AuthorizationException) as exc_info:
            await service.delete_user(
                session=test_db,
                user_id=user1.id,
                current_user=user2,
            )

        assert exc_info.value.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS

    # ===================== Тесты authenticate_user =====================

    @pytest.mark.asyncio
    async def test_authenticate_user_success_username(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешная аутентификация по username."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(
            username='testuser',
            password='Password123!',
        )

        result = await service.authenticate_user(
            session=test_db,
            login='testuser',
            password='Password123!',
        )

        assert 'user' in result
        assert 'tokens' in result
        assert result['user'].username == 'testuser'
        assert 'access_token' in result['tokens']
        assert 'refresh_token' in result['tokens']

    @pytest.mark.asyncio
    async def test_authenticate_user_success_email(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешная аутентификация по email."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(
            username='testuser',
            email='test@example.com',
            password='Password123!',
        )

        result = await service.authenticate_user(
            session=test_db,
            login='test@example.com',
            password='Password123!',
        )

        assert result['user'].username == 'testuser'

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Неверные учетные данные."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(
            username='testuser',
            password='Password123!',
        )

        with pytest.raises(AuthenticationException) as exc_info:
            await service.authenticate_user(
                session=test_db,
                login='testuser',
                password='WrongPassword!',
            )

        assert exc_info.value.error_code == ErrorCode.INVALID_CREDENTIALS

    @pytest.mark.asyncio
    async def test_authenticate_user_blocked(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Аутентификация заблокированного пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(
            username='blocked',
            password='Password123!',
            is_blocked=True,
        )

        with pytest.raises(AuthorizationException) as exc_info:
            await service.authenticate_user(
                session=test_db,
                login='blocked',
                password='Password123!',
            )

        assert exc_info.value.error_code == ErrorCode.USER_BLOCKED

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Аутентификация неактивного пользователя."""
        repository = UserRepository()
        service = UserService(repository)
        await create_test_user(
            username='inactive',
            password='Password123!',
            active=False,
        )

        with pytest.raises(AuthorizationException) as exc_info:
            await service.authenticate_user(
                session=test_db,
                login='inactive',
                password='Password123!',
            )

        assert exc_info.value.error_code == ErrorCode.USER_DEACTIVATED

    # ===================== Тесты refresh_tokens =====================

    @pytest.mark.asyncio
    async def test_refresh_tokens_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное обновление токенов."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(username='testuser')

        from src.app.core.security import create_refresh_token

        refresh_token = create_refresh_token({
            'sub': user.username,
            'user_id': user.id,
        })

        result = await service.refresh_tokens(
            session=test_db,
            refresh_token=refresh_token,
        )

        assert 'user' in result
        assert 'tokens' in result
        assert result['user'].id == user.id
        assert 'access_token' in result['tokens']
        assert 'refresh_token' in result['tokens']

    @pytest.mark.asyncio
    async def test_refresh_tokens_invalid_token(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Неверный refresh токен."""
        repository = UserRepository()
        service = UserService(repository)

        with pytest.raises(AuthenticationException) as exc_info:
            await service.refresh_tokens(
                session=test_db,
                refresh_token='invalid.token.here',
            )

        assert exc_info.value.error_code == ErrorCode.INVALID_REFRESH_TOKEN

    @pytest.mark.asyncio
    async def test_refresh_tokens_user_not_found(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Refresh токен для несуществующего пользователя."""
        repository = UserRepository()
        service = UserService(repository)

        from src.app.core.security import create_refresh_token

        refresh_token = create_refresh_token({
            'sub': 'nonexistent',
            'user_id': 999,
        })

        with pytest.raises(AuthenticationException) as exc_info:
            await service.refresh_tokens(
                session=test_db,
                refresh_token=refresh_token,
            )

        assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND

    # ===================== Тесты update_user_password =====================

    @pytest.mark.asyncio
    async def test_update_user_password_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешная смена пароля."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(
            username='testuser',
            password='OldPassword123!',
        )

        result = await service.update_user_password(
            session=test_db,
            user_id=user.id,
            current_password='OldPassword123!',
            new_password='NewPassword123!',
            current_user=user,
        )

        assert result.id == user.id

        auth_result = await service.authenticate_user(
            session=test_db,
            login='testuser',
            password='NewPassword123!',
        )
        assert auth_result['user'].id == user.id

    @pytest.mark.asyncio
    async def test_update_user_password_incorrect_current(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Неверный текущий пароль."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(
            username='testuser',
            password='CorrectPassword123!',
        )

        with pytest.raises(AuthenticationException) as exc_info:
            await service.update_user_password(
                session=test_db,
                user_id=user.id,
                current_password='WrongPassword123!',
                new_password='NewPassword123!',
                current_user=user,
            )

        assert exc_info.value.error_code == (
            ErrorCode.INCORRECT_CURRENT_PASSWORD
        )

    @pytest.mark.asyncio
    async def test_update_user_password_same_as_old_in_password_method(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Новый пароль совпадает со старым в методе update_user_password."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(
            username='testuser',
            password='Password123!',
        )

        with pytest.raises(ValidationException) as exc_info:
            await service.update_user_password(
                session=test_db,
                user_id=user.id,
                current_password='Password123!',
                new_password='Password123!',
                current_user=user,
            )

        assert exc_info.value.error_code == ErrorCode.PASSWORD_SAME_AS_OLD

    @pytest.mark.asyncio
    async def test_update_user_password_admin_changes_other(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Администратор меняет пароль другому пользователю."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)
        regular_user = await create_test_user(
            username='regular',
            password='OldPassword123!',
        )

        result = await service.update_user_password(
            session=test_db,
            user_id=regular_user.id,
            current_password='OldPassword123!',
            new_password='AdminChangedPassword123!',
            current_user=admin,
        )

        assert result.id == regular_user.id

        auth_result = await service.authenticate_user(
            session=test_db,
            login='regular',
            password='AdminChangedPassword123!',
        )
        assert auth_result['user'].id == regular_user.id

    # ===================== Тесты search_users =====================

    @pytest.mark.asyncio
    async def test_search_users_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешный поиск пользователей."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)

        await create_test_user(username='john_doe', email='john@example.com')
        await create_test_user(username='jane_doe', email='jane@example.com')
        await create_test_user(
            username='alice_smith', email='alice@example.com'
        )
        await create_test_user(username='bob_johnson', email='bob@example.com')

        results_doe = await service.search_users(
            session=test_db,
            query='doe',
            current_user=admin,
        )

        results_alice = await service.search_users(
            session=test_db,
            query='alice@example.com',
            current_user=admin,
        )

        assert len(results_doe) == 2
        assert len(results_alice) == 1
        assert results_alice[0].username == 'alice_smith'

    @pytest.mark.asyncio
    async def test_search_users_regular_user_denied(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Обычный пользователь не может искать пользователей."""
        repository = UserRepository()
        service = UserService(repository)
        regular_user = await create_test_user(username='regular')

        with pytest.raises(AuthorizationException) as exc_info:
            await service.search_users(
                session=test_db,
                query='test',
                current_user=regular_user,
            )

        assert exc_info.value.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS

    @pytest.mark.asyncio
    async def test_search_users_empty_query(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Поиск с пустым запросом (должен вернуть пустой список)."""
        repository = UserRepository()
        service = UserService(repository)
        admin = await create_test_user(username='admin', is_superuser=True)

        results = await service.search_users(
            session=test_db,
            query='',
            current_user=admin,
        )

        assert results == []

    # ===================== Тесты get_user_short_info =====================

    @pytest.mark.asyncio
    async def test_get_user_short_info_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение краткой информации."""
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(
            username='testuser',
            email='test@example.com',
            phone='+79161234567',
        )

        result = await service.get_user_short_info(
            session=test_db,
            user_id=user.id,
        )

        assert result is not None
        assert result.id == user.id
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
        assert result.phone == '+79161234567'

    @pytest.mark.asyncio
    async def test_get_user_short_info_not_found(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Краткая информация для несуществующего пользователя."""
        repository = UserRepository()
        service = UserService(repository)

        result = await service.get_user_short_info(
            session=test_db,
            user_id=999,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_short_info_inactive(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Краткая информация для неактивного пользователя.

        Не должна возвращаться.
        """
        repository = UserRepository()
        service = UserService(repository)
        user = await create_test_user(
            username='inactive',
            active=False,
        )

        result = await service.get_user_short_info(
            session=test_db,
            user_id=user.id,
        )

        assert result is None

    # ===================== Тесты вспомогательных методов =====================

    @pytest.mark.asyncio
    async def test_is_superuser_or_none(
        self,
        create_test_user: Callable,
    ) -> None:
        """Проверка метода _is_superuser_or_none."""
        repository = UserRepository()
        service = UserService(repository)

        regular_user = await create_test_user(username='regular')
        admin_user = await create_test_user(
            username='admin', is_superuser=True
        )

        assert service._is_superuser_or_none(None) is False
        assert service._is_superuser_or_none(regular_user) is False
        assert service._is_superuser_or_none(admin_user) is True

    @pytest.mark.asyncio
    async def test_check_user_access(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка метода _check_user_access."""
        repository = UserRepository()
        service = UserService(repository)

        user1 = await create_test_user(username='user1')
        await create_test_user(username='user2')
        admin = await create_test_user(username='admin', is_superuser=True)

        with pytest.raises(AuthenticationException):
            await service._check_user_access(user1, None, 'просмотр')

        try:
            await service._check_user_access(user1, user1, 'просмотр')
        except AuthorizationException:
            pytest.fail('Пользователь должен иметь доступ к своему профилю')

        try:
            await service._check_user_access(user1, admin, 'просмотр')
        except AuthorizationException:
            pytest.fail('Администратор должен иметь доступ ко всем профилям')

    # ===================== Тесты на ошибки =====================

    @pytest.mark.asyncio
    async def test_service_internal_server_error_on_create(
        self,
        test_db: AsyncSession,
        mocker: MockerFixture,
    ) -> None:
        """Исключение при создании пользователя (имитация ошибки БД)."""
        repository = UserRepository()
        service = UserService(repository)

        user_data = UserCreate(
            username='testuser',
            email='test@example.com',
            phone=None,
            tg_id=None,
            password='Password123!',
        )

        mock_create = mocker.patch.object(repository, 'create')
        mock_create.side_effect = Exception('Database connection failed')

        with pytest.raises(InternalServerException) as exc_info:
            await service.create_user(
                session=test_db,
                user_create=user_data,
            )

        assert exc_info.value.error_code == ErrorCode.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_get_user_service_factory(self) -> None:
        """Тест фабрики get_user_service."""
        from src.app.api.v1.users.service import get_user_service

        service = get_user_service()

        assert isinstance(service, UserService)
        assert isinstance(service.repository, UserRepository)
