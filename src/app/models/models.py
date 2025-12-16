"""Модели базы данных для модуля пользователей.

Модуль содержит ORM-модели SQLAlchemy 2.0 для работы с таблицей пользователей.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.constants import Limits
from src.app.db.base import Base

if TYPE_CHECKING:
    from app.api.v1.booking.models import Booking
    from app.api.v1.cafes.models import Cafe


class User(Base):
    """Модель пользователя системы.

    Хранит информацию о пользователях: клиентах, менеджерах и администраторах.

    Attributes:
        id: Уникальный идентификатор пользователя.
        username: Уникальное имя пользователя.
        email: Электронная почта пользователя.
        phone: Номер телефона пользователя.
        tg_id: Идентификатор Telegram для уведомлений.
        password_hash: Хеш пароля пользователя.
        is_blocked: Флаг блокировки пользователя.
        is_superuser: Флаг администратора системы.
        created_at: Дата и время создания записи.
        updated_at: Дата и время последнего обновления записи.
        active: Флаг активности пользователя.
        bookings: Список бронирований пользователя.
        managed_cafes: Кафе, которыми управляет пользователь.

    Notes:
        - Все модели наследуются от Base (DeclarativeBase)
        - Используем новый стиль SQLAlchemy 2.0 (Mapped)
        - Обязательные поля: created_at, updated_at, active

    """

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(Limits.MAX_USERNAME_LENGTH),
        unique=True,
        nullable=False,
        comment=f'Имя пользователя от {Limits.MIN_USERNAME_LENGTH} до '
        f'{Limits.MAX_USERNAME_LENGTH} символов',
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(Limits.MAX_EMAIL_LENGTH),
        unique=True,
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(Limits.MAX_PHONE_LENGTH),
        unique=True,
        nullable=True,
        comment=f'Номер телефона от {Limits.MIN_PHONE_LENGTH} до '
        f'{Limits.MAX_PHONE_LENGTH} символов',
    )
    tg_id: Mapped[str | None] = mapped_column(
        String(Limits.MAX_TG_ID_LENGTH), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(Limits.MAX_PASSWORD_LENGTH), nullable=False
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    active: Mapped[bool] = mapped_column(default=True)

    bookings: Mapped[List['Booking']] = relationship(
        'Booking',
        back_populates='user',
        cascade='all, delete-orphan',
    )
    managed_cafes: Mapped[List['Cafe']] = relationship(
        'Cafe',
        secondary='cafe_managers',
        back_populates='managers',
    )

    def __repr__(self) -> str:
        """Строковое представление объекта User.

        Returns:
            Строка с идентификатором и именем пользователя.

        """
        return f"<User(id={self.id}, username='{self.username}')>"


cafe_managers = Table(
    'cafe_managers',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
)
