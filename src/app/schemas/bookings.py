from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import BookingStatus, Examples, Limits
from app.schemas.cafes import CafeShortInfo
from app.schemas.slot import TimeSlotShortInfo
from app.schemas.tables import TableShortInfo
from app.schemas.users import UserShortInfo


class TableSlotSchema(BaseModel):
    """Схема связки столика и временного слота.

    Содержит информацию о выбранном столике и слоте бронирования.
    """

    table_id: int = Field(description='ID столика')
    slot_id: int = Field(description='ID временного слота')

    model_config = ConfigDict(from_attributes=True)


class BookingBase(BaseModel):
    """Базовая схема бронирования.

    Содержит общие поля, используемые при создании и обновлении бронирования.
    Все поля описаны для проверки корректности обновлений.
    """

    guest_number: int | None = Field(
        None, gt=0, description='Количество гостей'
    )
    cafe_id: int | None = Field(None, gt=0, description='ID кафе')
    note: str | None = Field(
        None,
        max_length=Limits.MAX_BOOKING_NOTE_LENGTH,
        description='Комментарий к бронированию',
    )
    booking_date: date | None = Field(
        None,
        description='Дата бронирования (YYYY-MM-DD).',
    )
    status: BookingStatus | None = Field(
        None, description='Статус бронирования'
    )
    table_slots: list[TableSlotSchema] | None = Field(
        None,
        validation_alias='tables_slots',
        serialization_alias='tables_slots',
        description='Список связок столов и временных слотов',
    )

    model_config = ConfigDict(extra='forbid', populate_by_name=True)


class TableSlotInfo(BaseModel):
    """Схема связки столика и временного слота для ответов."""

    id: int = Field(description='ID записи')
    table: TableShortInfo = Field(description='Столик')
    slot: TimeSlotShortInfo = Field(description='Временной слот')

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BookingBase):
    """Схема для создания нового бронирования.

    Наследует базовую схему, но делает обязательными поля,
    необходимые при создании бронирования.
    """

    guest_number: int = Field(..., gt=0, description='Количество гостей')
    cafe_id: int = Field(..., description='ID кафе')
    booking_date: date = Field(
        ...,
        description='Дата бронирования (YYYY-MM-DD).',
    )
    status: BookingStatus = Field(
        ...,
        description='Статус бронирования',
    )
    table_slots: list[TableSlotSchema] = Field(
        ...,
        validation_alias='tables_slots',
        serialization_alias='tables_slots',
        description='Список связок столов и временных слотов',
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            'examples': [
                {
                    'guest_number': 2,
                    'cafe_id': 1,
                    'booking_date': Examples.DATE_TOMORROW,
                    'note': 'Столик у окна',
                    'status': BookingStatus.BOOKING,
                    'tables_slots': [
                        {'table_id': 3, 'slot_id': 5},
                    ],
                }
            ]
        },
    )


class BookingUpdate(BookingBase):
    """Схема для обновления существующего бронирования.

    Наследует базовую схему и добавляет поле active.
    Все поля описаны для проверки корректности обновления.
    """

    active: bool | None = Field(
        default=None,
        description='Признак активности бронирования',
        validation_alias='is_active',
        serialization_alias='is_active',
    )

    model_config = ConfigDict(
        extra='forbid',
        validate_default=True,
        populate_by_name=True,
        json_schema_extra={
            'examples': [
                {
                    'booking_date': Examples.DATE_DAY_AFTER,
                    'note': 'Перенести на вечер',
                    'status': BookingStatus.ACTIVE,
                    'is_active': True,
                }
            ]
        },
    )


class BookingDB(BookingBase):
    """Схема для отображения бронирования в ответах API.

    Содержит полную информацию о бронировании, включая связанные
    сущности пользователя и кафе.
    """

    id: int = Field(description='ID бронирования')
    user: UserShortInfo = Field(description='Пользователь')
    cafe: CafeShortInfo = Field(description='Кафе')
    table_slots: list[TableSlotInfo] = Field(
        validation_alias='tables_slots',
        serialization_alias='tables_slots',
        description='Список связок столов и временных слотов',
    )
    created_at: datetime = Field(
        description='Дата и время создания (date-time)'
    )
    updated_at: datetime = Field(
        description='Дата и время обновления (date-time)'
    )
    active: bool = Field(
        description='Признак активности бронирования',
        validation_alias='is_active',
        serialization_alias='is_active',
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BookingInfo(BookingDB):
    """Схема ответа о бронировании."""
