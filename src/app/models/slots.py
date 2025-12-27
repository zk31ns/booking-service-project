from datetime import datetime, time

from sqlalchemy import ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Slot(Base):
    """Модель слота для временных интервалов кафе.

    Attributes:
        id: Уникальный идентификатор слота (первичный ключ).
        cafe_id: Идентификатор кафе (внешний ключ).
        start_time: Время начала слота.
        end_time: Время окончания слота.
        created_at: Дата и время создания записи.
        updated_at: Дата и время последнего обновления.
        active: Флаг активности слота (по умолчанию True).

    """

    __tablename__ = 'slots'

    id: Mapped[int] = mapped_column(primary_key=True)
    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafes.id', ondelete='CASCADE'), nullable=False, index=True
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
    active: Mapped[bool] = mapped_column(default=True)
