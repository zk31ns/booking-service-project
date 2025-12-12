"""Base для всех ORM моделей.

Все модели должны наследоваться от этого Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""

    pass


__all__ = ['Base']
