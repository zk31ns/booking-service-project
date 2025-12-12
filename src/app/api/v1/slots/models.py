from datetime import datetime, time
from sqlalchemy import ForeignKey, Time, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship


from src.app.db.base import Base


class Slot(Base):
    __tablename__ = 'slots'

    id: Mapped[int] = mapped_column(primary_key=True)
    cafe_id: Mapped[int] = mapped_column(ForeignKey('cafes.id'), nullable=False)
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
