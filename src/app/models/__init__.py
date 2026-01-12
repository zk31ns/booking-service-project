"""Модели базы данных."""

from app.models.actions import Action, action_cafes
from app.models.booking import Booking, TableSlot
from app.models.cafes import Cafe
from app.models.dishes import Dish, dish_cafes
from app.models.media import Media
from app.models.slots import Slot
from app.models.tables import Table
from app.models.users import User, cafe_managers

__all__ = [
    'User',
    'cafe_managers',
    'Dish',
    'Action',
    'dish_cafes',
    'action_cafes',
    'Cafe',
    'Table',
    'Media',
    'Booking',
    'TableSlot',
    'Slot',
]
__models__ = [
    User,
    cafe_managers,
    Cafe,
    Table,
    Dish,
    Action,
    dish_cafes,
    action_cafes,
    Media,
    Booking,
    TableSlot,
    Slot,
]
