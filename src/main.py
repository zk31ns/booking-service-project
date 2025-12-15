"""FastAPI приложение для бронирования мест в кафе.

Main entry point приложения.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.v1 import health
from src.app.api.v1.users import router as users_router
from src.app.core.config import settings
from src.app.core.constants import API_V1_PREFIX, TAGS_HEALTH, TAGS_USERS
from src.app.core.logging import logger, setup_logging

# Инициализировать логирование
setup_logging()

# Lifespan-менеджер для старта и завершения приложения


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan-менеджер для старта и завершения приложения FastAPI."""
    # Startup
    startup_msg = (
        f'Application startup | Title: {settings.app_title} '
        f'v{settings.app_version}'
    )
    logger.info(startup_msg)
    logger.info(
        f'Environment: {settings.environment} | Debug: {settings.debug}',
    )
    db_url = (
        settings.database_url.split('@')[1]
        if '@' in settings.database_url
        else 'configured'
    )
    logger.info(f'Database: {db_url}')
    logger.info(f'Frontend URL: {settings.frontend_url}')
    yield
    # Shutdown
    logger.info('Application shutdown')


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description='API для бронирования мест в кафе',
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
    lifespan=lifespan,
)

# Добавить CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ========== Routers ==========
# Health check
app.include_router(health.router, prefix=API_V1_PREFIX, tags=TAGS_HEALTH)


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
