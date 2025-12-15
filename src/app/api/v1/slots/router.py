from fastapi import APIRouter, Depends, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.slots.schemas import SlotCreate, SlotInfo, SlotUpdate
from app.api.v1.slots.service import SlotService
from app.db.session import get_session

router = APIRouter(prefix='/cafes/{cafe_id}/slots')


@router.get('', response_model=list[SlotInfo], status_code=status.HTTP_200_OK)
async def get_all_slots(
    cafe_id: int,
    show_inactive: bool = False,
    session: AsyncSession = Depends(get_session),
) -> list[SlotInfo]:
    """Получение всех слотов кафе."""
    service = SlotService(session)
    slots = await service.get_cafe_slots(cafe_id, show_inactive)
    logger.info(f'Получены слоты для кафе cafe_id={cafe_id}')
    return slots


@router.post('', response_model=SlotInfo, status_code=status.HTTP_201_CREATED)
async def create_slot(
    cafe_id: int,
    data: SlotCreate,
    session: AsyncSession = Depends(get_session),
) -> SlotInfo:
    """Создание нового слота для кафе."""
    service = SlotService(session)
    slot = await service.create_slot(cafe_id, data.start_time, data.end_time)
    await session.commit()
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
    """Обновление слота."""
    service = SlotService(session)
    slot = await service.update_slot(
        slot_id,
        data.start_time,
        data.end_time,
        data.active,
    )
    if not slot:
        logger.warning(f'Слот slot_id={slot_id} не найден')
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Слот не найден')
    await session.commit()
    logger.info(f'Обновлен слот slot_id={slot_id}')
    return slot


@router.delete('/{slot_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    cafe_id: int,
    slot_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удаление слота."""
    service = SlotService(session)
    result = await service.delete_slot(slot_id)
    if not result:
        logger.warning(f'Слот slot_id={slot_id} не найден')
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Слот не найден')
    await session.commit()
    logger.info(f'Удален слот slot_id={slot_id}')
