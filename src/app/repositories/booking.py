from datetime import date, time
from typing import List, Optional, Union

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.booking.schemas import BookingCreate, BookingUpdate
from app.core.constants import BookingStatus
from app.models import Booking, Slot, TableSlot, User

from .base import BaseCRUD


class BookingRepository(BaseCRUD[Booking]):
    """Репозиторий для работы с бронированиями столиков в кафе.

    Предоставляет методы для CRUD операций с бронированиями,
    проверки доступности столов и занятости пользователей.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy для работы с БД

        """
        super().__init__(session, Booking)

    async def is_occupied(
        self,
        table_id: int,
        slot_id: int,
        date: date,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """Проверить занят ли стол в указанный слот на дату.

        Args:
            table_id: ID стола
            slot_id: ID временного слота
            date: Дата бронирования
            exclude_booking_id: ID бронирования для исключения из проверки

        Returns:
            True если стол занят, False если свободен

        """
        stmt = (
            select(TableSlot)
            .join(self.model)
            .where(
                TableSlot.table_id == table_id,
                TableSlot.slot_id == slot_id,
                self.model.booking_date == date,
                self.model.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                ]),
                self.model.active.is_(True),
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
        """Проверить занят ли пользователь в указанный временной интервал.

        Args:
            user_id: ID пользователя
            start_time: Время начала проверяемого интервала
            end_time: Время окончания проверяемого интервала
            booking_date: Дата бронирования
            exclude_booking_id: ID бронирования для исключения из проверки

        Returns:
            True если пользователь занят, False если свободен

        """
        stmt = (
            select(Booking.id)
            .join(TableSlot, Booking.id == TableSlot.booking_id)
            .join(Slot, TableSlot.slot_id == Slot.id)
            .where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
                Booking.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                ]),
                Booking.active.is_(True),
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
        """Получить список бронирований с фильтрацией.

        Args:
            user_id: ID пользователя для фильтрации
            cafe_id: ID кафе для фильтрации

        Returns:
            Список бронирований

        """
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
        self, obj_in: BookingCreate, user: Optional[User] = None
    ) -> Booking:
        """Создать новое бронирование.

        Args:
            obj_in: Данные для создания бронирования
            user: Пользователь, создающий бронирование

        Returns:
            Созданное бронирование

        Raises:
            IntegrityError: При нарушении ограничений базы данных

        """
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
        """Обновить существующее бронирование.

        Обрабатывает обновление простых полей через UPDATE запрос
        и связей table_slots через ORM отношения.

        Args:
            booking: Обновляемое бронирование
            update_booking: Схема с данными от пользователя (все поля)
            data: Валидированные данные для простого UPDATE
                  (исключает table_slots и поля со значением None)

        Returns:
            Обновленное бронирование

        Raises:
            IntegrityError: При нарушении ограничений базы данных

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

        await self.session.refresh(booking)
        return booking

    async def get_expired_bookings(
        self,
        now: date,
    ) -> int:
        """Поиск истёкших бронирований.

        Args:
            now: дата сравнения с датой бронирования

        Returns:
            Количество найденных записей

        """
        query = select(func.count(Booking.id)).where(
            Booking.booking_date < now,
            Booking.status.in_([
                BookingStatus.PENDING,
                BookingStatus.CONFIRMED,
            ]),
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def cleanup_expired_bookings(
        self,
        now: date,
    ) -> None:
        """Очистка истёкших бронирований.

        Args:
            now: дата сравнения с датой бронирования

        Returns:
            None

        """
        query = (
            update(Booking)
            .where(
                Booking.booking_date < now,
                Booking.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                ]),
            )
            .values(status=BookingStatus.COMPLETED, active=False)
        )
        await self.session.execute(query)
