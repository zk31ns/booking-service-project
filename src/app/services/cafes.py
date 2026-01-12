from uuid import UUID

from fastapi import status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import (
    AppException,
    ConflictException,
    InternalServerException,
    NotFoundException,
)
from app.models.cafes import Cafe
from app.models.media import Media
from app.models.users import User, cafe_managers
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
    ) -> list[Cafe]:
        """Получить список всех кафе.

        Args:
            active_only: Флаг фильтрации только активных кафе.

        Returns:
            list[Cafe]: Список объектов кафе.

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
            AppException: Если кафе не найдено (статус 404).
            AppException: Если кафе удалено (статус 410).

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
            AppException: Если кафе с таким названием уже существует
                (статус 409).
            AppException: Если менеджеры не указаны или не найдены
                (статус 400/404).

        """
        existing_cafe = await self.cafe_repository.get_by_name(
            cafe_create.name,
        )
        if existing_cafe:
            await self._raise_conflict(ErrorCode.CAFE_ALREADY_EXISTS)

        if cafe_create.photo_id is not None:
            await self._validate_photo_exists(cafe_create.photo_id)

        managers = await self._get_managers_by_ids(
            cafe_create.managers_id,
            allow_empty=False,
        )

        cafe_data = cafe_create.model_dump(exclude={'managers_id'})
        cafe = await self.cafe_repository.create(cafe_data)

        cafe.managers = managers
        await self.session.commit()
        await self.session.refresh(cafe)

        return cafe

    async def update_cafe(self, cafe_id: int, cafe_update: CafeUpdate) -> Cafe:
        """Обновить данные кафе.

        Args:
            cafe_id: Идентификатор кафе.
            cafe_update: Данные для обновления кафе.

        Returns:
            Cafe: Обновленный объект кафе.

        Raises:
            AppException: Если кафе не найдено (статус 404).
            AppException: Если кафе удалено (статус 410).
            AppException: Если кафе с таким названием уже существует
                (статус 400).
            AppException: Если не удалось обновить кафе (статус 500).
            AppException: Если хотя бы один менеджер не найден (статус 404).

        """
        cafe = await self.get_cafe_by_id(cafe_id)
        if cafe_update.name and cafe_update.name != cafe.name:
            existing_cafe = await self.cafe_repository.get_by_name(
                cafe_update.name,
            )
            if existing_cafe and existing_cafe.id != cafe_id:
                await self._raise_conflict(ErrorCode.CAFE_ALREADY_EXISTS)

        if cafe_update.photo_id is not None:
            await self._validate_photo_exists(cafe_update.photo_id)

        if cafe_update.managers_id is not None:
            if cafe_update.managers_id:
                cafe.managers = await self._get_managers_by_ids(
                    cafe_update.managers_id,
                    allow_empty=True,
                )

        update_data = cafe_update.model_dump(
            exclude={'managers_id'},
            exclude_none=True,
        )
        for key, value in update_data.items():
            setattr(cafe, key, value)

        await self.session.commit()
        await self.session.refresh(cafe)
        return cafe

    async def delete_cafe(self, cafe_id: int) -> bool:
        """Удалить кафе (логическое удаление).

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            bool: True, если удаление выполнено успешно.

        Raises:
            AppException: Если кафе не найдено (статус 404).
            AppException: Если кафе удалено (статус 410).
            AppException: Если не удалось удалить кафе (статус 500).

        """
        await self.get_cafe_by_id(cafe_id)
        result = await self.cafe_repository.delete(cafe_id)
        if not result:
            raise InternalServerException(ErrorCode.CAFE_DELETE_FAILED)
        return True

    async def set_cafe_photo(self, cafe_id: int, photo_id: UUID) -> bool:
        """Установить фото для кафе.

        Args:
            cafe_id: Идентификатор кафе.
            photo_id: Идентификатор фотографии.

        Returns:
            bool: True, если операция выполнена успешно.

        Raises:
            AppException: Если кафе не найдено (статус 404).
            AppException: Если кафе удалено (статус 410).
            AppException: Если не удалось установить фото (статус 500).

        """
        await self.get_cafe_by_id(cafe_id)
        await self._validate_photo_exists(photo_id)
        result = await self.cafe_repository.set_photo(cafe_id, photo_id)
        if not result:
            raise InternalServerException(ErrorCode.CAFE_PHOTO_UPDATE_FAILED)
        return True

    async def _validate_photo_exists(self, photo_id: UUID) -> None:
        """Проверить, что фото существует в таблице media."""
        result = await self.session.execute(
            select(Media).where(Media.id == photo_id, Media.active)
        )
        media = result.scalar_one_or_none()
        if not media:
            raise NotFoundException(ErrorCode.MEDIA_NOT_FOUND)

    async def _get_managers_by_ids(
        self,
        manager_ids: list[int],
        allow_empty: bool,
    ) -> list[User]:
        """Получить список менеджеров по ID с валидацией."""
        if not manager_ids:
            if allow_empty:
                return []
            raise AppException(
                error_code=ErrorCode.MANAGERS_REQUIRED,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        result = await self.session.execute(
            select(User).where(User.id.in_(manager_ids))
        )
        managers = list(result.scalars().all())
        missing_ids = sorted(set(manager_ids) - {user.id for user in managers})
        if missing_ids:
            raise NotFoundException(
                ErrorCode.USER_NOT_FOUND,
                extra={'user_ids': missing_ids},
            )
        return managers

    async def get_cafe_stats(self, cafe_id: int) -> dict:
        """Получить статистику по кафе.

        Args:
            cafe_id: Идентификатор кафе.

        Returns:
            dict: Статистика по кафе.

        Raises:
            AppException: Если кафе не найдено (статус 404).
            AppException: Если кафе удалено (статус 410).

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

    async def add_manager(
        self,
        cafe_id: int,
        user_id: int,
    ) -> None:
        """Добавить менеджера к кафе.

        Args:
            cafe_id: ID кафе.
            user_id: ID пользователя.

        Raises:
            AppException: Если кафе или пользователь не найдены.
            AppException: Если пользователь уже менеджер кафе.

        """
        await self.get_cafe_by_id(cafe_id)

        user_result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException(
                ErrorCode.USER_NOT_FOUND,
                extra={'user_id': user_id},
            )

        existing = await self.session.execute(
            select(cafe_managers).where(
                (cafe_managers.c.cafe_id == cafe_id)
                & (cafe_managers.c.user_id == user_id)
            )
        )
        if existing.scalar() is not None:
            raise ConflictException(
                ErrorCode.MANAGER_ALREADY_ASSIGNED,
                extra={'user_id': user_id, 'cafe_id': cafe_id},
            )

        await self.session.execute(
            insert(cafe_managers).values(
                cafe_id=cafe_id,
                user_id=user_id,
            )
        )
        await self.session.commit()

    async def remove_manager(
        self,
        cafe_id: int,
        user_id: int,
    ) -> None:
        """Удалить менеджера от кафе.

        Args:
            cafe_id: ID кафе.
            user_id: ID пользователя.

        Raises:
            AppException: Если связь не найдена.

        """
        from sqlalchemy import delete

        await self.get_cafe_by_id(cafe_id)

        result = await self.session.execute(
            select(cafe_managers).where(
                (cafe_managers.c.cafe_id == cafe_id)
                & (cafe_managers.c.user_id == user_id)
            )
        )
        if result.scalar() is None:
            raise NotFoundException(
                ErrorCode.MANAGER_NOT_ASSIGNED,
                extra={'user_id': user_id, 'cafe_id': cafe_id},
            )

        await self.session.execute(
            delete(cafe_managers).where(
                (cafe_managers.c.cafe_id == cafe_id)
                & (cafe_managers.c.user_id == user_id)
            )
        )
        await self.session.commit()
