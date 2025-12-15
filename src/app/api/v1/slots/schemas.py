# src/app/api/v1/slots/schemas.py
from datetime import datetime, time

from pydantic import BaseModel, Field


class SlotCreate(BaseModel):
    """Входные данные для создания слота."""

    start_time: time = Field(..., description="Время начала слота")
    end_time: time = Field(..., description="Время окончания слота")


class SlotUpdate(BaseModel):
    """Входные данные для обновления слота."""

    start_time: time | None = Field(None, description="Время начала слота")
    end_time: time | None = Field(None, description="Время окончания слота")
    active: bool | None = Field(None, description="Активен ли слот")


class SlotInfo(BaseModel):
    """Выходные данные слота."""

    id: int
    cafe_id: int
    start_time: time
    end_time: time
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True
