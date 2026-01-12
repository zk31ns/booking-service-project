"""Базовые мixin классы для сервисов.

Содержит часто используемые методы валидации и обработки ошибок
для уменьшения дублирования кода в сервис-слое.
"""

from typing import Generic, TypeVar

from fastapi import status

from app.core.base import TimestampedModel
from app.core.constants import ErrorCode, Messages
from app.core.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
)

ModelType = TypeVar('ModelType', bound=TimestampedModel)


class EntityValidationMixin(Generic[ModelType]):
    """Mixin с методами валидации сущностей.

    Содержит стандартные методы для проверки существования,
    активности и других общих условий сущностей.

    Generic:
        ModelType: Тип модели, которая наследует TimestampedModel

    """

    async def _validate_exists(
        self,
        entity: ModelType | None,
        entity_name: str,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ) -> ModelType:
        """Проверить что сущность существует.

        Args:
            entity: Объект сущности для проверки (может быть None).
            entity_name: Название сущности для error сообщения.
            error_code: Код ошибки для использования (по
                умолчанию VALIDATION_ERROR).
            status_code: HTTP статус код (по умолчанию 404).

        Returns:
            Проверенная сущность.

        Raises:
            AppException: Если сущность не найдена или None.

        Examples:
            >>> cafe = await self.cafe_repository.get(cafe_id)
            >>> validated_cafe = await self._validate_exists(
            ...     cafe, 'Cafe', ErrorCode.CAFE_NOT_FOUND
            ... )

        """
        if not entity:
            detail = Messages.errors.get(
                error_code,
                f'{entity_name} not found',
            )
            raise AppException(
                error_code=error_code,
                status_code=status_code,
                detail=detail,
            )
        return entity

    async def _validate_active(
        self,
        entity: ModelType,
        entity_name: str,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        status_code: int = status.HTTP_410_GONE,
    ) -> ModelType:
        """Проверить что сущность активна.

        Args:
            entity: Объект сущности для проверки.
            entity_name: Название сущности для error сообщения.
            error_code: Код ошибки для использования.
            status_code: HTTP статус код (по умолчанию 410).

        Returns:
            Проверенная активная сущность.

        Raises:
            AppException: Если сущность неактивна.

        Examples:
            >>> cafe = await self.cafe_repository.get(cafe_id)
            >>> await self._validate_exists(
            ...     cafe, 'Cafe', ErrorCode.CAFE_NOT_FOUND
            ... )
            >>> await self._validate_active(
            ...     cafe, 'Cafe', ErrorCode.CAFE_INACTIVE
            ... )

        """
        if not entity.active:
            detail = Messages.errors.get(
                error_code,
                f'{entity_name} is inactive',
            )
            raise AppException(
                error_code=error_code,
                status_code=status_code,
                detail=detail,
            )
        return entity

    async def _validate_exists_and_active(
        self,
        entity: ModelType | None,
        entity_name: str,
        not_found_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        inactive_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
    ) -> ModelType:
        """Проверить что сущность существует и активна.

        Комбинирует проверки exists и active в одном вызове для удобства.

        Args:
            entity: Объект сущности для проверки.
            entity_name: Название сущности для error сообщения.
            not_found_code: Код ошибки если не найдена.
            inactive_code: Код ошибки если неактивна.

        Returns:
            Проверенная активная сущность.

        Raises:
            AppException: Если сущность не найдена или неактивна.

        Examples:
            >>> cafe = await self.cafe_repository.get(cafe_id)
            >>> valid_cafe = await self._validate_exists_and_active(
            ...     cafe,
            ...     'Cafe',
            ...     ErrorCode.CAFE_NOT_FOUND,
            ...     ErrorCode.CAFE_INACTIVE,
            ... )

        """
        entity = await self._validate_exists(
            entity,
            entity_name,
            not_found_code,
            status.HTTP_404_NOT_FOUND,
        )
        await self._validate_active(
            entity,
            entity_name,
            inactive_code,
            status.HTTP_410_GONE,
        )
        return entity

    async def _raise_conflict(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
    ) -> None:
        """Выбросить исключение конфликта данных (409).

        Args:
            error_code: Код ошибки.
            detail: Дополнительное описание ошибки.

        Raises:
            ConflictException: С статусом 409 Conflict.

        """
        raise ConflictException(
            error_code=error_code,
            detail=detail or Messages.errors.get(error_code, 'Conflict'),
        )

    async def _raise_not_found(
        self,
        error_code: ErrorCode,
        entity_name: str = 'Entity',
    ) -> None:
        """Выбросить исключение "не найдено" (404).

        Args:
            error_code: Код ошибки.
            entity_name: Название сущности для сообщения.

        Raises:
            NotFoundException: С статусом 404 Not Found.

        """
        detail = Messages.errors.get(
            error_code,
            f'{entity_name} not found',
        )
        raise NotFoundException(
            error_code=error_code,
            detail=detail,
        )

    async def _raise_inactive(
        self,
        error_code: ErrorCode,
        entity_name: str = 'Entity',
    ) -> None:
        """Выбросить исключение "сущность неактивна" (410).

        Args:
            error_code: Код ошибки.
            entity_name: Название сущности для сообщения.

        Raises:
            AppException: С статусом 410 Gone.

        """
        detail = Messages.errors.get(
            error_code,
            f'{entity_name} is inactive',
        )
        raise AppException(
            error_code=error_code,
            status_code=status.HTTP_410_GONE,
            detail=detail,
        )


__all__ = ['EntityValidationMixin']
