from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_db
from src.app.core.constants import API, Limits
from src.app.repositories.cafes import CafeRepository
from src.app.repositories.tables import TableRepository
from src.app.schemas.tables import Table, TableCreate, TableUpdate
from src.app.services.tables import TableService

router = APIRouter(prefix='/tables', tags=API.TABLES)


def get_table_service(
    db: AsyncSession = Depends(get_db),
) -> TableService:
    """Получить сервис для работы со столиками."""
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
    skip: int = Query(0, ge=0, description='Количество записей для пропуска'),
    limit: int = Query(
        Limits.DEFAULT_PAGE_SIZE,
        ge=1,
        le=Limits.MAX_PAGE_SIZE,
        description=f'Количество записей на странице ({Limits.MAX_PAGE_SIZE})',
    ),
    active_only: bool = Query(True, description='Только активные столики'),
    table_service: TableService = Depends(get_table_service),
) -> list[Table]:
    """Получить все столики для кафе."""
    tables = await table_service.get_all_tables_for_cafe(
        cafe_id=cafe_id,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return [Table.model_validate(t) for t in tables]


@router.get(
    '/{table_id}',
    response_model=Table,
    summary='Получить столик по ID',
    responses={
        404: {'description': 'Столик не найден'},
        410: {'description': 'Столик удален или кафе удалено'},
    },
)
async def get_table(
    table_id: int,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Получить столик по ID."""
    table = await table_service.get_table_by_id(table_id)
    return Table.model_validate(table)


@router.get(
    '/cafe/{cafe_id}/{table_id}',
    response_model=Table,
    summary='Получить столик по ID кафе и ID столика',
    responses={
        404: {'description': 'Столик не найден в этом кафе'},
        410: {'description': 'Столик удален'},
    },
)
async def get_table_by_cafe_and_id(
    cafe_id: int,
    table_id: int,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Получить столик по ID кафе и ID столика."""
    table = await table_service.get_table_by_cafe_and_id(cafe_id, table_id)
    return Table.model_validate(table)


@router.post(
    '/',
    response_model=Table,
    status_code=status.HTTP_201_CREATED,
    summary='Создать новый столик',
    responses={
        404: {'description': 'Кафе не найдено'},
        400: {'description': 'Нельзя добавить столик в удаленное кафе'},
    },
)
async def create_table(
    table_create: TableCreate,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Создать новый столик."""
    table = await table_service.create_table(table_create)
    return Table.model_validate(table)


@router.patch(
    '/{table_id}',
    response_model=Table,
    summary='Обновить столик',
    responses={
        404: {'description': 'Столик не найден'},
        400: {
            'description': 'Количество мест должно быть положительным числом',
        },
    },
)
async def update_table(
    table_id: int,
    table_update: TableUpdate,
    table_service: TableService = Depends(get_table_service),
) -> Table:
    """Обновить столик."""
    table = await table_service.update_table(table_id, table_update)
    return Table.model_validate(table)


@router.delete(
    '/{table_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удалить столик',
    responses={404: {'description': 'Столик не найдено'}},
)
async def delete_table(
    table_id: int,
    table_service: TableService = Depends(get_table_service),
) -> None:
    """Удалить столик (логически)."""
    await table_service.delete_table(table_id)


@router.get(
    '/{table_id}/stats',
    summary='Получить статистику по столику',
    responses={404: {'description': 'Столик не найден'}},
)
async def get_table_stats(
    table_id: int,
    table_service: TableService = Depends(get_table_service),
) -> dict:
    """Получить статистику по столику."""
    return await table_service.get_table_stats(table_id)
