from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_db
from src.app.core.constants import TAGS_CAFES, Limits, RedisKey, Times
from src.app.core.redis_cache import RedisCache
from src.app.repositories.cafes import CafeRepository
from src.app.repositories.tables import TableRepository
from src.app.schemas.cafes import Cafe, CafeCreate, CafeUpdate
from src.app.services.cafes import CafeService

router = APIRouter(prefix='/cafes', tags=TAGS_CAFES)


def get_cafe_service(db: AsyncSession = Depends(get_db)) -> CafeService:
    """Получить сервис для работы с кафе."""
    cafe_repository = CafeRepository(db)
    table_repository = TableRepository(db)
    return CafeService(cafe_repository, table_repository)


@router.get(
    '/',
    response_model=list[Cafe],
    summary='Получить список всех кафе',
    description='Возвращает список кафе с пагинацией',
)
async def get_cafes(
    skip: int = Query(0, ge=0, description='Количество записей для пропуска'),
    limit: int = Query(
        Limits.DEFAULT_PAGE_SIZE,
        ge=1,
        le=Limits.MAX_PAGE_SIZE,
        description=f'Количество записей на странице ({Limits.MAX_PAGE_SIZE})',
    ),
    active_only: bool = Query(True, description='Только активные кафе'),
    cafe_service: CafeService = Depends(get_cafe_service),
) -> list[Cafe]:
    """Получить все кафе."""
    cache_key = f'{RedisKey.CACHE_KEY_ALL_CAFES}:{skip}:{limit}:{active_only}'
    cached_data = await RedisCache.get(cache_key)
    if cached_data is not None:
        return [Cafe(**item) for item in cached_data]
    cafes = await cafe_service.get_all_cafes(
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    await RedisCache.set(
        cache_key,
        cafes,
        expire=Times.REDIS_CACHE_EXPIRE_TIME,
    )
    return [Cafe.model_validate(c) for c in cafes]


@router.get(
    '/{cafe_id}',
    response_model=Cafe,
    summary='Получить кафе по ID',
    responses={
        404: {'description': 'Кафе не найдено'},
        410: {'description': 'Кафе удалено'},
    },
)
async def get_cafe(
    cafe_id: int,
    cafe_service: CafeService = Depends(get_cafe_service),
) -> Cafe:
    """Получить кафе по ID."""
    cafe = await cafe_service.get_cafe_by_id(cafe_id)
    return Cafe.model_validate(cafe)


@router.post(
    '/',
    response_model=Cafe,
    status_code=status.HTTP_201_CREATED,
    summary='Создать новое кафе',
    responses={400: {'description': 'Кафе с таким названием уже существует'}},
)
async def create_cafe(
    cafe_create: CafeCreate,
    cafe_service: CafeService = Depends(get_cafe_service),
) -> Cafe:
    """Создать новое кафе."""
    cafe = await cafe_service.create_cafe(cafe_create)
    await RedisCache.delete_pattern(f'{RedisKey.CACHE_KEY_ALL_CAFES}:*')
    return Cafe.model_validate(cafe)


@router.patch(
    '/{cafe_id}',
    response_model=Cafe,
    summary='Обновить кафе',
    responses={
        404: {'description': 'Кафе не найдено'},
        400: {'description': 'Кафе с таким названием уже существует'},
    },
)
async def update_cafe(
    cafe_id: int,
    cafe_update: CafeUpdate,
    cafe_service: CafeService = Depends(get_cafe_service),
) -> Cafe:
    """Обновить кафе."""
    cafe = await cafe_service.update_cafe(cafe_id, cafe_update)
    await RedisCache.delete_pattern(f'{RedisKey.CACHE_KEY_ALL_CAFES}:*')
    return Cafe.model_validate(cafe)


@router.delete(
    '/{cafe_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удалить кафе',
    responses={404: {'description': 'Кафе не найдено'}},
)
async def delete_cafe(
    cafe_id: int,
    cafe_service: CafeService = Depends(get_cafe_service),
) -> None:
    """Удалить кафе (логически)."""
    await cafe_service.delete_cafe(cafe_id)
    await RedisCache.delete_pattern(f'{RedisKey.CACHE_KEY_ALL_CAFES}:*')
    return
