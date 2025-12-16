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
    app_title: str = 'Booking Seats API'
    app_version: str = '1.0.0'
    debug: bool = False
    environment: str = Field(
        default='development', description='dev или prod', env='ENVIRONMENT'
    )

    # ========== Server ==========
    host: str = Field(..., env='HOST')
    port: int = Field(..., env='PORT')

    # ========== Database ==========
    database_url: str = Field(
        ...,
        env='DATABASE_URL',
        description='Async PostgreSQL URL (пример: postgresql+asyncpg://user:password@host:port/db)',
    )
    db_echo: bool = Field(default=False, env='DB_ECHO')  # SQL logs в консоль

    # ========== JWT & Auth ==========
    jwt_secret_key: str = Field(
        ..., env='JWT_SECRET_KEY', description='Секретный ключ для JWT'
    )
    jwt_algorithm: str = Field(default='HS256', env='JWT_ALGORITHM')
    access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
    refresh_token_expire_days: int = REFRESH_TOKEN_EXPIRE_DAYS

    # ========== Redis ==========
    redis_url: str = Field(
        ..., env='REDIS_URL', description='Redis connection URL'
    )

    # ========== RabbitMQ / Celery ==========
    rabbitmq_url: str = Field(
        ..., env='RABBITMQ_URL', description='RabbitMQ broker URL'
    )
    celery_broker_url: str = Field(
        default='',
        env='CELERY_BROKER_URL',
        description='Celery broker (по умолчанию RABBITMQ_URL)',
    )
    celery_result_backend: str = Field(
        default='',
        env='CELERY_RESULT_BACKEND',
        description='Celery result backend (по умолчанию REDIS_URL)',
    )

    # ========== Files / Media ==========
    max_upload_size: int = MAX_UPLOAD_SIZE_BYTES  # 5MB in bytes
    allowed_image_types: str = Field(
        default='image/jpeg,image/png', env='ALLOWED_IMAGE_TYPES'
    )
    media_path: str = Field(default='/app/media', env='MEDIA_PATH')

    # ========== Logging ==========
    log_level: str = Field(default='INFO', env='LOG_LEVEL')
    log_file: str = Field(default='logs/app.log', env='LOG_FILE')
    log_rotation: str = Field(default='10 MB', env='LOG_ROTATION')
    log_retention: str = Field(default='7 days', env='LOG_RETENTION')

    # ========== CORS ==========
    frontend_url: str = Field(
        ..., env='FRONTEND_URL', description='URL фронтенда'
    )
    allowed_origins: list = Field(
        default=['http://localhost:3000', 'http://localhost:8000'],
        env='ALLOWED_ORIGINS',
    )

    # ========== Email (опционально) ==========
    smtp_server: str = Field(
        default='', env='SMTP_SERVER', description='SMTP сервер'
    )
    smtp_port: int = Field(default=587, env='SMTP_PORT')
    smtp_user: str = Field(
        default='', env='SMTP_USER', description='SMTP пользователь'
    )
    smtp_password: str = Field(
        default='', env='SMTP_PASSWORD', description='SMTP пароль'
    )

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
        return self.celery_broker_url or self.rabbitmq_url

    @property
    def celery_backend(self) -> str:
        """Вернуть URL бэкенда для Celery."""
        return self.celery_result_backend or self.redis_url


# Глобальный объект настроек
settings = Settings()

# Экспорт для импорта в других модулях
__all__ = ['Settings', 'settings']
