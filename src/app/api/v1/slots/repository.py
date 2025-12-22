from datetime import time
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot import Slot


class SlotRepository:
    """Repository для CRUD операций со слотами."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория."""
        self.session = session

    async def create(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
    ) -> Slot:
        """Создание нового слота.

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
            f'Создан слот id={slot.id} для кафе cafe_id={cafe_id}, '
            f'время: {start_time}-{end_time}'
        )
        return slot

    async def get_by_id(self, slot_id: int) -> Optional[Slot]:
        """Получение слота по ID."""
        query = select(Slot).where(Slot.id == slot_id)
        result = await self.session.execute(query)
        slot = result.scalar_one_or_none()

        if slot:
            logger.info(f'Получен слот id={slot_id}')
        else:
            logger.warning(f'Слот id={slot_id} не найден')

        return slot

    async def get_all_by_cafe(
        self,
        cafe_id: int,
        show_inactive: bool = False,
    ) -> list[Slot]:
        """Получение всех слотов кафе."""
        query = select(Slot).where(Slot.cafe_id == cafe_id)

        if not show_inactive:
            query = query.where(Slot.active.is_(True))

        query = query.order_by(Slot.start_time)
        result = await self.session.execute(query)
        slots = result.scalars().all()

        logger.info(
            f'Получено {len(slots)} слотов для кафе cafe_id={cafe_id} '
            f'(показывать неактивные={show_inactive})'
        )
        return slots

    async def update(
        self,
        slot_id: int,
        cafe_id: int,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        active: Optional[bool] = None,
    ) -> Optional[Slot]:
        """Обновление слота."""
        slot = await self.get_by_id(slot_id)
        if not slot or slot.cafe_id != cafe_id:
            return None

        if start_time is not None:
            slot.start_time = start_time
        if end_time is not None:
            slot.end_time = end_time
        if active is not None:
            slot.active = active

        await self.session.flush()
        return slot

    async def delete(self, slot_id: int, cafe_id: int) -> bool:
        """Логическое удаление слота (установка active=False)."""
        slot = await self.get_by_id(slot_id)
        if not slot or slot.cafe_id != cafe_id:
            return False

        slot.active = False
        await self.session.flush()
        return True
