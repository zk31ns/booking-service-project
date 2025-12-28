"""Инициализация и настройка очереди задач Celery."""

from typing import Any, Dict, Optional

from celery import Celery, Task
from celery.schedules import crontab
from celery.signals import setup_logging as celery_setup_logging
from celery.signals import task_postrun, task_prerun

from app.core.config import settings
from app.core.constants import EventType, Times
from app.core.logging import logger, setup_logging

celery_app = Celery(
    'booking',
    broker=settings.rabbitmq_url,
    backend=settings.celery_result_backend,
)

# Настройка Celery
celery_app.conf.update(
    timezone=Times.TIME_ZONE,
    enable_utc=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_delivery_mode='persistent',
    task_time_limit=None,
    task_soft_time_limit=None,
    worker_prefetch_multiplier=1,
    result_backend_transport_options={
        'result_chord_ordered': True,
    },
    task_ignore_result=False,
    result_expires=Times.RABBITMQ_RESULT_EXPIRE,
    worker_hijack_root_logger=False,
)

# Настройка расписания для Celery Beat
celery_app.conf.beat_schedule = {
    'periodically_cleanup_expired_bookings': {
        'task': 'cleanup_expired_bookings',
        'schedule': crontab(
            hour=Times.CLEANUP_EXPIRED_BOOKINGS_START_HOUR,
            minute=Times.CLEANUP_EXPIRED_BOOKINGS_START_MINUTES
        ),
        'options': {
            'expires': Times.CELERY_BEAT_EXPIRED,
        },
    },
}


@celery_setup_logging.connect
def configure_loguru_for_celery(**kwargs: Any) -> None:
    """Настройка Loguru при запуске Celery worker."""
    setup_logging()
    logger.info('SYSTEM: Loguru was configured for Celery worker.')


@task_prerun.connect
def task_prerun_handler(
    sender: Optional[Celery] = None,
    task_id: Optional[str] = None,
    task: Optional[Task] = None,
    args: Optional[tuple[Any, ...]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> None:
    """Логирование старта задачи."""
    logger.info(
        f'SYSTEM: {EventType.TASK_STARTED} Task: {task.name} ID: {task_id}',
        extra={
            'task_id': task_id,
            'task_name': task.name,
            'args': args,
            'kwargs': kwargs,
        },
    )


@task_postrun.connect
def task_postrun_handler(
    sender: Optional[Celery] = None,
    task_id: Optional[str] = None,
    task: Optional[Task] = None,
    retval: Any = None,
    state: Optional[str] = None,
    **extra: Any,
) -> None:
    """Логирование завершения задачи."""
    logger.info(
        f'SYSTEM: {EventType.TASK_FINISHED} Task: {task.name} ID: {task_id}',
        extra={
            'task_id': task_id,
            'task_name': task.name,
            'state': state,
            'result': retval,
        },
    )


celery_app.autodiscover_tasks(['app.core.celery_tasks'])
