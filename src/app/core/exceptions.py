"""Исключения приложения и форматирование ошибок для API."""

from typing import Any

from fastapi import HTTPException, status

from app.core.constants import ErrorCode, Messages


class AppException(HTTPException):
    """Базовое исключение приложения с единым форматом ответа.

    Attributes:
        error_code: Код ошибки из перечисления ErrorCode.
        status_code: HTTP статус.
        detail: Сформированное тело ошибки.
        headers: Заголовки ответа.
        extra: Дополнительные поля ответа.

    """

    def __init__(
        self,
        error_code: ErrorCode,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализировать исключение с кодом и деталями.

        Args:
            error_code: Код ошибки ErrorCode.
            status_code: HTTP статус (по умолчанию 400).
            detail: Текст ошибки; если не указан, берется из Messages.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        self.error_code = error_code
        self.extra = extra or {}

        error_detail = detail or Messages.error(error_code)

        super().__init__(
            status_code=status_code,
            detail=self._format_detail(error_detail),
            headers=headers or {'X-Error-Code': error_code.value},
        )

    def _format_detail(self, detail: str) -> dict[str, Any]:
        """Сформировать тело ошибки в едином формате.

        Args:
            detail: Текст сообщения об ошибке.

        Returns:
            dict[str, Any]: Словарь с кодом, сообщением и timestamp.

        """
        return {
            'code': self.error_code.value,
            'message': detail,
            'timestamp': '2024-01-01T00:00:00Z',
            **self.extra,
        }


class AuthenticationException(AppException):
    """Ошибка аутентификации (HTTP 401)."""

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для ошибки аутентификации.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class AuthorizationException(AppException):
    """Ошибка авторизации (HTTP 403)."""

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для ошибки авторизации.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class NotFoundException(AppException):
    """Ошибка отсутствия ресурса (HTTP 404)."""

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для отсутствующего ресурса.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class ConflictException(AppException):
    """Ошибка конфликта данных (HTTP 409)."""

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для конфликта данных.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class ValidationException(AppException):
    """Ошибка валидации данных (HTTP 422)."""

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для ошибки валидации.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class InternalServerException(AppException):
    """Внутренняя ошибка сервера (HTTP 500)."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для внутренней ошибки сервера.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class ServiceUnavailableException(AppException):
    """Сервис временно недоступен (HTTP 503)."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.SERVICE_UNAVAILABLE,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для недоступного сервиса.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class TelegramApiException(AppException):
    """Ошибка взаимодействия с Telegram API (HTTP 502)."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.BAD_GATEWAY,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Создать исключение для ошибки Telegram API.

        Args:
            error_code: Код ошибки ErrorCode.
            detail: Текст сообщения об ошибке.
            headers: Заголовки HTTP ответа.
            extra: Дополнительные поля ответа.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            headers=headers,
            extra=extra,
        )
