from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_superuser,
    get_db,
    require_cafe_manager,
)
from app.core.constants import API, ErrorCode, Messages
from app.models import User
from app.repositories.cafes import CafeRepository
from app.repositories.tables import TableRepository
from app.schemas.cafes import Cafe, CafeCreate, CafeUpdate, CafeWithRelations
from app.services.cafes import CafeService

router = APIRouter(prefix='/cafes', tags=API.CAFES)


def get_cafe_service(db: AsyncSession = Depends(get_db)) -> CafeService:
    """Получить сервис для работы с кафе.

    Args:
        db: Сессия БД (внедряется автоматически).

    Returns:
        CafeService: Сервис для работы с кафе.

    """
    cafe_repository = CafeRepository(db)
    table_repository = TableRepository(db)
    return CafeService(cafe_repository, table_repository, db)


@router.get(
    '',
    response_model=list[Cafe],
    summary='Получить список всех кафе',
    description='Возвращает список всех кафе',
)
async def get_cafes(
    active_only: bool = Query(True, description='Только активные кафе'),
    cafe_service: CafeService = Depends(get_cafe_service),
) -> list[Cafe]:
    """Получить список всех кафе.

    Args:
        active_only: Флаг фильтрации только активных кафе.
        cafe_service: Сервис для работы с кафе (внедряется автоматически).

    Returns:
        List[Cafe]: Список кафе.

    """
    return await cafe_service.get_all_cafes(
        active_only=active_only,
    )


@router.get(
    '/{cafe_id}',
    response_model=Cafe,
    summary='Получить кафе по ID',
    responses={
        404: {'description': Messages.errors[ErrorCode.CAFE_NOT_FOUND]},
        410: {'description': Messages.errors[ErrorCode.CAFE_INACTIVE]},
    },
)
async def get_cafe(
    cafe_id: int,
    cafe_service: CafeService = Depends(get_cafe_service),
) -> Cafe:
    """Получить кафе по идентификатору.

    Args:
        cafe_id: Идентификатор кафе.
        cafe_service: Сервис для работы с кафе (внедряется автоматически).

    Returns:
        Cafe: Объект кафе.

    Raises:
        HTTPException: Если кафе не найдено (статус 404).
        HTTPException: Если кафе удалено (статус 410).

    """
    return await cafe_service.get_cafe_by_id(cafe_id)


@router.post(
    '',
    response_model=CafeWithRelations,
    status_code=status.HTTP_201_CREATED,
    summary='Создать новое кафе',
    responses={
        400: {'description': Messages.errors[ErrorCode.VALIDATION_ERROR]},
        409: {'description': Messages.errors[ErrorCode.CAFE_ALREADY_EXISTS]},
    },
)
async def create_cafe(
    cafe_create: CafeCreate,
    cafe_service: CafeService = Depends(get_cafe_service),
    _current_user: User = Depends(get_current_superuser),
) -> Cafe:
    """Создать новое кафе.

    Args:
        cafe_create: Данные для создания кафе.
        cafe_service: Сервис для работы с кафе (внедряется автоматически).

    Returns:
        Cafe: Созданное кафе.

    Raises:
        HTTPException: 400 - Ошибка валидации.
        HTTPException: 409 - Кафе с таким названием уже существует.

    """
    return await cafe_service.create_cafe(cafe_create)


@router.patch(
    '/{cafe_id}',
    response_model=CafeWithRelations,
    summary='Обновить кафе',
    responses={
        404: {'description': Messages.errors[ErrorCode.CAFE_NOT_FOUND]},
        400: {'description': Messages.errors[ErrorCode.VALIDATION_ERROR]},
        409: {'description': Messages.errors[ErrorCode.DATA_CONFLICT]},
    },
)
async def update_cafe(
    cafe_id: int,
    cafe_update: CafeUpdate,
    cafe_service: CafeService = Depends(get_cafe_service),
    _current_user: User = Depends(require_cafe_manager),
) -> Cafe:
    """Обновить данные кафе.

    Args:
        cafe_id: Идентификатор кафе.
        cafe_update: Данные для обновления кафе.
        cafe_service: Сервис для работы с кафе (внедряется автоматически).

    Returns:
        Cafe: Обновленный объект кафе.

    Raises:
        HTTPException: 404 - Если кафе не найдено.
        HTTPException: 409 - При конфликте данных.

    """
    return await cafe_service.update_cafe(cafe_id, cafe_update)
