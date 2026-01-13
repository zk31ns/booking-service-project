from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Examples, Limits
from app.schemas.base import AuditedSchema
from app.schemas.users import UserShortInfo


class CafeBase(BaseModel):
    """Базовая схема для кафе.

    Attributes:
        name: Название кафе.
        address: Адрес кафе.
        phone: Телефон кафе.
        description: Описание кафе.

    """

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


class CafeShortInfo(BaseModel):
    """Краткая информация о кафе.

    Attributes:
        id: Идентификатор кафе.
        name: Название кафе.
        address: Адрес кафе.
        phone: Телефон кафе.
        description: Описание кафе.
        photo_id: Идентификатор фото.

    """

    id: int
    name: str
    address: str
    phone: str
    description: str | None = None
    photo_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CafeCreate(CafeBase):
    """Схема для создания кафе.

    Attributes:
        photo_id: Идентификатор фото.
        managers_id: Идентификаторы менеджеров кафе.

    """

    photo_id: UUID = Field(
        description='ID фотографии кафе',
    )
    managers_id: list[int] = Field(
        description='ID менеджеров кафе',
    )
    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'name': 'Кафе Уют',
                'address': 'ул. Ленина, 1',
                'phone': '+79990001122',
                'description': 'Небольшое уютное кафе',
                'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'managers_id': [1, 2],
            }
        }
    )


class CafeUpdate(BaseModel):
    """Схема для обновления кафе.

    Attributes:
        name: Название кафе.
        address: Адрес кафе.
        phone: Телефон кафе.
        description: Описание кафе.
        active: Флаг активности.
        managers_id: Идентификаторы менеджеров кафе.
        photo_id: Идентификатор фото.

    """

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
    active: bool | None = Field(
        None,
        validation_alias='is_active',
        serialization_alias='is_active',
        description='Флаг активности кафе',
    )
    managers_id: list[int] | None = Field(
        default=None,
        description='ID менеджеров кафе',
    )
    photo_id: UUID | None = Field(
        default=None,
        description='ID фотографии кафе',
    )
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            'example': {
                'name': 'Кафе Сладкоежка',
                'description': 'Обновленное описание',
                'is_active': True,
                'managers_id': [2],
            }
        },
    )


class CafeInDBBase(AuditedSchema):
    """Базовая схема кафе в БД.

    Attributes:
        name: Название кафе.
        address: Адрес кафе.
        phone: Телефон кафе.
        description: Описание кафе.
        photo_id: Идентификатор фото.
        managers: Менеджеры кафе.

    """

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
    managers: list[UserShortInfo] = Field(
        default_factory=list,
        description='Менеджеры кафе',
    )


class Cafe(CafeInDBBase):
    """Схема кафе для API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'examples': [
                {
                    'id': 1,
                    'name': 'Кафе Уют',
                    'address': 'ул. Ленина, 1',
                    'phone': '+79990001122',
                    'description': 'Небольшое кафе',
                    'photo_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                    'managers': [
                        {
                            'id': 10,
                            'username': 'manager',
                            'email': 'manager@example.com',
                            'phone': '+79990002233',
                            'tg_id': '123456789',
                        }
                    ],
                    'is_active': True,
                    'created_at': Examples.DATETIME,
                    'updated_at': Examples.DATETIME,
                }
            ]
        },
    )


class CafeWithRelations(Cafe):
    """Схема кафе с отношениями.

    Attributes:
        tables_count: Количество столов.
        managers: Менеджеры кафе.

    """

    tables_count: int | None = None
    managers: list[UserShortInfo] = Field(
        default_factory=list,
        description='Менеджеры кафе',
    )
