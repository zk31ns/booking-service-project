from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from .models import User
from .validators import validate_phone_format


class UserBase(BaseModel):
    """Базовая схема пользователя.

    Содержит основные поля пользователя, такие как username,
    email, phone и tg_id.

    Attributes:
        username (str): Уникальное имя пользователя.
        email (Optional[EmailStr]): Электронная почта пользователя.
        phone (Optional[str]): Номер телефона пользователя в формате E.164.
        tg_id (Optional[str]): Идентификатор Telegram для уведомлений.

    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description='Уникальное имя пользователя',
    )
    email: Optional[EmailStr] = Field(
        None,
        description='Электронная почта пользователя',
    )
    phone: Optional[str] = Field(
        None,
        description='Номер телефона пользователя в формате E.164',
    )
    tg_id: Optional[str] = Field(
        None,
        max_length=100,
        description='Идентификатор Telegram для уведомлений',
    )


class UserCreate(UserBase):
    """Схема для создания нового пользователя.

    Наследует поля от UserBase и добавляет обязательное поле password.
    Валидирует формат телефона и проверяет, что указан хотя бы один
    контакт (email или phone).

    Attributes:
        password (str): Пароль пользователя. Обязательное поле.

    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description='Пароль пользователя',
    )

    @field_validator('phone')
    def validate_phone(cls, phone: str | None) -> str | None:  # noqa: N805
        """Валидирует формат телефонного номера."""
        return validate_phone_format(phone)

    @model_validator(mode='after')
    def validate_contact_info(self) -> 'UserCreate':
        """Проверяет, что хотя бы один из контактов указан.

        Returns:
            UserCreate: Возвращает экземпляр UserCreate.

        Raises:
            ValueError: Если не указан ни email, ни phone.

        """
        if self.email is None and self.phone is None:
            raise ValueError('Укажите хотя бы email или телефон для связи.')
        return self

    class Config:
        """Конфигурация Pydantic схемы."""

        json_schema_extra = {
            'example': {
                'username': 'ivanov',
                'email': 'ivanov@example.com',
                'phone': '+79161234567',
                'tg_id': '123456789',
                'password': 'securepassword123',
            },
        }


class UserUpdate(BaseModel):
    """Схема для обновления информации о пользователе.

    Все поля опциональны для частичного обновления.

    Attributes:
        username (Optional[str]): Уникальное имя пользователя.
        email (Optional[EmailStr]): Электронная почта пользователя.
        phone (Optional[str]): Номер телефона пользователя в формате E.164.
        tg_id (Optional[str]): Идентификатор Telegram для уведомлений.
        password (Optional[str]): Новый пароль пользователя.
        is_blocked (Optional[bool]): Флаг блокировки пользователя.
        is_superuser (Optional[bool]): Флаг администратора системы.
        active (Optional[bool]): Флаг активности пользователя.

    """

    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description='Уникальное имя пользователя',
    )
    email: Optional[EmailStr] = Field(
        None,
        description='Электронная почта пользователя',
    )
    phone: Optional[str] = Field(
        None,
        description='Номер телефона пользователя в формате E.164',
    )
    tg_id: Optional[str] = Field(
        None,
        max_length=100,
        description='Идентификатор Telegram для уведомлений',
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description='Новый пароль пользователя',
    )
    is_blocked: Optional[bool] = Field(
        None,
        description='Флаг блокировки пользователя',
    )
    is_superuser: Optional[bool] = Field(
        None,
        description='Флаг администратора системы',
    )
    active: Optional[bool] = Field(
        None,
        description='Флаг активности пользователя',
    )

    @field_validator('phone')
    def validate_phone(cls, phone: str | None) -> str | None:  # noqa: N805
        """Валидирует формат телефонного номера."""
        return validate_phone_format(phone)


class UserInfo(UserBase):
    """Схема для отображения информации о пользователе.

    Содержит дополнительные поля, такие как id, флаги состояния
    и временные метки. Используется для формирования ответов API.

    Attributes:
        id (int): Уникальный идентификатор пользователя.
        is_superuser (bool): Флаг администратора системы.
        is_blocked (bool): Флаг блокировки пользователя.
        active (bool): Флаг активности пользователя.
        created_at (datetime): Дата и время создания записи.
        updated_at (datetime): Дата и время последнего обновления записи.

    """

    id: int = Field(..., description='Уникальный идентификатор пользователя')
    is_superuser: bool = Field(..., description='Флаг администратора системы')
    is_blocked: bool = Field(..., description='Флаг блокировки пользователя')
    active: bool = Field(..., description='Флаг активности пользователя')
    created_at: datetime = Field(
        ...,
        description='Дата и время создания записи',
    )
    updated_at: datetime = Field(
        ...,
        description='Дата и время обновления записи',
    )

    @classmethod
    def from_orm(cls, obj: User) -> 'UserInfo':
        """Создает экземпляр UserInfo из ORM-объекта.

        Args:
            obj: ORM-объект пользователя.

        Returns:
            UserInfo: Экземпляр UserInfo.

        """
        return cls.model_validate(obj, from_attributes=True)

    class Config:
        """Конфигурация Pydantic схемы."""

        from_attributes = True
        json_schema_extra = {
            'example': {
                'id': 1,
                'username': 'ivanov',
                'email': 'ivanov@example.com',
                'phone': '+79161234567',
                'tg_id': '123456789',
                'is_superuser': False,
                'is_blocked': False,
                'active': True,
                'created_at': '2024-01-15T10:30:00',
                'updated_at': '2024-01-15T10:30:00',
            },
        }


class UserShortInfo(BaseModel):
    """Краткая информация о пользователе.

    Используется для вложенных объектов в других схемах.

    Attributes:
        id (int): Уникальный идентификатор пользователя.
        username (str): Уникальное имя пользователя.
        email (Optional[str]): Электронная почта пользователя.
        phone (Optional[str]): Номер телефона пользователя.
        tg_id (Optional[str]): Идентификатор Telegram.

    """

    id: int = Field(..., description='Уникальный идентификатор пользователя')
    username: str = Field(..., description='Уникальное имя пользователя')
    email: Optional[str] = Field(
        None,
        description='Электронная почта пользователя',
    )
    phone: Optional[str] = Field(
        None,
        description='Номер телефона пользователя',
    )
    tg_id: Optional[str] = Field(None, description='Идентификатор Telegram')

    class Config:
        """Конфигурация Pydantic схемы."""

        from_attributes = True
