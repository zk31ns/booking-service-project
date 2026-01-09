"""Обработка ошибок в задачах Celery."""

from typing import Any, Dict, Tuple, Type

import aiohttp
from celery import Task
from celery.app.trace import ExceptionInfo

from app.core.constants import EventType, Limits, Times
from app.core.logging import logger


class BaseTask(Task):
    """Базовый класс для логирования ошибок в задачах Celery."""

    autoretry_for: Tuple[Type[Exception], ...] = (aiohttp.ClientError,)
    max_retries: int = Limits.TASK_MAX_RETRIES
    default_retry_delay: int = Times.CELERY_TASK_RETRY_DELAY
    acks_late: bool = True

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        einfo: ExceptionInfo,
    ) -> None:
        """Вызывается при финальной ошибке (после всех retry).

        Args:
            exc: Исключение, вызвавшее ошибку
            task_id: ID задачи
            args: Позиционные аргументы задачи
            kwargs: Именованные аргументы задачи
            einfo: Информация об исключении (traceback)

        """
        logger.error(
            'SYSTEM: {} Error occurs while sending reminder for task {}: {}',
            EventType.TASK_FAILED,
            self.name,
            exc,
            exc_info=True,
        )

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        einfo: ExceptionInfo,
    ) -> None:
        """Вызывается при retry.

        Args:
            exc: Исключение, вызвавшее retry
            task_id: ID задачи
            args: Позиционные аргументы задачи
            kwargs: Именованные аргументы задачи
            einfo: Информация об исключении

        """
        logger.warning(
            'SYSTEM: {} Network error for task {}, retry {}: {}',
            EventType.TASK_FAILED,
            self.name,
            self.request.retries,
            exc,
        )
