from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_manager_or_superuser,
    get_current_user,
)
from app.core.constants import API, ErrorCode, RedisKey, Times
from app.core.database import get_session
from app.core.exceptions import AuthorizationException
from app.core.redis_cache import RedisCache
from app.models import User
from app.schemas.slot import SlotCreate, SlotInfo, SlotUpdate
from app.services.slot import SlotService

router = APIRouter(prefix='/cafe/{cafe_id}/time_slots', tags=API.SLOTS)


@router.get('', response_model=list[SlotInfo], status_code=status.HTTP_200_OK)
async def get_all_slots(
    cafe_id: int,
    show_all: bool = Query(
        False,
        description='Включать неактивные временные слоты.',
    ),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SlotInfo]:
    """Возвращает список слотов времени для кафе.

    Args:
        cafe_id: Идентификатор кафе.
        show_all: Возвращать ли неактивные слоты.
        session: Сессия БД.
        current_user: Текущий пользователь.

    Returns:
        list[SlotInfo]: Список слотов.

    """
    if show_all:
        try:
            await get_current_manager_or_superuser(current_user, session)
        except AuthorizationException:
            show_all = False

    cache_key = f'{RedisKey.CACHE_KEY_ALL_SLOTS}:{cafe_id}:{show_all}'
    cached_data = await RedisCache.get(cache_key)
    if cached_data is not None:
        return [SlotInfo(**item) for item in cached_data]

    service = SlotService(session)
    slots = await service.get_cafe_slots(cafe_id, show_all)
    slots_response = [SlotInfo.model_validate(slot) for slot in slots]
    logger.info(f'Loaded time slots for cafe_id={cafe_id}')
    await RedisCache.set(
        cache_key,
        [s.model_dump(mode='json') for s in slots_response],
        expire=Times.REDIS_CACHE_EXPIRE_TIME,
    )
    return slots_response


@router.get('/{slot_id}', response_model=SlotInfo)
async def get_slot(
    cafe_id: int,
    slot_id: int,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> SlotInfo:
    """Возвращает слот времени по идентификатору.

    Args:
        cafe_id: Идентификатор кафе.
        slot_id: Идентификатор слота.
        session: Сессия БД.
        _current_user: Текущий пользователь.

    Returns:
        SlotInfo: Слот времени.

    Raises:
        HTTPException: Слот не найден.

    """
    service = SlotService(session)
    slot = await service.get_slot(slot_id)
    if not slot or slot.cafe_id != cafe_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCode.SLOT_NOT_FOUND,
        )
    return SlotInfo.model_validate(slot)


@router.post('', response_model=SlotInfo, status_code=status.HTTP_201_CREATED)
async def create_slot(
    cafe_id: int,
    data: SlotCreate,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_manager_or_superuser),
) -> SlotInfo:
    """Создает слот времени.

    Доступно менеджерам и администраторам.

    Args:
        cafe_id: Идентификатор кафе.
        data: Данные для создания слота.
        session: Сессия БД.
        _current_user: Текущий пользователь.

    Returns:
        SlotInfo: Созданный слот.

    """
    service = SlotService(session)
    slot = await service.create_slot(cafe_id, data.start_time, data.end_time)
    await session.commit()
    cache_pattern = f'{RedisKey.CACHE_KEY_ALL_SLOTS}:{cafe_id}:*'
    await RedisCache.delete_pattern(cache_pattern)
    logger.info(f'Created time slot for cafe_id={cafe_id}')
    return SlotInfo.model_validate(slot)


@router.patch(
    '/{slot_id}',
    response_model=SlotInfo,
    status_code=status.HTTP_200_OK,
)
async def update_slot(
    cafe_id: int,
    slot_id: int,
    data: SlotUpdate,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_manager_or_superuser),
) -> SlotInfo:
    """Обновляет слот времени.

    Доступно менеджерам и администраторам.

    Args:
        cafe_id: Идентификатор кафе.
        slot_id: Идентификатор слота.
        data: Данные для обновления слота.
        session: Сессия БД.
        _current_user: Текущий пользователь.

    Returns:
        SlotInfo: Обновленный слот.

    Raises:
        HTTPException: Слот не найден.

    """
    service = SlotService(session)
    slot = await service.update_slot(
        slot_id,
        cafe_id,
        data.start_time,
        data.end_time,
        data.active,
    )
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCode.SLOT_NOT_FOUND,
        )
    await session.commit()
    cache_pattern = f'{RedisKey.CACHE_KEY_ALL_SLOTS}:{cafe_id}:*'
    await RedisCache.delete_pattern(cache_pattern)
    logger.info(f'Updated time slot id={slot_id}')
    return SlotInfo.model_validate(slot)
