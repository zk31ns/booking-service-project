from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.cafe import Cafe
from src.app.schemas.cafe import CafeCreate, CafeUpdate


class CafeRepository:
    """Репозиторий для работы с кафе."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория кафе."""
        self.session = session

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Cafe]:
        """Получить все кафе."""
        query = select(Cafe)
        if active_only:
            query = query.where(Cafe.active)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(
        self,
        cafe_id: int,
    ) -> Optional[Cafe]:
        """Получить кафе по ID."""
        query = select(Cafe).where(Cafe.id == cafe_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Optional[Cafe]:
        """Получить кафе по названию."""
        query = select(Cafe).where(Cafe.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        cafe_create: CafeCreate,
    ) -> Cafe:
        """Создать новое кафе."""
        cafe = Cafe(**cafe_create.model_dump())
        self.session.add(cafe)
        await self.session.commit()
        await self.session.refresh(cafe)
        return cafe

    async def update(
        self,
        cafe_id: int,
        cafe_update: CafeUpdate,
    ) -> Optional[Cafe]:
        """Обновить кафе."""
        cafe = await self.get_by_id(cafe_id)
        if not cafe:
            return None
        update_data = cafe_update.model_dump(exclude_unset=True)
        if update_data:
            stmt = update(Cafe).where(Cafe.id == cafe_id).values(**update_data)
            await self.session.execute(stmt)
            await self.session.commit()
            await self.session.refresh(cafe)
        return cafe

    async def delete(
        self,
        cafe_id: int,
    ) -> bool:
        """Логическое удаление кафе."""
        cafe = await self.get_by_id(cafe_id)
        if not cafe:
            return False
        await self.session.execute(
            update(Cafe).where(Cafe.id == cafe_id).values(active=False),
        )
        await self.session.commit()
        return True

    async def set_photo(
        self,
        cafe_id: int,
        photo_id: UUID,
    ) -> bool:
        """Установить фото для кафе."""
        cafe = await self.get_by_id(cafe_id)
        if not cafe:
            return False

        stmt = update(Cafe).where(Cafe.id == cafe_id).values(photo_id=photo_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def exists(
        self,
        cafe_id: int,
    ) -> bool:
        """Проверить существование кафе."""
        query = select(Cafe.id).where(Cafe.id == cafe_id)
        result = await self.session.execute(query)
        return result.scalar() is not None

    async def count_active(self) -> int:
        """Количество активных кафе."""
        query = select(Cafe).where(Cafe.active)
        result = await self.session.execute(query)
        return len(result.scalars().all())
