"""Модели базы данных."""

from src.app.models.action import Action
from src.app.models.cafe import Cafe
from src.app.models.dish import Dish
from src.app.models.models import User, cafe_managers
from src.app.models.table import Table

__all__ = ['User', 'cafe_managers', 'Dish', 'Action', 'Cafe', 'Table']
__models__ = [User, Cafe, Table, Dish, Action]
