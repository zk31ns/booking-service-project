from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dishes.schemas import DishCreate, DishUpdate
from app.models import Cafe, Dish


class DishRepository:
    """Репозиторий для работы с блюдами."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализировать репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        self.session = session

    async def get_all(
        self, show_all: bool = False, cafe_id: int | None = None
    ) -> list[Dish]:
        """Получить список блюд.

        Args:
            show_all: Возвращать неактивные блюда.
            cafe_id: Фильтр по ID кафе.

        Returns:
            list[Dish]: Список блюд.

        """
        stmt = select(Dish)
        if not show_all:
            stmt = stmt.where(Dish.active)
        if cafe_id is not None:
            stmt = stmt.join(Dish.cafes).where(Cafe.id == cafe_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, dish_id: int) -> Dish | None:
        """Получить блюдо по ID.

        Args:
            dish_id: Идентификатор блюда.

        Returns:
            Dish | None: Блюдо или None.

        """
        stmt = select(Dish).where(Dish.id == dish_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, dish_data: DishCreate, cafes: list['Cafe']) -> Dish:
        """Создать блюдо и привязать к кафе.

        Args:
            dish_data: Данные для создания блюда.
            cafes: Список кафе для привязки.

        Returns:
            Dish: Созданное блюдо.

        """
        payload = dish_data.model_dump()
        payload.pop('cafes_id', None)
        if payload.get('photo_id') is not None:
            payload['photo_id'] = str(payload['photo_id'])
        dish = Dish(**payload)
        dish.cafes = cafes
        self.session.add(dish)
        await self.session.flush()
        return dish

    async def update(
        self,
        dish_id: int,
        dish_data: DishUpdate,
        cafes: list['Cafe'] | None,
    ) -> Dish | None:
        """Обновить блюдо.

        Args:
            dish_id: Идентификатор блюда.
            dish_data: Данные для обновления.
            cafes: Список кафе для привязки (если передан).

        Returns:
            Dish | None: Обновленное блюдо или None.

        """
        dish = await self.get_by_id(dish_id)
        if not dish:
            return None

        update_data = dish_data.model_dump(exclude_unset=True)
        update_data.pop('cafes_id', None)
        if update_data.get('photo_id') is not None:
            update_data['photo_id'] = str(update_data['photo_id'])
        for field, value in update_data.items():
            setattr(dish, field, value)
        if cafes is not None:
            dish.cafes = cafes

        await self.session.flush()
        return dish

    async def delete(self, dish_id: int) -> bool:
        """Деактивировать блюдо.

        Args:
            dish_id: Идентификатор блюда.

        Returns:
            bool: True, если блюдо деактивировано.

        """
        dish = await self.get_by_id(dish_id)
        if not dish:
            return False

        dish.active = False
        await self.session.flush()
        return True


if TYPE_CHECKING:
    from app.models import Cafe
