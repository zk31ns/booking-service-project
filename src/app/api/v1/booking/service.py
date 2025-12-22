from typing import Dict, List, Tuple, Optional, Union
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.repositories import CafeRepository, TableRepository
from src.app.api.v1.slots.repository import SlotRepository
from src.app.api.v1.users.repository import UserRepository
from src.app.models import User, Booking, Table, Slot, Cafe
from src.app.api.v1.booking.schemas import (
    BookingCreate, BookingUpdate, TableSlot
)
from src.app.core.constants import ErrorCode, BookingStatus
from src.app.core.exceptions import (
    AppException, AuthenticationException,
    NotFoundException, ValidationException,
)
from .repository import BookingRepository


class BookingService:
    def __init__(
        self,
        booking_repo: BookingRepository,
        cafe_repo: CafeRepository,
        user_repo: UserRepository,
        table_repo: TableRepository,
        slot_repo: SlotRepository,
    ):
        self.booking_repo = booking_repo
        self.cafe_repo = cafe_repo
        self.user_repo = user_repo
        self.table_repo = table_repo
        self.slot_repo = slot_repo

    async def create_booking(
        self,
        booking_in: BookingCreate,
        session: AsyncSession,
        user: User,
    ) -> Booking:
        """Создать бронирование."""
        self._validate_booking_date(booking_in.booking_date)

        cafe = await self._validate_cafe(booking_in.cafe_id, session)

        tables = await self._validate_new_table_slots(
            table_slots=booking_in.table_slots,
            cafe_id=booking_in.cafe_id,
            session=session,
            booking_date=booking_in.booking_date,
            user=user,
            guest_number=booking_in.guest_number,
        )

        await self._validate_guest_number(booking_in.guest_number)

        if booking_in.guest_number is not None and (
            booking_in.guest_number > self._calculate_total_seats(tables)
        ):
            raise AppException(ErrorCode.NOT_ENOUGH_SEATS)

        booking = await self.booking_repo.create(
            obj_in=booking_in,
            session=session,
            user=user,
        )

        # Запустить фоновые задачи (уведомления)
        await self._trigger_celery_tasks(booking, user, cafe)

        return booking

    async def get_all_bookings(
        self,
        current_user: User,
        session: AsyncSession,
        show_all: bool = True,
        cafe_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ):
        """
        Для суперюзеров и менеджеров:
            - Получить все бронирование
            - сортировать по кафе
            - сортировать по пользователю
            - получить свои бронирования
        Для пользователей:
            - получить свои бронирования
        """
        is_manager = await self.user_repo.is_manager(
            session=session, user_id=current_user.id
        )
        if (
            not current_user.is_superuser and not is_manager
        ) or not show_all:

            user_id = current_user.id

        bookings = await self.booking_repo.get_multi(
            session=session,
            user_id=user_id,
            cafe_id=cafe_id,
        )

        return bookings

    async def get_booking(
        self,
        current_user: User,
        booking_id: int,
        session: AsyncSession,
    ):
        """Получить бронирование по id."""
        booking = await self.__get_booking_or_404(
            booking_id=booking_id, session=session
        )

        await self._check_booking_permissions(
            session=session,
            current_user=current_user,
            booking=booking
        )
        return booking

    async def modify_booking(
        self,
        booking_update: BookingUpdate,
        current_user: User,
        booking_id: int,
        session: AsyncSession,
    ):
        """Изменить, перенести или отменить бронь."""
        booking = await self.__get_booking_or_404(
            booking_id=booking_id,
            session=session
        )

        await self._check_booking_permissions(
            session=session,
            current_user=current_user,
            booking=booking
        )

        changes = booking_update.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        if not changes:
            return booking

        actual_changes = {}

        for field, new_value in changes.items():
            old_value = getattr(booking, field, None)

            if field == 'table_slots':
                new_slots = {
                    (item['table_id'], item['slot_id'])
                    for item in (new_value or [])
                }
                old_slots = {
                    (slot.table_id, slot.slot_id)
                    for slot in (old_value or [])
                }
                if new_slots != old_slots:
                    actual_changes[field] = new_value

            elif new_value != old_value:
                actual_changes[field] = new_value

        if not actual_changes:
            return booking

        await self._validate_update_data(
            booking=booking,
            changes=actual_changes,
            session=session,
            current_user=current_user,
        )

        updated_booking = await self.booking_repo.update(
            session=session,
            booking=booking,
            changes=actual_changes,
        )
        return updated_booking

    async def _validate_update_data(
        self,
        booking: Booking,
        changes: dict,
        session: AsyncSession,
        current_user: User
    ) -> None:
        """Валидация изменений."""

        booking_date = changes.get('booking_date', booking.booking_date)
        cafe_id = changes.get('cafe_id', booking.cafe_id)
        guest_number = changes.get('guest_number', booking.guest_number)

        if 'table_slots' in changes:
            table_slots = changes['table_slots']
        else:
            table_slots = [
                {"table_id": ts.table_id, "slot_id": ts.slot_id}
                for ts in booking.table_slots
            ]

        # Валидация отдельных полей
        if 'booking_date' in changes:
            self._validate_booking_date(booking_date)

        if 'cafe_id' in changes:
            await self._validate_cafe(cafe_id, session)

        if 'guest_number' in changes:
            await self._validate_guest_number(guest_number)

        validate_tables = any(key in changes for key in [
            'table_slots', 'booking_date', 'cafe_id'
        ])

        if validate_tables:
            await self._validate_new_table_slots(
                table_slots=table_slots,
                cafe_id=cafe_id,
                session=session,
                booking_date=booking_date,
                user=current_user,
                guest_number=guest_number,
                exclude_booking_id=booking.id
            )

    async def _validate_new_table_slots(
        self,
        table_slots: List[TableSlot],
        cafe_id: int,
        session: AsyncSession,
        booking_date: date,
        user: User,
        guest_number: Optional[int] = None,
        exclude_booking_id: Optional[int] = None,
    ):
        """Валидировать столики и окошки со временем"""
        tables = set()
        for table_slot in table_slots:
            if exclude_booking_id is None:
                table_id, slot_id = table_slot.table_id, table_slot.slot_id
            else:
                table_id, slot_id = table_slot['table_id'], table_slot['slot_id']

            table, slot = await self._validate_table_slot(
                table_id,
                slot_id,
                cafe_id,
                session
            )

            if await self.booking_repo.is_occupied(
                table_id,
                slot_id,
                booking_date,
                session,
                exclude_booking_id
            ):
                raise AppException(ErrorCode.TABLE_ALREADY_BOOKED)

            if await self.booking_repo.user_is_busy(
                user.id,
                slot.start_time,
                slot.end_time,
                booking_date,
                session,
                exclude_booking_id
            ):
                raise AppException(ErrorCode.USER_ALREADY_BOOKED)

            tables.add(table)

        return tables

    async def _validate_guest_number(
            self, guest_number: int
    ):
        if guest_number <= 0:
            raise AppException(ErrorCode.VALIDATION_ERROR)

    async def _validate_cafe(
        self, cafe_id: int, session: AsyncSession
    ) -> Cafe:
        """Валидация кафе."""
        cafe = await self.cafe_repo.get_by_id(cafe_id)
        if not cafe:
            raise NotFoundException(ErrorCode.CAFE_NOT_FOUND)
        if not cafe.active:
            raise AppException(ErrorCode.CAFE_INACTIVE)
        return cafe

    async def __get_booking_or_404(
        self, booking_id: int, session: AsyncSession
    ):
        """Проверить существование бронирования и полчить его."""
        booking = await self.booking_repo.get(
            booking_id=booking_id,
            session=session,
        )
        if booking is None:
            raise NotFoundException(ErrorCode.BOOKING_NOT_FOUND)
        return booking

    async def _check_booking_permissions(
        self,
        session: AsyncSession,
        current_user: User,
        booking: Booking
    ):
        is_manager = await self.user_repo.is_manager(session, current_user.id)

        if not current_user.is_superuser and not is_manager:
            if booking.user_id != current_user.id:
                raise AuthenticationException(
                    ErrorCode.INSUFFICIENT_PERMISSIONS
                )

    def _validate_booking_date(self, booking_date: date):
        """Проверить что дата брони в будущем."""
        if booking_date <= date.today():
            raise AppException(ErrorCode.BOOKING_PAST_DATE)

    async def _validate_table_slot(
        self,
        table_id: int,
        slot_id: int,
        cafe_id: int,
        session: AsyncSession
    ) -> Tuple[Table, Slot]:
        """Валидация стола и слота."""
        table = await self.table_repo.get_by_id(table_id)
        if not table or table.cafe_id != cafe_id:
            raise ValidationException(ErrorCode.TABLE_NOT_FOUND)
        if not table.active:
            raise AppException(ErrorCode.TABLE_INACTIVE)

        slot = await self.slot_repo.get_by_id(slot_id)
        if not slot:
            raise ValidationException(ErrorCode.SLOT_NOT_FOUND)
        if not slot.active:
            raise AppException(ErrorCode.SLOT_INACTIVE)
        return table, slot

    def _calculate_total_seats(self, tables: set) -> int:
        """Подсчитать общее количество мест."""
        return sum(table.seats for table in tables) if tables else 0

    async def _trigger_celery_tasks(
        self,
        booking: Booking,
        user: User,
        cafe: Cafe
    ):
        """Запустить фоновые задачи (уведомления)."""
        # Здесь можно добавить вызов Celery задач
        pass
