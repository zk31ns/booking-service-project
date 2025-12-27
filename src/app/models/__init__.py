"""Модели базы данных."""

from app.models.actions import Action
from app.models.cafes import Cafe
from app.models.dishes import Dish
from app.models.media import Media
from app.models.models import User, cafe_managers
from app.models.tables import Table

__all__ = ['User', 'cafe_managers', 'Dish', 'Action', 'Cafe', 'Table', 'Media']
__models__ = [User, Cafe, Table, Dish, Action, Media]
