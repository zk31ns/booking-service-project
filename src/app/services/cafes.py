from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode, Messages
from app.models.cafes import Cafe
from app.models.users import User
from app.repositories.cafes import CafeRepository
from app.repositories.tables import TableRepository
from app.schemas.cafes import CafeCreate, CafeUpdate
from app.services.base import EntityValidationMixin


class CafeService(EntityValidationMixin[Cafe]):
    """Сервис для работы с кафе."""

    def __init__(
        self,
        cafe_repository: CafeRepository,
        table_repository: TableRepository,
        session: AsyncSession,
    ) -> None:
        """Инициализация сервиса кафе.

        Args:
            cafe_repository: Репозиторий для работы с кафе.
            table_repository: Репозиторий для работы со столиками.
            session: Асинхронная сессия SQLAlchemy.

        """
        self.cafe_repository = cafe_repository
        self.table_repository = table_repository
        self.session = session

    async def get_all_cafes(
        self,
        active_only: bool = True,
    ) -> List[Cafe]:
        """Получить список всех кафе.

        Args:
            active_only: Флаг фильтрации только активных кафе.

        Returns:
            List[Cafe]: Список объектов кафе.

        """
        return await self.cafe_repository.get_all(
            active_only=active_only,
        )

    async def get_cafe_by_id(self, cafe_id: int) -> Cafe:
        """Получить кафе по идентификатору.

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            Cafe: Объект кафе.

        Raises:
            HTTPException: Если кафе не найдено (статус 404).
            HTTPException: Если кафе удалено (статус 410).

        """
        cafe = await self.cafe_repository.get_by_id(cafe_id)
        return await self._validate_exists_and_active(
            cafe,
            'Cafe',
            ErrorCode.CAFE_NOT_FOUND,
            ErrorCode.CAFE_INACTIVE,
        )

    async def create_cafe(self, cafe_create: CafeCreate) -> Cafe:
        """Создать новое кафе.

        Args:
            cafe_create: Данные для создания кафе.

        Returns:
            Cafe: Созданный объект кафе.

        Raises:
            HTTPException: Если кафе с таким названием уже существует
            (статус 409).
            HTTPException: Если хотя бы один менеджер не найден (статус 404).

        """
        existing_cafe = await self.cafe_repository.get_by_name(
            cafe_create.name,
        )
        if existing_cafe:
            await self._raise_conflict(ErrorCode.CAFE_ALREADY_EXISTS)

        # Проверить что все менеджеры существуют
        if cafe_create.managers_id:
            managers_result = await self.session.execute(
                select(User).where(User.id.in_(cafe_create.managers_id))
            )
            managers = managers_result.scalars().all()
            if len(managers) != len(cafe_create.managers_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=Messages.errors[ErrorCode.USER_NOT_FOUND],
                )

        # Создать кафе без менеджеров
        cafe_data = cafe_create.model_dump(exclude={'managers_id'})
        cafe = await self.cafe_repository.create(cafe_data)

        # Добавить менеджеров
        if cafe_create.managers_id:
            managers_result = await self.session.execute(
                select(User).where(User.id.in_(cafe_create.managers_id))
            )
            managers = managers_result.scalars().all()
            cafe.managers = managers
            await self.session.commit()

        return cafe

    async def update_cafe(self, cafe_id: int, cafe_update: CafeUpdate) -> Cafe:
        """Обновить данные кафе.

        Args:
            cafe_id: Идентификатор кафе.
            cafe_update: Данные для обновления кафе.

        Returns:
            Cafe: Обновленный объект кафе.

        Raises:
            HTTPException: Если кафе не найдено (статус 404).
            HTTPException: Если кафе удалено (статус 410).
            HTTPException: Если кафе с таким названием уже существует
            (статус 400).
            HTTPException: Если не удалось обновить кафе (статус 500).
            HTTPException: Если хотя бы один менеджер не найден (статус 404).

        """
        cafe = await self.get_cafe_by_id(cafe_id)
        if cafe_update.name and cafe_update.name != cafe.name:
            existing_cafe = await self.cafe_repository.get_by_name(
                cafe_update.name,
            )
            if existing_cafe and existing_cafe.id != cafe_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=Messages.errors[ErrorCode.CAFE_ALREADY_EXISTS],
                )

        # Проверить менеджеров если они указаны
        if cafe_update.managers_id is not None:
            if cafe_update.managers_id:  # Если не пустой список
                managers_result = await self.session.execute(
                    select(User).where(User.id.in_(cafe_update.managers_id))
                )
                managers = managers_result.scalars().all()
                if len(managers) != len(cafe_update.managers_id):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=Messages.errors[ErrorCode.USER_NOT_FOUND],
                    )
            # Обновить менеджеров в объекте кафе
            if cafe_update.managers_id:
                managers_result = await self.session.execute(
                    select(User).where(User.id.in_(cafe_update.managers_id))
                )
                cafe.managers = managers_result.scalars().all()
            else:
                cafe.managers = []

        # Обновить остальные поля
        update_data = cafe_update.model_dump(
            exclude={'managers_id'},
            exclude_none=True,
        )
        for key, value in update_data.items():
            setattr(cafe, key, value)

        await self.session.commit()
        return cafe

    async def delete_cafe(self, cafe_id: int) -> bool:
        """Удалить кафе (логическое удаление).

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            bool: True, если удаление выполнено успешно.

        Raises:
            HTTPException: Если кафе не найдено (статус 404).
            HTTPException: Если кафе удалено (статус 410).
            HTTPException: Если не удалось удалить кафе (статус 500).

        """
        await self.get_cafe_by_id(cafe_id)
        result = await self.cafe_repository.delete(cafe_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=Messages.errors[ErrorCode.CAFE_DELETE_FAILED],
            )
        return True

    async def set_cafe_photo(self, cafe_id: int, photo_id: UUID) -> bool:
        """Установить фото для кафе.

        Args:
            cafe_id: Идентификатор кафе.
            photo_id: Идентификатор фотографии.

        Returns:
            bool: True, если операция выполнена успешно.

        Raises:
            HTTPException: Если кафе не найдено (статус 404).
            HTTPException: Если кафе удалено (статус 410).
            HTTPException: Если не удалось установить фото (статус 500).

        """
        await self.get_cafe_by_id(cafe_id)
        result = await self.cafe_repository.set_photo(cafe_id, photo_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=Messages.errors[ErrorCode.CAFE_PHOTO_UPDATE_FAILED],
            )
        return True

    async def get_cafe_stats(self, cafe_id: int) -> dict:
        """Получить статистику по кафе.

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            dict: Статистика по кафе.

        Raises:
            HTTPException: Если кафе не найдено (статус 404).
            HTTPException: Если кафе удалено (статус 410).

        """
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
