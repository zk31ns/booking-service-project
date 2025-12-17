"""Pytest configuration and fixtures for tests."""

import asyncio
from datetime import timedelta
from typing import Any, AsyncGenerator, Callable, Coroutine, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.core.constants import Times
from src.app.core.security import create_access_token
from src.app.db.base import Base
from src.app.models.models import User
from src.main import app


@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for a test."""
    # Create test database engine (in-memory SQLite for testing)
    test_engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,
        future=True,
    )

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
def client() -> TestClient:
    """Get TestClient for FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Создает асинхронного клиента для тестов."""
    async with AsyncClient(app=app, base_url='http://test') as client:
        yield client


@pytest.fixture
def create_test_user(
    test_db: AsyncSession,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """Создает тестового пользователя в базе данных."""
    from src.app.api.v1.users.repository import UserRepository

    async def _create_user(
        username: str = 'testuser',
        email: str = 'test@example.com',
        password: str = 'Password123!',
        is_superuser: bool = False,
        phone: str | None = '+79161234567',
        tg_id: str | None = None,
        is_blocked: bool = False,
        active: bool = True,
    ) -> User:
        repository = UserRepository()

        user_data = {
            'username': username,
            'email': email,
            'password': password,
            'phone': phone,
            'tg_id': tg_id,
            'is_superuser': is_superuser,
            'is_blocked': is_blocked,
            'active': active,
        }

        user = await repository.create(test_db, user_data)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    return _create_user


@pytest.fixture
def auth_headers() -> Callable[..., Dict[str, str]]:
    """Создает заголовки авторизации для тестового пользователя."""

    def _auth_headers(
        user_id: int = 1,
        username: str = 'testuser',
        expires_delta: timedelta | None = None,
    ) -> Dict[str, str]:
        token_data = {
            'sub': username,
            'user_id': user_id,
        }

        token = create_access_token(
            data=token_data,
            expires_delta=(
                expires_delta or timedelta(minutes=Times.ACCESS_TOKEN_MINUTES)
            ),
        )
        return {'Authorization': f'Bearer {token}'}

    return _auth_headers


@pytest.fixture
def admin_auth_headers() -> Callable[..., Dict[str, str]]:
    """Создает заголовки авторизации для администратора."""

    def _admin_auth_headers() -> Dict[str, str]:
        token_data = {
            'sub': 'admin',
            'user_id': 1,
        }

        token = create_access_token(data=token_data)
        return {'Authorization': f'Bearer {token}'}

    return _admin_auth_headers


@pytest.fixture
def expired_auth_headers() -> Callable[..., Dict[str, str]]:
    """Создает заголовки с просроченным токеном."""

    def _expired_auth_headers() -> Dict[str, str]:
        token_data = {
            'sub': 'testuser',
            'user_id': 1,
        }

        token = create_access_token(
            data=token_data, expires_delta=timedelta(minutes=-5)
        )
        return {'Authorization': f'Bearer {token}'}

    return _expired_auth_headers
