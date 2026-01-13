"""Базовые схемы ответов API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.constants import Times


class BaseResponse(BaseModel):
    """Базовая схема ответа API."""

    model_config = ConfigDict(from_attributes=True, extra='ignore')

    @field_serializer('*', when_used='json', check_fields=False)
    def _format_datetime(self, value: object) -> object:
        if isinstance(value, datetime):
            return value.strftime(Times.DATETIME_FORMAT)
        return value


class TimestampedSchema(BaseResponse):
    """Схема с id и временем создания."""

    id: int | UUID = Field(..., description='Идентификатор записи')
    created_at: datetime = Field(..., description='Время создания')


class ActiveSchema(BaseResponse):
    """Схема с id и флагом активности."""

    id: int = Field(..., description='Идентификатор записи')
    active: bool = Field(
        default=True,
        description='Флаг активности',
        validation_alias='is_active',
        serialization_alias='is_active',
    )


class AuditedSchema(BaseResponse):
    """Схема с id, аудитом и флагом активности."""

    id: int = Field(..., description='Идентификатор записи')
    active: bool = Field(
        default=True,
        description='Флаг активности',
        validation_alias='is_active',
        serialization_alias='is_active',
    )
    created_at: datetime = Field(..., description='Время создания')
    updated_at: datetime = Field(..., description='Время обновления')


__all__ = [
    'BaseResponse',
    'TimestampedSchema',
    'ActiveSchema',
    'AuditedSchema',
]
