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
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание столика (например, "VIP стол", "у окна")',
    )


class TableCreate(TableBase):
    """Схема для создания столика."""

    cafe_id: int = Field(description='ID кафе')


class TableUpdate(BaseModel):
    """Схема для обновления столика."""

    seats: int | None = Field(
        None,
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
    )
    description: str | None = Field(
        None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
    )
    active: bool | None = None


class TableInDBBase(AuditedSchema):
    """Базовая схема столика в БД."""

    cafe_id: int
    seats: int = Field(
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
        description='Количество мест за столиком',
    )
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание столика (например, "VIP стол", "у окна")',
    )


class Table(TableInDBBase):
    """Схема для ответа API."""

    pass


class TableWithCafe(Table):
    """Столик с информацией о кафе."""

    cafe_name: str | None = None
    cafe_address: str | None = None
