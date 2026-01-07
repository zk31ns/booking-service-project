from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Limits


class DishBase(BaseModel):
    """Базовая схема блюда."""

    name: str = Field(
        ...,
        min_length=Limits.DISH_NAME_MIN_LENGTH,
        max_length=Limits.DISH_NAME_MAX_LENGTH,
    )
    description: Optional[str] = Field(
        None, max_length=Limits.DISH_DESCRIPTION_MAX_LENGTH
    )
    price: Decimal = Field(..., gt=Limits.DISH_PRICE_MIN)
    photo_id: Optional[str] = Field(None)


class DishCreate(DishBase):
    """Схема для создания блюда."""

    pass


class DishUpdate(BaseModel):
    """Схема для обновления блюда."""

    name: Optional[str] = Field(
        None,
        min_length=Limits.DISH_NAME_MIN_LENGTH,
        max_length=Limits.DISH_NAME_MAX_LENGTH,
    )
    description: Optional[str] = Field(
        None, max_length=Limits.DISH_DESCRIPTION_MAX_LENGTH
    )
    price: Optional[Decimal] = Field(None, gt=Limits.DISH_PRICE_MIN)
    photo_id: Optional[str] = Field(None)


class DishInfo(DishBase):
    """Схема блюда для получения информации."""

    id: int
    active: bool

    model_config = ConfigDict(from_attributes=True)
