from datetime import time
from typing import List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.slots.models import Slot
from app.api.v1.slots.repository import SlotRepository
from app.core.constants import ErrorCode
from app.core.exceptions import ConflictException, ValidationException


class SlotService:
    """Бизнес-логика для слотов."""

    def __init__(self, session: AsyncSession):
        self.repo = SlotRepository(session)

    async def create_slot(
            self,
            cafe_id: int,
            start_time: time,
            end_time: time,
    ) -> Slot:
        """Создание слота с проверками."""
        if start_time >= end_time:
            raise ValidationException(
                error_code=ErrorCode.INVALID_TIME_RANGE,
                detail='Время начала должно быть раньше времени окончания'
            )

        existing_slots = await self.repo.get_all_by_cafe(cafe_id, show_inactive=True)
        for slot in existing_slots:
            if self._slots_overlap(slot.start_time, slot.end_time, start_time, end_time):
                raise ConflictException(
                    error_code=ErrorCode.SLOT_OVERLAP,
                    detail='Интервал времени пересекается с существующим слотом'
                )

        slot = await self.repo.create(cafe_id, start_time, end_time)
        logger.info(
            f'Создан слот id={slot.id} для кафе cafe_id={cafe_id}, '
            f'время: {start_time}-{end_time}'
        )
        return slot

    def _slots_overlap(self, s1_start: time, s1_end: time, s2_start: time, s2_end: time) -> bool:
        """Проверка пересечения двух временных интервалов."""
        t1_start = s1_start.replace(tzinfo=None)
        t1_end = s1_end.replace(tzinfo=None)
        t2_start = s2_start.replace(tzinfo=None)
        t2_end = s2_end.replace(tzinfo=None)

        return t1_start < t2_end and t2_start < t1_end

    async def get_slot(self, slot_id: int) -> Optional[Slot]:
        """Получение слота."""
        return await self.repo.get_by_id(slot_id)

    async def get_cafe_slots(self, cafe_id: int, show_inactive: bool = False) -> List[Slot]:
        """Получение слотов кафе."""
        return await self.repo.get_all_by_cafe(cafe_id, show_inactive)

    async def update_slot(
            self,
            slot_id: int,
            start_time: Optional[time] = None,
            end_time: Optional[time] = None,
            active: Optional[bool] = None,
    ) -> Optional[Slot]:
        """Обновление слота."""
        if start_time is not None and end_time is not None and start_time >= end_time:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                detail='Время начала должно быть раньше времени окончания'
            )

        slot = await self.repo.update(slot_id, start_time, end_time, active)
        if slot:
            logger.info(f'Обновлен слот id={slot_id}')
        return slot

    async def delete_slot(self, slot_id: int) -> bool:
        """Удаление слота."""
        result = await self.repo.delete(slot_id)
        if result:
            logger.info(f'Удален слот id={slot_id}')
        return result
