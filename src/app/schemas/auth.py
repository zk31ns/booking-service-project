from pydantic import BaseModel, Field


class AuthData(BaseModel):
    """Схема входа для получения токена."""

    login: str = Field(
        ...,
        description='Логин пользователя (email или телефон)',
    )
    password: str = Field(
        ...,
        description='Пароль пользователя',
        json_schema_extra={'format': 'password', 'writeOnly': True},
    )
