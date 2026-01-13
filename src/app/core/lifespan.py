"""События жизненного цикла приложения."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import async_session_maker
from app.core.redis_cache import RedisCache
from app.repositories.users import UserRepository


async def ensure_superadmin() -> None:
    """Создать администратора при пустой базе пользователей."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        existing_users = await user_repo.get_multi(limit=1, active_only=False)
        if existing_users:
            return
        await user_repo.create_user({
            'username': settings.superadmin_username,
            'password': settings.superadmin_password,
            'is_superuser': True,
            'is_blocked': False,
            'active': True,
        })


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом приложения."""
    redis_connection = await redis.from_url(
        settings.redis_url, encoding='utf-8', decode_responses=False
    )
    RedisCache.init(redis_connection)
    await ensure_superadmin()
    yield
    await redis_connection.close()
