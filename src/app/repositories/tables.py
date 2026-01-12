from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tables import Table
from app.repositories.base import BaseCRUD
from app.schemas.tables import TableCreateDB, TableUpdate


class TableRepository(BaseCRUD[Table]):
    """Репозиторий для работы со столиками."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        """Инициализировать репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        super().__init__(session, Table)

    async def get_by_id(
        self,
        table_id: int,
    ) -> Table | None:
        """Получить столик по ID.

        Args:
            table_id: Идентификатор столика.

        Returns:
            Table | None: Объект столика или None.

        """
        stmt = (
            select(self.model)
            .options(selectinload(self.model.cafe))
            .where(self.model.id == table_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_for_cafe(
        self,
        cafe_id: int,
        active_only: bool = True,
    ) -> list[Table]:
        """Получить список столиков для кафе.

        Args:
            cafe_id: Идентификатор кафе.
            active_only: Флаг возврата только активных столиков.

        Returns:
            list[Table]: Список столиков.

        """
        stmt = select(self.model).where(self.model.cafe_id == cafe_id)
        stmt = stmt.options(selectinload(self.model.cafe))
        if active_only:
            stmt = stmt.where(self.model.active)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_cafe_and_id(
        self,
        cafe_id: int,
        table_id: int,
    ) -> Table | None:
        """Получить столик по ID кафе и ID столика.

        Args:
            cafe_id: Идентификатор кафе.
            table_id: Идентификатор столика.

        Returns:
            Table | None: Объект столика или None.

        """
        stmt = (
            select(self.model)
            .options(selectinload(self.model.cafe))
            .where(
                and_(
                    self.model.id == table_id,
                    self.model.cafe_id == cafe_id,
                ),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        table_create: TableCreateDB,
    ) -> Table:
        """Создать столик.

        Args:
            table_create: Данные для создания столика.

        Returns:
            Table: Созданный столик.

        """
        table = await super().create(table_create)
        await self.session.commit()
        return await self.get_by_id(table.id)

    async def update(
        self,
        table_id: int,
        table_update: TableUpdate,
    ) -> Table | None:
        """Обновить столик.

        Args:
            table_id: Идентификатор столика.
            table_update: Данные для обновления.

        Returns:
            Table | None: Обновленный столик или None.

        """
        table = await super().get(table_id)
        if not table:
            return None
        updated_table = await super().update(table, table_update)
        await self.session.commit()
        return await self.get_by_id(updated_table.id)

    async def delete(
        self,
        table_id: int,
    ) -> bool:
        """Удалить столик (логическое удаление).

        Args:
            table_id: Идентификатор столика.

        Returns:
            bool: True, если удаление прошло успешно.

        """
        table = await super().get(table_id)
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
        """Посчитать количество активных столиков для кафе.

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            int: Количество активных столиков.

        """
        stmt = select(self.model).where(
            and_(self.model.cafe_id == cafe_id, self.model.active),
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    async def exists(
        self,
        table_id: int,
    ) -> bool:
        """Проверить существование столика.

        Args:
            table_id: Идентификатор столика.

        Returns:
            bool: True, если столик существует.

        """
        return await super().get(table_id) is not None
