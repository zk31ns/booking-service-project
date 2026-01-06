"""Базовый класс для всех репозиториев.

Предоставляет стандартные CRUD операции для всех моделей.
"""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar('ModelType', bound=Base)


class BaseCRUD(Generic[ModelType]):
    """Базовый класс для CRUD репозиториев.

    Предоставляет стандартные операции создания, чтения, обновления и удаления
    для любой ORM модели SQLAlchemy.

    Generic:
        ModelType: Тип ORM модели, с которой работает репозиторий

    Attributes:
        session: Асинхронная сессия SQLAlchemy
        model: Класс модели ORM

    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]) -> None:
        """Инициализирует базовый репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy для работы с БД
            model: Класс модели ORM для работы

        """
        self.session = session
        self.model = model

    async def create(self, obj_in: dict | object) -> ModelType:
        """Создать новый объект в базе данных.

        Args:
            obj_in: Данные для создания (словарь или Pydantic модель)

        Returns:
            Созданный объект модели

        """
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump(exclude_unset=True)
        elif isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.__dict__

        db_obj = self.model(**obj_data)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def get(self, obj_id: int | str) -> Optional[ModelType]:
        """Получить объект по ID.

        Args:
            obj_id: ID объекта

        Returns:
            Объект модели или None если не найден

        """
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Получить список объектов с пагинацией.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список объектов модели

        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, db_obj: ModelType, obj_in: dict | object
    ) -> ModelType:
        """Обновить существующий объект.

        Args:
            db_obj: Объект из базы данных
            obj_in: Новые данные (словарь или Pydantic модель)

        Returns:
            Обновленный объект

        """
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump(exclude_unset=True)
        elif isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.__dict__

        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, obj_id: int | str) -> bool:
        """Удалить объект по ID.

        Args:
            obj_id: ID объекта для удаления

        Returns:
            True если объект был удален, False если не найден

        """
        db_obj = await self.get(obj_id)
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.flush()
            return True
        return False
