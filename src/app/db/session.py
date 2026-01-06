"""Конфигурация асинхронного подключения к PostgreSQL.

Использует SQLAlchemy 2.0 async.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.constants import ErrorCode
from app.core.logging import logger

from ..core.config import settings

# Создать асинхронный движок
engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    future=True,
    pool_pre_ping=True,  # Проверка соединения перед использованием
)

# Создать фабрику сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator:
    """Dependency для FastAPI — получить сессию БД."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f'{ErrorCode.INTERNAL_SERVER_ERROR}: {e}')
            raise


__all__ = ['engine', 'async_session_maker', 'get_session']
