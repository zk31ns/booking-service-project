from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.actions.constants import DEFAULT_LIMIT, DEFAULT_SKIP
from app.api.v1.actions.schemas import (
    ActionCreate,
    ActionInfo,
    ActionUpdate,
)
from app.api.v1.actions.service import ActionService
from app.db import get_session

router = APIRouter(prefix='/actions', tags=['actions'])


async def get_action_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ActionService:
    """Получить сервис для работы с акциями."""
    return ActionService(session)


@router.get('/', response_model=list[ActionInfo])
async def get_actions(
    skip: int = DEFAULT_SKIP,
    limit: int = DEFAULT_LIMIT,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
) -> list[ActionInfo]:
    """Получить список всех акций."""
    return await service.get_all_actions(skip, limit)


@router.get('/{action_id}', response_model=ActionInfo)
async def get_action(
    action_id: int,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
) -> ActionInfo:
    """Получить акцию по ID."""
    action = await service.get_action(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Action not found'
        )
    return action


@router.post(
    '/', response_model=ActionInfo, status_code=status.HTTP_201_CREATED
)
async def create_action(
    action_data: ActionCreate,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
) -> ActionInfo:
    """Создать новую акцию."""
    return await service.create_action(action_data)


@router.patch('/{action_id}', response_model=ActionInfo)
async def update_action(
    action_id: int,
    action_data: ActionUpdate,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
) -> ActionInfo:
    """Обновить акцию."""
    action = await service.update_action(action_id, action_data)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Action not found'
        )
    return action


@router.delete('/{action_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: int,
    service: Annotated[ActionService, Depends(get_action_service)] = None,
) -> None:
    """Удалить акцию."""
    success = await service.delete_action(action_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Action not found'
        )
