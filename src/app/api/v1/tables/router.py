from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_cafe_manager
from app.core.constants import API, ErrorCode, Messages
from app.models import User
from app.repositories.cafes import CafeRepository
from app.repositories.tables import TableRepository
from app.schemas.tables import Table, TableCreate, TableCreateDB, TableUpdate
from app.services.tables import TableService

router = APIRouter(prefix='/cafe/{cafe_id}/tables', tags=API.TABLES)


def get_table_service(
    db: AsyncSession = Depends(get_db),
) -> TableService:
    """Создать сервис для работы со столиками.

    Args:
        db: Асинхронная сессия БД.

    Returns:
        TableService: Сервис работы со столиками.

    """
    cafe_repository = CafeRepository(db)
    table_repository = TableRepository(db)
    return TableService(cafe_repository, table_repository)


@router.get(
    '',
    response_model=list[Table],
    summary='Список столиков в кафе',
    description=(
        'Получение списка столиков для выбранного кафе. '
        'Администратор и менеджер могут видеть все столики, '
        'обычные пользователи — только активные.'
    ),
)
async def get_tables_for_cafe(
    cafe_id: int,
    show_all: bool = Query(
        False,
        description=(
            'Показывать все столики, включая неактивные. '
            'По умолчанию возвращаются только активные.'
        ),
    ),
    table_service: TableService = Depends(get_table_service),
) -> list[Table]:
    """Получить список столиков для кафе.

    Args:
        cafe_id: ID кафе.
        show_all: Флаг показа всех столиков.
        table_service: Сервис для работы со столиками.

    Returns:
        list[Table]: Список столиков.

    """
    return await table_service.get_all_tables_for_cafe(
        cafe_id=cafe_id,
        active_only=not show_all,
    )


@router.get(
    '/{table_id}',
    response_model=Table,
    summary='Получение информации о столике в кафе по его ID',
    responses={
        404: {'description': Messages.errors[ErrorCode.TABLE_NOT_FOUND]},
        410: {'description': Messages.errors[ErrorCode.TABLE_INACTIVE]},
    },
)
async def get_table(
    cafe_id: int,
    table_id: int,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Получить информацию о столике по ID и ID кафе.

    Args:
        cafe_id: ID кафе.
        table_id: ID столика.
        table_service: Сервис для работы со столиками.

    Returns:
        Table: Данные столика.

    """
    return await table_service.get_table_by_cafe_and_id(cafe_id, table_id)


@router.post(
    '',
    response_model=Table,
    status_code=status.HTTP_201_CREATED,
    summary='Создать новый столик в кафе',
    responses={
        404: {'description': Messages.errors[ErrorCode.CAFE_NOT_FOUND]},
        400: {'description': Messages.errors[ErrorCode.CAFE_INACTIVE]},
    },
)
async def create_table(
    cafe_id: int,
    table_create: TableCreate,
    table_service: TableService = Depends(get_table_service),
    _current_user: User = Depends(require_cafe_manager),
) -> Table:
    """Создать новый столик в кафе.

    Args:
        cafe_id: ID кафе.
        table_create: Данные для создания столика.
        table_service: Сервис для работы со столиками.

    Returns:
        Table: Созданный столик.

    """
    table_create_db = TableCreateDB.model_validate({
        **table_create.model_dump(),
        'cafe_id': cafe_id,
    })
    return await table_service.create_table(table_create_db)


@router.patch(
    '/{table_id}',
    response_model=Table,
    summary='Обновление информации о столике в кафе по его ID',
    responses={
        404: {'description': Messages.errors[ErrorCode.TABLE_NOT_FOUND]},
        400: {'description': Messages.errors[ErrorCode.INVALID_SEATS_COUNT]},
    },
)
async def update_table(
    cafe_id: int,
    table_id: int,
    table_update: TableUpdate,
    table_service: TableService = Depends(get_table_service),
    _current_user: User = Depends(require_cafe_manager),
) -> Table:
    """Обновить информацию о столике в кафе.

    Args:
        cafe_id: ID кафе.
        table_id: ID столика.
        table_update: Данные для обновления.
        table_service: Сервис для работы со столиками.

    Returns:
        Table: Обновленный столик.

    """
    await table_service.get_table_by_cafe_and_id(cafe_id, table_id)
    return await table_service.update_table(table_id, table_update)
