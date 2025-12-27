from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.app.api.v1.users.schemas import UserShortInfo
from src.app.core.constants import BookingStatus, Limits


class CafeShort(BaseModel):
    """Краткая информация о кафе.

    Используется для вложенного отображения кафе в ответах API.
    """

    id: int


class TableSlotSchema(BaseModel):
    """Схема для связки стола и временного слота.

    Представляет информацию о конкретном столе и времени бронирования.
    """

    table_id: int
    slot_id: int

    model_config = ConfigDict(from_attributes=True)


class BookingBase(BaseModel):
    """Базовая схема бронирования.

    Содержит общие поля, используемые для создания и обновления бронирований.
    Все поля опциональны для поддержки частичного обновления.
    """

    guest_number: int | None = Field(None, gt=0)
    cafe_id: int | None = Field(None, gt=0)
    note: str | None = Field(None, max_length=Limits.MAX_BOOKING_NOTE_LENGTH)
    booking_date: date | None = None
    status: BookingStatus | None = None
    table_slots: list[TableSlotSchema] | None = None

    model_config = ConfigDict(extra='forbid')


class BookingCreate(BookingBase):
    """Схема для создания нового бронирования.

    Наследует базовую схему, но делает обязательными поля,
    необходимые для создания бронирования.
    """

    guest_number: int = Field(..., gt=0)
    cafe_id: int
    booking_date: date
    table_slots: list[TableSlotSchema]


class BookingUpdate(BookingBase):
    """Схема для обновления существующего бронирования.

    Наследует базовую схему и добавляет поле is_active.
    Все поля опциональны для поддержки частичного обновления.
    """

    is_active: bool | None = Field(default=None)

    model_config = ConfigDict(extra='forbid', validate_default=True)


class BookingDB(BookingBase):
    """Схема для отображения бронирования в ответах API.

    Содержит полную информацию о бронировании включая связанные сущности
    и метаданные. Используется для ответов GET запросов.
    """

    id: int
    user: UserShortInfo
    cafe: CafeShort
    table_slots: list[TableSlotSchema]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
