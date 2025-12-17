"""Тесты API эндпоинтов пользователей."""

from typing import Callable, Dict

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.constants import ErrorCode
from src.app.models.models import User


@pytest.mark.asyncio
class TestUsersAPI:
    """Тесты для эндпоинтов пользователей."""

    async def test_register_user_success(
        self,
        async_client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        """Тест успешной регистрации пользователя."""
        user_data = {
            'username': 'testuser',
            'password': 'Password123!',
            'email': 'test@example.com',
            'phone': '+79161234567',
        }

        response = await async_client.post('/api/v1/users', json=user_data)

        assert response.status_code == status.HTTP_201_CREATED

        user_response_data = response.json()
        assert user_response_data['username'] == user_data['username']
        assert user_response_data['email'] == user_data['email']
        assert user_response_data['phone'] == user_data['phone']
        assert 'id' in user_response_data
        assert 'password' not in user_response_data

    async def test_register_user_missing_contact(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Тест регистрации без email и телефона."""
        user_data = {'username': 'testuser', 'password': 'Password123!'}

        response = await async_client.post('/api/v1/users', json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'хотя бы email или телефон' in response.text

    async def test_register_user_duplicate_username(
        self,
        async_client: AsyncClient,
        create_test_user: Callable[..., User],
    ) -> None:
        """Тест регистрации с уже существующим username."""
        existing_user = create_test_user()

        duplicate_user_data = {
            'username': existing_user.username,
            'password': 'Password123!',
            'email': 'new@example.com',
        }

        response = await async_client.post(
            '/api/v1/users', json=duplicate_user_data
        )

        assert response.status_code == status.HTTP_409_CONFLICT

        error_response_data = response.json()
        assert error_response_data['code'] == (
            ErrorCode.USER_ALREADY_EXISTS.value
        )

    async def test_login_success(
        self,
        async_client: AsyncClient,
        create_test_user: Callable[..., User],
    ) -> None:
        """Тест успешного входа."""
        test_user = create_test_user(password='Password123!')

        login_credentials = {
            'username': test_user.username,
            'password': 'Password123!',
        }

        response = await async_client.post(
            '/api/v1/auth/login', data=login_credentials
        )

        assert response.status_code == status.HTTP_200_OK

        auth_response_data = response.json()
        assert 'access_token' in auth_response_data
        assert 'refresh_token' in auth_response_data
        assert auth_response_data['token_type'] == 'bearer'
        assert 'user' in auth_response_data

    async def test_login_invalid_credentials(
        self,
        async_client: AsyncClient,
        create_test_user: Callable[..., User],
    ) -> None:
        """Тест входа с неверными данными."""
        test_user = create_test_user()

        wrong_credentials = {
            'username': test_user.username,
            'password': 'wrongpassword',
        }

        response = await async_client.post(
            '/api/v1/auth/login', data=wrong_credentials
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        error_response_data = response.json()
        assert error_response_data['code'] == (
            ErrorCode.INVALID_CREDENTIALS.value
        )

    async def test_get_current_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест получения текущего пользователя."""
        headers = auth_headers()

        response = await async_client.get('/api/v1/users/me', headers=headers)

        assert response.status_code == status.HTTP_200_OK

        user_response_data = response.json()
        assert 'id' in user_response_data
        assert 'username' in user_response_data
        assert 'email' in user_response_data

    async def test_get_current_user_unauthorized(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Тест получения текущего пользователя без авторизации."""
        response = await async_client.get('/api/v1/users/me')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_update_current_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест обновления текущего пользователя."""
        headers = auth_headers()
        update_data = {'username': 'newusername'}

        response = await async_client.patch(
            '/api/v1/users/me', json=update_data, headers=headers
        )

        assert response.status_code == status.HTTP_200_OK

        updated_user_data = response.json()
        assert updated_user_data['username'] == 'newusername'

    async def test_change_password_success(
        self,
        async_client: AsyncClient,
        auth_headers: Callable[..., Dict[str, str]],
        create_test_user: Callable[..., User],
    ) -> None:
        """Тест успешной смены пароля."""
        test_user = create_test_user(password='OldPassword123!')
        headers = auth_headers(
            user_id=test_user.id, username=test_user.username
        )

        password_change_data = {
            'current_password': 'OldPassword123!',
            'new_password': 'NewPassword456!',
        }

        response = await async_client.post(
            '/api/v1/users/me/password',
            json=password_change_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_change_password_wrong_current(
        self,
        async_client: AsyncClient,
        auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест смены пароля с неверным текущим паролем."""
        headers = auth_headers()

        password_change_data = {
            'current_password': 'wrongpassword',
            'new_password': 'NewPassword456!',
        }

        response = await async_client.post(
            '/api/v1/users/me/password',
            json=password_change_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        error_response_data = response.json()
        assert error_response_data['code'] == (
            ErrorCode.INVALID_CREDENTIALS.value
        )

    async def test_delete_current_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест успешного удаления своего аккаунта."""
        headers = auth_headers()

        response = await async_client.delete(
            '/api/v1/users/me',
            headers=headers,
            params={'confirm': True},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_current_user_without_confirm(
        self,
        async_client: AsyncClient,
        auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест удаления аккаунта без подтверждения."""
        headers = auth_headers()

        response = await async_client.delete(
            '/api/v1/users/me',
            headers=headers,
            params={'confirm': False},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        error_response_data = response.json()
        assert error_response_data['code'] == (
            ErrorCode.CONFIRMATION_REQUIRED.value
        )

    async def test_get_user_by_id_as_admin(
        self,
        async_client: AsyncClient,
        admin_auth_headers: Callable[..., Dict[str, str]],
        create_test_user: Callable[..., User],
    ) -> None:
        """Тест получения пользователя по ID администратором."""
        test_user = create_test_user()
        headers = admin_auth_headers()

        response = await async_client.get(
            f'/api/v1/users/{test_user.id}', headers=headers
        )

        assert response.status_code == status.HTTP_200_OK

        user_response_data = response.json()
        assert user_response_data['id'] == test_user.id

    async def test_get_user_by_id_not_found(
        self,
        async_client: AsyncClient,
        admin_auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест получения несуществующего пользователя."""
        headers = admin_auth_headers()

        response = await async_client.get(
            '/api/v1/users/999999', headers=headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        error_response_data = response.json()
        assert error_response_data['code'] == ErrorCode.USER_NOT_FOUND.value

    async def test_search_users_as_admin(
        self,
        async_client: AsyncClient,
        admin_auth_headers: Callable[..., Dict[str, str]],
        create_test_user: Callable[..., User],
    ) -> None:
        """Тест поиска пользователей администратором."""
        create_test_user(username='searchtest')
        headers = admin_auth_headers()

        response = await async_client.get(
            '/api/v1/users/search', params={'query': 'search'}, headers=headers
        )

        assert response.status_code == status.HTTP_200_OK

        search_results = response.json()
        assert len(search_results) >= 1

        assert any(
            found_user['username'] == 'searchtest'
            for found_user in search_results
        )

    async def test_search_users_min_length(
        self,
        async_client: AsyncClient,
        admin_auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест поиска с слишком коротким запросом."""
        headers = admin_auth_headers()

        short_query = 'a'
        response = await async_client.get(
            '/api/v1/users/search',
            params={'query': short_query},
            headers=headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_users_list_as_admin(
        self,
        async_client: AsyncClient,
        admin_auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест получения списка пользователей администратором."""
        headers = admin_auth_headers()

        response = await async_client.get('/api/v1/users', headers=headers)

        assert response.status_code == status.HTTP_200_OK

        users_list_response = response.json()
        assert isinstance(users_list_response, list)

    async def test_get_users_list_pagination(
        self,
        async_client: AsyncClient,
        admin_auth_headers: Callable[..., Dict[str, str]],
    ) -> None:
        """Тест пагинации списка пользователей."""
        headers = admin_auth_headers()

        response = await async_client.get(
            '/api/v1/users', params={'skip': 0, 'limit': 2}, headers=headers
        )

        assert response.status_code == status.HTTP_200_OK

        paginated_users = response.json()
        assert len(paginated_users) <= 2
