"""Тесты для модуля безопасности: JWT, хеширование паролей, валидация токенов.

Тестирует функции из src/app/core/security.py
"""

from datetime import timedelta
from typing import Any, Dict

import pytest

from src.app.core.security import (
    TokenData,
    create_access_token,
    create_refresh_token,
    create_tokens_pair,
    decode_access_token,
    decode_refresh_token,
    get_current_user_id_from_token,
    get_current_username_from_token,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)


@pytest.mark.unit
class TestPasswordHashing:
    """Тесты для хеширования паролей."""

    def test_verify_password_success(self) -> None:
        """Успешная проверка пароля."""
        password = 'SecurePassword123!'
        hashed_password = get_password_hash(password)

        result = verify_password(password, hashed_password)

        assert result is True

    def test_verify_password_wrong_password(self) -> None:
        """Проверка с неверным паролем."""
        password = 'SecurePassword123!'
        wrong_password = 'WrongPassword456!'
        hashed_password = get_password_hash(password)

        result = verify_password(wrong_password, hashed_password)

        assert result is False

    def test_verify_password_empty_password(self) -> None:
        """Проверка с пустым паролем."""
        hashed_password = get_password_hash('password')

        result = verify_password('', hashed_password)

        assert result is False

    def test_get_password_hash_success(self) -> None:
        """Успешное создание хеша пароля."""
        password = 'TestPassword123!'

        hashed_password = get_password_hash(password)

        assert hashed_password is not None
        assert isinstance(hashed_password, str)
        assert len(hashed_password) > 0
        assert hashed_password != password

    def test_get_password_hash_different_for_same_password(self) -> None:
        """Проверка что хеши разные для одного пароля (из-за соли)."""
        password = 'TestPassword123!'

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.unit
class TestTokenCreation:
    """Тесты для создания токенов."""

    def test_create_access_token_success(self) -> None:
        """Успешное создание access токена."""
        data: Dict[str, Any] = {
            'sub': 'testuser',
            'user_id': 1,
            'custom_field': 'value',
        }

        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3

    def test_create_access_token_with_expires_delta(self) -> None:
        """Создание access токена с кастомным временем жизни."""
        data = {'sub': 'testuser', 'user_id': 1}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta)

        assert token is not None

    def test_create_refresh_token_success(self) -> None:
        """Успешное создание refresh токена."""
        data = {'sub': 'testuser', 'user_id': 1}

        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3

    def test_create_refresh_token_with_expires_delta(self) -> None:
        """Создание refresh токена с кастомным временем жизни."""
        data = {'sub': 'testuser', 'user_id': 1}
        expires_delta = timedelta(days=14)

        token = create_refresh_token(data, expires_delta)

        assert token is not None

    def test_create_tokens_pair_success(self) -> None:
        """Успешное создание пары токенов."""
        user_id = 1
        username = 'testuser'

        tokens = create_tokens_pair(user_id, username)

        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert 'token_type' in tokens
        assert tokens['token_type'] == 'bearer'
        assert isinstance(tokens['access_token'], str)
        assert isinstance(tokens['refresh_token'], str)
        assert tokens['access_token'] != tokens['refresh_token']


