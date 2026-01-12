from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import TimestampedModel

action_cafes = Table(
    'action_cafes',
    TimestampedModel.metadata,
    Column('action_id', Integer, ForeignKey('actions.id'), primary_key=True),
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
)


if TYPE_CHECKING:
    from app.models.cafes import Cafe


class Action(TimestampedModel):
    """Модель акции и специального предложения кафе."""

    __tablename__ = 'actions'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    photo_id: Mapped[str] = mapped_column(nullable=True)
    cafes: Mapped[list['Cafe']] = relationship(
        'Cafe',
        secondary=action_cafes,
        back_populates='actions',
        lazy='selectin',
    )
