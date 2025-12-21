"""Pytest configuration and fixtures for tests."""

import asyncio
from datetime import time
from typing import AsyncGenerator, Callable, Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app.db.base import Base
from src.main import app


@pytest.fixture(scope='session')
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
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
    async_session = sessionmaker(
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
def mock_slot_factory() -> Callable:
    """Создание макета объекта slot."""

    def _make_slot(
        id_: int = 1,
        cafe_id: int = 1,
        start: time = time(9, 0),
        end: time = time(10, 0),
        active: bool = True,
    ) -> MagicMock:
        """Создание макета объекта slot."""
        slot = MagicMock()
        slot.id = id_
        slot.cafe_id = cafe_id
        slot.start_time = start
        slot.end_time = end
        slot.active = active
        return slot
    return _make_slot

# Optional: Override database dependency for tests
# @pytest.fixture
# async def override_get_session(test_db: AsyncSession):
#     async def get_session_override():
#         yield test_db
#     app.dependency_overrides[get_session] = get_session_override
#     yield
#     app.dependency_overrides.clear()
