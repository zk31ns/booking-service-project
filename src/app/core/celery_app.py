"""Инициализация и настройка очереди задач Celery."""

from celery import Celery

from app.core.config import settings
from app.core.constants import Times

celery_app = Celery(
    'booking',
    broker=settings.RABBITMQ_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Настройка Celery
celery_app.conf.update(
    # часовой пояс
    timezone=Times.TIME_ZONE,
    enable_utc=True,
    # параметры сериализации
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    # параметры персистентности задач
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_delivery_mode='persistent',
    # параметры отложенных задач
    task_time_limit=None,
    task_soft_time_limit=None,
    worker_prefetch_multiplier=1,
    # параметры хранения задач для RabbitMQ backend
    result_backend_transport_options={
        'result_chord_ordered': True,
    },
    task_ignore_result=False,
    result_expires=Times.RABBITMQ_RESULT_EXPIRE,
)

celery_app.autodiscover_tasks(['app.core.celery_tasks'])
