from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, Numeric, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import TimestampedModel

dish_cafes = Table(
    'dish_cafes',
    TimestampedModel.metadata,
    Column('dish_id', Integer, ForeignKey('dishes.id'), primary_key=True),
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
)


if TYPE_CHECKING:
    from app.models.cafes import Cafe


class Dish(TimestampedModel):
    """Модель блюда для меню кафе."""

    __tablename__ = 'dishes'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    photo_id: Mapped[str] = mapped_column(nullable=True)
    cafes: Mapped[list['Cafe']] = relationship(
        'Cafe',
        secondary=dish_cafes,
        back_populates='dishes',
        lazy='selectin',
    )
