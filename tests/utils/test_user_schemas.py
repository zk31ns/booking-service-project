"""Тесты для Pydantic схем пользователей.

Тестирует валидацию, преобразование данных и бизнес-правила
в схемах UserCreate, UserUpdate и других.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.app.api.v1.users.schemas import (
    UserBase,
    UserCreate,
    UserInfo,
    UserUpdate,
)
from src.app.core.constants import Limits
from src.app.models.models import User


class TestUserBaseSchema:
    """Тесты для базовой схемы UserBase."""

    def test_user_base_valid_data(self) -> None:
        """Валидация корректных данных для UserBase."""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '+79161234567',
            'tg_id': '123456789',
        }

        user_base = UserBase(**data)

        assert user_base.username == 'testuser'
        assert user_base.email == 'test@example.com'
        assert user_base.phone == '+79161234567'
        assert user_base.tg_id == '123456789'

    def test_user_base_minimal_data(self) -> None:
        """Валидация минимальных данных (только username)."""
        data = {
            'username': 'minimal',
            'email': None,
            'phone': None,
            'tg_id': None,
        }

        user_base = UserBase.model_validate(data)

        assert user_base.username == 'minimal'
        assert user_base.email is None
        assert user_base.phone is None
        assert user_base.tg_id is None

    def test_user_base_username_length_validation(self) -> None:
        """Проверка валидации длины username."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username='ab', email=None, phone=None, tg_id=None)
        assert 'username' in str(exc_info.value)

        long_username = 'a' * (Limits.MAX_USERNAME_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            UserBase(
                username=long_username, email=None, phone=None, tg_id=None
            )
        assert 'username' in str(exc_info.value)


class TestUserCreateSchema:
    """Тесты для схемы UserCreate."""

    def test_user_create_valid_data(self) -> None:
        """Валидация корректных данных для UserCreate."""
        data = {
            'username': 'newuser',
            'password': 'Password123!',
            'email': 'new@example.com',
            'phone': '+79161234567',
            'tg_id': None,
        }

        user_create = UserCreate.model_validate(data)

        assert user_create.username == 'newuser'
        assert user_create.password == 'Password123!'
        assert user_create.email == 'new@example.com'
        assert user_create.phone == '+79161234567'
        assert user_create.tg_id is None

    def test_user_create_password_validation(self) -> None:
        """Проверка валидации пароля."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username='testuser',
                password='short',
                email=None,
                phone=None,
                tg_id=None,
            )
        assert 'password' in str(exc_info.value)


class TestUserInfoSchema:
    """Тесты для схемы UserInfo."""

    def test_user_info_from_orm(self) -> None:
        """Проверка преобразования ORM модели в UserInfo."""
        user_create = UserCreate(
            username='newuser',
            password='Password123!',
            email='new@example.com',
            phone='+79161234567',
            tg_id=None,
        )

        user_model = User(
            id=1,
            username=user_create.username,
            email=user_create.email,
            phone=user_create.phone,
            password_hash='hashed_password',
            is_superuser=False,
            is_blocked=False,
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        user_info = UserInfo.from_orm(user_model)

        assert user_info.username == 'newuser'
        assert user_info.email == 'new@example.com'
        assert user_info.phone == '+79161234567'
        assert user_info.active is True


class TestUserUpdateSchema:
    """Тесты для схемы UserUpdate."""

    def test_user_update_merge(self) -> None:
        """Проверка слияния данных при обновлении."""
        original_data = {
            'username': 'original',
            'email': 'original@example.com',
            'phone': '+79160000000',
            'is_blocked': False,
        }

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

        merged_data = original_data.copy()
        update_dict = update_data.model_dump(exclude_unset=True)
        merged_data.update(update_dict)

        assert merged_data['username'] == 'updated'
        assert merged_data['email'] == 'updated@example.com'
        assert merged_data['phone'] == '+79160000000'
        assert merged_data['is_blocked'] is False
