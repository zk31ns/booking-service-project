from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.actions.repository import ActionRepository
from app.api.v1.actions.schemas import (
    ActionCreate,
    ActionInfo,
    ActionUpdate,
)
from app.models import Cafe


class ActionService:
    """Сервис для работы с акциями."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализировать сервис.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        self.repository = ActionRepository(session)

    async def get_all_actions(
        self, show_all: bool = False, cafe_id: int | None = None
    ) -> list[ActionInfo]:
        """Получить список акций.

        Args:
            show_all: Возвращать неактивные акции.
            cafe_id: Фильтр по ID кафе.

        Returns:
            list[ActionInfo]: Список акций.

        """
        actions = await self.repository.get_all(
            show_all=show_all, cafe_id=cafe_id
        )
        return [ActionInfo.model_validate(action) for action in actions]

    async def get_action(self, action_id: int) -> ActionInfo | None:
        """Получить акцию по ID.

        Args:
            action_id: Идентификатор акции.

        Returns:
            ActionInfo | None: Акция или None.

        """
        action = await self.repository.get_by_id(action_id)
        if not action:
            return None
        return ActionInfo.model_validate(action)

    async def create_action(self, action_data: ActionCreate) -> ActionInfo:
        """Создать акцию.

        Args:
            action_data: Данные для создания акции.

        Returns:
            ActionInfo: Созданная акция.

        """
        cafes = await self._get_cafes(action_data.cafes_id)
        action = await self.repository.create(action_data, cafes)
        return ActionInfo.model_validate(action)

    async def update_action(
        self, action_id: int, action_data: ActionUpdate
    ) -> ActionInfo | None:
        """Обновить акцию.

        Args:
            action_id: Идентификатор акции.
            action_data: Данные для обновления.

        Returns:
            ActionInfo | None: Обновленная акция или None.

        """
        cafes = None
        if action_data.cafes_id is not None:
            cafes = await self._get_cafes(action_data.cafes_id)
        action = await self.repository.update(action_id, action_data, cafes)
        if not action:
            return None
        return ActionInfo.model_validate(action)

    async def delete_action(self, action_id: int) -> bool:
        """Деактивировать акцию.

        Args:
            action_id: Идентификатор акции.

        Returns:
            bool: True, если акция деактивирована.

        """
        return await self.repository.delete(action_id)

    async def _get_cafes(self, cafes_id: list[int]) -> list[Cafe]:
        """Получить список кафе по идентификаторам.

        Args:
            cafes_id: Список ID кафе.

        Returns:
            list[Cafe]: Список кафе.

        Raises:
            HTTPException: Если хотя бы одно кафе не найдено.

        """
        if not cafes_id:
            return []
        stmt = select(Cafe).where(Cafe.id.in_(cafes_id))
        result = await self.repository.session.execute(stmt)
        cafes = list(result.scalars().all())
        if len(cafes) != len(set(cafes_id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Cafe not found',
            )
        return cafes
