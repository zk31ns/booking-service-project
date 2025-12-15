from datetime import datetime, time

from sqlalchemy import CheckConstraint, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Slot(Base):
    """Модель слота для временных интервалов кафе."""

    __tablename__ = 'slots'

    id: Mapped[int] = mapped_column(primary_key=True)
    # Нужно будет заменить на ForeignKey когда будет таблица Cafe
    cafe_id: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        UniqueConstraint(
            'cafe_id', 'start_time', 'end_time',
            name='uq_cafe_slots'
        ),
        CheckConstraint('start_time < end_time', name='ck_slot_time_order'),
    )
