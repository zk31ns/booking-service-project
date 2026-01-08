from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import TimestampedModel


class Action(TimestampedModel):
    """Модель акции и специального предложения кафе."""

    __tablename__ = 'actions'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    photo_id: Mapped[str] = mapped_column(nullable=True)
