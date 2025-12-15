"""Создание задач Celery."""

import asyncio
from datetime import datetime
from http import HTTPStatus

import aiohttp
from celery import Task

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.constants import EventType, Times
from app.core.logging import logger


@celery_app.task(
    name='send_booking_reminder',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_booking_reminder(self: Task,
                          booking_id: int,
                          telegram_id: str,
                          cafe_name: str,
                          booking_date: datetime,
                          start_time: str
                          ) -> None:
    """Отправка напоминания о бронировании в Telegram.

    Запускает асинхронный код.
    Задача Выполняется один раз в указанное время.

    Args:
        self: экземпляр задачи
        booking_id: ID бронирования
        telegram_id: ID пользователя в Telegram
        cafe_name: название кафе
        booking_date: дата бронирования
        start_time: дата начала слота бронирования

    """
    logger.info(
        f'SYSTEM: {EventType.TASK_STARTED} for booking {booking_id} '
        f'(task_id: {self.request.id})'
    )

    try:
        asyncio.run(_send_reminder_async(booking_id,
                                         telegram_id,
                                         cafe_name,
                                         booking_date,
                                         start_time))
        logger.info(
            f'SYSTEM: {EventType.TASK_FINISHED} for booking {booking_id} '
            f'(task_id: {self.request.id})'
        )
    except aiohttp.ClientError as exc:
        logger.warning(
            f'Network error for booking {booking_id}, '
            f'retry {self.request.retries}: {exc}'
        )
        raise self.retry(exc=exc, countdown=(60 * (2 ** self.request.retries)))
    except Exception as exc:
        logger.error(
            'Error occurs while sending reminder for booking '
            f'{booking_id}: {exc}',
            exc_info=True
        )
        raise self.retry(exc=exc)


async def _send_reminder_async(booking_id: int,
                               telegram_id: str,
                               cafe_name: str,
                               booking_date: datetime,
                               start_time: str) -> None:
    """Асинхронная отправка напоминания.

    Args:
        booking_id: ID бронирования
        telegram_id: ID пользователя в Telegram
        cafe_name: название кафе
        booking_date: дата бронирования
        start_time: дата начала слота бронирования

    """
    date_formatted = booking_date.strftime('%d.%m.%Y')
    message_text = f"""🔔 <b>Напоминание о бронировании</b>
    📅 <b>Дата:</b> {date_formatted}
    🏠 <b>Заведение:</b> {cafe_name}
    ⏰ <b>Время бронирования:</b> {start_time}
    Ждём вас!"""

    await _send_telegram_message(
        telegram_id=telegram_id,
        text=message_text
    )

    logger.info(
        f'SYSTEM: {EventType.REMINDER_SENT} for booking {booking_id} '
        f'(telegram_id: {telegram_id})')


async def _send_telegram_message(
    telegram_id: str,
    text: str,
 ) -> None:
    """Отправка сообщения в Telegram пользователя.

    Args:
        telegram_id: ID пользователя в Telegram
        text: текст сообщения

    """
    url = (f'{settings.TELEGRAM_API_URL}/bot'
           f'{settings.TELEGRAM_BOT_TOKEN}/sendMessage')

    payload = {
        'chat_id': telegram_id,
        'text': text,
        'parse_mode': 'HTML',
    }

    timeout = aiohttp.ClientTimeout(total=Times.TELEGRAM_REQUEST_TIMEOUT,
                                    connect=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            response_data = await response.json()
            if response.status != HTTPStatus.OK or not response_data.get('ok'):
                error_description = response_data.get('description',
                                                      'Unknown error')
                logger.error(
                    f'Telegram API error: {error_description} '
                    f'(status: {response.status})'
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f'Telegram API error: {error_description}',
                    headers=response.headers
                )
