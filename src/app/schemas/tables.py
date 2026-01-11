from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Limits
from app.schemas.base import AuditedSchema
from app.schemas.cafes import CafeShortInfo


class TableBase(BaseModel):
    """Base schema for tables."""

    seats: int = Field(
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
        validation_alias='seat_number',
        serialization_alias='seat_number',
        description='Number of seats at the table',
    )
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Table description',
    )


class TableCreate(TableBase):
    """API schema for creating a table (without cafe_id)."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TableCreateDB(TableBase):
    """Internal schema for table creation with cafe_id."""

    cafe_id: int = Field(description='Cafe ID')

    model_config = ConfigDict(populate_by_name=True)


class TableUpdate(BaseModel):
    """API schema for updating a table."""

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

    model_config = ConfigDict(populate_by_name=True)


class TableInDBBase(AuditedSchema):
    """DB-backed schema for table responses."""

    seats: int = Field(
        ge=Limits.MIN_SEATS,
        le=Limits.MAX_SEATS,
        validation_alias='seat_number',
        serialization_alias='seat_number',
        description='Number of seats at the table',
    )
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Table description',
    )
    active: bool = Field(
        default=True,
        validation_alias='is_active',
        serialization_alias='is_active',
        description='Is active',
    )
    cafe: CafeShortInfo | None = Field(
        default=None,
        description='Cafe info',
    )

    model_config = ConfigDict(populate_by_name=True)


class Table(TableInDBBase):
    """API schema for table responses."""

    pass


class TableWithCafe(Table):
    """Table response with extra cafe fields (legacy)."""

    cafe_name: str | None = None
    cafe_address: str | None = None
