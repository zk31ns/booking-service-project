from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import Table
from app.schemas.table import TableCreate, TableUpdate


class TableRepository:
    """Репозиторий для работы со столиками."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория столы."""
        self.session = session

    async def get_all_for_cafe(
        self,
        cafe_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Table]:
        """Получить все столики для кафе."""
        query = select(Table).where(Table.cafe_id == cafe_id)
        if active_only:
            query = query.where(Table.active)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, table_id: int) -> Optional[Table]:
        """Получить столик по ID."""
        query = select(Table).where(Table.id == table_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_cafe_and_id(
        self,
        cafe_id: int,
        table_id: int,
    ) -> Optional[Table]:
        """Получить столик по ID кафе и ID столика."""
        query = select(Table).where(
            and_(Table.id == table_id, Table.cafe_id == cafe_id),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, table_create: TableCreate) -> Table:
        """Создать новый столик."""
        table = Table(**table_create.model_dump())
        self.session.add(table)
        await self.session.commit()
        await self.session.refresh(table)
        return table

    async def update(
        self,
        table_id: int,
        table_update: TableUpdate,
    ) -> Optional[Table]:
        """Обновить столик."""
        table = await self.get_by_id(table_id)
        if not table:
            return None

        update_data = table_update.model_dump(exclude_unset=True)
        if update_data:
            stmt = (
                update(Table).where(Table.id == table_id).values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            await self.session.refresh(table)
        return table

    async def delete(self, table_id: int) -> bool:
        """Логическое удаление столика."""
        table = await self.get_by_id(table_id)
        if not table:
            return False

        stmt = update(Table).where(Table.id == table_id).values(active=False)
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def count_for_cafe(self, cafe_id: int) -> int:
        """Количество столиков в кафе."""
        query = select(Table).where(
            and_(Table.cafe_id == cafe_id, Table.active),
        )
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def exists(self, table_id: int) -> bool:
        """Проверить существование столика."""
        query = select(Table.id).where(Table.id == table_id)
        result = await self.session.execute(query)
        return result.scalar() is not None
