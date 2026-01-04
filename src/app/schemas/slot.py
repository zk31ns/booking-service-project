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
