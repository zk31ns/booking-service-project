from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dishes.constants import DEFAULT_LIMIT, DEFAULT_SKIP
from app.api.v1.dishes.schemas import DishCreate, DishInfo, DishUpdate
from app.api.v1.dishes.service import DishService
from app.db import get_session

router = APIRouter(prefix='/dishes', tags=['dishes'])


async def get_dish_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DishService:
    """Получить сервис для работы с блюдами."""
    return DishService(session)


@router.get('/', response_model=list[DishInfo])
async def get_dishes(
    skip: int = DEFAULT_SKIP,
    limit: int = DEFAULT_LIMIT,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
) -> list[DishInfo]:
    """Получить список всех блюд."""
    return await service.get_all_dishes(skip, limit)


@router.get('/{dish_id}', response_model=DishInfo)
async def get_dish(
    dish_id: int,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
) -> DishInfo:
    """Получить блюдо по ID."""
    dish = await service.get_dish(dish_id)
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Dish not found'
        )
    return dish


@router.post('/', response_model=DishInfo, status_code=status.HTTP_201_CREATED)
async def create_dish(
    dish_data: DishCreate,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
) -> DishInfo:
    """Создать новое блюдо."""
    return await service.create_dish(dish_data)


@router.patch('/{dish_id}', response_model=DishInfo)
async def update_dish(
    dish_id: int,
    dish_data: DishUpdate,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
) -> DishInfo:
    """Обновить блюдо."""
    dish = await service.update_dish(dish_id, dish_data)
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Dish not found'
        )
    return dish


@router.delete('/{dish_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish(
    dish_id: int,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
) -> None:
    """Удалить блюдо."""
    success = await service.delete_dish(dish_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Dish not found'
        )
