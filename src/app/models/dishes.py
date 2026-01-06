from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TimestampedModel


class Dish(TimestampedModel):
    """Модель блюда для меню кафе."""

    __tablename__ = 'dishes'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    photo_id: Mapped[str] = mapped_column(nullable=True)