@pytest.mark.unit
class TestTokenDecoding:
    """Тесты для декодирования токенов."""

    def test_decode_access_token_success(self) -> None:
        """Успешное декодирование access токена."""
        data = {'sub': 'testuser', 'user_id': 1, 'extra': 'value'}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded['sub'] == 'testuser'
        assert decoded['user_id'] == 1
        assert decoded['extra'] == 'value'
        assert decoded['type'] == 'access'
        assert 'exp' in decoded

    def test_decode_access_token_invalid_token(self) -> None:
        """Декодирование невалидного токена."""
        invalid_token = 'invalid.token.here'

        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_decode_access_token_wrong_type(self) -> None:
        """Декодирование refresh токена как access."""
        data = {'sub': 'testuser', 'user_id': 1}
        refresh_token = create_refresh_token(data)

        decoded = decode_access_token(refresh_token)

        assert decoded is None

    def test_decode_access_token_expired(self) -> None:
        """Декодирование просроченного access токена."""
        data = {'sub': 'testuser', 'user_id': 1}
        expires_delta = timedelta(minutes=-5)
        expired_token = create_access_token(data, expires_delta)

        decoded = decode_access_token(expired_token)

        assert decoded is None

    def test_decode_refresh_token_success(self) -> None:
        """Успешное декодирование refresh токена."""
        data = {'sub': 'testuser', 'user_id': 1, 'extra': 'value'}
        token = create_refresh_token(data)

        decoded = decode_refresh_token(token)

        assert decoded is not None
        assert decoded['sub'] == 'testuser'
        assert decoded['user_id'] == 1
        assert decoded['extra'] == 'value'
        assert decoded['type'] == 'refresh'
        assert 'exp' in decoded

    def test_decode_refresh_token_invalid_token(self) -> None:
        """Декодирование невалидного refresh токена."""
        invalid_token = 'invalid.token.here'

        decoded = decode_refresh_token(invalid_token)

        assert decoded is None

    def test_decode_refresh_token_wrong_type(self) -> None:
        """Декодирование access токена как refresh."""
        data = {'sub': 'testuser', 'user_id': 1}
        access_token = create_access_token(data)

        decoded = decode_refresh_token(access_token)

        assert decoded is None

    def test_decode_refresh_token_expired(self) -> None:
        """Декодирование просроченного refresh токена."""
        data = {'sub': 'testuser', 'user_id': 1}
        expires_delta = timedelta(days=-1)
        expired_token = create_refresh_token(data, expires_delta)

        decoded = decode_refresh_token(expired_token)

        assert decoded is None


@pytest.mark.unit
class TestTokenDataExtraction:
    """Тесты для извлечения данных из токенов."""

    def test_get_current_user_id_from_token_success(self) -> None:
        """Успешное получение user_id из токена."""
        data = {'sub': 'testuser', 'user_id': 42}
        token = create_access_token(data)

        user_id = get_current_user_id_from_token(token)

        assert user_id == 42

    def test_get_current_user_id_from_token_no_user_id(self) -> None:
        """Получение user_id из токена без user_id."""
        data = {'sub': 'testuser'}
        token = create_access_token(data)

        user_id = get_current_user_id_from_token(token)

        assert user_id is None

    def test_get_current_user_id_from_token_invalid(self) -> None:
        """Получение user_id из невалидного токена."""
        user_id = get_current_user_id_from_token('invalid.token')

        assert user_id is None

    def test_get_current_username_from_token_success(self) -> None:
        """Успешное получение username из токена."""
        data = {'sub': 'testuser', 'user_id': 1}
        token = create_access_token(data)

        username = get_current_username_from_token(token)

        assert username == 'testuser'

    def test_get_current_username_from_token_no_sub(self) -> None:
        """Получение username из токена без sub."""
        data = {'user_id': 1}
        token = create_access_token(data)

        username = get_current_username_from_token(token)

        assert username is None

    def test_get_current_username_from_token_invalid(self) -> None:
        """Получение username из невалидного токена."""
        username = get_current_username_from_token('invalid.token')

        assert username is None


@pytest.mark.unit
class TestVerifyRefreshToken:
    """Тесты для проверки refresh токенов."""

    def test_verify_refresh_token_success(self) -> None:
        """Успешная проверка refresh токена."""
        data = {'sub': 'testuser', 'user_id': 1}
        refresh_token = create_refresh_token(data)

        token_data = verify_refresh_token(refresh_token)

        assert token_data is not None
        assert isinstance(token_data, TokenData)
        assert token_data.username == 'testuser'
        assert token_data.user_id == 1

    def test_verify_refresh_token_invalid_token(self) -> None:
        """Проверка невалидного refresh токена."""
        invalid_token = 'invalid.token.here'

        token_data = verify_refresh_token(invalid_token)

        assert token_data is None

    def test_verify_refresh_token_access_token(self) -> None:
        """Проверка access токена как refresh."""
        data = {'sub': 'testuser', 'user_id': 1}
        access_token = create_access_token(data)

        token_data = verify_refresh_token(access_token)

        assert token_data is None

    def test_verify_refresh_token_missing_fields(self) -> None:
        """Проверка refresh токена без обязательных полей."""
        data = {'user_id': 1}
        token = create_refresh_token(data)

        token_data = verify_refresh_token(token)

        assert token_data is None

    def test_verify_refresh_token_expired(self) -> None:
        """Проверка просроченного refresh токена."""
        data = {'sub': 'testuser', 'user_id': 1}
        expires_delta = timedelta(days=-1)
        expired_token = create_refresh_token(data, expires_delta)

        token_data = verify_refresh_token(expired_token)

        assert token_data is None


