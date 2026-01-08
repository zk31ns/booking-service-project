from datetime import date, datetime

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.core.constants import BookingStatus, Limits


class TableSlot(Base):
    """Модель связи между столами и временными слотами.

    Связывает конкретный стол с конкретным временным слотом в бронировании.
    Представляет собой таблицу связи many-to-many между Booking, Table и Slot.
    """

    __tablename__ = 'table_slots'
    __table_args__ = (
        Index('ix_table_slot_booking', 'booking_id'),
        Index('ix_table_slot_table_slot', 'table_id', 'slot_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False
    )
    table_id: Mapped[int] = mapped_column(
        ForeignKey('tables.id'), nullable=False
    )
    slot_id: Mapped[int] = mapped_column(
        ForeignKey('slots.id'), nullable=False
    )

    table = relationship(
        'Table',
        lazy='selectin',
    )
    slot = relationship(
        'Slot',
        lazy='selectin',
    )
    booking = relationship(
        'Booking',
        back_populates='table_slots',
        lazy='selectin',
    )


class Booking(Base):
    """Модель бронирований столиков в кафе.

    Основная модель, представляющая бронирование столиков пользователями.
    Содержит информацию о дате, времени, количестве гостей и
    связанных сущностях.
    """

    __tablename__ = 'bookings'
    __table_args__ = (
        Index('ix_booking_cafe', 'cafe_id'),
        Index('ix_booking_user', 'user_id'),
        Index('ix_booking_date', 'booking_date'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Integer,
        nullable=False,
        default=BookingStatus.PENDING,
    )
    note: Mapped[str | None] = mapped_column(
        String(Limits.MAX_BOOKING_NOTE_LENGTH)
    )
    guest_number: Mapped[int] = mapped_column(Integer, nullable=False)
    table_slots: Mapped[list[TableSlot]] = relationship(
        'TableSlot',
        back_populates='booking',
        lazy='selectin',
        cascade='all, delete-orphan',
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), server_onupdate=func.now()
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False
    )
    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafes.id'), nullable=False
    )
    user = relationship('User', back_populates='bookings', lazy='selectin')
    cafe = relationship('Cafe', lazy='selectin')
