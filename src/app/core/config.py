"""Application configuration using Pydantic Settings v2.

Читает переменные из .env файла и окружения.
"""

from pydantic import Field
from pydantic_settings import BaseSettings

from .constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    MAX_UPLOAD_SIZE_BYTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


class Settings(BaseSettings):
    """Основные настройки приложения."""

    # ========== App Settings ==========
    APP_TITLE: str = 'Booking Seats API'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default='development', description='dev или prod')

    # ========== Server ==========
    HOST: str = '0.0.0.0'
    PORT: int = 8000

    # ========== Database ==========
    DATABASE_URL: str = Field(
        default='postgresql+asyncpg://user:password@localhost:5433/booking_db',
        description='Async PostgreSQL URL (нестандартный порт 5433)',
    )
    DB_ECHO: bool = False  # SQL logs в консоль

    # ========== JWT & Auth ==========
    JWT_SECRET_KEY: str = Field(
        default='your-secret-key-change-in-production',
        description='Секретный ключ для JWT',
    )
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS: int = REFRESH_TOKEN_EXPIRE_DAYS

    # ========== Redis ==========
    REDIS_URL: str = Field(
        default='redis://localhost:6379/0',
        description='Redis connection URL',
    )

    # ========== RabbitMQ / Celery ==========
    RABBITMQ_URL: str = Field(
        default='amqp://guest:guest@localhost:5672/',
        description='RabbitMQ broker URL',
    )
    CELERY_BROKER_URL: str = Field(
        default='',
        description='Celery broker (по умолчанию RABBITMQ_URL)',
    )
    CELERY_RESULT_BACKEND: str = Field(
        default='',
        description='Celery result backend (по умолчанию REDIS_URL)',
    )

    # ========== Files / Media ==========
    MAX_UPLOAD_SIZE: int = MAX_UPLOAD_SIZE_BYTES  # 5MB in bytes
    ALLOWED_IMAGE_TYPES: str = 'image/jpeg,image/png'
    MEDIA_PATH: str = '/app/media'

    # ========== Logging ==========
    LOG_LEVEL: str = 'INFO'
    LOG_FILE: str = 'logs/app.log'
    LOG_ROTATION: str = '10 MB'
    LOG_RETENTION: str = '7 days'

    # ========== CORS ==========
    FRONTEND_URL: str = Field(
        default='http://localhost:3000',
        description='URL фронтенда',
    )
    ALLOWED_ORIGINS: list = Field(
        default=['http://localhost:3000', 'http://localhost:8000'],
    )

    # ========== Email (опционально) ==========
    SMTP_SERVER: str = Field(default='', description='SMTP сервер')
    SMTP_PORT: int = 587
    SMTP_USER: str = Field(default='', description='SMTP пользователь')
    SMTP_PASSWORD: str = Field(default='', description='SMTP пароль')

    # ========== Telegram bot ID ==========
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_API_URL: str = 'https://api.telegram.org'

    class Config:
        """Pydantic конфигурация."""

        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

    @property
    def celery_broker(self) -> str:
        """Вернуть URL брокера для Celery."""
        return self.CELERY_BROKER_URL or self.RABBITMQ_URL

    @property
    def celery_backend(self) -> str:
        """Вернуть URL бэкенда для Celery."""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL


# Глобальный объект настроек
settings = Settings()

# Экспорт для импорта в других модулях
__all__ = ['Settings', 'settings']
