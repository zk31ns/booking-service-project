from datetime import time

from pydantic import BaseModel, Field

from app.schemas.base import AuditedSchema


class SlotCreate(BaseModel):
    """Входные данные для создания слота.

    Attributes:
        start_time: Время начала слота.
        end_time: Время окончания слота.

    """

    start_time: time = Field(..., description='Время начала слота')
    end_time: time = Field(..., description='Время окончания слота')

    model_config = {
        "json_schema_extra": {
            "example": {
                "end_time": "10:00",
                "start_time": "09:05"
            }
        }
    }


class SlotUpdate(BaseModel):
    """Входные данные для обновления слота.

    Attributes:
        start_time: Время начала слота или None если не изменяется.
        end_time: Время окончания слота или None если не изменяется.
        active: Активен ли слот или None если не изменяется.

    """

    start_time: time | None = Field(None, description='Время начала слота')
    end_time: time | None = Field(None, description='Время окончания слота')
    active: bool | None = Field(None, description='Активен ли слот')

    model_config = {
        "json_schema_extra": {
            "example": {
                "active": True,
                "end_time": "10:00",
                "start_time": "09:05"
            }
        }
    }


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

    cafe_id: int
    start_time: time
    end_time: time
