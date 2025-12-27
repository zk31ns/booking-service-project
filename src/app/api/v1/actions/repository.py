from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.actions.schemas import ActionCreate, ActionUpdate
from app.models import Action


class ActionRepository:
    """Репозиторий для работы с акциями."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session."""
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Action]:
        """Получить все акции."""
        stmt = select(Action).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, action_id: int) -> Optional[Action]:
        """Получить акцию по ID."""
        stmt = select(Action).where(Action.id == action_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, action_data: ActionCreate) -> Action:
        """Создать новую акцию."""
        action = Action(**action_data.model_dump())
        self.session.add(action)
        await self.session.flush()
        return action

    async def update(
        self, action_id: int, action_data: ActionUpdate
    ) -> Optional[Action]:
        """Обновить акцию."""
        action = await self.get_by_id(action_id)
        if not action:
            return None

        update_data = action_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(action, field, value)

        await self.session.flush()
        return action

    async def delete(self, action_id: int) -> bool:
        """Логическое удаление акции."""
        action = await self.get_by_id(action_id)
        if not action:
            return False

        action.active = False
        await self.session.flush()
        return True
