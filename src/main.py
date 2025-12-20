"""FastAPI приложение для бронирования мест в кафе.

Main entry point приложения.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.v1 import health
from src.app.api.v1.slots.router import router as slots_router
from src.app.core.config import settings
from src.app.core.constants import API_V1_PREFIX, TAGS_HEALTH, TAGS_SLOTS
from src.app.core.lifespan import lifespan
from src.app.core.logging import setup_logging

# Инициализировать логирование
setup_logging()

# Создать приложение
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

app.include_router(slots_router, prefix=API_V1_PREFIX, tags=TAGS_SLOTS)

# TODO: Booking router (Анастасия)
# app.include_router(booking_router, prefix=API_V1_PREFIX, tags=TAGS_BOOKING)

# TODO: Media router (Данил, Лев)
# app.include_router(media_router, prefix=API_V1_PREFIX, tags=TAGS_MEDIA)
# ============================
