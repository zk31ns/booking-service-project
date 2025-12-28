from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.constants import Limits
from src.app.models.cafes import Cafe
from src.app.repositories.base import BaseCRUD
from src.app.schemas.cafes import CafeCreate, CafeUpdate


class CafeRepository(BaseCRUD[Cafe]):
    """Репозиторий для работы с кафе."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория кафе.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        super().__init__(session, Cafe)

    async def get_all(
        self,
        skip: int = Limits.DEFAULT_SKIP,
        limit: int = Limits.DEFAULT_LIMIT,
        active_only: bool = True,
    ) -> List[Cafe]:
        """Получить все кафе.

        Args:
            skip: Количество записей для пропуска.
            limit: Максимальное количество записей.
            active_only: Флаг для фильтрации только активных кафе.

        Returns:
            List[Cafe]: Список кафе.

        """
        query = select(self.model)
        if active_only:
            query = query.where(self.model.active)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_name(
        self,
        name: str,
    ) -> Optional[Cafe]:
        """Получить кафе по названию.

        Args:
            name: Название кафе.

        Returns:
            Optional[Cafe]: Кафе или None, если не найдено.

        """
        query = select(self.model).where(self.model.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        cafe_create: CafeCreate,
    ) -> Cafe:
        """Создать новое кафе.

        Args:
            cafe_create: Данные для создания кафе.

        Returns:
            Cafe: Созданное кафе.

        """
        cafe = await super().create(cafe_create)
        await self.session.commit()
        return cafe

    async def update(
        self,
        cafe_id: int,
        cafe_update: CafeUpdate,
    ) -> Optional[Cafe]:
        """Обновить кафе.

        Args:
            cafe_id: Идентификатор кафе.
            cafe_update: Данные для обновления кафе.

        Returns:
            Optional[Cafe]: Обновленное кафе или None, если не найдено.

        """
        cafe = await self.get(cafe_id)
        if not cafe:
            return None

        updated_cafe = await super().update(cafe, cafe_update)
        await self.session.commit()
        return updated_cafe

    async def delete(
        self,
        cafe_id: int,
    ) -> bool:
        """Удалить кафе (логическое удаление).

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            bool: True, если удаление успешно, иначе False.

        """
        cafe = await self.get(cafe_id)
        if not cafe:
            return False

        cafe.active = False
        self.session.add(cafe)
        await self.session.commit()
        return True

    async def set_photo(
        self,
        cafe_id: int,
        photo_id: UUID,
    ) -> bool:
        """Установить фото для кафе.

        Args:
            cafe_id: Идентификатор кафе.
            photo_id: Идентификатор фото.

        Returns:
            bool: True, если установка успешна, иначе False.

        """
        cafe = await self.get(cafe_id)
        if not cafe:
            return False

        cafe.photo_id = photo_id
        self.session.add(cafe)
        await self.session.commit()
        return True

    async def exists(
        self,
        cafe_id: int,
    ) -> bool:
        """Проверить существование кафе.

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            bool: True, если кафе существует, иначе False.

        """
        cafe = await self.get(cafe_id)
        return cafe is not None

    async def count_active(self) -> int:
        """Количество активных кафе.

        Returns:
            int: Количество активных кафе.

        """
        query = select(self.model).where(self.model.active)
        result = await self.session.execute(query)
        return len(result.scalars().all())
