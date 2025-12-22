from datetime import time, date
from typing import Dict, List, Optional, Union

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models import Booking, User, TableSlot, Slot
from src.app.core.constants import BookingStatus


class BookingRepository:
    """CRUD для бронирования столиков в кафе.
    Добавить деактивацию бронирования?"""

    def __init__(self):
        self.model = Booking

    async def get(
        self,
        booking_id: int,
        session: AsyncSession,
    ):
        booking = await session.execute(
            select(self.model).where(
                self.model.id == booking_id
            )
        )
        return booking.scalars().first()

    async def is_occupied(
        self,
        table_id: int,
        slot_id: int,
        date: date,
        session: AsyncSession,
        exclude_booking_id: Optional[int] = None
    ) -> bool:
        """Проверить, свободен ли стол в слот на эту дату."""

        stmt = select(TableSlot).join(self.model).where(
            TableSlot.table_id == table_id,
            TableSlot.slot_id == slot_id,
            self.model.booking_date == date,
            self.model.status.in_(
                [BookingStatus.BOOKING, BookingStatus.ACTIVE]
            ),
            self.model.is_active == True
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def user_is_busy(
        self,
        user_id: int,
        start_time: time,
        end_time: time,
        booking_date: date,
        session: AsyncSession,
        exclude_booking_id: Optional[int] = None
    ):
        """Проверить свободен ли пользователь в это время."""
        stmt = (
            select(Booking.id)
            .join(TableSlot, Booking.id == TableSlot.booking_id)
            .join(Slot, TableSlot.slot_id == Slot.id)
            .where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
                Booking.status.in_(
                    [BookingStatus.BOOKING, BookingStatus.ACTIVE]
                ),
                Booking.is_active == True,
                (start_time < Slot.end_time) & (end_time > Slot.start_time)
            )
            .limit(1)
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_multi(
        self,
        session: AsyncSession,
        user_id: Optional[int] = None,
        cafe_id: Optional[int] = None,
    ) -> List[Booking]:
        """Получение всех бронирований с фильтрацией."""

        query = (
            select(Booking)
            .options(
                selectinload(Booking.table_slots),
                selectinload(Booking.cafe),
                selectinload(Booking.user),
            )
        )

        if user_id is not None:
            query = query.where(Booking.user_id == user_id)

        if cafe_id is not None:
            query = query.where(Booking.cafe_id == cafe_id)

        result = await session.execute(query)
        return result.scalars().all()

    async def create(
            self,
            obj_in,
            session: AsyncSession,
            user: Optional[User] = None
    ) -> Union[Booking]:
        """Создание нового бронирования."""
        data = obj_in.dict(exclude={"table_slots"})

        if user is not None:
            data["user_id"] = user.id

        booking = Booking(**data)

        booking.table_slots = [
            TableSlot(
                table_id=ts.table_id,
                slot_id=ts.slot_id,
            )
            for ts in obj_in.table_slots
        ]

        session.add(booking)
        await session.commit()
        await session.refresh(booking)

        return booking

    async def update(
        self,
        session: AsyncSession,
        booking: Booking,
        changes: dict,
    ) -> Booking:
        """Обновить бронирование."""

        if 'table_slots' in changes:
            await self._bulk_replace_table_slots(
                session=session,
                booking=booking,
                new_slots=changes.pop('table_slots')
            )

        for field, value in changes.items():
            setattr(booking, field, value)

        await session.commit()
        await session.refresh(booking, ['table_slots'])
        return booking

    async def _bulk_replace_table_slots(
        self,
        session: AsyncSession,
        booking: Booking,
        new_slots: List[Dict[str, int]]
    ) -> None:
        """Замена table_slots через bulk operations."""

        await session.execute(
            delete(TableSlot).where(TableSlot.booking_id == booking.id)
        )

        if new_slots:
            await session.execute(
                TableSlot.__table__.insert(),
                [
                    {
                        "booking_id": booking.id,
                        "table_id": slot["table_id"],
                        "slot_id": slot["slot_id"]
                    }
                    for slot in new_slots
                ]
            )
        session.expire(booking, ['table_slots'])

    async def remove(
            self,
            db_obj,
            session: AsyncSession,
    ) -> Booking:
        """Удаление бронирования."""
        await session.delete(db_obj)
        await session.commit()
        return db_obj
