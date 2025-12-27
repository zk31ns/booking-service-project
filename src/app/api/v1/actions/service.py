from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.actions.constants import DEFAULT_LIMIT, DEFAULT_SKIP
from app.api.v1.actions.repository import ActionRepository
from app.api.v1.actions.schemas import (
    ActionCreate,
    ActionInfo,
    ActionUpdate,
)


class ActionService:
    """Сервис для работы с акциями."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with session."""
        self.repository = ActionRepository(session)

    async def get_all_actions(
        self, skip: int = DEFAULT_SKIP, limit: int = DEFAULT_LIMIT
    ) -> list[ActionInfo]:
        """Получить все акции."""
        actions = await self.repository.get_all(skip, limit)
        return [ActionInfo.model_validate(action) for action in actions]

    async def get_action(self, action_id: int) -> Optional[ActionInfo]:
        """Получить акцию по ID."""
        action = await self.repository.get_by_id(action_id)
        if not action:
            return None
        return ActionInfo.model_validate(action)

    async def create_action(self, action_data: ActionCreate) -> ActionInfo:
        """Создать новую акцию."""
        action = await self.repository.create(action_data)
        return ActionInfo.model_validate(action)

    async def update_action(
        self, action_id: int, action_data: ActionUpdate
    ) -> Optional[ActionInfo]:
        """Обновить акцию."""
        action = await self.repository.update(action_id, action_data)
        if not action:
            return None
        return ActionInfo.model_validate(action)

    async def delete_action(self, action_id: int) -> bool:
        """Удалить акцию (логическое удаление)."""
        return await self.repository.delete(action_id)
