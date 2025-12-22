"""Модели базы данных."""

from app.models.action import Action
from app.models.cafe import Cafe
from app.models.dish import Dish
from app.models.models import User, cafe_managers
from app.models.table import Table

__all__ = ['User', 'cafe_managers', 'Dish', 'Action', 'Cafe', 'Table']
__models__ = [User, Cafe, Table, Dish, Action]
