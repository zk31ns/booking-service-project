from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Limits
from app.models.tables import Table
from app.repositories.base import BaseCRUD
from app.schemas.tables import TableCreate, TableUpdate


class TableRepository(BaseCRUD[Table]):
    """Репозиторий для работы со столиками."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        """Инициализация репозитория столиков.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        super().__init__(session, Table)

    async def get_all_for_cafe(
        self,
        cafe_id: int,
        skip: int = Limits.DEFAULT_SKIP,
        limit: int = Limits.DEFAULT_LIMIT,
        active_only: bool = True,
    ) -> List[Table]:
        """Получить все столики для кафе.

        Args:
            cafe_id: Идентификатор кафе.
            skip: Количество записей для пропуска.
            limit: Максимальное количество записей.
            active_only: Флаг для фильтрации только активных столиков.

        Returns:
            List[Table]: Список столиков кафе.

        """
        query = select(self.model).where(self.model.cafe_id == cafe_id)
        if active_only:
            query = query.where(self.model.active)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_cafe_and_id(
        self,
        cafe_id: int,
        table_id: int,
    ) -> Optional[Table]:
        """Получить столик по ID кафе и ID столика.

        Args:
            cafe_id: Идентификатор кафе.
            table_id: Идентификатор столика.

        Returns:
            Optional[Table]: Столик или None, если не найден.

        """
        query = select(self.model).where(
            and_(self.model.id == table_id, self.model.cafe_id == cafe_id),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        table_create: TableCreate,
    ) -> Table:
        """Создать новый столик.

        Args:
            table_create: Данные для создания столика.

        Returns:
            Table: Созданный столик.

        """
        table = await super().create(table_create)
        await self.session.commit()
        await self.session.refresh(table)
        return table

    async def update(
        self,
        table_id: int,
        table_update: TableUpdate,
    ) -> Optional[Table]:
        """Обновить столик.

        Args:
            table_id: Идентификатор столика.
            table_update: Данные для обновления столика.

        Returns:
            Optional[Table]: Обновленный столик или None, если не найден.

        """
        table = await self.get(table_id)
        if not table:
            return None

        updated_table = await super().update(table, table_update)
        await self.session.commit()
        await self.session.refresh(updated_table)
        return updated_table

    async def delete(
        self,
        table_id: int,
    ) -> bool:
        """Удалить столик (логическое удаление).

        Args:
            table_id: Идентификатор столика.

        Returns:
            bool: True, если удаление успешно, иначе False.

        """
        table = await self.get(table_id)
        if not table:
            return False

        table.active = False
        self.session.add(table)
        await self.session.commit()
        return True

    async def count_for_cafe(
        self,
        cafe_id: int,
    ) -> int:
        """Количество столиков в кафе.

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            int: Количество активных столиков в кафе.

        """
        query = select(self.model).where(
            and_(self.model.cafe_id == cafe_id, self.model.active),
        )
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def exists(
        self,
        table_id: int,
    ) -> bool:
        """Проверить существование столика.

        Args:
            table_id: Идентификатор столика.

        Returns:
            bool: True, если столик существует, иначе False.

        """
        table = await self.get(table_id)
        return table is not None
