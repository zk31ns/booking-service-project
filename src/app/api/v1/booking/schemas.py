from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.app.api.v1.users.schemas import UserShortInfo
from src.app.core.constants import BookingStatus, Limits
from src.app.schemas.cafe import CafeBase


class TableSlot(BaseModel):
    """Схема для окошек и столов."""
    table_id: int
    slot_id: int


class BookingBase(BaseModel):
    """Базовая схема бронирования."""
    guest_number: Optional[int] = Field(None, gt=0)
    cafe_id: Optional[int]
    note: Optional[str] = Field(
        None, max_length=Limits.MAX_BOOKING_NOTE_LENGTH
    )
    booking_date: Optional[date]
    status: Optional[BookingStatus] = BookingStatus.BOOKING
    table_slots: Optional[list[TableSlot]]

    class Config:
        extra = 'forbid'


class BookingCreate(BookingBase):
    """Схема создания бронирования."""
    guest_number: int = Field(..., gt=0)
    cafe_id: int
    booking_date: date
    table_slots: list[TableSlot]


class BookingUpdate(BookingBase):
    """Схема обновления бронирования."""
    is_active: Optional[bool] = Field(default=True)
    status: BookingStatus = BookingStatus.BOOKING


class BookingDB(BookingBase):
    """Схема для получения бронирования."""
    id: int
    user: UserShortInfo
    cafe: CafeBase
    table_slots: list[TableSlot]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True
