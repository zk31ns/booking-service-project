from typing import Optional
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.v1.slots.models import Slot


class SlotRepository:
    """Repository для CRUD операций со слотами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========== CREATE ==========
    async def create(
            self,
            cafe_id: int,
            start_time: time,
            end_time: time,
    ) -> Slot:
        """
        Создание нового слота.
        TODO: Добавить проверку активности кафе когда модель Cafe будет готова.
        """
        slot = Slot(
            cafe_id=cafe_id,
            start_time=start_time,
            end_time=end_time,
        )
        self.session.add(slot)
        await self.session.flush()

        logger.info(
            f'Created slot id={slot.id} for cafe_id={cafe_id}, '
            f'{start_time}-{end_time}'
        )
        return slot

    # ========== READ ==========
    async def get_by_id(self, slot_id: int) -> Optional[Slot]:
        """Получение слота по ID."""
        query = select(Slot).where(Slot.id == slot_id)
        result = await self.session.execute(query)
        slot = result.scalar_one_or_none()

        if slot:
            logger.info(f"Retrieved slot id={slot_id}")
        else:
            logger.warning(f"Slot id={slot_id} not found")

        return slot

    async def get_all_by_cafe(
            self,
            cafe_id: int,
            show_inactive: bool = False,
    ) -> list[Slot]:
        """Получение всех слотов кафе."""
        query = select(Slot).where(Slot.cafe_id == cafe_id)

        if not show_inactive:
            query = query.where(Slot.active is True)

        query = query.order_by(Slot.start_time)
        result = await self.session.execute(query)
        slots = result.scalars().all()

        logger.info(
            f'Retrieved {len(slots)} slots for cafe_id={cafe_id} '
            f'(show_inactive={show_inactive})'
        )
        return slots

    async def update(
            self,
            slot_id: int,
            start_time: Optional[time] = None,
            end_time: Optional[time] = None,
            active: Optional[bool] = None,
    ) -> Optional[Slot]:
        """Обновление слота."""
        slot = await self.get_by_id(slot_id)
        if not slot:
            return None

        if start_time is not None:
            slot.start_time = start_time
        if end_time is not None:
            slot.end_time = end_time
        if active is not None:
            slot.active = active

        await self.session.flush()

        logger.info(
            f'Updated slot id={slot_id}: '
            f'start_time={start_time}, end_time={end_time}, active={active}'
        )
        return slot

    async def delete(self, slot_id: int) -> bool:
        """Логическое удаление слота (установка active=False)."""
        slot = await self.get_by_id(slot_id)
        if not slot:
            return False

        slot.active = False
        await self.session.flush()

        logger.info(f'Deleted (deactivated) slot id={slot_id}')
        return True
