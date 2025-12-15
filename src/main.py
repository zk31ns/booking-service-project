"""FastAPI приложение для бронирования мест в кафе.

Main entry point приложения.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.v1 import health
from src.app.core.config import settings
from src.app.core.constants import API_V1_PREFIX, TAGS_HEALTH
from src.app.core.logging import logger, setup_logging

# Инициализировать логирование
setup_logging()

# Lifespan-менеджер для старта и завершения приложения


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan-менеджер для старта и завершения приложения FastAPI."""
    # Startup
    startup_msg = (
        f'Application startup | Title: {settings.APP_TITLE} '
        f'v{settings.APP_VERSION}'
    )
    logger.info(startup_msg)
    logger.info(
        f'Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}',
    )
    db_url = (
        settings.DATABASE_URL.split('@')[1]
        if '@' in settings.DATABASE_URL
        else 'configured'
    )
    logger.info(f'Database: {db_url}')
    logger.info(f'Frontend URL: {settings.FRONTEND_URL}')
    yield
    # Shutdown
    logger.info('Application shutdown')


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description='API для бронирования мест в кафе',
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
    lifespan=lifespan,
)

# Добавить CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ========== Routers ==========
# Health check
app.include_router(health.router, prefix=API_V1_PREFIX, tags=TAGS_HEALTH)


# TODO: Users/Auth router (Александр)
# app.include_router(users_router, prefix=API_V1_PREFIX, tags=TAGS_USERS)

# TODO: Cafes router (Павел)
# app.include_router(cafes_router, prefix=API_V1_PREFIX, tags=TAGS_CAFES)

# TODO: Tables router (Павел)
# app.include_router(tables_router, prefix=API_V1_PREFIX, tags=TAGS_TABLES)

# TODO: Slots router (Лев)
# app.include_router(slots_router, prefix=API_V1_PREFIX, tags=TAGS_SLOTS)

# TODO: Booking router (Анастасия)
# app.include_router(booking_router, prefix=API_V1_PREFIX, tags=TAGS_BOOKING)

# TODO: Media router (Данил, Лев)
# app.include_router(media_router, prefix=API_V1_PREFIX, tags=TAGS_MEDIA)
# ============================
