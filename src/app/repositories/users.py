"""Репозиторий для работы с пользователями.

Содержит CRUD операции для модели User с поддержкой асинхронности
и соответствием бизнес-правилам проекта.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from app.core.constants import Limits
from app.core.security import get_password_hash, verify_password
from app.models.users import User, cafe_managers
from app.repositories.base import BaseCRUD


class UserRepository(BaseCRUD[User]):
    """Репозиторий для работы с пользователями.

    Предоставляет методы для CRUD операций и специфичные для пользователей
    методы поиска и аутентификации.

    Attributes:
        session: Асинхронная сессия SQLAlchemy
        model: Модель пользователя (User)

    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий с моделью User.

        Args:
            session: Асинхронная сессия для работы с базой данных

        """
        super().__init__(session=session, model=User)

    async def get(
        self,
        user_id: Union[int, UUID],
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по его ID.

        Args:
            user_id: Идентификатор пользователя
            active_only: Если True, возвращает только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.id == user_id)
        if active_only:
            query = query.where(self.model.active.is_(True))
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = Limits.DEFAULT_PAGE_SIZE,
        active_only: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[User]:
        """Получает список пользователей с пагинацией и фильтрацией.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            active_only: Если True, возвращает только активных пользователей
            filters: Словарь фильтров {поле: значение}

        Returns:
            Список пользователей

        """
        query = select(self.model)
        if active_only:
            query = query.where(self.model.active.is_(True))
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if value is None:
                        query = query.where(
                            getattr(self.model, field).is_(None),
                        )
                    else:
                        query = query.where(
                            getattr(self.model, field) == value,
                        )
        query = (
            query.offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_username(
        self,
        username: str,
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по имени пользователя.

        Args:
            username: Имя пользователя
            active_only: Если True, ищет только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.username == username)
        if active_only:
            query = query.where(self.model.active.is_(True))
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_email(
        self,
        email: str,
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по email.

        Args:
            email: Электронная почта пользователя
            active_only: Если True, ищет только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.email == email)
        if active_only:
            query = query.where(self.model.active.is_(True))
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_phone(
        self,
        phone: str,
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по номеру телефона.

        Args:
            phone: Номер телефона
            active_only: Если True, ищет только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.phone == phone)
        if active_only:
            query = query.where(self.model.active.is_(True))
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create_user(
        self,
        user_data: Dict[str, Any],
        commit: bool = True,
    ) -> User:
        """Создаёт нового пользователя.

        Args:
            user_data: Данные пользователя (словарь)
            commit: Если True, коммитит изменения

        Returns:
            Созданный пользователь

        Note:
            Автоматически хеширует пароль если передан ключ 'password'

        """
        user_data = user_data.copy()

        if 'password' in user_data:
            password = user_data.pop('password')
            user_data['password_hash'] = get_password_hash(password)

        db_user = await super().create(user_data)

        if commit:
            await self.session.commit()
            await self.session.refresh(db_user)

        return db_user

    async def update_user(
        self,
        user: User,
        update_data: Dict[str, Any],
        commit: bool = True,
    ) -> User:
        """Обновляет существующего пользователя.

        Args:
            user: Объект пользователя для обновления
            update_data: Данные для обновления (словарь)
            commit: Если True, коммитит изменения

        Returns:
            Обновлённый пользователь

        Note:
            Автоматически хеширует пароль если передан ключ 'password'

        """
        update_data = update_data.copy()

        if 'password' in update_data:
            password = update_data.pop('password')
            update_data['password_hash'] = get_password_hash(password)

        updated_user = await super().update(user, update_data)

        if commit:
            await self.session.commit()
            await self.session.refresh(updated_user)

        return updated_user

    async def delete_user(
        self,
        user_id: Union[int, UUID],
        hard_delete: bool = False,
        commit: bool = True,
    ) -> Optional[User]:
        """Удаляет пользователя.

        Args:
            user_id: Идентификатор пользователя
            hard_delete: Если True, физически удаляет запись,
                        иначе устанавливает active=False
            commit: Если True, коммитит изменения

        Returns:
            Удалённый пользователь или None, если не найден

        """
        user = await self.get(user_id, active_only=False)

        if not user:
            return None

        if hard_delete:
            await self.session.delete(user)
        else:
            user.active = False
            self.session.add(user)

        if commit:
            await self.session.commit()

        return user

    async def authenticate(
        self,
        login: str,
        password: str,
    ) -> Optional[User]:
        """Аутентифицирует пользователя.

        Ищет пользователя по username, email или phone и проверяет пароль.

        Args:
            login: Имя пользователя, email или телефон
            password: Пароль для проверки

        Returns:
            Аутентифицированный пользователь или None

        """
        user = await self.get_by_username(login, active_only=False)

        if not user and '@' in login:
            user = await self.get_by_email(login, active_only=False)

        if not user and login.startswith('+'):
            user = await self.get_by_phone(login, active_only=False)

        if not user:
            return None

        if not user.active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def exists(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> bool:
        """Проверяет существование пользователя.

        Args:
            username: Имя пользователя для проверки
            email: Email для проверки
            phone: Телефон для проверки

        Returns:
            True если пользователь существует, иначе False

        """
        query = select(self.model.id).limit(1)
        conditions: List[BinaryExpression] = []
        if username:
            conditions.append(self.model.username == username)
        if email:
            conditions.append(self.model.email == email)
        if phone:
            conditions.append(self.model.phone == phone)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar() is not None

    async def count(
        self,
        active_only: bool = True,
    ) -> int:
        """Подсчитывает количество пользователей.

        Args:
            active_only: Если True, считает только активных пользователей

        Returns:
            Количество пользователей

        """
        query = select(self.model.id)

        if active_only:
            query = query.where(self.model.active.is_(True))

        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def update_password(
        self,
        user: User,
        new_password: str,
        commit: bool = True,
    ) -> User:
        """Обновляет пароль пользователя.

        Args:
            user: Объект пользователя
            new_password: Новый пароль
            commit: Если True, коммитит изменения

        Returns:
            Обновлённый пользователь

        """
        return await self.update_user(
            user=user,
            update_data={'password': new_password},
            commit=commit,
        )

    async def search(
        self,
        query_str: str,
        skip: int = 0,
        limit: int = Limits.DEFAULT_PAGE_SIZE,
        active_only: bool = True,
    ) -> List[User]:
        """Ищет пользователей по строке запроса.

        Args:
            query_str: Строка поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            active_only: Если True, ищет только активных пользователей

        Returns:
            Список найденных пользователей

        """
        conditions: List[BooleanClauseList] = []
        if query_str:
            conditions.append(self.model.username.ilike(f'%{query_str}%'))
        if active_only:
            conditions.append(self.model.active.is_(True))

        search_query = select(self.model).where(and_(*conditions))
        search_query = (
            search_query.offset(skip)
            .limit(limit)
            .order_by(self.model.username)
        )

        result = await self.session.execute(search_query)
        return list(result.scalars().all())

    async def is_manager(
        self,
        user_id: int,
    ) -> bool:
        """Проверить является ли пользователь менеджером."""
        stmt = select(exists().where(cafe_managers.c.user_id == user_id))
        result = await self.session.execute(stmt)
        return result.scalar() is not None
