from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.app.api.v1.dishes.constants import (
    DISH_DESCRIPTION_MAX_LENGTH,
    DISH_NAME_MAX_LENGTH,
    DISH_NAME_MIN_LENGTH,
    DISH_PRICE_MIN,
)


class DishBase(BaseModel):
    """Базовая схема блюда."""

    name: str = Field(
        ...,
        min_length=DISH_NAME_MIN_LENGTH,
        max_length=DISH_NAME_MAX_LENGTH,
    )
    description: Optional[str] = Field(
        None, max_length=DISH_DESCRIPTION_MAX_LENGTH
    )
    price: Decimal = Field(..., gt=DISH_PRICE_MIN)
    photo_id: Optional[str] = Field(None)


class DishCreate(DishBase):
    """Схема для создания блюда."""

    pass


class DishUpdate(BaseModel):
    """Схема для обновления блюда."""

    name: Optional[str] = Field(
        None,
        min_length=DISH_NAME_MIN_LENGTH,
        max_length=DISH_NAME_MAX_LENGTH,
    )
    description: Optional[str] = Field(
        None, max_length=DISH_DESCRIPTION_MAX_LENGTH
    )
    price: Optional[Decimal] = Field(None, gt=DISH_PRICE_MIN)
    photo_id: Optional[str] = Field(None)


class DishInfo(DishBase):
    """Схема блюда для получения информации."""

    id: int
    active: bool

    class Config:  # noqa: D106
        """Pydantic config."""

        from_attributes = True
