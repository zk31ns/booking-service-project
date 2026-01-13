from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.core.constants import Examples, Limits, UserRole
from app.models.users import User
from app.utils.validators import validate_phone_format


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
        min_length=Limits.MIN_USERNAME_LENGTH,
        max_length=Limits.MAX_USERNAME_LENGTH,
        description='Уникальное имя пользователя',
    )
    email: EmailStr | None = Field(
        None,
        description='Электронная почта пользователя',
    )
    phone: str | None = Field(
        None,
        description='Номер телефона пользователя в формате E.164',
    )
    tg_id: str | None = Field(
        None,
        max_length=Limits.MAX_TG_ID_LENGTH,
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
        min_length=Limits.MIN_PASSWORD_LENGTH,
        max_length=Limits.MAX_PASSWORD_LENGTH,
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
        role (Optional[UserRole]): Роль пользователя.
        active (Optional[bool]): Флаг активности пользователя.
        managed_cafes (Optional[List[int]]): ID кафе, которыми управляет
            пользователь.

    """

    username: str | None = Field(
        None,
        min_length=Limits.MIN_USERNAME_LENGTH,
        max_length=Limits.MAX_USERNAME_LENGTH,
        description='Уникальное имя пользователя',
    )
    email: EmailStr | None = Field(
        None,
        description='Электронная почта пользователя',
    )
    phone: str | None = Field(
        None,
        description='Номер телефона пользователя в формате E.164',
    )
    tg_id: str | None = Field(
        None,
        max_length=Limits.MAX_TG_ID_LENGTH,
        description='Идентификатор Telegram для уведомлений',
    )
    password: str | None = Field(
        None,
        min_length=Limits.MIN_PASSWORD_LENGTH,
        max_length=Limits.MAX_PASSWORD_LENGTH,
        description='Новый пароль пользователя',
    )
    role: UserRole | None = Field(
        None,
        description='Роль пользователя',
    )
    active: bool | None = Field(
        None,
        description='Флаг активности пользователя',
        alias='is_active',
    )
    managed_cafes: list[int] | None = Field(
        None,
        description='ID кафе, которыми управляет пользователь',
    )

    @field_validator('phone')
    def validate_phone(cls, phone: str | None) -> str | None:  # noqa: N805
        """Валидирует формат телефонного номера."""
        return validate_phone_format(phone)

    model_config = ConfigDict(extra='forbid', populate_by_name=True)


class UserInfo(UserBase):
    """Схема для отображения информации о пользователе.

    Содержит дополнительные поля, такие как id, флаги состояния
    и временные метки. Используется для формирования ответов API.

    Attributes:
        id (int): Уникальный идентификатор пользователя.
        role (UserRole): Роль пользователя.
        active (bool): Флаг активности пользователя.
        created_at (datetime): Дата и время создания записи.
        updated_at (datetime): Дата и время последнего обновления записи.
        managed_cafes (List[int]): ID кафе, которыми управляет пользователь.

    """

    id: int = Field(..., description='Уникальный идентификатор пользователя')
    role: UserRole = Field(
        default=UserRole.USER,
        description='Роль пользователя',
    )
    active: bool = Field(
        ...,
        description='Флаг активности пользователя',
        alias='is_active',
    )
    created_at: datetime = Field(
        ...,
        description='Дата и время создания записи',
    )
    updated_at: datetime = Field(
        ...,
        description='Дата и время обновления записи',
    )
    managed_cafes: list[int] = Field(
        default_factory=list,
        description='ID кафе, которыми управляет пользователь',
    )

    @field_validator('managed_cafes', mode='before')
    def parse_managed_cafes(  # noqa: N805
        cls,  # noqa: N805
        value: object,
    ) -> list[int]:
        """Преобразует managed_cafes в список ID кафе."""
        if value is None:
            return []
        if isinstance(value, list):
            if value and hasattr(value[0], 'id'):
                return [cafe.id for cafe in value]
            return value
        return []

    @classmethod
    def from_orm(cls, obj: User) -> 'UserInfo':
        """Создает экземпляр UserInfo из ORM-объекта.

        Args:
            obj: ORM-объект пользователя.

        Returns:
            UserInfo: Экземпляр UserInfo.

        """
        user_info = cls.model_validate(obj, from_attributes=True)
        user_info.role = cls._resolve_role(obj)
        return user_info

    @staticmethod
    def _resolve_role(user: User) -> UserRole:
        """Определяет роль пользователя по данным модели."""
        if user.is_superuser:
            return UserRole.ADMIN
        if getattr(user, 'managed_cafes', None):
            if user.managed_cafes:
                return UserRole.MANAGER
        return UserRole.USER

    class Config:
        """Конфигурация Pydantic схемы."""

        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'id': 1,
                'username': 'ivanov',
                'email': 'ivanov@example.com',
                'phone': '+79161234567',
                'tg_id': '123456789',
                'role': UserRole.USER,
                'is_active': True,
                'managed_cafes': [1, 2],
                'created_at': Examples.DATETIME,
                'updated_at': Examples.DATETIME,
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
    email: str | None = Field(
        None,
        description='Электронная почта пользователя',
    )
    phone: str | None = Field(
        None,
        description='Номер телефона пользователя',
    )
    tg_id: str | None = Field(None, description='Идентификатор Telegram')

    class Config:
        """Конфигурация Pydantic схемы."""

        from_attributes = True
