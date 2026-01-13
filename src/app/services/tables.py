from app.core.constants import ErrorCode, Limits
from app.core.exceptions import (
    InternalServerException,
    NotFoundException,
    ValidationException,
)
from app.models.tables import Table
from app.repositories.cafes import CafeRepository
from app.repositories.tables import TableRepository
from app.schemas.tables import TableCreateDB, TableUpdate
from app.services.base import EntityValidationMixin


class TableService(EntityValidationMixin[Table]):
    """Сервис для работы со столиками."""

    def __init__(
        self,
        cafe_repository: CafeRepository,
        table_repository: TableRepository,
    ) -> None:
        """Инициализировать сервис.

        Args:
            cafe_repository: Репозиторий для работы с кафе.
            table_repository: Репозиторий для работы со столиками.

        """
        self.cafe_repository = cafe_repository
        self.table_repository = table_repository

    async def get_all_tables_for_cafe(
        self,
        cafe_id: int,
        active_only: bool = True,
        allow_inactive_cafe: bool = False,
    ) -> list[Table]:
        """Получить список столиков для кафе.

        Args:
            cafe_id: Идентификатор кафе.
            active_only: Возвращать только активные столики.
            allow_inactive_cafe: Разрешить неактивные кафе.

        Returns:
            list[Table]: Список столиков.

        Raises:
            AppException: Если кафе не найдено или неактивно.

        """
        cafe = await self.cafe_repository.get_by_id(cafe_id)
        if not cafe:
            raise NotFoundException(ErrorCode.CAFE_NOT_FOUND)
        if not allow_inactive_cafe and not cafe.active:
            raise NotFoundException(ErrorCode.CAFE_NOT_FOUND)
        return await self.table_repository.get_all_for_cafe(
            cafe_id=cafe_id,
            active_only=active_only,
        )

    async def get_table_by_id(self, table_id: int) -> Table:
        """Получить столик по ID.

        Args:
            table_id: Идентификатор столика.

        Returns:
            Table: Столик.

        Raises:
            AppException: Если столик не найден или неактивен.

        """
        table = await self.table_repository.get_by_id(table_id)
        table = await self._validate_exists_and_active(
            table,
            'Table',
            ErrorCode.TABLE_NOT_FOUND,
            ErrorCode.TABLE_INACTIVE,
        )
        cafe = await self.cafe_repository.get_by_id(table.cafe_id)
        await self._validate_exists_and_active(
            cafe,
            'Cafe',
            ErrorCode.CAFE_NOT_FOUND,
            ErrorCode.CAFE_INACTIVE,
        )

        return table

    async def get_table_by_cafe_and_id(
        self,
        cafe_id: int,
        table_id: int,
        allow_inactive: bool = False,
    ) -> Table:
        """Получить столик по ID кафе и ID столика.

        Args:
            cafe_id: Идентификатор кафе.
            table_id: Идентификатор столика.
            allow_inactive: Разрешить неактивные столики.

        Returns:
            Table: Столик.

        Raises:
            AppException: Если столик не найден или неактивен.

        """
        table = await self.table_repository.get_by_cafe_and_id(
            cafe_id,
            table_id,
        )
        if not table:
            raise NotFoundException(ErrorCode.TABLE_NOT_FOUND)
        if not allow_inactive and not table.active:
            raise NotFoundException(ErrorCode.TABLE_NOT_FOUND)
        if not allow_inactive and table.cafe and not table.cafe.active:
            raise NotFoundException(ErrorCode.CAFE_NOT_FOUND)
        return table

    async def create_table(self, table_create: TableCreateDB) -> Table:
        """Создать столик.

        Args:
            table_create: Данные для создания столика.

        Returns:
            Table: Созданный столик.

        Raises:
            AppException: Если кафе не найдено, неактивно
            или некорректны места.

        """
        cafe = await self.cafe_repository.get_by_id(table_create.cafe_id)
        await self._validate_exists_and_active(
            cafe,
            'Cafe',
            ErrorCode.CAFE_NOT_FOUND,
            ErrorCode.CAFE_INACTIVE,
        )
        self._validate_seats(table_create.seats)
        return await self.table_repository.create(table_create)

    async def update_table(
        self,
        table_id: int,
        table_update: TableUpdate,
    ) -> Table:
        """Обновить столик.

        Args:
            table_id: Идентификатор столика.
            table_update: Данные для обновления.

        Returns:
            Table: Обновленный столик.

        Raises:
            AppException: Если столик не найден/неактивен
            или валидация не прошла.

        """
        await self.get_table_by_id(table_id)
        if table_update.seats is not None:
            self._validate_seats(table_update.seats)
        updated_table = await self.table_repository.update(
            table_id,
            table_update,
        )
        if not updated_table:
            raise InternalServerException(ErrorCode.INTERNAL_SERVER_ERROR)

        return updated_table

    async def delete_table(self, table_id: int) -> bool:
        """Деактивировать столик.

        Args:
            table_id: Идентификатор столика.

        Returns:
            bool: True, если столик деактивирован.

        Raises:
            AppException: Если столик не найден или неактивен.

        """
        await self.get_table_by_id(table_id)
        result = await self.table_repository.delete(table_id)
        if not result:
            raise InternalServerException(ErrorCode.INTERNAL_SERVER_ERROR)
        return True

    def _validate_seats(self, seats: int) -> None:
        """Проверить корректность количества мест."""
        if seats < Limits.MIN_SEATS or seats > Limits.MAX_SEATS:
            raise ValidationException(ErrorCode.INVALID_SEATS_COUNT)
