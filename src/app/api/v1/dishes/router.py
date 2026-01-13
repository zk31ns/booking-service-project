from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_manager_or_superuser,
    get_current_user,
)
from app.api.v1.dishes.schemas import DishCreate, DishInfo, DishUpdate
from app.api.v1.dishes.service import DishService
from app.core.constants import API
from app.core.database import get_session
from app.models import User

router = APIRouter(prefix='/dishes', tags=API.DISHES)


async def get_dish_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DishService:
    """Получить сервис для работы с блюдами.

    Args:
        session: Асинхронная сессия SQLAlchemy.

    Returns:
        DishService: Сервис для работы с блюдами.

    """
    return DishService(session)


@router.get('', response_model=list[DishInfo])
async def get_dishes(
    show_all: bool = Query(
        True,
        description=(
            'Показывать все блюда или нет. По умолчанию показывает все блюда'
        ),
    ),
    cafe_id: int | None = Query(
        None, description='Фильтр по ID кафе, если нужен.'
    ),
    session: AsyncSession = Depends(get_session),
    service: Annotated[DishService, Depends(get_dish_service)] = None,
    _current_user: User = Depends(get_current_user),
) -> list[DishInfo]:
    """Получить список блюд.

    Args:
        show_all: Возвращать неактивные блюда.
        cafe_id: Фильтр по ID кафе.
        session: Асинхронная сессия БД.
        service: Сервис для работы с блюдами.
        current_user: Текущий пользователь.

    Returns:
        list[DishInfo]: Список блюд.

    """
    return await service.get_all_dishes(show_all=show_all, cafe_id=cafe_id)


@router.get('/{dish_id}', response_model=DishInfo)
async def get_dish(
    dish_id: int,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
    _current_user: User = Depends(get_current_user),
) -> DishInfo:
    """Получить блюдо по ID.

    Args:
        dish_id: Идентификатор блюда.
        service: Сервис для работы с блюдами.
        _current_user: Текущий пользователь.

    Returns:
        DishInfo: Блюдо.

    """
    return await service.get_dish(dish_id)


@router.post('', response_model=DishInfo, status_code=status.HTTP_201_CREATED)
async def create_dish(
    dish_data: DishCreate,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
    _current_user: User = Depends(get_current_manager_or_superuser),
) -> DishInfo:
    """Создать блюдо.

    Args:
        dish_data: Данные для создания блюда.
        service: Сервис для работы с блюдами.
        _current_user: Текущий пользователь.

    Returns:
        DishInfo: Созданное блюдо.

    """
    return await service.create_dish(dish_data)


@router.patch('/{dish_id}', response_model=DishInfo)
async def update_dish(
    dish_id: int,
    dish_data: DishUpdate,
    service: Annotated[DishService, Depends(get_dish_service)] = None,
    _current_user: User = Depends(get_current_manager_or_superuser),
) -> DishInfo:
    """Обновить блюдо по ID.

    Args:
        dish_id: Идентификатор блюда.
        dish_data: Данные для обновления.
        service: Сервис для работы с блюдами.
        _current_user: Текущий пользователь.

    Returns:
        DishInfo: Обновленное блюдо.

    """
    return await service.update_dish(dish_id, dish_data)
