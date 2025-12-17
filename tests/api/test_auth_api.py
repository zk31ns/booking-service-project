from typing import Callable

import pytest
from fastapi import status
from httpx import AsyncClient

from src.app.core.constants import ErrorCode
from src.app.models.models import User


@pytest.mark.asyncio
class TestAuthAPI:
    """Тесты для эндпоинтов аутентификации."""

    async def test_refresh_token_success(
        self,
        async_client: AsyncClient,
        create_test_user: Callable[..., User],
    ) -> None:
        """Тест успешного обновления токена."""
        test_user = create_test_user(password='Password123!')

        login_response = await async_client.post(
            '/api/v1/auth/login',
            data={'username': test_user.username, 'password': 'Password123!'},
        )
        login_response_data = login_response.json()
        refresh_token = login_response_data['refresh_token']

        refresh_response = await async_client.post(
            '/api/v1/auth/refresh', json={'refresh_token': refresh_token}
        )

        assert refresh_response.status_code == status.HTTP_200_OK

        new_tokens_data = refresh_response.json()
        assert 'access_token' in new_tokens_data
        assert 'refresh_token' in new_tokens_data

    async def test_refresh_token_invalid(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Тест обновления с невалидным токеном."""
        response = await async_client.post(
            '/api/v1/auth/refresh',
            json={'refresh_token': 'invalid.token.here'},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        error_response_data = response.json()
        assert error_response_data['code'] == (
            ErrorCode.INVALID_REFRESH_TOKEN.value
        )
