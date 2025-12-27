from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Action(Base):
    """Модель акции и специального предложения кафе."""

    __tablename__ = 'actions'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    photo_id: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
    active: Mapped[bool] = mapped_column(default=True)
