from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.actions.schemas import ActionCreate, ActionUpdate
from app.core.constants import Limits
from app.models import Action, Cafe
from app.repositories.base import BaseCRUD


class ActionRepository(BaseCRUD[Action]):
    """Репозиторий для работы с акциями."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализировать репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        """
        super().__init__(session, Action)

    async def get_all(
        self, show_all: bool = False, cafe_id: int | None = None
    ) -> list[Action]:
        """Получить список акций.

        Args:
            show_all: Возвращать неактивные акции.
            cafe_id: Фильтр по ID кафе.

        Returns:
            list[Action]: Список акций.

        """
        stmt = select(Action)
        if not show_all:
            stmt = stmt.where(Action.active)
        if cafe_id is not None:
            stmt = stmt.join(Action.cafes).where(Cafe.id == cafe_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, action_id: int) -> Action | None:
        """Получить акцию по ID.

        Args:
            action_id: Идентификатор акции.

        Returns:
            Action | None: Акция или None.

        """
        return await self.get(action_id)

    async def create(
        self, action_data: ActionCreate, cafes: list['Cafe']
    ) -> Action:
        """Создать акцию и привязать к кафе.

        Args:
            action_data: Данные для создания акции.
            cafes: Список кафе для привязки.

        Returns:
            Action: Созданная акция.

        """
        payload = action_data.model_dump()
        payload.pop('cafes_id', None)
        description = payload.get('description') or ''
        payload['name'] = (
            description[: Limits.ACTION_NAME_MAX_LENGTH] or 'Action'
        )
        if payload.get('photo_id') is not None:
            payload['photo_id'] = str(payload['photo_id'])
        action = Action(**payload)
        action.cafes = cafes
        self.session.add(action)
        await self.session.flush()
        await self.session.refresh(action)
        return action

    async def update(
        self,
        action_id: int,
        action_data: ActionUpdate,
        cafes: list['Cafe'] | None,
    ) -> Action | None:
        """Обновить акцию.

        Args:
            action_id: Идентификатор акции.
            action_data: Данные для обновления.
            cafes: Список кафе для привязки (если передан).

        Returns:
            Action | None: Обновленная акция или None.

        """
        action = await self.get(action_id)
        if not action:
            return None

        update_data = action_data.model_dump(exclude_unset=True)
        update_data.pop('cafes_id', None)
        if update_data.get('photo_id') is not None:
            update_data['photo_id'] = str(update_data['photo_id'])
        if cafes is not None:
            action.cafes = cafes

        return await super().update(action, update_data)

    async def delete(self, action_id: int) -> bool:
        """Деактивировать акцию.

        Args:
            action_id: Идентификатор акции.

        Returns:
            bool: True, если акция деактивирована.

        """
        action = await self.get_by_id(action_id)
        if not action:
            return False

        action.active = False
        await self.session.flush()
        return True


if TYPE_CHECKING:
    from app.models import Cafe
