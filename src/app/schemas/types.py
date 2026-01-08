"""TypedDict определения для API ответов и внутренних структур данных.

Содержит строгие типы для словарей, используемых в API и сервисах.
Обеспечивает проверку типов на уровне IDE и статического анализа.
"""

from typing import Any, TypedDict


class TokenDict(TypedDict):
    """Словарь с информацией о JWT токенах.

    Используется для передачи информации о токенах доступа и обновления
    между функциями и в API ответах.

    Attributes:
        access_token: JWT токен доступа для API запросов.
        refresh_token: JWT токен обновления для получения нового access token.
        token_type: Тип токена (обычно 'bearer').

    """

    access_token: str
    refresh_token: str
    token_type: str


class AuthResponseDict(TypedDict):
    """Полный ответ аутентификации с информацией о пользователе.

    Возвращается при успешной аутентификации через POST /auth/login.

    Attributes:
        access_token: JWT токен доступа.
        refresh_token: JWT токен обновления.
        token_type: Тип токена (обычно 'bearer').
        user: Информация о пользователе (из схемы UserInfo).

    """

    access_token: str
    refresh_token: str
    token_type: str
    user: dict[str, Any]


class RefreshTokenResponseDict(TypedDict):
    """Ответ при обновлении access токена.

    Возвращается при успешном обновлении через POST /auth/refresh.

    Attributes:
        access_token: Новый JWT токен доступа.
        refresh_token: Новый или существующий токен обновления.
        token_type: Тип токена (обычно 'bearer').
        user: Обновленная информация о пользователе.

    """

    access_token: str
    refresh_token: str
    token_type: str
    user: dict[str, Any]


class AuthenticateResultDict(TypedDict):
    """Внутренний результат аутентификации пользователя.

    Используется для передачи результата от сервиса аутентификации
    к роутеру API. Содержит информацию о пользователе и токены.

    Attributes:
        user: Объект или словарь с информацией о пользователе (схема UserInfo).
        tokens: Словарь с access_token, refresh_token и token_type.

    """

    user: Any
    tokens: dict[str, str]


class ErrorResponseDict(TypedDict, total=False):
    """Стандартный словарь ошибки для API ответов.

    Используется для унификации формата ошибок во всех API ответах.

    Attributes:
        detail: Описание ошибки для пользователя.
        code: Код ошибки из enum ErrorCode.
        status_code: HTTP статус-код ошибки.

    """

    detail: str
    code: str
    status_code: int
