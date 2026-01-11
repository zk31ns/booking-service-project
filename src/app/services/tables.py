from fastapi import HTTPException, status

from app.core.constants import ErrorCode, Limits, Messages
from app.models.tables import Table
from app.repositories.cafes import CafeRepository
from app.repositories.tables import TableRepository
from app.schemas.tables import TableCreateDB, TableUpdate


class TableService:
    """Сервис для работы со столиками."""

    def __init__(
        self,
        cafe_repository: CafeRepository,
        table_repository: TableRepository,
    ) -> None:
        """Инициализация сервиса столиков.

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
    ) -> list[Table]:
        """Получить список столиков для указанного кафе.

        Args:
            cafe_id: Идентификатор кафе.
            active_only: Флаг фильтрации только активных столиков.

        Returns:
            List[Table]: Список объектов столиков.

        Raises:
            HTTPException: Если кафе не найдено или удалено (статус 404).

        """
        cafe = await self.cafe_repository.get_by_id(cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.errors[ErrorCode.CAFE_NOT_FOUND],
            )
        if not cafe.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=Messages.errors[ErrorCode.CAFE_INACTIVE],
            )
        return await self.table_repository.get_all_for_cafe(
            cafe_id=cafe_id,
            active_only=active_only,
        )

    async def get_table_by_id(self, table_id: int) -> Table:
        """Получить столик по идентификатору.

        Args:
            table_id: Идентификатор столика.

        Returns:
            Table: Объект столика.

        Raises:
            HTTPException: Если столик не найден (статус 404).
            HTTPException: Если столик удален (статус 410).
            HTTPException: Если кафе столика удалено (статус 410).

        """
        table = await self.table_repository.get_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.errors[ErrorCode.TABLE_NOT_FOUND],
            )
        if not table.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=Messages.errors[ErrorCode.TABLE_INACTIVE],
            )
        cafe = await self.cafe_repository.get_by_id(table.cafe_id)
        if not cafe or not cafe.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=Messages.errors[ErrorCode.CAFE_INACTIVE],
            )

        return table

    async def get_table_by_cafe_and_id(
        self,
        cafe_id: int,
        table_id: int,
    ) -> Table:
        """Получить столик по идентификаторам кафе и столика.

        Args:
            cafe_id: Идентификатор кафе.
            table_id: Идентификатор столика.

        Returns:
            Table: Объект столика.

        Raises:
            HTTPException: Если столик не найден в указанном кафе (статус 404).
            HTTPException: Если столик удален (статус 410).

        """
        table = await self.table_repository.get_by_cafe_and_id(
            cafe_id,
            table_id,
        )
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.errors[ErrorCode.TABLE_NOT_FOUND],
            )
        if not table.active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=Messages.errors[ErrorCode.TABLE_INACTIVE],
            )

        return table

    async def create_table(self, table_create: TableCreateDB) -> Table:
        """Создать новый столик.

        Args:
            table_create: Данные для создания столика.

        Returns:
            Table: Созданный объект столика.

        Raises:
            HTTPException: Если кафе не найдено (статус 404).
            HTTPException: Если кафе удалено (статус 400).
            HTTPException: Если количество мест меньше 1 (статус 400).

        """
        cafe = await self.cafe_repository.get_by_id(table_create.cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.errors[ErrorCode.CAFE_NOT_FOUND],
            )
        if not cafe.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Messages.errors[ErrorCode.CAFE_INACTIVE],
            )
        if table_create.seats < Limits.MIN_SEATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Messages.errors[ErrorCode.INVALID_SEATS_COUNT],
            )
        return await self.table_repository.create(table_create)

    async def update_table(
        self,
        table_id: int,
        table_update: TableUpdate,
    ) -> Table:
        """Обновить данные столика.

        Args:
            table_id: Идентификатор столика.
            table_update: Данные для обновления столика.

        Returns:
            Table: Обновленный объект столика.

        Raises:
            HTTPException: Если столик не найден (статус 404).
            HTTPException: Если столик удален (статус 410).
            HTTPException: Если кафе столика удалено (статус 410).
            HTTPException: Если количество мест меньше 1 (статус 400).
            HTTPException: Если не удалось обновить столик (статус 500).

        """
        await self.get_table_by_id(table_id)
        if (
            table_update.seats is not None
            and table_update.seats < Limits.MIN_SEATS
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Messages.errors[ErrorCode.INVALID_SEATS_COUNT],
            )
        updated_table = await self.table_repository.update(
            table_id,
            table_update,
        )
        if not updated_table:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=Messages.errors[ErrorCode.INTERNAL_SERVER_ERROR],
            )

        return updated_table

    async def delete_table(self, table_id: int) -> bool:
        """Удалить столик (логическое удаление).

        Args:
            table_id: Идентификатор столика.

        Returns:
            bool: True, если удаление выполнено успешно.

        Raises:
            HTTPException: Если столик не найден (статус 404).
            HTTPException: Если столик удален (статус 410).
            HTTPException: Если кафе столика удалено (статус 410).
            HTTPException: Если не удалось удалить столик (статус 500).

        """
        await self.get_table_by_id(table_id)
        result = await self.table_repository.delete(table_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=Messages.errors[ErrorCode.INTERNAL_SERVER_ERROR],
            )

        return True

    async def get_table_stats(self, table_id: int) -> dict:
        """Получить статистику по столику.

        Args:
            table_id: Идентификатор столика.

        Returns:
            dict: Статистика по столику.

        Raises:
            HTTPException: Если столик не найден (статус 404).
            HTTPException: Если столик удален (статус 410).
            HTTPException: Если кафе столика удалено (статус 410).

        """
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
