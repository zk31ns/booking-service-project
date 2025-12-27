"""Модели базы данных."""

from src.app.models.actions import Action
from src.app.models.cafes import Cafe
from src.app.models.dishes import Dish
from src.app.models.media import Media
from src.app.models.models import User, cafe_managers
from src.app.models.tables import Table

__all__ = ['User', 'cafe_managers', 'Dish', 'Action', 'Cafe', 'Table', 'Media']
__models__ = [User, Cafe, Table, Dish, Action, Media]
