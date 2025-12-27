"""Управление кэшем Redis."""

import json
from typing import Any, Optional

from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.declarative import DeclarativeMeta

from src.app.core.constants import Times


class RedisCache:
    """Класс для работы с кэшем Redis.

    Реализует методы для сериализации данных,
    кэширования и получения информации из кэша.
    """

    redis: Optional[Redis] = None

    @classmethod
    def init(cls, redis: Redis) -> None:
        """Инициализация подключения Redis."""
        cls.redis = redis

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Получение данных из кэша.

        Args:
            key: ключ для поиска в Redis

        Returns:
            Десериализованные данные или None

        """
        if not cls.redis:
            return None
        cached = await cls.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    @classmethod
    def _serialize_value(cls, value: Any) -> str:
        """Сериализация значения в JSON.

        Поддерживает:
        - Pydantic модели
        - SQLAlchemy модели
        - Списки моделей
        - Dict и базовые типы
        """
        # Списки:
        if isinstance(value, list):
            if len(value) == 0:
                return json.dumps([])
            first_item = value[0]
            # Список моделей Pydantic
            if isinstance(first_item, BaseModel):
                return json.dumps([item.model_dump() for item in value])
            # Список моделей SQLAlchemy
            if isinstance(first_item.__class__, DeclarativeMeta):
                return json.dumps([
                    cls._sqlalchemy_to_dict(item) for item in value
                ])
            # Простой список
            return json.dumps(value)
        # Одиночная модель Pydantic
        if isinstance(value, BaseModel):
            return json.dumps(value.model_dump())
        # Одиночная модель SQLAlchemy
        if isinstance(value.__class__, DeclarativeMeta):
            return json.dumps(cls._sqlalchemy_to_dict(value))
        # Обычные типы данных
        return json.dumps(value)

    @staticmethod
    def _sqlalchemy_to_dict(obj: DeclarativeMeta) -> dict:
        """Конвертирует модель SQLAlchemy в dict.

        Args:
            obj: модель SQLAlchemy

        Returns:
            Dict с полями модели

        """
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            # сериализация объектов даты и времени
            if hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    @classmethod
    async def set(
        cls, key: str, value: Any, expire: int = Times.REDIS_CACHE_EXPIRE_TIME
    ) -> None:
        """Сохраняет данные в кэш.

        Args:
            key: ключ для хранения
            value: данные для кэширования
            expire: время жизни в секундах

        """
        if not cls.redis:
            return

        json_data = cls._serialize_value(value)
        await cls.redis.setex(key, expire, json_data)

    @classmethod
    async def delete(cls, key: str) -> None:
        """Удаление данных из кэша.

        Args:
            key: ключ для удаления

        """
        if not cls.redis:
            return
        await cls.redis.delete(key)

    @classmethod
    async def delete_pattern(cls, pattern: str) -> None:
        """Удаление всех ключей по паттерну.

        Args:
            pattern: паттерн для поиска ключей (например, "cafes:*")

        """
        if not cls.redis:
            return
        cursor = 0
        while True:
            cursor, keys = await cls.redis.scan(
                cursor, match=pattern, count=100
            )
            if keys:
                await cls.redis.delete(*keys)
            if cursor == 0:
                break
