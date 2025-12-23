"""Модели базы данных."""

from src.app.models.action import Action
from src.app.models.booking import Booking, TableSlot
from src.app.models.cafe import Cafe
from src.app.models.dish import Dish
from src.app.models.models import User, cafe_managers
from src.app.models.slot import Slot
from src.app.models.table import Table

__all__ = [
    'User',
    'cafe_managers',
    'Dish',
    'Action',
    'Cafe',
    'Table',
    'Booking',
    'TableSlot',
    'Slot',
]
__models__ = [User, Cafe, Table, Dish, Action, Booking, Slot]
