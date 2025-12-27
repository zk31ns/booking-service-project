from datetime import time

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slots import Slot


class SlotRepository:
    """Repository для CRUD операций со слотами."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория.

        Args:
            session: Сессия БД.

        """
        self.session = session

    async def create(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
    ) -> Slot:
        """Создание нового слота.

        Args:
            cafe_id: Идентификатор кафе.
            start_time: Время начала слота.
            end_time: Время окончания слота.

        Returns:
            Slot: Созданный слот.

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

    async def get_by_id(self, slot_id: int) -> Slot | None:
        """Получение слота по ID.

        Args:
            slot_id: Идентификатор слота.

        Returns:
            Slot | None: Слот или None если не найден.

        """
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
        """Получение всех слотов кафе.

        Args:
            cafe_id: Идентификатор кафе.
            show_inactive: Показывать ли неактивные слоты. По умолчанию False.

        Returns:
            list[Slot]: Список слотов, отсортированный по времени начала.

        """
        query = select(Slot).where(Slot.cafe_id == cafe_id)

        if not show_inactive:
            query = query.where(Slot.active.is_(True))

        query = query.order_by(Slot.start_time)
        result = await self.session.execute(query)
        slots = list(result.scalars().all())

        logger.info(
            f'Получено {len(slots)} слотов для кафе cafe_id={cafe_id} '
            f'(показывать неактивные={show_inactive})'
        )
        return slots

    async def update(
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

        """
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
        """Логическое удаление слота.

        Args:
            slot_id: Идентификатор слота.
            cafe_id: Идентификатор кафе (для проверки принадлежности).

        Returns:
            bool: True если слот успешно удален, False если не найден.

        """
        slot = await self.get_by_id(slot_id)
        if not slot or slot.cafe_id != cafe_id:
            return False

        slot.active = False
        await self.session.flush()
        return True
