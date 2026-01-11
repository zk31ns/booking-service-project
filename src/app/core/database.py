"""Единое подключение к базе данных PostgreSQL.

Централизованное управление подключением к БД, connection pool и сессиями.
Все сервисы и репозитории должны использовать только этот модуль.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.constants import ErrorCode
from app.core.logging import logger

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
    """Dependency для FastAPI — получить сессию БД.

    Автоматически выполняет commit при успешном завершении
    или rollback при ошибке.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f'{ErrorCode.INTERNAL_SERVER_ERROR}: {e}')
            # logger.error('{}: {}', type(e).__name__, repr(e), exc_info=True)
            raise


async def close_db_connection() -> None:
    """Закрыть все соединения с БД при завершении приложения."""
    await engine.dispose()
    logger.info('Database connections closed')
