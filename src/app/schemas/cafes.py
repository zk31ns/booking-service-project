from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Limits


class CafeBase(BaseModel):
    """Базовая схема для кафе."""

    name: str = Field(
        min_length=Limits.MIN_CAFE_NAME_LENGTH,
        max_length=Limits.MAX_CAFE_NAME_LENGTH,
        description='Название кафе',
    )
    address: str = Field(
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Адрес кафе',
    )
    phone: str = Field(
        min_length=Limits.MIN_PHONE_LENGTH,
        max_length=Limits.MAX_PHONE_LENGTH,
        description='Телефон кафе',
    )
    description: Optional[str] = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание кафе',
    )


class CafeCreate(CafeBase):
    """Схема для создания кафе."""

    photo_id: Optional[UUID] = Field(
        default=None,
        description='ID фотографии кафе',
    )


class CafeUpdate(BaseModel):
    """Схема для обновления кафе."""

    name: Optional[str] = Field(
        None,
        min_length=Limits.MIN_CAFE_NAME_LENGTH,
        max_length=Limits.MAX_CAFE_NAME_LENGTH,
    )
    address: Optional[str] = Field(
        None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
    )
    phone: Optional[str] = Field(
        None,
        min_length=Limits.MIN_PHONE_LENGTH,
        max_length=Limits.MAX_PHONE_LENGTH,
    )
    description: Optional[str] = Field(
        None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
    )
    active: Optional[bool] = None


class CafeInDBBase(CafeBase):
    """Базовая схема кафе в БД."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    # photo_id: Optional[UUID] = None
    active: bool
    created_at: datetime
    updated_at: datetime


class Cafe(CafeInDBBase):
    """Схема для ответа API."""

    pass


class CafeWithRelations(Cafe):
    """Кафе с отношениями."""

    tables_count: Optional[int] = None
