from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode, RedisKey, Times
from app.core.redis_cache import RedisCache
from app.db.session import get_session
from app.schemas.slot import SlotCreate, SlotInfo, SlotUpdate
from app.services.slot import SlotService

router = APIRouter(prefix='/cafes/{cafe_id}/slots')


@router.get('', response_model=list[SlotInfo], status_code=status.HTTP_200_OK)
async def get_all_slots(
    cafe_id: int,
    show_inactive: bool = False,
    session: AsyncSession = Depends(get_session),
) -> list[SlotInfo]:
    """Получение всех слотов кафе."""
    cache_key = f'{RedisKey.CACHE_KEY_ALL_SLOTS}:{cafe_id}:{show_inactive}'
    cached_data = await RedisCache.get(cache_key)
    if cached_data is not None:
        return [SlotInfo(**item) for item in cached_data]
    service = SlotService(session)
    slots = await service.get_cafe_slots(cafe_id, show_inactive)
    slots_response = [SlotInfo.model_validate(slot) for slot in slots]
    logger.info(f'Получены слоты для кафе cafe_id={cafe_id}')
    await RedisCache.set(
        cache_key,
        [s.model_dump(mode='json') for s in slots_response],
        expire=Times.REDIS_CACHE_EXPIRE_TIME,
    )
    return slots_response


@router.post('', response_model=SlotInfo, status_code=status.HTTP_201_CREATED)
async def create_slot(
    cafe_id: int,
    data: SlotCreate,
    session: AsyncSession = Depends(get_session),
) -> SlotInfo:
    """Создание нового слота для кафе.

    Args:
        cafe_id: Идентификатор кафе.
        data: Данные для создания слота (время начала и окончания).
        session: Сессия БД (внедряется автоматически).

    Returns:
        SlotInfo: Информация о созданном слоте.

    """
    service = SlotService(session)
    slot = await service.create_slot(cafe_id, data.start_time, data.end_time)
    await session.commit()
    cache_pattern = f'{RedisKey.CACHE_KEY_ALL_SLOTS}:{cafe_id}:*'
    await RedisCache.delete_pattern(cache_pattern)
    logger.info(f'Создан слот для кафе cafe_id={cafe_id}')
    return slot


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
) -> SlotInfo:
    """Обновление слота.

    Args:
        cafe_id: Идентификатор кафе.
        slot_id: Идентификатор слота.
        data: Данные для обновления слота (может содержать время и статус).
        session: Сессия БД (внедряется автоматически).

    Returns:
        SlotInfo: Информация об обновленном слоте.

    Raises:
        HTTPException: Если слот не найден (статус 404).

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
    slot_response = SlotInfo.model_validate(slot)
    await session.commit()
    cache_pattern = f'{RedisKey.CACHE_KEY_ALL_SLOTS}:{cafe_id}:*'
    await RedisCache.delete_pattern(cache_pattern)
    logger.info(f'Обновлен слот slot_id={slot_id}')
    return slot_response


@router.delete('/{slot_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    cafe_id: int,
    slot_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удаление слота.

    Args:
        cafe_id: Идентификатор кафе.
        slot_id: Идентификатор слота.
        session: Сессия БД (внедряется автоматически).

    Returns:
        None: Не возвращает данные (статус 204 No Content).

    Raises:
        HTTPException: Если слот не найден (статус 404).

    """
    service = SlotService(session)
    result = await service.delete_slot(slot_id, cafe_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCode.SLOT_NOT_FOUND,
        )
    await session.commit()
    cache_pattern = f'{RedisKey.CACHE_KEY_ALL_SLOTS}:{cafe_id}:*'
    await RedisCache.delete_pattern(cache_pattern)
    logger.info(f'Удален слот slot_id={slot_id}')
