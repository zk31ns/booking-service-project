from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.constants import API, ErrorCode, Messages
from app.repositories.cafes import CafeRepository
from app.repositories.tables import TableRepository
from app.schemas.tables import Table, TableCreate, TableUpdate
from app.services.tables import TableService

router = APIRouter(prefix='/tables', tags=API.TABLES)


def get_table_service(
    db: AsyncSession = Depends(get_db),
) -> TableService:
    """Получить сервис для работы со столиками.

    Args:
        db: Сессия БД (внедряется автоматически).

    Returns:
        TableService: Сервис для работы со столиками.

    """
    cafe_repository = CafeRepository(db)
    table_repository = TableRepository(db)
    return TableService(cafe_repository, table_repository)


@router.get(
    '/',
    response_model=list[Table],
    summary='Получить столики для кафе',
    description='Возвращает список столиков для указанного кафе',
)
async def get_tables_for_cafe(
    cafe_id: int = Query(..., description='ID кафе'),
    active_only: bool = Query(True, description='Только активные столики'),
    table_service: TableService = Depends(get_table_service),
) -> list[Table]:
    """Получить список столиков для указанного кафе.

    Args:
        cafe_id: Идентификатор кафе.
        active_only: Флаг фильтрации только активных столиков.
        table_service: Сервис работы со столиками (внедряется автоматически).

    Returns:
        List[Table]: Список столиков кафе.

    """
    return await table_service.get_all_tables_for_cafe(
        cafe_id=cafe_id,
        active_only=active_only,
    )


@router.get(
    '/{table_id}',
    response_model=Table,
    summary='Получить столик по ID',
    responses={
        404: {'description': Messages.errors[ErrorCode.TABLE_NOT_FOUND]},
        410: {'description': Messages.errors[ErrorCode.TABLE_INACTIVE]},
    },
)
async def get_table(
    table_id: int,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Получить столик по идентификатору.

    Args:
        table_id: Идентификатор столика.
        table_service: Сервис работы со столиками (внедряется автоматически).

    Returns:
        Table: Объект столика.

    Raises:
        HTTPException: Если столик не найден (статус 404).
        HTTPException: Если столик удален или кафе удалено (статус 410).

    """
    return await table_service.get_table_by_id(table_id)


@router.post(
    '/',
    response_model=Table,
    status_code=status.HTTP_201_CREATED,
    summary='Создать новый столик',
    responses={
        404: {'description': Messages.errors[ErrorCode.CAFE_NOT_FOUND]},
        400: {'description': Messages.errors[ErrorCode.CAFE_INACTIVE]},
    },
)
async def create_table(
    table_create: TableCreate,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Создать новый столик.

    Args:
        table_create: Данные для создания столика.
        table_service: Сервис работы со столиками (внедряется автоматически).

    Returns:
        Table: Созданный столик.

    Raises:
        HTTPException: Если кафе не найдено (статус 404).
        HTTPException: Если кафе удалено (статус 400).

    """
    return await table_service.create_table(table_create)


@router.patch(
    '/{table_id}',
    response_model=Table,
    summary='Обновить столик',
    responses={
        404: {'description': Messages.errors[ErrorCode.TABLE_NOT_FOUND]},
        400: {
            'description': Messages.errors[ErrorCode.INVALID_SEATS_COUNT],
        },
    },
)
async def update_table(
    table_id: int,
    table_update: TableUpdate,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Обновить данные столика.

    Args:
        table_id: Идентификатор столика.
        table_update: Данные для обновления столика.
        table_service: Сервис работы со столиками (внедряется автоматически).

    Returns:
        Table: Обновленный объект столика.

    Raises:
        HTTPException: Если столик не найден (статус 404).
        HTTPException: Если количество мест отрицательное число (статус 400).

    """
    return await table_service.update_table(table_id, table_update)
