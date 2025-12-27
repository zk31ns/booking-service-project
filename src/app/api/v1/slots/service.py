from datetime import time

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.slots.repository import SlotRepository
from app.core.constants import ErrorCode
from app.core.exceptions import ConflictException, ValidationException
from app.models.slots import Slot
from app.repositories.cafes import CafeRepository


class SlotService:
    """Бизнес-логика для слотов."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса слотов.

        Args:
            session: Сессия БД.

        """
        self.session = session
        self.repo = SlotRepository(session)

    async def _validate_cafe_exists(self, cafe_id: int) -> None:
        """Проверка существования кафе.

        Args:
            cafe_id: Идентификатор кафе.

        Raises:
            ValidationException: Если кафе не найдено.

        """
        cafe_repo = CafeRepository(self.session)
        cafe = await cafe_repo.get_by_id(cafe_id)

        if not cafe:
            raise ValidationException(
                error_code=ErrorCode.CAFE_NOT_FOUND,
                detail=f'Кафе с ID {cafe_id} не найдено',
            )

    async def create_slot(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
    ) -> Slot:
        """Создание слота с проверками.

        Args:
            cafe_id: Идентификатор кафе.
            start_time: Время начала слота.
            end_time: Время окончания слота.

        Returns:
            Slot: Созданный слот.

        Raises:
            ValidationException: Если кафе не найдено,
            время некорректно или есть пересечение.

        """
        await self._validate_cafe_exists(cafe_id)
        if start_time >= end_time:
            raise ValidationException(
                error_code=ErrorCode.INVALID_TIME_RANGE,
                detail='Время начала должно быть раньше времени окончания',
            )

        await self._validate_slot_overlap(cafe_id, start_time, end_time)
        slot = await self.repo.create(cafe_id, start_time, end_time)
        logger.info(
            f'Создан слот id={slot.id} для кафе cafe_id={cafe_id}, '
            f'время: {start_time}-{end_time}'
        )
        return slot

    def _slots_overlap(
        self, s1_start: time, s1_end: time, s2_start: time, s2_end: time
    ) -> bool:
        """Проверка пересечения двух временных интервалов.

        Args:
            s1_start: Время начала первого интервала.
            s1_end: Время окончания первого интервала.
            s2_start: Время начала второго интервала.
            s2_end: Время окончания второго интервала.

        Returns:
            bool: True если интервалы пересекаются, иначе False.

        """
        return s1_start < s2_end and s2_start < s1_end

    async def get_slot(self, slot_id: int) -> Slot | None:
        """Получение слота.

        Args:
            slot_id: Идентификатор слота.

        Returns:
            Slot | None: Слот или None если не найден.

        """
        return await self.repo.get_by_id(slot_id)

    async def get_cafe_slots(
        self, cafe_id: int, show_inactive: bool = False
    ) -> list[Slot]:
        """Получение слотов кафе.

        Args:
            cafe_id: Идентификатор кафе.
            show_inactive: Показывать ли неактивные слоты.

        Returns:
            list[Slot]: Список слотов, отсортированный по времени начала.

        """
        return await self.repo.get_all_by_cafe(cafe_id, show_inactive)

    async def update_slot(
        self,
        slot_id: int,
        cafe_id: int,
        start_time: time | None = None,
        end_time: time | None = None,
        active: bool | None = None,
    ) -> Slot | None:
        """Обновление слота.

        Args:
            slot_id: Идентификатор слота.
            cafe_id: Идентификатор кафе (для проверки принадлежности).
            start_time: Новое время начала или None если не изменяется.
            end_time: Новое время окончания или None если не изменяется.
            active: Новый статус активности или None если не изменяется.

        Returns:
            Slot | None: Обновленный слот или None если слот не найден.

        Raises:
            ValidationException: Если время некорректно или есть пересечение.

        """
        slot = await self.repo.get_by_id(slot_id)

        if not slot or slot.cafe_id != cafe_id:
            return None
        final_start = start_time if start_time is not None else slot.start_time
        final_end = end_time if end_time is not None else slot.end_time
        if final_start >= final_end:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                detail='Время начала должно быть раньше времени окончания',
            )

        if start_time is not None or end_time is not None:
            await self._validate_slot_overlap(
                cafe_id, final_start, final_end, exclude_slot_id=slot_id
            )

        if start_time is not None:
            slot.start_time = start_time
        if end_time is not None:
            slot.end_time = end_time
        if active is not None:
            slot.active = active

        await self.session.flush()
        logger.info(f'Обновлен слот id={slot_id}')
        return slot

    async def delete_slot(self, slot_id: int, cafe_id: int) -> bool:
        """Удаление слота (логическое удаление).

        Args:
            slot_id: Идентификатор слота.
            cafe_id: Идентификатор кафе (для проверки принадлежности).

        Returns:
            bool: True если слот успешно удален, False если не найден.

        """
        slot = await self.repo.get_by_id(slot_id)
        if not slot or slot.cafe_id != cafe_id:
            return False

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
        """Проверка пересечения с существующими слотами.

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
                        f'Интервал времени пересекается с существующим слотом '
                        f'(id={slot.id}, {slot.start_time}-{slot.end_time})'
                    ),
                )
