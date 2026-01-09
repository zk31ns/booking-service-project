from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dishes.schemas import DishCreate, DishUpdate
from app.models import Dish


class DishRepository:
    """Репозиторий для работы с блюдами."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def get_all(self) -> list[Dish]:
        """Получить все блюда."""
        stmt = select(Dish)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, dish_id: int) -> Dish | None:
        """Получить блюдо по ID."""
        stmt = select(Dish).where(Dish.id == dish_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, dish_data: DishCreate) -> Dish:
        """Создать новое блюдо."""
        dish = Dish(**dish_data.model_dump())
        self.session.add(dish)
        await self.session.flush()
        return dish

    async def update(self, dish_id: int, dish_data: DishUpdate) -> Dish | None:
        """Обновить блюдо."""
        dish = await self.get_by_id(dish_id)
        if not dish:
            return None

        update_data = dish_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dish, field, value)

        await self.session.flush()
        return dish

    async def delete(self, dish_id: int) -> bool:
        """Логическое удаление блюда."""
        dish = await self.get_by_id(dish_id)
        if not dish:
            return False

        dish.active = False
        await self.session.flush()
        return True
