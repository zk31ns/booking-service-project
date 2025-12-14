from typing import List, Optional
from datetime import time

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.v1.slots.models import Slot
from app.api.v1.slots.repository import SlotRepository
from app.core.exceptions import ConflictException, ValidationException
from app.core.constants import ErrorCode


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

        # 1. Проверка start_time < end_time
        if start_time >= end_time:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                detail="start_time must be less than end_time"
            )

        # 2. Проверка пересечения слотов
        # Получаем слоты ДО создания нового (коммиченные данные)
        existing_slots = await self.repo.get_all_by_cafe(cafe_id, show_inactive=True)
        for slot in existing_slots:
            if self._slots_overlap(slot.start_time, slot.end_time, start_time, end_time):
                raise ConflictException(
                    error_code=ErrorCode.CONFLICT,
                    detail="Slot time range overlaps with existing slot"
                )

        # 3. Создание
        slot = await self.repo.create(cafe_id, start_time, end_time)
        logger.info(
            f"Created slot id={slot.id} for cafe_id={cafe_id}, "
            f"{start_time}-{end_time}"
        )
        return slot

    def _slots_overlap(self, s1_start: time, s1_end: time, s2_start: time, s2_end: time) -> bool:
        """Проверка пересечения двух временных интервалов.

        Два интервала пересекаются, если:
        - Начало второго раньше конца первого И
        - Начало первого раньше конца второго
        """
        return s1_start < s2_end and s2_start < s1_end

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
                detail="start_time must be less than end_time"
            )

        slot = await self.repo.update(slot_id, start_time, end_time, active)
        if slot:
            logger.info(f"Updated slot id={slot_id}")
        return slot

    async def delete_slot(self, slot_id: int) -> bool:
        """Удаление слота."""
        result = await self.repo.delete(slot_id)
        if result:
            logger.info(f"Deleted slot id={slot_id}")
        return result
