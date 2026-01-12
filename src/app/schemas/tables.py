from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Examples, Limits
from app.schemas.base import AuditedSchema
from app.schemas.cafes import CafeShortInfo


class TableBase(BaseModel):
    """Базовая схема столика."""

    seats: int = Field(
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
        validation_alias='seat_number',
        serialization_alias='seat_number',
        description='Количество мест за столом',
    )
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание столика',
    )


class TableCreate(TableBase):
    """Схема создания столика (без cafe_id)."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            'example': {
                'seat_number': 2,
                'description': 'У окна',
            }
        },
    )


class TableCreateDB(TableBase):
    """Внутренняя схема создания столика с cafe_id."""

    cafe_id: int = Field(description='ID кафе')

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            'example': {
                'cafe_id': 1,
                'seat_number': 4,
                'description': 'У барной стойки',
            }
        },
    )


class TableUpdate(BaseModel):
    """Схема обновления столика."""

    seats: int | None = Field(
        None,
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
        validation_alias='seat_number',
        serialization_alias='seat_number',
    )
    description: str | None = Field(
        None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
    )
    active: bool | None = Field(
        None,
        validation_alias='is_active',
        serialization_alias='is_active',
    )
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            'example': {
                'seat_number': 4,
                'description': 'У барной стойки',
                'is_active': True,
            }
        },
    )


class TableInDBBase(AuditedSchema):
    """Схема ответа о столике из БД."""

    seats: int = Field(
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
        validation_alias='seat_number',
        serialization_alias='seat_number',
        description='Количество мест за столом',
    )
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание столика',
    )
    active: bool = Field(
        default=True,
        validation_alias='is_active',
        serialization_alias='is_active',
        description='Активен',
    )
    cafe: CafeShortInfo | None = Field(
        default=None,
        description='Информация о кафе',
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            'example': {
                'id': 1,
                'seat_number': 4,
                'description': 'У окна',
                'is_active': True,
                'created_at': Examples.DATETIME,
                'updated_at': Examples.DATETIME,
            }
        },
    )


class Table(TableInDBBase):
    """Схема ответа о столике."""

    pass


class TableWithCafe(Table):
    """Схема ответа о столике с данными кафе (legacy)."""

    cafe_name: str | None = None
    cafe_address: str | None = None
