"""Базовые schema классы для всех моделей ответов.

Содержит базовые классы для стандартизации response структур
и уменьшения дублирования кода в schema файлах.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    """Базовый класс для всех ответов API.

    Содержит стандартную конфигурацию для работы с ORM моделями.
    """

    model_config = ConfigDict(from_attributes=True, extra='ignore')


class TimestampedSchema(BaseResponse):
    """Базовый класс для объектов с временными метками.

    Содержит поля created_at для отслеживания времени создания записи.
    Используется для объектов, которые отслеживают только время создания.

    Attributes:
        id: Уникальный идентификатор записи.
        created_at: Дата и время создания записи.

    Examples:
        class MediaInfo(TimestampedSchema):
            id: UUID
            file_size: int
            created_at: datetime

    """

    id: int | UUID = Field(..., description='Уникальный идентификатор')
    created_at: datetime = Field(
        ..., description='Дата и время создания записи'
    )


class ActiveSchema(BaseResponse):
    """Базовый класс для объектов с флагом активности.

    Содержит поле active для отслеживания активности записи (soft delete).
    Используется для объектов, которые поддерживают мягкое удаление.

    Attributes:
        id: Уникальный идентификатор записи.
        active: Флаг активности записи (True = активна, False = удалена).

    Examples:
        class TableInfo(ActiveSchema):
            id: int
            cafe_id: int
            seats: int
            active: bool

    """

    id: int = Field(..., description='Уникальный идентификатор')
    active: bool = Field(default=True, description='Флаг активности записи')


class AuditedSchema(BaseResponse):
    """Базовый класс для объектов с полными audit полями.

    Содержит все audit поля: created_at, updated_at, active.
    Это наиболее полная и часто используемая схема для ответов.

    Attributes:
        id: Уникальный идентификатор записи.
        created_at: Дата и время создания записи.
        updated_at: Дата и время последнего обновления.
        active: Флаг активности записи.

    Examples:
        class SlotInfo(AuditedSchema):
            id: int
            cafe_id: int
            start_time: time
            end_time: time
            active: bool
            created_at: datetime
            updated_at: datetime

    """

    id: int = Field(..., description='Уникальный идентификатор')
    active: bool = Field(default=True, description='Флаг активности записи')
    created_at: datetime = Field(
        ..., description='Дата и время создания записи'
    )
    updated_at: datetime = Field(
        ..., description='Дата и время последнего обновления'
    )


__all__ = [
    'BaseResponse',
    'TimestampedSchema',
    'ActiveSchema',
    'AuditedSchema',
]
