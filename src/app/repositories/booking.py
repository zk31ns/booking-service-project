from datetime import date, time

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import BookingStatus
from app.models import Booking, Slot, TableSlot, User
from app.schemas import BookingCreate, BookingUpdate

from .base import BaseCRUD


class BookingRepository(BaseCRUD[Booking]):
    """Репозиторий для работы с бронированиями."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализировать репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        super().__init__(session, Booking)

    async def is_occupied(
        self,
        table_id: int,
        slot_id: int,
        date: date,
        exclude_booking_id: int | None = None,
    ) -> bool:
        """Проверить, занят ли столик в указанную дату и слот.

        Args:
            table_id: ID столика.
            slot_id: ID временного слота.
            date: Дата бронирования.
            exclude_booking_id: ID бронирования для исключения из проверки.

        Returns:
            bool: True, если столик занят; иначе False.

        """
        stmt = (
            select(TableSlot)
            .join(self.model)
            .where(
                TableSlot.table_id == table_id,
                TableSlot.slot_id == slot_id,
                self.model.booking_date == date,
                self.model.status.in_([
                    BookingStatus.BOOKING,
                    BookingStatus.ACTIVE,
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
        exclude_booking_id: int | None = None,
    ) -> bool:
        """Проверить, занят ли пользователь в заданном временном интервале.

        Args:
            user_id: ID пользователя.
            start_time: Время начала.
            end_time: Время окончания.
            booking_date: Дата бронирования.
            exclude_booking_id: ID бронирования для исключения из проверки.

        Returns:
            bool: True, если пользователь занят; иначе False.

        """
        stmt = (
            select(Booking.id)
            .join(TableSlot, Booking.id == TableSlot.booking_id)
            .join(Slot, TableSlot.slot_id == Slot.id)
            .where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
                Booking.status.in_([
                    BookingStatus.BOOKING,
                    BookingStatus.ACTIVE,
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
        user_id: int | None = None,
        cafe_id: int | None = None,
        show_all: bool = False,
    ) -> list[Booking]:
        """Получить список бронирований с фильтрами.

        Args:
            user_id: ID пользователя для фильтра.
            cafe_id: ID кафе для фильтра.
            show_all: Показывать все бронирования, включая неактивные.

        Returns:
            list[Booking]: Список бронирований.

        """
        query = select(Booking).options(
            selectinload(Booking.table_slots).selectinload(TableSlot.table),
            selectinload(Booking.table_slots).selectinload(TableSlot.slot),
            selectinload(Booking.cafe),
            selectinload(Booking.user),
        )

        if user_id is not None:
            query = query.where(Booking.user_id == user_id)

        if cafe_id is not None:
            query = query.where(Booking.cafe_id == cafe_id)

        if not show_all:
            query = query.where(Booking.active.is_(True))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get(self, obj_id: int | str) -> Booking | None:
        """Получить бронирование по ID с зависимыми сущностями."""
        query = (
            select(Booking)
            .options(
                selectinload(Booking.table_slots).selectinload(
                    TableSlot.table
                ),
                selectinload(Booking.table_slots).selectinload(TableSlot.slot),
                selectinload(Booking.cafe),
                selectinload(Booking.user),
            )
            .where(Booking.id == obj_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self, obj_in: BookingCreate, user: User | None = None
    ) -> Booking:
        """Создать бронирование и связки столов со слотами.

        Args:
            obj_in: Данные для создания бронирования.
            user: Пользователь, который создает бронирование.

        Returns:
            Booking: Созданное бронирование.

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
        await self.session.flush()
        await self.session.refresh(booking)
        refreshed = await self.get(booking.id)
        return refreshed or booking

    async def update(
        self,
        booking: Booking,
        update_booking: BookingUpdate,
        data: dict[str, int | str | date | bool],
    ) -> Booking:
        """Обновить бронирование и связи table_slots.

        Args:
            booking: Модель бронирования.
            update_booking: Данные для обновления (связи и поля).
            data: Поля для SQL UPDATE (table_slots обрабатываются отдельно).

        Returns:
            Booking: Обновленное бронирование.

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
        refreshed = await self.get(booking.id)
        return refreshed or booking

    async def get_expired_bookings(
        self,
        now: date,
    ) -> int:
        """Получить количество просроченных бронирований.

        Args:
            now: Текущая дата.

        Returns:
            int: Количество просроченных бронирований.

        """
        query = select(func.count(Booking.id)).where(
            Booking.booking_date < now,
            Booking.status.in_([
                BookingStatus.BOOKING,
            ]),
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def cleanup_expired_bookings(
        self,
        now: date,
    ) -> None:
        """Перевести просроченные бронирования в COMPLETED и деактивировать.

        Args:
            now: Текущая дата.

        Returns:
            None

        """
        query = (
            update(Booking)
            .where(
                Booking.booking_date < now,
                Booking.status.in_([
                    BookingStatus.BOOKING,
                ]),
            )
            .values(status=BookingStatus.CANCELED, active=False)
        )
        await self.session.execute(query)
