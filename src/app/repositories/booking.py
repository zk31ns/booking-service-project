from datetime import date, time
from typing import List, Optional, Union

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.api.v1.booking.schemas import BookingCreate, BookingUpdate
from src.app.core.constants import BookingStatus
from src.app.models import Booking, Slot, TableSlot, User


class BookingRepository:
    """CRUD для бронирования столиков в кафе."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий."""
        self.session = session
        self.model = Booking

    async def get(
        self,
        booking_id: int,
    ) -> Booking | None:
        """Получить бронь."""
        booking = await self.session.execute(
            select(self.model).where(self.model.id == booking_id)
        )
        return booking.scalars().first()

    async def is_occupied(
        self,
        table_id: int,
        slot_id: int,
        date: date,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """Проверить, свободен ли стол в слот на эту дату."""
        stmt = (
            select(TableSlot)
            .join(self.model)
            .where(
                TableSlot.table_id == table_id,
                TableSlot.slot_id == slot_id,
                self.model.booking_date == date,
                self.model.status.in_([
                    BookingStatus.BOOKING,
                    BookingStatus.CONFIRMED,
                ]),
                self.model.is_active.is_(True),
            )
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def user_is_busy(
        self,
        user_id: int,
        start_time: time,
        end_time: time,
        booking_date: date,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """Проверить свободен ли пользователь в это время."""
        stmt = (
            select(Booking.id)
            .join(TableSlot, Booking.id == TableSlot.booking_id)
            .join(Slot, TableSlot.slot_id == Slot.id)
            .where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
                Booking.status.in_([
                    BookingStatus.BOOKING,
                    BookingStatus.CONFIRMED,
                ]),
                Booking.is_active.is_(True),
                (start_time < Slot.end_time) & (end_time > Slot.start_time),
            )
            .limit(1)
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_multi(
        self,
        user_id: Optional[int] = None,
        cafe_id: Optional[int] = None,
    ) -> List[Booking]:
        """Получение всех бронирований с фильтрацией."""
        query = select(Booking).options(
            selectinload(Booking.table_slots),
            selectinload(Booking.cafe),
            selectinload(Booking.user),
        )

        if user_id is not None:
            query = query.where(Booking.user_id == user_id)

        if cafe_id is not None:
            query = query.where(Booking.cafe_id == cafe_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        obj_in: BookingCreate,
        user: Optional[User] = None
    ) -> Booking:
        """Создание нового бронирования."""
        data = obj_in.dict(exclude={'table_slots'})

        if user is not None:
            data['user_id'] = user.id

        booking = Booking(**data)

        booking.table_slots = [
            TableSlot(
                table_id=ts.table_id,
                slot_id=ts.slot_id,
            )
            for ts in obj_in.table_slots
        ]

        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)

        return booking

    async def update(
        self,
        booking: Booking,
        update_booking: BookingUpdate,
        data: dict[str, Union[int, str, date, bool]],
    ) -> Booking:
        """Обновить бронь.

        update_booking: Схема с данными от пользователя
        (все поля, включая None)
        data: Уже валидированные и обработанные данные для простого UPDATE
               (исключает table_slots и поля со значением None)
        """
        if data:
            stmt = (
                update(Booking).where(Booking.id == booking.id).values(**data)
            )
            await self.session.execute(stmt)

        if update_booking.table_slots is not None and hasattr(
            update_booking, 'model_fields_set'
        ):
            booking.table_slots.clear()

            for slot_schema in update_booking.table_slots:
                table_slot = TableSlot(
                    table_id=slot_schema.table_id, slot_id=slot_schema.slot_id
                )
                booking.table_slots.append(table_slot)

        await self.session.commit()
        await self.session.refresh(booking)
        return booking
