from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Limits


class TableBase(BaseModel):
    """Базовая схема для столика."""

    seats: int = Field(
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
        description='Количество мест за столиком',
    )
    description: Optional[str] = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание столика (например, "VIP стол", "у окна")',
    )


class TableCreate(TableBase):
    """Схема для создания столика."""

    cafe_id: int = Field(description='ID кафе')


class TableUpdate(BaseModel):
    """Схема для обновления столика."""

    seats: Optional[int] = Field(
        None,
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
    )
    description: Optional[str] = Field(
        None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
    )
    active: Optional[bool] = None


class TableInDBBase(TableBase):
    """Базовая схема столика в БД."""

    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    cafe_id: int
    active: bool
    created_at: datetime
    updated_at: datetime


class Table(TableInDBBase):
    """Схема для ответа API."""

    pass


class TableWithCafe(Table):
    """Столик с информацией о кафе."""

    cafe_name: Optional[str] = None
    cafe_address: Optional[str] = None
