from datetime import UTC, datetime, time

from sqlalchemy import Time
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.base import Base


class Slot(Base):
    """Модель слота для временных интервалов кафе."""

    __tablename__ = 'slots'

    id: Mapped[int] = mapped_column(primary_key=True)
    # TODO Нужно будет заменить на ForeignKey когда будет таблица Cafe
    cafe_id: Mapped[int] = mapped_column(nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )
    active: Mapped[bool] = mapped_column(default=True)
