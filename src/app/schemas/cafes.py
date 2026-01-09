from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import Limits
from app.schemas.base import AuditedSchema
from app.schemas.users import UserShortInfo


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
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание кафе',
    )


class CafeCreate(CafeBase):
    """Схема для создания кафе."""

    photo_id: UUID = Field(
        description='ID фотографии кафе',
    )
    managers_id: list[int] | None = Field(
        default=None,
        description='ID менеджеров кафе (опционально, можно добавить позже)',
    )


class CafeUpdate(BaseModel):
    """Схема для обновления кафе."""

    name: str | None = Field(
        None,
        min_length=Limits.MIN_CAFE_NAME_LENGTH,
        max_length=Limits.MAX_CAFE_NAME_LENGTH,
    )
    address: str | None = Field(
        None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
    )
    phone: str | None = Field(
        None,
        min_length=Limits.MIN_PHONE_LENGTH,
        max_length=Limits.MAX_PHONE_LENGTH,
    )
    description: str | None = Field(
        None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
    )
    active: bool | None = None
    managers_id: list[int] | None = Field(
        default=None,
        description='ID менеджеров кафе',
    )


class CafeInDBBase(AuditedSchema):
    """Базовая схема кафе в БД."""

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
    description: str | None = Field(
        default=None,
        max_length=Limits.MAX_DESCRIPTION_LENGTH,
        description='Описание кафе',
    )
    photo_id: UUID | None = None


class Cafe(CafeInDBBase):
    """Схема для ответа API."""

    pass


class CafeWithRelations(Cafe):
    """Кафе с отношениями."""

    tables_count: int | None = None
    managers: list[UserShortInfo] = Field(
        default_factory=list,
        description='Менеджеры кафе',
    )
