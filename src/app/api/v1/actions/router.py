from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_manager_or_superuser,
    get_current_user,
)
from app.api.v1.actions.schemas import (
    ActionCreate,
    ActionInfo,
    ActionUpdate,
)
from app.api.v1.actions.service import ActionService
from app.core.constants import API
from app.core.database import get_session
from app.models import User

router = APIRouter(prefix='/actions', tags=API.ACTIONS)


async def get_action_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ActionService:
    """Получить сервис для работы с акциями.

    Args:
        session: Асинхронная сессия SQLAlchemy.

    Returns:
        ActionService: Сервис для работы с акциями.

    """
    return ActionService(session)


@router.get('', response_model=list[ActionInfo])
async def get_actions(
    show_all: bool = Query(False, description='Включать неактивные акции.'),
    cafe_id: int | None = Query(
        None, description='Фильтр по ID кафе, если нужен.'
    ),
    service: Annotated[ActionService, Depends(get_action_service)] = None,
    _current_user: User = Depends(get_current_user),
) -> list[ActionInfo]:
    """Получить список акций.

    Args:
        show_all: Возвращать неактивные акции.
        cafe_id: Фильтр по ID кафе.
        service: Сервис для работы с акциями.
        _current_user: Текущий пользователь.

    Returns:
        list[ActionInfo]: Список акций.

    """
    return await service.get_all_actions(show_all=show_all, cafe_id=cafe_id)


@router.get('/{action_id}', response_model=ActionInfo)
async def get_action(
    action_id: int,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
    _current_user: User = Depends(get_current_user),
) -> ActionInfo:
    """Получить акцию по ID.

    Args:
        action_id: Идентификатор акции.
        service: Сервис для работы с акциями.
        _current_user: Текущий пользователь.

    Returns:
        ActionInfo: Акция.

    """
    return await service.get_action(action_id)


@router.post(
    '', response_model=ActionInfo, status_code=status.HTTP_201_CREATED
)
async def create_action(
    action_data: ActionCreate,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
    _current_user: User = Depends(get_current_manager_or_superuser),
) -> ActionInfo:
    """Создать акцию.

    Args:
        action_data: Данные для создания акции.
        service: Сервис для работы с акциями.
        _current_user: Текущий пользователь.

    Returns:
        ActionInfo: Созданная акция.

    """
    return await service.create_action(action_data)


@router.patch('/{action_id}', response_model=ActionInfo)
async def update_action(
    action_id: int,
    action_data: ActionUpdate,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
    _current_user: User = Depends(get_current_manager_or_superuser),
) -> ActionInfo:
    """Обновить акцию по ID.

    Args:
        action_id: Идентификатор акции.
        action_data: Данные для обновления.
        service: Сервис для работы с акциями.
        _current_user: Текущий пользователь.

    Returns:
        ActionInfo: Обновленная акция.

    """
    return await service.update_action(action_id, action_data)