@pytest.mark.unit
class TestTokenDataModel:
    """Тесты для модели TokenData."""

    def test_token_data_creation(self) -> None:
        """Создание модели TokenData."""
        token_data = TokenData(username='testuser', user_id=1)

        assert token_data.username == 'testuser'
        assert token_data.user_id == 1

    def test_token_data_optional_fields(self) -> None:
        """Создание TokenData с опциональными полями."""
        token_data = TokenData()

        assert token_data.username is None
        assert token_data.user_id is None

    def test_token_data_partial_fields(self) -> None:
        """Создание TokenData с частичными полями."""
        token_data = TokenData(username='testuser')

        assert token_data.username == 'testuser'
        assert token_data.user_id is None


@pytest.mark.unit
class TestTokenEdgeCases:
    """Тесты edge cases для токенов."""

    def test_create_token_empty_data(self) -> None:
        """Создание токена с пустыми данными."""
        data: dict[str, Any] = {}

        token = create_access_token(data)

        assert token is not None
        decoded = decode_access_token(token)
        assert decoded is not None
        assert 'exp' in decoded
        assert decoded['type'] == 'access'

    def test_create_token_large_data(self) -> None:
        """Создание токена с большими данными."""
        large_data = {
            'sub': 'testuser',
            'user_id': 1,
            'roles': ['admin', 'user', 'manager'],
            'permissions': ['read', 'write', 'delete'],
            'metadata': {'created_at': '2024-01-01', 'active': True},
        }

        token = create_access_token(large_data)

        assert token is not None
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded['roles'] == ['admin', 'user', 'manager']
        assert decoded['permissions'] == ['read', 'write', 'delete']
        assert decoded['metadata'] == ({
            'created_at': '2024-01-01',
            'active': True,
        })

    def test_token_with_special_characters(self) -> None:
        """Создание токена с специальными символами в username."""
        data = {'sub': 'test.user@email.com', 'user_id': 1}

        token = create_access_token(data)

        assert token is not None
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded['sub'] == 'test.user@email.com'

    def test_token_verification_after_decode(self) -> None:
        """Проверка валидности токена после декодирования."""
        original_data = {'sub': 'testuser', 'user_id': 1, 'custom': 'data'}
        token = create_access_token(original_data)

        decoded = decode_access_token(token)
        assert decoded is not None

        for key, value in original_data.items():
            assert decoded[key] == value


@pytest.mark.unit
class TestIntegrationSecurity:
    """Интеграционные тесты для модуля безопасности."""

    def test_full_token_flow(self) -> None:
        """Полный цикл: создание, декодирование, проверка токена."""
        user_id = 123
        username = 'integration_user'

        tokens = create_tokens_pair(user_id, username)

        access_decoded = decode_access_token(tokens['access_token'])
        refresh_decoded = decode_refresh_token(tokens['refresh_token'])

        assert access_decoded is not None
        assert refresh_decoded is not None
        assert access_decoded['sub'] == username
        assert access_decoded['user_id'] == user_id
        assert refresh_decoded['sub'] == username
        assert refresh_decoded['user_id'] == user_id

        extracted_user_id = get_current_user_id_from_token(
            tokens['access_token']
        )
        extracted_username = get_current_username_from_token(
            tokens['access_token']
        )

        assert extracted_user_id == user_id
        assert extracted_username == username

        refresh_data = verify_refresh_token(tokens['refresh_token'])

        assert refresh_data is not None
        assert refresh_data.username == username
        assert refresh_data.user_id == user_id

    def test_password_hash_and_verify_integration(self) -> None:
        """Интеграционный тест хеширования и проверки пароля."""
        password = 'VerySecurePassword@123'

        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password('wrong_password', hashed) is False
        assert verify_password('', hashed) is False

    def test_token_expiration_flow(self) -> None:
        """Тест истечения срока действия токена."""
        data = {'sub': 'testuser', 'user_id': 1}

        expired_token = create_access_token(data, timedelta(seconds=-1))

        decoded = decode_access_token(expired_token)
        assert decoded is None

        user_id = get_current_user_id_from_token(expired_token)
        username = get_current_username_from_token(expired_token)

        assert user_id is None
        assert username is None
