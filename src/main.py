"""FastAPI приложение для бронирования мест в кафе.

Main entry point приложения.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.v1 import health
from src.app.core.config import settings
from src.app.core.constants import API_V1_PREFIX, TAGS_HEALTH
from src.app.core.logging import logger, setup_logging

# Инициализировать логирование
setup_logging()

# Создать приложение
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description='API для бронирования мест в кафе',
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
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

# Users/Auth (TODO: Александр)
# app.include_router(users_router, prefix=API_V1_PREFIX, tags=TAGS_USERS)

# Cafes (TODO: Павел)
# app.include_router(cafes_router, prefix=API_V1_PREFIX, tags=TAGS_CAFES)

# Tables (TODO: Павел)
# app.include_router(tables_router, prefix=API_V1_PREFIX, tags=TAGS_TABLES)

# Slots (TODO: Лев)
# app.include_router(slots_router, prefix=API_V1_PREFIX, tags=TAGS_SLOTS)

# Booking (TODO: Анастасия)
# app.include_router(booking_router, prefix=API_V1_PREFIX, tags=TAGS_BOOKING)

# Media (TODO: Данил + Лев)
# app.include_router(media_router, prefix=API_V1_PREFIX, tags=TAGS_MEDIA)


# ========== Lifecycle Events ==========
@app.on_event('startup')
async def startup() -> None:
    """Действия при запуске приложения."""
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


@app.on_event('shutdown')
async def shutdown() -> None:
    """Действия при завершении приложения."""
    logger.info('Application shutdown')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'main:app',
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
