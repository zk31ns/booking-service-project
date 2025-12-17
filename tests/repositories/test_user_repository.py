"""Тесты для UserRepository.

Тестирует CRUD операции и специфичные методы
для работы с пользователями в базе данных.
"""

from typing import Callable, Dict

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.v1.users.repository import UserRepository
from src.app.core.security import verify_password
from src.app.models.models import User


@pytest.mark.asyncio
class TestUserRepository:
    """Тесты для методов UserRepository."""

    # ===================== Тесты метода get =====================

    async def test_get_user_by_id_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение пользователя по ID."""
        repository = UserRepository()
        test_user = await create_test_user(username='testuser')

        user = await repository.get(test_db, user_id=test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.username == 'testuser'
        assert user.active is True

    async def test_get_user_by_id_not_found(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Попытка получить несуществующего пользователя."""
        repository = UserRepository()

        user = await repository.get(test_db, user_id=999)

        assert user is None

    async def test_get_user_by_id_inactive_with_active_only(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Попытка получить неактивного пользователя с active_only=True."""
        repository = UserRepository()
        inactive_user = await create_test_user(
            username='inactive', active=False
        )

        user = await repository.get(test_db, user_id=inactive_user.id)

        assert user is None

    async def test_get_user_by_id_inactive_without_active_only(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Получение неактивного пользователя с active_only=False."""
        repository = UserRepository()
        inactive_user = await create_test_user(
            username='inactive', active=False
        )

        user = await repository.get(
            test_db, user_id=inactive_user.id, active_only=False
        )

        assert user is not None
        assert user.id == inactive_user.id
        assert user.active is False

    # ===================== Тесты метода get_multi =====================

    async def test_get_multi_users_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное получение списка пользователей."""
        repository = UserRepository()
        for i in range(5):
            await create_test_user(username=f'user{i}')

        users = await repository.get_multi(test_db)

        assert isinstance(users, list)
        assert len(users) == 5
        assert all(isinstance(user, User) for user in users)

    async def test_get_multi_users_with_pagination(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Получение списка пользователей с пагинацией."""
        repository = UserRepository()
        for i in range(10):
            await create_test_user(username=f'user{i}')

        users_page1 = await repository.get_multi(test_db, skip=0, limit=3)

        users_page2 = await repository.get_multi(test_db, skip=3, limit=3)

        assert len(users_page1) == 3
        assert len(users_page2) == 3

        user_ids_page1 = {user.id for user in users_page1}
        user_ids_page2 = {user.id for user in users_page2}
        assert user_ids_page1.isdisjoint(user_ids_page2)

    async def test_get_multi_users_active_only(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Фильтрация только активных пользователей."""
        repository = UserRepository()
        await create_test_user(username='active1', active=True)
        await create_test_user(username='active2', active=True)
        await create_test_user(username='inactive', active=False)

        active_users = await repository.get_multi(test_db, active_only=True)
        all_users = await repository.get_multi(test_db, active_only=False)

        assert len(active_users) == 2
        assert len(all_users) == 3

    async def test_get_multi_users_with_filters(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Фильтрация пользователей по параметрам."""
        repository = UserRepository()
        await create_test_user(username='admin', is_superuser=True)
        await create_test_user(username='blocked', is_blocked=True)
        await create_test_user(username='regular', is_superuser=False)

        superusers = await repository.get_multi(
            test_db, filters={'is_superuser': True}
        )

        blocked = await repository.get_multi(
            test_db, filters={'is_blocked': True}
        )

        regular = await repository.get_multi(
            test_db, filters={'is_superuser': False}
        )

        assert len(superusers) == 1
        assert superusers[0].username == 'admin'

        assert len(blocked) == 1
        assert blocked[0].username == 'blocked'

        assert len(regular) == 2

    async def test_get_multi_users_order_by_created_at(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка сортировки по дате создания."""
        repository = UserRepository()
        user1 = await create_test_user(username='user1')
        user2 = await create_test_user(username='user2')

        users = await repository.get_multi(test_db)

        assert users[0].id == user2.id
        assert users[1].id == user1.id

    # ===================== Тесты методов get_by_* =====================

    async def test_get_by_username_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешный поиск пользователя по username."""
        repository = UserRepository()
        await create_test_user(username='testuser')

        user = await repository.get_by_username(test_db, 'testuser')

        assert user is not None
        assert user.username == 'testuser'

    async def test_get_by_username_not_found(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Поиск несуществующего пользователя по username."""
        repository = UserRepository()

        user = await repository.get_by_username(test_db, 'nonexistent')

        assert user is None

    async def test_get_by_email_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешный поиск пользователя по email."""
        repository = UserRepository()
        await create_test_user(username='testuser', email='test@example.com')

        user = await repository.get_by_email(test_db, 'test@example.com')

        assert user is not None
        assert user.email == 'test@example.com'

    async def test_get_by_phone_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешный поиск пользователя по телефону."""
        repository = UserRepository()
        await create_test_user(username='testuser', phone='+79161234567')

        user = await repository.get_by_phone(test_db, '+79161234567')

        assert user is not None
        assert user.phone == '+79161234567'

    async def test_get_by_methods_with_active_only(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Поиск пользователей с учетом флага активности."""
        repository = UserRepository()
        await create_test_user(
            username='inactive',
            email='inactive@example.com',
            phone='+79160000000',
            active=False,
        )

        user_by_username = await repository.get_by_username(
            test_db, 'inactive', active_only=True
        )
        user_by_email = await repository.get_by_email(
            test_db, 'inactive@example.com', active_only=True
        )
        user_by_phone = await repository.get_by_phone(
            test_db, '+79160000000', active_only=True
        )

        user_by_username_all = await repository.get_by_username(
            test_db, 'inactive', active_only=False
        )

        assert user_by_username is None
        assert user_by_email is None
        assert user_by_phone is None
        assert user_by_username_all is not None

    # ===================== Тесты метода create =====================

    async def test_create_user_success(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Успешное создание пользователя."""
        repository = UserRepository()
        user_data: Dict[str, str] = {
            'username': 'newuser',
            'email': 'new@example.com',
            'phone': '+79161234567',
            'password': 'Password123!',
        }

        user = await repository.create(test_db, user_data)

        assert user is not None
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.phone == '+79161234567'
        assert user.active is True
        assert user.is_superuser is False
        assert user.is_blocked is False
        assert user.password_hash is not None
        assert 'password' not in user.__dict__

        assert verify_password('Password123!', user.password_hash)

    async def test_create_user_without_commit(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Создание пользователя без автоматического коммита."""
        repository = UserRepository()
        user_data = {
            'username': 'testuser',
            'password': 'Password123!',
            'email': 'test@example.com',
        }

        user = await repository.create(test_db, user_data, commit=False)

        assert user is not None
        assert user.id is None

        await test_db.commit()
        await test_db.refresh(user)

        assert user.id is not None
        assert user.username == 'testuser'

    async def test_create_user_with_custom_fields(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Создание пользователя с кастомными полями."""
        repository = UserRepository()
        user_data = {
            'username': 'admin',
            'password': 'Password123!',
            'email': 'admin@example.com',
            'is_superuser': True,
            'is_blocked': False,
            'tg_id': '123456789',
        }

        user = await repository.create(test_db, user_data)

        assert user.is_superuser is True
        assert user.is_blocked is False
        assert user.tg_id == '123456789'

    # ===================== Тесты метода update =====================

    async def test_update_user_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное обновление пользователя."""
        repository = UserRepository()
        user = await create_test_user(username='original')

        update_data = {
            'username': 'updated',
            'email': 'updated@example.com',
        }

        updated_user = await repository.update(test_db, user, update_data)

        assert updated_user.username == 'updated'
        assert updated_user.email == 'updated@example.com'
        assert updated_user.id == user.id

    async def test_update_user_password(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Обновление пароля пользователя."""
        repository = UserRepository()
        user = await create_test_user(
            username='testuser', password='OldPassword123!'
        )

        old_password_hash = user.password_hash
        update_data = {'password': 'NewPassword456!'}

        updated_user = await repository.update(test_db, user, update_data)

        assert updated_user.password_hash != old_password_hash
        assert verify_password('NewPassword456!', updated_user.password_hash)
        assert not verify_password(
            'OldPassword123!', updated_user.password_hash
        )

    async def test_update_user_partial(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Частичное обновление пользователя."""
        repository = UserRepository()
        user = await create_test_user(
            username='testuser',
            email='original@example.com',
            phone='+79160000000',
        )

        original_phone = user.phone
        update_data = {'username': 'updated'}

        updated_user = await repository.update(test_db, user, update_data)

        assert updated_user.username == 'updated'
        assert updated_user.email == 'original@example.com'
        assert updated_user.phone == original_phone

    async def test_update_user_without_commit(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Обновление пользователя без коммита."""
        repository = UserRepository()
        user = await create_test_user(username='original')

        update_data = {'username': 'updated'}

        updated_user = await repository.update(
            test_db, user, update_data, commit=False
        )

        assert updated_user.username == 'updated'

        await test_db.refresh(user)
        assert user.username == 'original'

        await test_db.commit()
        await test_db.refresh(user)
        assert user.username == 'updated'

    # ===================== Тесты метода delete =====================

    async def test_delete_user_soft_delete(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Мягкое удаление пользователя (деактивация)."""
        repository = UserRepository()
        user = await create_test_user(username='todelete')

        deleted_user = await repository.delete(test_db, user.id)

        assert deleted_user is not None
        assert deleted_user.id == user.id
        assert deleted_user.active is False

        found_user = await repository.get(test_db, user.id)
        assert found_user is None

        found_user_all = await repository.get(
            test_db, user.id, active_only=False
        )
        assert found_user_all is not None
        assert found_user_all.active is False

    async def test_delete_user_hard_delete(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Жесткое удаление пользователя."""
        repository = UserRepository()
        user = await create_test_user(username='todelete')

        deleted_user = await repository.delete(
            test_db, user.id, hard_delete=True
        )

        assert deleted_user is not None

        found_user = await repository.get(test_db, user.id, active_only=False)
        assert found_user is None

    async def test_delete_user_not_found(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Попытка удалить несуществующего пользователя."""
        repository = UserRepository()

        deleted_user = await repository.delete(test_db, 999)

        assert deleted_user is None

        async def test_delete_user_without_commit(
            self: TestUserRepository,
            test_db: AsyncSession,
            create_test_user: Callable,
        ) -> None:
            """Удаление пользователя без коммита."""
            repository = UserRepository()
            user = await create_test_user(username='todelete')

            deleted_user = await repository.delete(
                test_db, user.id, commit=False
            )

            assert deleted_user is not None
            assert deleted_user.active is False

            db_user = await repository.get(test_db, user.id)
            assert db_user is not None
            assert db_user.active is True

            await test_db.commit()
            db_user = await repository.get(test_db, user.id)
            assert db_user is None

    # ===================== Тесты метода authenticate =====================

    async def test_authenticate_by_username_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешная аутентификация по username."""
        repository = UserRepository()
        await create_test_user(
            username='testuser',
            password='Password123!',
        )

        user = await repository.authenticate(
            test_db, 'testuser', 'Password123!'
        )

        assert user is not None
        assert user.username == 'testuser'

    async def test_authenticate_by_email_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешная аутентификация по email."""
        repository = UserRepository()
        await create_test_user(
            username='testuser',
            email='test@example.com',
            password='Password123!',
        )

        user = await repository.authenticate(
            test_db, 'test@example.com', 'Password123!'
        )

        assert user is not None
        assert user.username == 'testuser'

    async def test_authenticate_by_phone_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешная аутентификация по телефону."""
        repository = UserRepository()
        await create_test_user(
            username='testuser',
            phone='+79161234567',
            password='Password123!',
        )

        user = await repository.authenticate(
            test_db, '+79161234567', 'Password123!'
        )

        assert user is not None
        assert user.username == 'testuser'

    async def test_authenticate_wrong_password(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Аутентификация с неверным паролем."""
        repository = UserRepository()
        await create_test_user(
            username='testuser',
            password='CorrectPassword123!',
        )

        user = await repository.authenticate(
            test_db, 'testuser', 'WrongPassword!'
        )

        assert user is None

    async def test_authenticate_inactive_user(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Аутентификация неактивного пользователя."""
        repository = UserRepository()
        await create_test_user(
            username='inactive',
            password='Password123!',
            active=False,
        )

        user = await repository.authenticate(
            test_db, 'inactive', 'Password123!'
        )

        assert user is None

    async def test_authenticate_user_not_found(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Аутентификация несуществующего пользователя."""
        repository = UserRepository()

        user = await repository.authenticate(
            test_db, 'nonexistent', 'Password123!'
        )

        assert user is None

    # ===================== Тесты метода exists =====================

    async def test_exists_by_username(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка существования пользователя по username."""
        repository = UserRepository()
        await create_test_user(username='existing')

        assert await repository.exists(test_db, username='existing') is True
        assert (
            await repository.exists(test_db, username='nonexistent') is False
        )

    async def test_exists_by_email(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка существования пользователя по email."""
        repository = UserRepository()
        await create_test_user(
            username='testuser', email='existing@example.com'
        )

        assert (
            await repository.exists(test_db, email='existing@example.com')
            is True
        )
        assert (
            await repository.exists(test_db, email='nonexistent@example.com')
            is False
        )

    async def test_exists_by_phone(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка существования пользователя по телефону."""
        repository = UserRepository()
        await create_test_user(username='testuser', phone='+79161234567')

        assert await repository.exists(test_db, phone='+79161234567') is True
        assert await repository.exists(test_db, phone='+79160000000') is False

    async def test_exists_multiple_conditions(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка существования по нескольким условиям."""
        repository = UserRepository()
        await create_test_user(
            username='user1',
            email='user1@example.com',
            phone='+79161111111',
        )
        await create_test_user(
            username='user2',
            email='user2@example.com',
            phone='+79162222222',
        )

        assert (
            await repository.exists(
                test_db,
                username='user1',
                email='user1@example.com',
            )
            is True
        )
        assert (
            await repository.exists(
                test_db,
                username='user1',
                email='wrong@example.com',
            )
            is False
        )

    # ===================== Тесты метода count =====================

    async def test_count_users(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Подсчет количества пользователей."""
        repository = UserRepository()
        for i in range(3):
            await create_test_user(username=f'active{i}')
        await create_test_user(username='inactive', active=False)

        assert await repository.count(test_db) == 3
        assert await repository.count(test_db, active_only=False) == 4

    async def test_count_empty_database(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Подсчет в пустой базе данных."""
        repository = UserRepository()

        assert await repository.count(test_db) == 0

    # ===================== Тесты метода update_password =====================

    async def test_update_password_success(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Успешное обновление пароля."""
        repository = UserRepository()
        user = await create_test_user(
            username='testuser', password='OldPassword123!'
        )

        updated_user = await repository.update_password(
            test_db, user, 'NewPassword456!'
        )

        assert verify_password('NewPassword456!', updated_user.password_hash)
        assert not verify_password(
            'OldPassword123!', updated_user.password_hash
        )

    async def test_update_password_without_commit(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Обновление пароля без коммита."""
        repository = UserRepository()
        user = await create_test_user(
            username='testuser', password='OldPassword123!'
        )

        old_hash = user.password_hash

        updated_user = await repository.update_password(
            test_db, user, 'NewPassword456!', commit=False
        )

        assert verify_password('NewPassword456!', updated_user.password_hash)

        # Проверяем, что в базе старый хэш
        await test_db.refresh(user)
        assert user.password_hash == old_hash

        # Коммитим и проверяем
        await test_db.commit()
        await test_db.refresh(user)
        assert verify_password('NewPassword456!', user.password_hash)

    # ===================== Тесты метода search =====================

    async def test_search_users_by_username(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Поиск пользователей по части username."""
        repository = UserRepository()
        await create_test_user(username='john_doe')
        await create_test_user(username='jane_doe')
        await create_test_user(username='alice_smith')

        results_doe = await repository.search(test_db, 'doe')
        results_alice = await repository.search(test_db, 'alice')

        assert len(results_doe) == 2
        assert len(results_alice) == 1
        assert results_alice[0].username == 'alice_smith'

    async def test_search_users_case_insensitive(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Поиск без учета регистра."""
        repository = UserRepository()
        await create_test_user(username='TestUser')

        results_lower = await repository.search(test_db, 'test')
        results_upper = await repository.search(test_db, 'TEST')

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert results_lower[0].username == 'TestUser'

    async def test_search_users_with_pagination(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Поиск с пагинацией."""
        repository = UserRepository()
        for i in range(10):
            await create_test_user(username=f'user{i}')

        page1 = await repository.search(test_db, 'user', skip=0, limit=3)
        page2 = await repository.search(test_db, 'user', skip=3, limit=3)

        assert len(page1) == 3
        assert len(page2) == 3

        user_ids_page1 = {user.id for user in page1}
        user_ids_page2 = {user.id for user in page2}
        assert user_ids_page1.isdisjoint(user_ids_page2)

    async def test_search_users_empty_query(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Поиск с пустым запросом."""
        repository = UserRepository()
        await create_test_user(username='testuser')

        results = await repository.search(test_db, '')

        assert len(results) >= 1

    async def test_search_users_active_only(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Поиск только активных пользователей."""
        repository = UserRepository()
        await create_test_user(username='active_user', active=True)
        await create_test_user(username='inactive_user', active=False)

        active_results = await repository.search(
            test_db, 'user', active_only=True
        )
        all_results = await repository.search(
            test_db, 'user', active_only=False
        )

        assert len(active_results) == 1
        assert active_results[0].username == 'active_user'
        assert len(all_results) == 2

    async def test_search_users_order_by_username(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Проверка сортировки результатов поиска."""
        repository = UserRepository()
        await create_test_user(username='charlie')
        await create_test_user(username='alice')
        await create_test_user(username='bob')

        results = await repository.search(test_db, '')

        usernames = [user.username for user in results]
        assert usernames == ['alice', 'bob', 'charlie']

    # ================== Тесты инициализации и edge cases ==================

    async def test_repository_init(self) -> None:
        """Проверка инициализации репозитория."""
        repository = UserRepository()

        assert repository.model == User
        assert hasattr(repository, 'get')
        assert hasattr(repository, 'create')
        assert hasattr(repository, 'update')
        assert hasattr(repository, 'delete')
        assert hasattr(repository, 'authenticate')

    async def test_create_user_with_invalid_fields(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Создание пользователя с несуществующими полями."""
        repository = UserRepository()
        user_data = {
            'username': 'testuser',
            'password': 'Password123!',
            'nonexistent_field': 'value',
        }

        user = await repository.create(test_db, user_data)

        assert user is not None
        assert not hasattr(user, 'nonexistent_field')

    async def test_update_user_with_invalid_fields(
        self,
        test_db: AsyncSession,
        create_test_user: Callable,
    ) -> None:
        """Обновление пользователя с несуществующими полями."""
        repository = UserRepository()
        user = await create_test_user(username='testuser')

        update_data = {
            'username': 'updated',
            'nonexistent_field': 'value',
        }

        updated_user = await repository.update(test_db, user, update_data)

        assert updated_user.username == 'updated'
        assert not hasattr(updated_user, 'nonexistent_field')
