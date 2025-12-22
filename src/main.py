"""FastAPI приложение для бронирования мест в кафе.

Main entry point приложения.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.v1 import health
from src.app.api.v1.actions import router as actions_router
from src.app.api.v1.dishes import router as dishes_router
from src.app.api.v1.media import router as media_router
from src.app.api.v1.slots import router as slots_router
from src.app.api.v1.users import router as users_router
from src.app.core.config import settings
from src.app.core.constants import API
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
app.include_router(health.router, prefix=API.V1_PREFIX, tags=API.HEALTH)

# Users and Authentication
app.include_router(users_router, prefix=API.V1_PREFIX)

# Slots
app.include_router(slots_router, prefix=API.V1_PREFIX, tags=API.SLOTS)

# Dishes
app.include_router(dishes_router, prefix=API.V1_PREFIX)

# Actions
app.include_router(actions_router, prefix=API.V1_PREFIX)

# Media
app.include_router(media_router, prefix=API.V1_PREFIX, tags=API.MEDIA)


# TODO: Cafes router (Павел)
# app.include_router(cafes_router, prefix=API.V1_PREFIX, tags=API.CAFES)

# TODO: Tables router (Павел)
# app.include_router(tables_router, prefix=API.V1_PREFIX, tags=API.TABLES)

# TODO: Booking router (Анастасия)
# app.include_router(booking_router, prefix=API.V1_PREFIX, tags=API.BOOKING)
# ============================
