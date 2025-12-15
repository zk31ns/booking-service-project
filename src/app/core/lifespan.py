
"""События жизненного цикла приложения."""

from typing import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from app.core.config import settings
from app.core.redis_cache import RedisCache


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом приложения."""
    redis_connection = await redis.from_url(settings.REDIS_URL,
                                            encoding='utf-8',
                                            decode_responses=False)
    RedisCache.init(redis_connection)
    yield
    await redis_connection.close()
