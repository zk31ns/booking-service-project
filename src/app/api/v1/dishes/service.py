from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dishes.repository import DishRepository
from app.api.v1.dishes.schemas import DishCreate, DishInfo, DishUpdate
from app.models import Cafe


class DishService:
    """Сервис для работы с блюдами."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализировать сервис.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        self.repository = DishRepository(session)

    async def get_all_dishes(
        self, show_all: bool = False, cafe_id: int | None = None
    ) -> list[DishInfo]:
        """Получить список блюд.

        Args:
            show_all: Возвращать неактивные блюда.
            cafe_id: Фильтр по ID кафе.

        Returns:
            list[DishInfo]: Список блюд.

        """
        dishes = await self.repository.get_all(
            show_all=show_all, cafe_id=cafe_id
        )
        return [DishInfo.model_validate(dish) for dish in dishes]

    async def get_dish(self, dish_id: int) -> DishInfo | None:
        """Получить блюдо по ID.

        Args:
            dish_id: Идентификатор блюда.

        Returns:
            DishInfo | None: Блюдо или None.

        """
        dish = await self.repository.get_by_id(dish_id)
        if not dish:
            return None
        return DishInfo.model_validate(dish)

    async def create_dish(self, dish_data: DishCreate) -> DishInfo:
        """Создать блюдо.

        Args:
            dish_data: Данные для создания блюда.

        Returns:
            DishInfo: Созданное блюдо.

        """
        cafes = await self._get_cafes(dish_data.cafes_id)
        dish = await self.repository.create(dish_data, cafes)
        return DishInfo.model_validate(dish)

    async def update_dish(
        self, dish_id: int, dish_data: DishUpdate
    ) -> DishInfo | None:
        """Обновить блюдо.

        Args:
            dish_id: Идентификатор блюда.
            dish_data: Данные для обновления.

        Returns:
            DishInfo | None: Обновленное блюдо или None.

        """
        cafes = None
        if dish_data.cafes_id is not None:
            cafes = await self._get_cafes(dish_data.cafes_id)
        dish = await self.repository.update(dish_id, dish_data, cafes)
        if not dish:
            return None
        return DishInfo.model_validate(dish)

    async def delete_dish(self, dish_id: int) -> bool:
        """Деактивировать блюдо.

        Args:
            dish_id: Идентификатор блюда.

        Returns:
            bool: True, если блюдо деактивировано.

        """
        return await self.repository.delete(dish_id)

    async def _get_cafes(self, cafes_id: list[int]) -> list[Cafe]:
        """Получить список кафе по идентификаторам.

        Args:
            cafes_id: Список ID кафе.

        Returns:
            list[Cafe]: Список кафе.

        Raises:
            HTTPException: Если хотя бы одно кафе не найдено.

        """
        if not cafes_id:
            return []
        stmt = select(Cafe).where(Cafe.id.in_(cafes_id))
        result = await self.repository.session.execute(stmt)
        cafes = list(result.scalars().all())
        if len(cafes) != len(set(cafes_id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Cafe not found',
            )
        return cafes
