from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dishes.repository import DishRepository
from app.api.v1.dishes.schemas import DishCreate, DishInfo, DishUpdate


class DishService:
    """Сервис для работы с блюдами."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with session."""
        self.repository = DishRepository(session)

    async def get_all_dishes(self) -> list[DishInfo]:
        """Получить все блюда."""
        dishes = await self.repository.get_all()
        return [DishInfo.model_validate(dish) for dish in dishes]

    async def get_dish(self, dish_id: int) -> Optional[DishInfo]:
        """Получить блюдо по ID."""
        dish = await self.repository.get_by_id(dish_id)
        if not dish:
            return None
        return DishInfo.model_validate(dish)

    async def create_dish(self, dish_data: DishCreate) -> DishInfo:
        """Создать новое блюдо."""
        dish = await self.repository.create(dish_data)
        return DishInfo.model_validate(dish)

    async def update_dish(
        self, dish_id: int, dish_data: DishUpdate
    ) -> Optional[DishInfo]:
        """Обновить блюдо."""
        dish = await self.repository.update(dish_id, dish_data)
        if not dish:
            return None
        return DishInfo.model_validate(dish)

    async def delete_dish(self, dish_id: int) -> bool:
        """Удалить блюдо (логическое удаление)."""
        return await self.repository.delete(dish_id)
