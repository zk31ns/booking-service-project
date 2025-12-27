from typing import List

from fastapi import HTTPException, status

from src.app.models.tables import Table
from src.app.repositories.cafes import CafeRepository
from src.app.repositories.tables import TableRepository
from src.app.schemas.tables import TableCreate, TableUpdate


class TableService:
    """Сервис для работы со столиками."""

    def __init__(
        self,
        cafe_repository: CafeRepository,
        table_repository: TableRepository,
    ) -> None:
        """Инициализация сервиса."""
        self.cafe_repository = cafe_repository
        self.table_repository = table_repository

    async def get_all_tables_for_cafe(
        self,
        cafe_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Table]:
        """Получить все столики для кафе."""
        cafe = await self.cafe_repository.get_by_id(cafe_id)
        if not cafe or not cafe.active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Кафе не найдено или удалено',
            )
        return await self.table_repository.get_all_for_cafe(
            cafe_id=cafe_id,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

    async def get_table_by_id(self, table_id: int) -> Table:
        """Получить столик по ID."""
        table = await self.table_repository.get_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Столик не найден',
            )
        if not table.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail='Столик удален',
            )
        cafe = await self.cafe_repository.get_by_id(table.cafe_id)
        if not cafe or not cafe.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail='Кафе этого столика удалено',
            )

        return table

    async def get_table_by_cafe_and_id(
        self,
        cafe_id: int,
        table_id: int,
    ) -> Table:
        """Получить столик по ID кафе и ID столика."""
        table = await self.table_repository.get_by_cafe_and_id(
            cafe_id,
            table_id,
        )
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Столик не найден в этом кафе',
            )
        if not table.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail='Столик удален',
            )

        return table

    async def create_table(self, table_create: TableCreate) -> Table:
        """Создать новый столик."""
        cafe = await self.cafe_repository.get_by_id(table_create.cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Кафе не найдено',
            )
        if not cafe.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Нельзя добавить столик в удаленное кафе',
            )
        if table_create.seats < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Количество мест должно быть положительным числом',
            )
        return await self.table_repository.create(table_create)

    async def update_table(
        self,
        table_id: int,
        table_update: TableUpdate,
    ) -> Table:
        """Обновить столик."""
        await self.get_table_by_id(table_id)
        if table_update.seats is not None and table_update.seats < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Количество мест должно быть положительным числом',
            )
        updated_table = await self.table_repository.update(
            table_id,
            table_update,
        )
        if not updated_table:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Не удалось обновить столик',
            )

        return updated_table

    async def delete_table(self, table_id: int) -> bool:
        """Удалить столик (логически)."""
        await self.get_table_by_id(table_id)
        result = await self.table_repository.delete(table_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Не удалось удалить столик',
            )

        return True

    async def get_table_stats(self, table_id: int) -> dict:
        """Получить статистику по столику."""
        table = await self.get_table_by_id(table_id)
        cafe = await self.cafe_repository.get_by_id(table.cafe_id)

        return {
            'table_id': table_id,
            'cafe_id': table.cafe_id,
            'cafe_name': cafe.name if cafe else None,
            'seats': table.seats,
            'is_active': table.active,
            'created_at': table.created_at,
            'updated_at': table.updated_at,
        }
