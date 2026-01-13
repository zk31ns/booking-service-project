from datetime import time
from zoneinfo import ZoneInfo

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode, Messages
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.slots import Slot
from app.repositories.cafes import CafeRepository
from app.repositories.slot import SlotRepository


class SlotService:
    """Бизнес-логика для слотов."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса слотов.

        Args:
            session: Сессия БД.

        """
        self.session = session
        self.repo = SlotRepository(session)

    def _normalize_time(self, t: time) -> time:
        """Приводит объект time к UTC."""
        return t.replace(tzinfo=ZoneInfo('UTC')) if t.tzinfo is None else t

    async def _validate_cafe_exists(self, cafe_id: int) -> None:
        """Проверяет существование кафе.

        Args:
            cafe_id: Идентификатор кафе.

        Raises:
            NotFoundException: Если кафе не найдено.

        """
        await self._get_cafe(cafe_id, allow_inactive=False)

    async def _get_cafe(self, cafe_id: int, allow_inactive: bool) -> object:
        """Получить кафе с проверкой активности."""
        cafe_repo = CafeRepository(self.session)
        cafe = await cafe_repo.get(cafe_id)

        if not cafe or (not allow_inactive and not cafe.active):
            raise NotFoundException(
                ErrorCode.CAFE_NOT_FOUND,
                extra={'cafe_id': cafe_id},
            )
        return cafe

    async def create_slot(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
        description: str | None = None,
    ) -> Slot:
        """Создает слот с проверками.

        Args:
            cafe_id: Идентификатор кафе.
            start_time: Время начала слота.
            end_time: Время окончания слота.
            description: Описание слота или None.

        Returns:
            Slot: Созданный слот.

        Raises:
            NotFoundException: Если кафе не найдено.
            ValidationException: Если время некорректно.
            ConflictException: Если найдено пересечение со слотом.

        """
        await self._validate_cafe_exists(cafe_id)
        start_time = self._normalize_time(start_time)
        end_time = self._normalize_time(end_time)
        if start_time >= end_time:
            raise ValidationException(
                error_code=ErrorCode.INVALID_TIME_RANGE,
                detail=Messages.errors[ErrorCode.INVALID_TIME_RANGE],
            )

        await self._validate_slot_overlap(cafe_id, start_time, end_time)
        slot = await self.repo.create(
            cafe_id,
            start_time,
            end_time,
            description=description,
        )
        slot_id = slot.id
        slot = await self.repo.get(slot_id)
        if slot is None:
            raise NotFoundException(
                ErrorCode.SLOT_NOT_FOUND,
                extra={'slot_id': slot_id},
            )
        logger.info(
            f'Создан слот id={slot.id} для кафе cafe_id={cafe_id}, '
            f'время: {start_time}-{end_time}'
        )
        return slot

    def _slots_overlap(
        self, s1_start: time, s1_end: time, s2_start: time, s2_end: time
    ) -> bool:
        """Проверяет пересечение двух временных интервалов.

        Args:
            s1_start: Время начала первого интервала.
            s1_end: Время окончания первого интервала.
            s2_start: Время начала второго интервала.
            s2_end: Время окончания второго интервала.

        Returns:
            bool: True если интервалы пересекаются, иначе False.

        """
        s1_start = self._normalize_time(s1_start)
        s1_end = self._normalize_time(s1_end)
        s2_start = self._normalize_time(s2_start)
        s2_end = self._normalize_time(s2_end)
        return s1_start < s2_end and s2_start < s1_end

    async def get_slot(
        self,
        cafe_id: int,
        slot_id: int,
        allow_inactive: bool = False,
    ) -> Slot:
        """Получает слот.

        Args:
            cafe_id: Идентификатор кафе.
            slot_id: Идентификатор слота.
            allow_inactive: Разрешить неактивные слоты и кафе.

        Returns:
            Slot: Найденный слот.

        Raises:
            NotFoundException: Если слот не найден или не принадлежит кафе.

        """
        await self._get_cafe(cafe_id, allow_inactive=allow_inactive)
        slot = await self.repo.get(slot_id)
        if (
            not slot
            or slot.cafe_id != cafe_id
            or (not allow_inactive and not slot.active)
        ):
            raise NotFoundException(
                ErrorCode.SLOT_NOT_FOUND,
                extra={'slot_id': slot_id},
            )
        return slot

    async def get_cafe_slots(
        self,
        cafe_id: int,
        show_inactive: bool = False,
        allow_inactive_cafe: bool = False,
    ) -> list[Slot]:
        """Получает слоты кафе.

        Args:
            cafe_id: Идентификатор кафе.
            show_inactive: Показывать ли неактивные слоты.
            allow_inactive_cafe: Разрешить неактивные кафе.

        Returns:
            list[Slot]: Список слотов, отсортированный по времени начала.

        Raises:
            NotFoundException: Если кафе не найдено.

        """
        await self._get_cafe(cafe_id, allow_inactive=allow_inactive_cafe)
        return await self.repo.get_all_by_cafe(cafe_id, show_inactive)

    async def update_slot(
        self,
        slot_id: int,
        cafe_id: int,
        start_time: time | None = None,
        end_time: time | None = None,
        description: str | None = None,
        active: bool | None = None,
    ) -> Slot:
        """Обновляет слот.

        Args:
            slot_id: Идентификатор слота.
            cafe_id: Идентификатор кафе (для проверки принадлежности).
            start_time: Новое время начала или None если не изменяется.
            end_time: Новое время окончания или None если не изменяется.
            description: Новое описание или None если не изменяется.
            active: Новый статус активности или None если не изменяется.

        Returns:
            Slot: Обновленный слот.

        Raises:
            NotFoundException: Если слот не найден или не принадлежит кафе.
            ValidationException: Если время некорректно.
            ConflictException: Если найдено пересечение со слотом.

        """
        slot = await self.repo.get(slot_id)
        if not slot or slot.cafe_id != cafe_id:
            raise NotFoundException(
                ErrorCode.SLOT_NOT_FOUND,
                extra={'slot_id': slot_id},
            )

        final_start = self._normalize_time(
            start_time if start_time is not None else slot.start_time
        )
        final_end = self._normalize_time(
            end_time if end_time is not None else slot.end_time
        )

        if final_start >= final_end:
            raise ValidationException(
                error_code=ErrorCode.INVALID_TIME_RANGE,
                detail=Messages.errors[ErrorCode.INVALID_TIME_RANGE],
            )

        if start_time is not None or end_time is not None:
            await self._validate_slot_overlap(
                cafe_id, final_start, final_end, exclude_slot_id=slot_id
            )

        if start_time is not None:
            slot.start_time = start_time
        if end_time is not None:
            slot.end_time = end_time
        if description is not None:
            slot.description = description
        if active is not None:
            slot.active = active

        await self.session.flush()
        slot = await self.repo.get(slot_id)
        if slot is None:
            raise NotFoundException(
                ErrorCode.SLOT_NOT_FOUND,
                extra={'slot_id': slot_id},
            )
        logger.info(f'Обновлен слот id={slot_id}')
        return slot

    async def delete_slot(self, slot_id: int, cafe_id: int) -> bool:
        """Удаляет слот (логическое удаление).

        Args:
            slot_id: Идентификатор слота.
            cafe_id: Идентификатор кафе (для проверки принадлежности).

        Returns:
            bool: True если слот успешно деактивирован.

        Raises:
            NotFoundException: Если слот не найден или не принадлежит кафе.

        """
        slot = await self.repo.get(slot_id)
        if not slot or slot.cafe_id != cafe_id:
            raise NotFoundException(
                ErrorCode.SLOT_NOT_FOUND,
                extra={'slot_id': slot_id},
            )

        slot.active = False
        await self.session.flush()
        logger.info(f'Удален (деактивирован) слот id={slot_id}')
        return True

    async def _validate_slot_overlap(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
        exclude_slot_id: int | None = None,
    ) -> None:
        """Проверяет пересечение с существующими слотами.

        Args:
            cafe_id: Идентификатор кафе.
            start_time: Время начала проверяемого интервала.
            end_time: Время окончания проверяемого интервала.
            exclude_slot_id: ID слота, который исключить из проверки.

        Raises:
            ConflictException: Если найдено пересечение с существующим слотом.

        """
        existing_slots = await self.repo.get_all_by_cafe(
            cafe_id, show_inactive=False
        )

        for slot in existing_slots:
            if exclude_slot_id and slot.id == exclude_slot_id:
                continue

            if self._slots_overlap(
                slot.start_time, slot.end_time, start_time, end_time
            ):
                raise ConflictException(
                    error_code=ErrorCode.SLOT_OVERLAP,
                    detail=(
                        'Интервал времени пересекается с существующим слотом '
                        f'(id={slot.id}, {slot.start_time}-{slot.end_time})'
                    ),
                )
