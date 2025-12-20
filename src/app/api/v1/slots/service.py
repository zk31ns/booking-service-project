from datetime import time
from typing import TYPE_CHECKING, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.v1.slots.repository import SlotRepository
from src.app.core.constants import ErrorCode
from src.app.core.exceptions import ConflictException, ValidationException
from src.app.models.slot import Slot

if TYPE_CHECKING:
    from src.app.api.v1.cafes.repository import CafeRepository


class SlotService:
    """Бизнес-логика для слотов."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса слотов."""
        self.session = session
        self.repo = SlotRepository(session)

    async def _validate_cafe_exists(self, cafe_id: int) -> None:
        """Проверка существования кафе."""
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
        """Создание слота с проверками."""
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
        """Проверка пересечения двух временных интервалов."""
        return s1_start < s2_end and s2_start < s1_end

    async def get_slot(self, slot_id: int) -> Optional[Slot]:
        """Получение слота."""
        return await self.repo.get_by_id(slot_id)

    async def get_cafe_slots(
        self, cafe_id: int, show_inactive: bool = False
    ) -> list[Slot]:
        """Получение слотов кафе."""
        return await self.repo.get_all_by_cafe(cafe_id, show_inactive)

    async def update_slot(
        self,
        slot_id: int,
        cafe_id: int,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        active: Optional[bool] = None,
    ) -> Optional[Slot]:
        """Обновление слота."""
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
        """Удаление слота."""
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
        exclude_slot_id: Optional[int] = None,
    ) -> None:
        """Проверка пересечения с существующими слотами."""
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
