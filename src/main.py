"""FastAPI приложение для бронирования мест в кафе.

Main entry point приложения.
"""

import os
import sys

# Добавить текущую директорию в sys.path для правильной работы импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health
from app.api.v1.actions import router as actions_router
from app.api.v1.booking import router as booking_router
from app.api.v1.cafes import router as cafes_router
from app.api.v1.dishes import router as dishes_router
from app.api.v1.media import router as media_router
from app.api.v1.slots import router as slots_router
from app.api.v1.tables import router as tables_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.constants import API
from app.core.lifespan import lifespan
from app.core.logging import setup_logging

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


# ========== Root Route ==========
@app.get('/', tags=['root'])
async def read_root() -> dict[str, str]:
    """Корневой endpoint приложения.

    Возвращает приветствие и информацию о приложении.
    """
    return {
        'message': 'Добро пожаловать в API бронирования мест в кафе!',
        'version': settings.app_version,
        'title': settings.app_title,
        'docs': '/docs',
        'redoc': '/redoc',
    }


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

# Booking
app.include_router(booking_router, prefix=API.V1_PREFIX, tags=API.BOOKING)

# Cafes
app.include_router(cafes_router, prefix=API.V1_PREFIX, tags=API.CAFES)

# Tables
app.include_router(tables_router, prefix=API.V1_PREFIX, tags=API.TABLES)
# ===========================
