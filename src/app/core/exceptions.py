"""Кастомные исключения приложения.

Содержит иерархию исключений для централизованной обработки ошибок.
Все исключения наследуются от AppException и преобразуются в HTTPException.
"""

from typing import Any

from fastapi import HTTPException, status

from app.core.constants import ErrorCode, Messages


class AppException(HTTPException):
    """Базовое исключение приложения.

    Наследуется от HTTPException и добавляет поддержку кодов ошибок
    и структурированных деталей.

    Attributes:
        error_code: Код ошибки из ErrorCode enum.
        status_code: HTTP статус код.
        detail: Детальное сообщение об ошибке.
        headers: HTTP заголовки ответа.
        extra: Дополнительные данные об ошибке.

    """

    def __init__(
        self,
        error_code: ErrorCode,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение.

        Args:
            error_code: Код ошибки из ErrorCode.
            status_code: HTTP статус код (по умолчанию 400).
            detail: Сообщение об ошибке. Если не указано, берётся из Messages.
            headers: Дополнительные HTTP заголовки.
            extra: Дополнительные данные для включения в ответ.

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
        """Форматирует детали ошибки в структурированный вид.

        Args:
            detail: Текст сообщения об ошибке.

        Returns:
            Словарь с детализированной информацией об ошибке.

        """
        return {
            'code': self.error_code.value,
            'message': detail,
            'timestamp': '2024-01-01T00:00:00Z',
            **self.extra,
        }


class AuthenticationException(AppException):
    """Исключение аутентификации.

    Используется для ошибок связанных с аутентификацией пользователя.
    Статус код: 401 UNAUTHORIZED.

    """

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение аутентификации.

        Args:
            error_code: Код ошибки аутентификации.
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class AuthorizationException(AppException):
    """Исключение авторизации.

    Используется для ошибок связанных с правами доступа.
    Статус код: 403 FORBIDDEN.

    """

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение авторизации.

        Args:
            error_code: Код ошибки авторизации.
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class NotFoundException(AppException):
    """Исключение 'Не найдено'.

    Используется когда запрашиваемый ресурс не существует.
    Статус код: 404 NOT FOUND.

    """

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение 'Не найдено'.

        Args:
            error_code: Код ошибки.
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class ConflictException(AppException):
    """Исключение конфликта.

    Используется когда запрос конфликтует с текущим состоянием ресурса.
    Статус код: 409 CONFLICT.

    """

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение конфликта.

        Args:
            error_code: Код ошибки конфликта.
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class ValidationException(AppException):
    """Исключение валидации.

    Используется для ошибок валидации входных данных.
    Статус код: 422 UNPROCESSABLE ENTITY.

    """

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение валидации.

        Args:
            error_code: Код ошибки валидации.
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class InternalServerException(AppException):
    """Исключение внутренней ошибки сервера.

    Используется для непредвиденных ошибок сервера.
    Статус код: 500 INTERNAL SERVER ERROR.

    """

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение внутренней ошибки.

        Args:
            error_code: Код ошибки (по умолчанию INTERNAL_SERVER_ERROR).
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class ServiceUnavailableException(AppException):
    """Исключение 'Сервис недоступен'.

    Используется когда сервис временно недоступен.
    Статус код: 503 SERVICE UNAVAILABLE.

    """

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.SERVICE_UNAVAILABLE,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение 'Сервис недоступен'.

        Args:
            error_code: Код ошибки (по умолчанию SERVICE_UNAVAILABLE).
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            headers=headers,
            extra=extra,
        )


class TelegramApiException(AppException):
    """Исключение 'Ошибка API Telegram'.

    Используется при неожиданном ответе API Telegram.
    Статус код: 502 Bad Gateway.

    """

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.BAD_GATEWAY,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение 'Сервис недоступен'.

        Args:
            error_code: Код ошибки (по умолчанию SERVICE_UNAVAILABLE).
            detail: Сообщение об ошибке.
            headers: HTTP заголовки.
            extra: Дополнительные данные.

        """
        super().__init__(
            error_code=error_code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            headers=headers,
            extra=extra,
        )
