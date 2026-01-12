from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import BookingStatus, Limits
from app.schemas.users import UserShortInfo


class CafeShort(BaseModel):
    """Краткая информация о кафе.

    Используется в ответах, чтобы не передавать все поля кафе.
    """

    id: int = Field(description='ID кафе')


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
        None, description='Список связок столов и временных слотов'
    )

    model_config = ConfigDict(extra='forbid')


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
    table_slots: list[TableSlotSchema] = Field(
        ...,
        description='Список связок столов и временных слотов',
    )

    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'guest_number': 2,
                    'cafe_id': 1,
                    'booking_date': '2026-01-15',
                    'note': 'Столик у окна',
                    'table_slots': [
                        {'table_id': 3, 'slot_id': 5},
                    ],
                }
            ]
        }
    )


class BookingUpdate(BookingBase):
    """Схема для обновления существующего бронирования.

    Наследует базовую схему и добавляет поле active.
    Все поля описаны для проверки корректности обновления.
    """

    active: bool | None = Field(
        default=None, description='Признак активности бронирования'
    )

    model_config = ConfigDict(
        extra='forbid',
        validate_default=True,
        json_schema_extra={
            'examples': [
                {
                    'booking_date': '2026-01-20',
                    'note': 'Перенести на вечер',
                    'status': 'confirmed',
                    'active': True,
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
    cafe: CafeShort = Field(description='Кафе')
    table_slots: list[TableSlotSchema] = Field(
        description='Список связок столов и временных слотов'
    )
    created_at: datetime = Field(
        description='Дата и время создания (date-time)'
    )
    updated_at: datetime = Field(
        description='Дата и время обновления (date-time)'
    )
    active: bool = Field(description='Признак активности бронирования')

    model_config = ConfigDict(from_attributes=True)
