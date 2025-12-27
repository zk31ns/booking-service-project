"""Модели базы данных."""

from app.models.actions import Action
from app.models.booking import Booking, TableSlot
from app.models.cafes import Cafe
from app.models.dishes import Dish
from app.models.media import Media
from app.models.models import User, cafe_managers
from app.models.slots import Slot
from app.models.tables import Table

__all__ = ['User', 'cafe_managers', 'Dish', 'Action', 'Cafe', 'Table', 'Media', 'Booking', 'TableSlot', 'Slot']
__models__ = [User, cafe_managers, Cafe, Table, Dish, Action, Media, Booking, TableSlot, Slot]
