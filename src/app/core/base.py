"""Base для всех ORM моделей.

Все модели должны наследоваться от этого Base.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""

    pass


class TimestampedModel(Base):
    """Базовый класс с временными метками и флагом активности.

    Содержит стандартные поля для всех моделей:
    - created_at: дата создания записи
    - updated_at: дата последнего обновления
    - active: флаг активности (для soft delete)

    Examples:
        class User(TimestampedModel):
            __tablename__ = 'users'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(default=True)


__all__ = ['Base', 'TimestampedModel']
