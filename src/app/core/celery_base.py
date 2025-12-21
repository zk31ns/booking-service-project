"""Обработка ошибок в задачах Celery."""

from typing import Any, Dict, Tuple, Type

import aiohttp
from celery import Task
from celery.app.trace import ExceptionInfo

from src.app.core.constants import EventType
from src.app.core.logging import logger


class BaseTask(Task):
    """Базовый класс для логирования ошибок в задачах Celery."""

    autoretry_for: Tuple[Type[Exception], ...] = (aiohttp.ClientError,)
    max_retries: int = 3
    default_retry_delay: int = 60
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
            f'SYSTEM: {EventType.TASK_FAILED} '
            'Error occurs while sending reminder for task '
            f'{self.name}: {exc}',
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
            f'SYSTEM: {EventType.TASK_FAILED} '
            f'Network error for task {self.name}, '
            f'retry {self.request.retries}: {exc}'
        )
