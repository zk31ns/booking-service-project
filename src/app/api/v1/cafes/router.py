from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_manager_or_superuser,
    get_current_user,
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
    summary='Получение списка кафе',
    description=(
        'Получение списка кафе. Для администраторов и менеджеров - '
        'все кафе (с возможностью выбора), для пользователей - '
        'только активные.'
    ),
)
async def get_cafes(
    show_all: bool = Query(
        True,
        description=(
            'Показывать все кафе или нет. По умолчанию показывает все кафе'
        ),
    ),
    cafe_service: CafeService = Depends(get_cafe_service),
    _current_user: User = Depends(get_current_user),
) -> list[Cafe]:
    """Получить список всех кафе.

    Args:
        show_all: Показывать все кафе, включая неактивные.
        cafe_service: Сервис для работы с кафе (внедряется автоматически).
        current_user: Текущий пользователь.

    Returns:
        List[Cafe]: Список кафе.

    """
    return await cafe_service.get_all_cafes(
        show_all=show_all,
    )


@router.post(
    '',
    response_model=CafeWithRelations,
    status_code=status.HTTP_201_CREATED,
    summary='Создать новое кафе',
    description='Создает новое кафе. Только для администраторов и менеджеров',
    responses={
        400: {'description': Messages.errors[ErrorCode.VALIDATION_ERROR]},
        409: {'description': Messages.errors[ErrorCode.CAFE_ALREADY_EXISTS]},
    },
)
async def create_cafe(
    cafe_create: CafeCreate,
    cafe_service: CafeService = Depends(get_cafe_service),
    _current_user: User = Depends(get_current_manager_or_superuser),
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


@router.get(
    '/{cafe_id}',
    response_model=Cafe,
    summary='Получить кафе по ID',
    responses={
        404: {'description': Messages.errors[ErrorCode.CAFE_NOT_FOUND]},
    },
)
async def get_cafe(
    cafe_id: int,
    cafe_service: CafeService = Depends(get_cafe_service),
    current_user: User = Depends(get_current_user),
) -> Cafe:
    """Получить кафе по идентификатору.

    Args:
        cafe_id: Идентификатор кафе.
        cafe_service: Сервис для работы с кафе (внедряется автоматически).
        current_user: Текущий пользователь.

    Returns:
        Cafe: Объект кафе.

    Raises:
        HTTPException: Если кафе не найдено (статус 404).

    """
    allow_inactive = current_user.is_superuser
    if not allow_inactive:
        allow_inactive = await cafe_service.is_user_manager(current_user.id)
    return await cafe_service.get_cafe_by_id(
        cafe_id,
        allow_inactive=allow_inactive,
    )


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
