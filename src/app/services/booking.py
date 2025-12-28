from datetime import date
from typing import Any, List, Optional, Tuple, Union

from app.api.v1.booking.schemas import (
    BookingCreate,
    BookingUpdate,
    TableSlotSchema,
)
from app.api.v1.users.repository import UserRepository
from app.core.constants import (
    BookingRules,
    BookingStatus,
    ErrorCode,
    UserRole,
)
from app.core.exceptions import (
    AppException,
    AuthenticationException,
    NotFoundException,
    ValidationException,
)
from app.models import Booking, Cafe, Slot, Table, User
from app.repositories import (
    BookingRepository,
    CafeRepository,
    TableRepository,
)
from app.repositories.slot import SlotRepository


class BookingService:
    """Сервис для управления бронированиями."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        cafe_repo: CafeRepository,
        user_repo: UserRepository,
        table_repo: TableRepository,
        slot_repo: SlotRepository,
    ) -> None:
        """Инициализирует сервис бронирования.

        Args:
            booking_repo: Репозиторий для работы с бронированиями
            cafe_repo: Репозиторий для работы с кафе
            user_repo: Репозиторий для работы с пользователями
            table_repo: Репозиторий для работы со столами
            slot_repo: Репозиторий для работы со слотами времени

        """
        self.booking_repo = booking_repo
        self.cafe_repo = cafe_repo
        self.user_repo = user_repo
        self.table_repo = table_repo
        self.slot_repo = slot_repo

    async def create_booking(
        self,
        booking_in: BookingCreate,
        user: User,
    ) -> Booking:
        """Создать новое бронирование.

        Args:
            booking_in: Данные для создания бронирования
            user: Пользователь, создающий бронирование

        Returns:
            Созданное бронирование

        Raises:
            AppException: Если дата бронирования в прошлом
            NotFoundException: Если кафе не найдено
            ValidationException: Если данные невалидны
            AppException: Если недостаточно мест или стол занят

        """
        self._validate_booking_date(booking_in.booking_date)

        cafe = await self._validate_cafe(booking_in.cafe_id)

        tables = await self._validate_new_table_slots(
            table_slots=booking_in.table_slots,
            cafe_id=booking_in.cafe_id,
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
            user=user,
        )

        await self._trigger_celery_tasks(booking, user, cafe)

        return booking

    async def get_all_bookings(
        self,
        current_user: User,
        show_all: bool = True,
        cafe_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> List[Booking]:
        """Получить список бронирований с учетом прав доступа.

        Для суперюзеров и менеджеров: все бронирования с возможностью
        фильтрации.
        Для обычных пользователей: только свои бронирования.

        Args:
            current_user: Текущий пользователь
            show_all: Показывать все бронирования (True) или
            только свои (False)
            cafe_id: ID кафе для фильтрации
            user_id: ID пользователя для фильтрации

        Returns:
            Список бронирований

        Raises:
            AuthenticationException: Если недостаточно прав

        """
        is_manager = await self.user_repo.is_manager(user_id=current_user.id)
        if (not current_user.is_superuser and not is_manager) or not show_all:
            user_id = current_user.id

        return await self.booking_repo.get_multi(
            user_id=user_id,
            cafe_id=cafe_id,
        )

    async def get_booking(
        self, current_user: User, booking_id: int
    ) -> Booking:
        """Получить бронирование по ID.

        Args:
            current_user: Текущий пользователь
            booking_id: ID бронирования

        Returns:
            Найденное бронирование

        Raises:
            NotFoundException: Если бронирование не найдено
            AuthenticationException: Если недостаточно прав

        """
        booking = await self.__get_booking_or_404(booking_id=booking_id)

        await self._check_booking_permissions(
            current_user=current_user, booking=booking
        )
        return booking

    async def update_booking(
        self,
        update_booking: BookingUpdate,
        booking_id: int,
        current_user: User,
    ) -> Booking:
        """Обновить существующее бронирование.

        Проверяет права доступа, валидирует данные и применяет бизнес-правила.

        Args:
            update_booking: Данные для обновления
            booking_id: ID обновляемого бронирования
            current_user: Текущий пользователь

        Returns:
            Обновленное бронирование

        Raises:
            NotFoundException: Если бронирование не найдено
            AppException: Если бронирование неактивно
            AppException: Если неверный переход статуса
            AuthenticationException: Если недостаточно прав
            ValidationException: Если данные невалидны

        """
        booking = await self.__get_booking_or_404(booking_id)

        user_role = self._get_user_role(current_user)

        if not booking.is_active and user_role != UserRole.ADMIN:
            raise AppException(ErrorCode.BOOKING_INACTIVE)

        update_data: dict[str, Union[int, str, date, bool]] = {}

        if update_booking.status is not None:
            await self._process_status_update(
                booking=booking,
                new_status_value=update_booking.status,
                user_role=user_role,
                update_data=update_data,
                current_user=current_user,
            )

        if update_booking.is_active is not None:
            await self._process_active_update(
                booking=booking,
                requested_active=update_booking.is_active,
                user_role=user_role,
                update_data=update_data,
                new_status=update_booking.status,
            )

        await self._check_booking_permissions(
            current_user=current_user, booking=booking
        )

        booking_date = booking.booking_date
        cafe_id = booking.cafe_id
        guest_number = booking.guest_number

        if update_booking.booking_date is not None:
            self._validate_booking_date(update_booking.booking_date)
            update_data['booking_date'] = update_booking.booking_date
            booking_date = update_booking.booking_date

        if update_booking.cafe_id is not None:
            await self._validate_cafe(update_booking.cafe_id)
            update_data['cafe_id'] = update_booking.cafe_id
            cafe_id = update_booking.cafe_id

        if update_booking.guest_number is not None:
            await self._validate_guest_number(update_booking.guest_number)
            update_data['guest_number'] = update_booking.guest_number
            guest_number = update_booking.guest_number

        if update_booking.table_slots is not None:
            table_slots: list[Any] = update_booking.table_slots
        else:
            table_slots = booking.table_slots

        validate_tables = any(
            key in update_data for key in ['booking_date', 'cafe_id']
        )

        if validate_tables or update_booking.table_slots is not None:
            await self._validate_new_table_slots(
                table_slots=table_slots,
                cafe_id=cafe_id,
                booking_date=booking_date,
                user=current_user,
                guest_number=guest_number,
                exclude_booking_id=booking.id,
            )

        if update_booking.note is not None:
            update_data['note'] = update_booking.note

        return await self.booking_repo.update(
            booking=booking, update_booking=update_booking, data=update_data
        )

    async def _validate_new_table_slots(
        self,
        table_slots: List[TableSlotSchema],
        cafe_id: int,
        booking_date: date,
        user: User,
        guest_number: Optional[int] = None,
        exclude_booking_id: Optional[int] = None,
    ) -> set:
        """Валидировать связки столов и временных слотов.

        Проверяет существование таблиц и слотов, их принадлежность кафе,
        доступность столов на указанную дату и занятость пользователя.

        Args:
            table_slots: Список связок стол+слот
            cafe_id: ID кафе
            booking_date: Дата бронирования
            user: Пользователь, для которого проверяется занятость
            guest_number: Количество гостей (опционально)
            exclude_booking_id: ID бронирования для исключения из проверки

        Returns:
            Множество валидных столов

        Raises:
            ValidationException: Если стол или слот не найдены
            AppException: Если стол уже занят
            AppException: Если пользователь уже имеет бронь на это время

        """
        tables = set()
        for table_slot in table_slots:
            table_id, slot_id = table_slot.table_id, table_slot.slot_id

            table, slot = await self._validate_table_slot(
                table_id, slot_id, cafe_id
            )

            if await self.booking_repo.is_occupied(
                table_id, slot_id, booking_date, exclude_booking_id
            ):
                raise AppException(ErrorCode.TABLE_ALREADY_BOOKED)

            if await self.booking_repo.user_is_busy(
                user.id,
                slot.start_time,
                slot.end_time,
                booking_date,
                exclude_booking_id,
            ):
                raise AppException(ErrorCode.USER_ALREADY_BOOKED)

            tables.add(table)

        return tables

    async def _validate_guest_number(self, guest_number: int) -> None:
        """Валидировать количество гостей.

        Args:
            guest_number: Количество гостей

        Raises:
            AppException: Если количество гостей <= 0

        """
        if guest_number <= 0:
            raise AppException(ErrorCode.VALIDATION_ERROR)

    async def _validate_cafe(self, cafe_id: int) -> Cafe:
        """Валидировать существование и активность кафе.

        Args:
            cafe_id: ID кафе

        Returns:
            Найденное кафе

        Raises:
            NotFoundException: Если кафе не найдено
            AppException: Если кафе неактивно

        """
        cafe = await self.cafe_repo.get_by_id(cafe_id)
        if not cafe:
            raise NotFoundException(ErrorCode.CAFE_NOT_FOUND)
        if not cafe.active:
            raise AppException(ErrorCode.CAFE_INACTIVE)
        return cafe

    async def __get_booking_or_404(self, booking_id: int) -> Booking:
        """Получить бронирование или выбросить исключение если не найдено.

        Args:
            booking_id: ID бронирования

        Returns:
            Найденное бронирование

        Raises:
            NotFoundException: Если бронирование не найдено

        """
        booking = await self.booking_repo.get(booking_id=booking_id)
        if booking is None:
            raise NotFoundException(ErrorCode.BOOKING_NOT_FOUND)
        return booking

    async def _is_manager(
        self,
        current_user: User,
    ) -> bool:
        """Проверить является ли пользователь менеджером.

        Args:
            current_user: Пользователь для проверки

        Returns:
            True если пользователь менеджер, иначе False

        """
        return await self.user_repo.is_manager(user_id=current_user.id)

    async def _check_booking_permissions(
        self, current_user: User, booking: Booking
    ) -> None:
        """Проверить права доступа к бронированию.

        Суперюзеры и менеджеры имеют доступ ко всем бронированиям.
        Обычные пользователи имеют доступ только к своим бронированиям.

        Args:
            current_user: Текущий пользователь
            booking: Бронирование для проверки

        Raises:
            AuthenticationException: Если недостаточно прав

        """
        if not current_user.is_superuser and not await self._is_manager(
            current_user
        ):
            if booking.user_id != current_user.id:
                raise AuthenticationException(
                    ErrorCode.INSUFFICIENT_PERMISSIONS
                )

    def _validate_booking_date(self, booking_date: date) -> None:
        """Проверить что дата бронирования в будущем.

        Args:
            booking_date: Дата для проверки

        Raises:
            AppException: Если дата в прошлом или сегодня

        """
        if booking_date <= date.today():
            raise AppException(ErrorCode.BOOKING_PAST_DATE)

    async def _validate_table_slot(
        self, table_id: int, slot_id: int, cafe_id: int
    ) -> Tuple[Table, Slot]:
        """Валидировать связку стол+слот.

        Args:
            table_id: ID стола
            slot_id: ID слота времени
            cafe_id: ID кафе для проверки принадлежности

        Returns:
            Кортеж (стол, слот)

        Raises:
            ValidationException: Если стол или слот не найдены
            AppException: Если стол или слот неактивны

        """
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
        """Подсчитать общее количество мест у столов.

        Args:
            tables: Множество столов

        Returns:
            Суммарное количество мест

        """
        return sum(table.seats for table in tables) if tables else 0

    def _get_user_role(self, user: User) -> UserRole:
        """Определить роль пользователя.

        Args:
            user: Пользователь для определения роли

        Returns:
            Роль пользователя

        """
        if user.is_superuser:
            return UserRole.ADMIN
        if self._is_manager(current_user=user):
            return UserRole.MANAGER
        return UserRole.CUSTOMER

    async def _process_status_update(
        self,
        booking: Booking,
        new_status_value: str,
        user_role: UserRole,
        update_data: dict,
        current_user: User,
    ) -> None:
        """Обработать изменение статуса бронирования.

        Проверяет разрешенные переходы статусов и устанавливает
        автоматическое значение is_active на основе нового статуса.

        Args:
            booking: Обновляемое бронирование
            new_status_value: Новое значение статуса
            user_role: Роль пользователя
            update_data: Словарь для накопления данных обновления
            current_user: Текущий пользователь

        Raises:
            AppException: Если переход статуса запрещен

        """
        current_status = BookingStatus(booking.status)
        new_status = BookingStatus(new_status_value)

        allowed_transitions = BookingRules.STATUS_TRANSITIONS[user_role].get(
            current_status, set()
        )

        if new_status not in allowed_transitions:
            raise AppException(ErrorCode.INVALID_STATUS_TRANSITION)

        update_data['status'] = new_status_value

        if 'is_active' not in update_data:
            update_data['is_active'] = (
                new_status in BookingRules.ACTIVE_STATUSES
            )

    async def _process_active_update(
        self,
        booking: Booking,
        requested_active: bool,
        user_role: UserRole,
        update_data: dict,
        new_status: Optional[str],
    ) -> None:
        """Обработать изменение активности бронирования.

        Правила:
        - Нельзя деактивировать активные статусы (PENDING, CONFIRMED)
        - Нельзя активировать неактивные статусы (CANCELLED, COMPLETED)
          кроме администратора

        Args:
            booking: Обновляемое бронирование
            requested_active: Запрашиваемое значение активности
            user_role: Роль пользователя
            update_data: Словарь для накопления данных обновления
            new_status: Новый статус

        Raises:
            AppException: Если запрос противоречит бизнес-правилам

        """
        status = new_status if new_status is not None else booking.status
        status_enum = BookingStatus(status)

        if requested_active:
            if (
                status_enum in BookingRules.INACTIVE_STATUSES
                and user_role != UserRole.ADMIN
            ):
                raise AppException(ErrorCode.CANNOT_ACTIVATE_INACTIVE_STATUS)

        else:
            if status_enum in BookingRules.ACTIVE_STATUSES:
                raise AppException(ErrorCode.CANNOT_DEACTIVATE_ACTIVE_STATUS)

        update_data['is_active'] = requested_active

    async def _trigger_celery_tasks(
        self, booking: Booking, user: User, cafe: Cafe
    ) -> None:
        """Запустить фоновые Celery задачи.

        Args:
            booking: Созданное бронирование
            user: Пользователь, создавший бронирование
            cafe: Кафе, для которого создано бронирование

        """
        # Здесь можно добавить вызов Celery задач
        pass
