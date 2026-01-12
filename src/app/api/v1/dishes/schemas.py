from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Limits
from app.schemas.base import AuditedSchema
from app.schemas.cafes import CafeShortInfo


class DishCreate(BaseModel):
    """Схема создания блюда.

    Attributes:
        name: Название блюда.
        description: Описание блюда.
        price: Цена блюда.
        photo_id: Идентификатор фото.
        cafes_id: Список идентификаторов кафе.

    """

    name: str = Field(
        ...,
        min_length=Limits.DISH_NAME_MIN_LENGTH,
        max_length=Limits.DISH_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        None, max_length=Limits.DISH_DESCRIPTION_MAX_LENGTH
    )
    price: Decimal = Field(..., gt=Limits.DISH_PRICE_MIN)
    photo_id: UUID = Field(..., description='ID фото.')
    cafes_id: list[int] = Field(..., description='Список ID кафе.')


class DishUpdate(BaseModel):
    """Схема обновления блюда.

    Attributes:
        name: Название блюда.
        description: Описание блюда.
        price: Цена блюда.
        photo_id: Идентификатор фото.
        cafes_id: Список идентификаторов кафе.
        active: Признак активности.

    """

    name: str | None = Field(
        None,
        min_length=Limits.DISH_NAME_MIN_LENGTH,
        max_length=Limits.DISH_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        None, max_length=Limits.DISH_DESCRIPTION_MAX_LENGTH
    )
    price: Decimal | None = Field(None, gt=Limits.DISH_PRICE_MIN)
    photo_id: UUID | None = Field(None, description='ID фото.')
    cafes_id: list[int] | None = Field(None, description='Список ID кафе.')
    active: bool | None = Field(
        None,
        validation_alias='is_active',
        serialization_alias='is_active',
        description='Признак активности блюда.',
    )

    model_config = ConfigDict(populate_by_name=True)


class DishInfo(AuditedSchema):
    """Схема ответа по блюду.

    Attributes:
        name: Название блюда.
        description: Описание блюда.
        price: Цена блюда.
        photo_id: Идентификатор фото.
        cafes: Список кафе, связанных с блюдом.
        active: Признак активности.

    """

    name: str = Field(
        ...,
        min_length=Limits.DISH_NAME_MIN_LENGTH,
        max_length=Limits.DISH_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        None, max_length=Limits.DISH_DESCRIPTION_MAX_LENGTH
    )
    price: Decimal = Field(..., gt=Limits.DISH_PRICE_MIN)
    photo_id: UUID | None = Field(None, description='ID фото.')
    cafes: list[CafeShortInfo] = Field(
        default_factory=list,
        description='Список кафе для этого блюда.',
    )
    active: bool = Field(
        ...,
        validation_alias='active',
        serialization_alias='is_active',
        description='Признак активности блюда.',
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra='ignore',
    )
