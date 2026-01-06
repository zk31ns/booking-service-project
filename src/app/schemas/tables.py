from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import Limits
from app.schemas.base import AuditedSchema


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


class TableInDBBase(AuditedSchema):
    """Базовая схема столика в БД."""

    cafe_id: int
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


class Table(TableInDBBase):
    """Схема для ответа API."""

    pass


class TableWithCafe(Table):
    """Столик с информацией о кафе."""

    cafe_name: Optional[str] = None
    cafe_address: Optional[str] = None
