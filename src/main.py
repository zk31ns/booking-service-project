"""FastAPI приложение для бронирования мест в кафе.

Main entry point приложения.
"""

import os
import sys

# Добавить текущую директорию в sys.path для правильной работы импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import root
from app.api.v1.actions import router as actions_router
from app.api.v1.booking import router as booking_router
from app.api.v1.cafes import router as cafes_router
from app.api.v1.dishes import router as dishes_router
from app.api.v1.media import router as media_router
from app.api.v1.slots import router as slots_router
from app.api.v1.tables import router as tables_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.constants import API, OPENAPI_TAGS
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
    openapi_tags=OPENAPI_TAGS,
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
# Greeting message
app.include_router(root.router, prefix=API.V1_PREFIX)

# Users and Authentication
app.include_router(users_router, prefix=API.V1_PREFIX)

# Cafes
app.include_router(cafes_router, prefix=API.V1_PREFIX)

# Tables
app.include_router(tables_router, prefix=API.V1_PREFIX)

# Time slots
app.include_router(slots_router, prefix=API.V1_PREFIX)

# Dishes
app.include_router(dishes_router, prefix=API.V1_PREFIX)

# Actions
app.include_router(actions_router, prefix=API.V1_PREFIX)

# Booking
app.include_router(booking_router, prefix=API.V1_PREFIX)

# Media
app.include_router(media_router, prefix=API.V1_PREFIX)
# ===========================
