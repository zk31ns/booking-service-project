from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from app.models.cafe import Cafe
from app.repositories.cafe import CafeRepository
from app.repositories.table import TableRepository
from app.schemas.cafe import CafeCreate, CafeUpdate


class CafeService:
    """Сервис для работы с кафе."""

    def __init__(
        self,
        cafe_repository: CafeRepository,
        table_repository: TableRepository,
    ) -> None:
        """Инициализация сервиса."""
        self.cafe_repository = cafe_repository
        self.table_repository = table_repository

    async def get_all_cafes(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Cafe]:
        """Получить все кафе."""
        return await self.cafe_repository.get_all(
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

    async def get_cafe_by_id(self, cafe_id: int) -> Cafe:
        """Получить кафе по ID."""
        cafe = await self.cafe_repository.get_by_id(cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Кафе не найдено',
            )
        if not cafe.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail='Кафе удалено',
            )
        return cafe

    async def create_cafe(self, cafe_create: CafeCreate) -> Cafe:
        """Создать новое кафе."""
        existing_cafe = await self.cafe_repository.get_by_name(
            cafe_create.name,
        )
        if existing_cafe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Кафе с таким названием уже существует',
            )
        return await self.cafe_repository.create(cafe_create)

    async def update_cafe(self, cafe_id: int, cafe_update: CafeUpdate) -> Cafe:
        """Обновить кафе."""
        cafe = await self.get_cafe_by_id(cafe_id)
        if cafe_update.name and cafe_update.name != cafe.name:
            existing_cafe = await self.cafe_repository.get_by_name(
                cafe_update.name,
            )
            if existing_cafe and existing_cafe.id != cafe_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Кафе с таким названием уже существует',
                )
        updated_cafe = await self.cafe_repository.update(cafe_id, cafe_update)
        if not updated_cafe:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Не удалось обновить кафе',
            )
        return updated_cafe

    async def delete_cafe(self, cafe_id: int) -> bool:
        """Удалить кафе (логически)."""
        await self.get_cafe_by_id(cafe_id)
        result = await self.cafe_repository.delete(cafe_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Не удалось удалить кафе',
            )
        return True

    async def set_cafe_photo(self, cafe_id: int, photo_id: UUID) -> bool:
        """Установить фото для кафе."""
        await self.get_cafe_by_id(cafe_id)
        result = await self.cafe_repository.set_photo(cafe_id, photo_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Не удалось установить фото для кафе',
            )
        return True

    async def get_cafe_stats(self, cafe_id: int) -> dict:
        """Получить статистику по кафе."""
        cafe = await self.get_cafe_by_id(cafe_id)
        tables_count = await self.table_repository.count_for_cafe(cafe_id)
        return {
            'cafe_id': cafe_id,
            'name': cafe.name,
            'tables_count': tables_count,
            'active': cafe.active,
            'created_at': cafe.created_at,
            'updated_at': cafe.updated_at,
        }
