"""Репозиторий для работы с пользователями.

Содержит CRUD операции для модели User с поддержкой асинхронности
и соответствием бизнес-правилам проекта.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.users.models import User
from app.core.security import get_password_hash, verify_password


class UserRepository:
    """Репозиторий для работы с пользователями.

    Предоставляет методы для CRUD операций и специфичные для пользователей
    методы поиска и аутентификации.

    Attributes:
        model: Модель пользователя (User)

    """

    def __init__(self) -> None:
        """Инициализирует репозиторий с моделью User."""
        self.model = User

    async def get(
        self,
        session: AsyncSession,
        user_id: Union[int, UUID],
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по его ID.

        Args:
            session: Асинхронная сессия для работы с базой данных
            user_id: Идентификатор пользователя
            active_only: Если True, возвращает только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.id == user_id)

        if active_only:
            query = query.where(self.model.active.is_(True))

        result = await session.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[User]:
        """Получает список пользователей с пагинацией и фильтрацией.

        Args:
            session: Асинхронная сессия
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

        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_username(
        self,
        session: AsyncSession,
        username: str,
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по имени пользователя.

        Args:
            session: Асинхронная сессия
            username: Имя пользователя
            active_only: Если True, ищет только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.username == username)

        if active_only:
            query = query.where(self.model.active.is_(True))

        result = await session.execute(query)
        return result.scalars().first()

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по email.

        Args:
            session: Асинхронная сессия
            email: Электронная почта пользователя
            active_only: Если True, ищет только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.email == email)

        if active_only:
            query = query.where(self.model.active.is_(True))

        result = await session.execute(query)
        return result.scalars().first()

    async def get_by_phone(
        self,
        session: AsyncSession,
        phone: str,
        active_only: bool = True,
    ) -> Optional[User]:
        """Получает пользователя по номеру телефона.

        Args:
            session: Асинхронная сессия
            phone: Номер телефона
            active_only: Если True, ищет только активных пользователей

        Returns:
            Найденный пользователь или None

        """
        query = select(self.model).where(self.model.phone == phone)

        if active_only:
            query = query.where(self.model.active.is_(True))

        result = await session.execute(query)
        return result.scalars().first()

    async def create(
        self,
        session: AsyncSession,
        user_data: Dict[str, Any],
        commit: bool = True,
    ) -> User:
        """Создаёт нового пользователя.

        Args:
            session: Асинхронная сессия
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

        db_user = self.model(**user_data)
        session.add(db_user)

        if commit:
            await session.commit()
            await session.refresh(db_user)

        return db_user

    async def update(
        self,
        session: AsyncSession,
        user: User,
        update_data: Dict[str, Any],
        commit: bool = True,
    ) -> User:
        """Обновляет существующего пользователя.

        Args:
            session: Асинхронная сессия
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

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        session.add(user)

        if commit:
            await session.commit()
            await session.refresh(user)

        return user

    async def delete(
        self,
        session: AsyncSession,
        user_id: Union[int, UUID],
        hard_delete: bool = False,
        commit: bool = True,
    ) -> Optional[User]:
        """Удаляет пользователя.

        Args:
            session: Асинхронная сессия
            user_id: Идентификатор пользователя
            hard_delete: Если True, физически удаляет запись,
                        иначе устанавливает active=False
            commit: Если True, коммитит изменения

        Returns:
            Удалённый пользователь или None, если не найден

        """
        user = await self.get(session, user_id, active_only=False)

        if not user:
            return None

        if hard_delete:
            await session.delete(user)
        else:
            user.active = False
            session.add(user)

        if commit:
            await session.commit()

        return user

    async def authenticate(
        self,
        session: AsyncSession,
        login: str,
        password: str,
    ) -> Optional[User]:
        """Аутентифицирует пользователя.

        Ищет пользователя по username, email или phone и проверяет пароль.

        Args:
            session: Асинхронная сессия
            login: Имя пользователя, email или телефон
            password: Пароль для проверки

        Returns:
            Аутентифицированный пользователь или None

        Raises:
            ValueError: Если пользователь не найден или пароль неверный

        """
        user = await self.get_by_username(session, login, active_only=False)

        if not user and '@' in login:
            user = await self.get_by_email(session, login, active_only=False)

        if not user and login.startswith('+'):
            user = await self.get_by_phone(session, login, active_only=False)

        if not user:
            return None

        if not user.active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def exists(
        self,
        session: AsyncSession,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> bool:
        """Проверяет существование пользователя.

        Args:
            session: Асинхронная сессия
            username: Имя пользователя для проверки
            email: Email для проверки
            phone: Телефон для проверки

        Returns:
            True если пользователь существует, иначе False

        """
        query = select(self.model.id).limit(1)

        conditions = []
        if username:
            conditions.append(self.model.username == username)
        if email:
            conditions.append(self.model.email == email)
        if phone:
            conditions.append(self.model.phone == phone)

        if conditions:
            query = query.where(and_(*conditions))

        result = await session.execute(query)
        return result.scalar() is not None

    async def count(
        self,
        session: AsyncSession,
        active_only: bool = True,
    ) -> int:
        """Подсчитывает количество пользователей.

        Args:
            session: Асинхронная сессия
            active_only: Если True, считает только активных пользователей

        Returns:
            Количество пользователей

        """
        query = select(self.model.id)

        if active_only:
            query = query.where(self.model.active.is_(True))

        result = await session.execute(query)
        return len(result.scalars().all())

    async def update_password(
        self,
        session: AsyncSession,
        user: User,
        new_password: str,
        commit: bool = True,
    ) -> User:
        """Обновляет пароль пользователя.

        Args:
            session: Асинхронная сессия
            user: Объект пользователя
            new_password: Новый пароль
            commit: Если True, коммитит изменения

        Returns:
            Обновлённый пользователь

        """
        return await self.update(
            session=session,
            user=user,
            update_data={'password': new_password},
            commit=commit,
        )

    async def search(
        self,
        session: AsyncSession,
        query_str: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[User]:
        """Ищет пользователей по строке запроса.

        Args:
            session: Асинхронная сессия
            query_str: Строка поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            active_only: Если True, ищет только активных пользователей

        Returns:
            Список найденных пользователей

        """
        search_query = select(self.model).where(
            and_(
                self.model.username.ilike(f'%{query_str}%'),
                self.model.active.is_(True) if active_only else True,
            ),
        )

        search_query = (
            search_query.offset(skip)
            .limit(limit)
            .order_by(self.model.username)
        )

        result = await session.execute(search_query)
        return result.scalars().all()
