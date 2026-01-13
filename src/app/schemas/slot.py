from datetime import time

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Examples
from app.schemas.base import AuditedSchema
from app.schemas.cafes import CafeShortInfo


class SlotCreate(BaseModel):
    """Входные данные для создания слота.

    Attributes:
        start_time: Время начала слота.
        end_time: Время окончания слота.

    """

    start_time: time = Field(..., description='Время начала слота')
    end_time: time = Field(..., description='Время окончания слота')
    description: str | None = Field(
        default=None,
        description='Описание слота',
    )

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'start_time': Examples.TIME_START,
                'end_time': Examples.TIME_END,
                'description': 'Утренние часы',
            }
        }
    )


class SlotUpdate(BaseModel):
    """Входные данные для обновления слота.

    Attributes:
        start_time: Время начала слота или None если не изменяется.
        end_time: Время окончания слота или None если не изменяется.
        active: Активен ли слот или None если не изменяется.

    """

    start_time: time | None = Field(None, description='Время начала слота')
    end_time: time | None = Field(None, description='Время окончания слота')
    description: str | None = Field(
        None,
        description='Описание слота',
    )
    active: bool | None = Field(
        None,
        description='Активен ли слот',
        validation_alias='is_active',
        serialization_alias='is_active',
    )

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'start_time': Examples.TIME_UPDATE_START,
                'end_time': Examples.TIME_UPDATE_END,
                'description': 'Обновленное описание',
                'is_active': True,
            }
        }
    )


class SlotInfo(AuditedSchema):
    """Выходные данные слота.

    Attributes:
        id: Уникальный идентификатор слота.
        cafe_id: Идентификатор кафе.
        start_time: Время начала слота.
        end_time: Время окончания слота.
        active: Статус активности слота.
        created_at: Дата и время создания слота.
        updated_at: Дата и время последнего обновления.

    """

    cafe: CafeShortInfo = Field(description='Кафе')
    start_time: time
    end_time: time
    description: str | None = None


class TimeSlotShortInfo(BaseModel):
    """Краткая информация о временном слоте."""

    id: int = Field(description='ID слота')
    start_time: time = Field(description='Время начала слота')
    end_time: time = Field(description='Время окончания слота')
    description: str | None = Field(
        default=None,
        description='Описание слота',
    )

    model_config = ConfigDict(from_attributes=True)
