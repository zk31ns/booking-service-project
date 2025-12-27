"""Создание задач Celery."""

import asyncio
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any, Dict

import aiohttp
from celery import Task

from src.app.core.celery_app import celery_app
from src.app.core.celery_base import BaseTask
from src.app.core.config import settings
from src.app.core.constants import EventType, Times
from src.app.core.logging import logger


@celery_app.task(
    name='send_booking_reminder',
    bind=True,
    base=BaseTask,
)
def send_booking_reminder(
    self: Task,
    booking_id: int,
    telegram_id: str,
    cafe_name: str,
    booking_date: datetime,
    start_time: str,
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
    asyncio.run(
        _send_reminder_async(
            booking_id, telegram_id, cafe_name, booking_date, start_time
        )
    )


async def _send_reminder_async(
    booking_id: int,
    telegram_id: str,
    cafe_name: str,
    booking_date: datetime,
    start_time: str,
) -> None:
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

    await _send_telegram_message(telegram_id=telegram_id, text=message_text)

    logger.info(
        f'SYSTEM: {EventType.REMINDER_SENT} for booking {booking_id} '
        f'(telegram_id: {telegram_id})'
    )


@celery_app.task(
    name='send_notify_manager',
    bind=True,
    base=BaseTask,
)
def notify_manager(
    self: Task,
    booking_id: int,
    telegram_id: str,
    cafe_name: str,
    user_name: str,
    table_seats: int,
    table_description: str,
    start_time: str,
    end_time: str,
    cancellation: bool,
) -> None:
    """Отправка напоминания о бронировании столика менеджеру в Telegram.

    Запускает асинхронный код.
    Задача Выполняется один раз немедленно.

    Args:
        self: экземпляр задачи
        booking_id: ID бронирования
        telegram_id: ID менеджера в Telegram
        cafe_name: название кафе
        user_name: имя пользователя, сделавшего бронирование
        table_seats: число мест за столом,
        table_description: описание стола,
        start_time: время начала слота бронирования
        end_time: время окончания слота бронирования
        cancellation: признак отмены бронирования


    """
    asyncio.run(
        _notify_manager_async(
            booking_id,
            telegram_id,
            cafe_name,
            user_name,
            table_seats,
            table_description,
            start_time,
            end_time,
            cancellation,
        )
    )


async def _notify_manager_async(
    booking_id: int,
    telegram_id: str,
    cafe_name: str,
    user_name: str,
    table_seats: int,
    table_description: str,
    start_time: str,
    end_time: str,
    cancellation: bool,
) -> None:
    """Асинхронная отправка уведомления менеджеру.

    Args:
        booking_id: ID бронирования
        telegram_id: ID менеджера в Telegram
        cafe_name: название кафе
        user_name: имя пользователя, сделавшего бронирование
        table_seats: число мест за столом,
        table_description: описание стола,
        start_time: время начала слота бронирования
        end_time: время окончания слота бронирования
        cancellation: признак отмены бронирования

    """
    message_type = '🔔 <b>Напоминание о новом бронировании</b>'
    if cancellation:
        message_type = '❌ <b>Напоминание об отмене бронирования</b>'
    message_text = f"""{message_type}
    🏠 <b>Заведение:</b> {cafe_name}
    🧑 <b>Посетитель:</b> {user_name}
    🪑 <b>Число мест:</b> {table_seats}
    📃 <b>Описание столика:</b> {table_description}
    ⏰ <b>Начало слота бронирования:</b> {start_time}
    ⏰ <b>Окончание слота бронирования:</b> {end_time}
    """

    await _send_telegram_message(telegram_id=telegram_id, text=message_text)
    logger.info(
        f'SYSTEM: {EventType.REMINDER_SENT} for manager on '
        f'booking {booking_id} (telegram_id: {telegram_id})'
    )


@celery_app.task(
    name='cleanup_expired_bookings',
    bind=True,
    base=BaseTask,
)
def cleanup_expired_bookings(self: Task) -> Dict[str, Any]:
    """Очистка истёкших бронирований.

    Периодическая задача.
    Находит бронирования, у которых:
    - Дата бронирования прошла
    - Статус всё ещё 'active' или 'pending'
    Меняет их статус на 'expired'.

    Returns:
        dict: Результат выполнения с количеством обработанных записей

    """
    logger.info(f'SYSTEM: {EventType.TASK_STARTED} for bookings cleanup ')
    result = asyncio.run(_cleanup_expired_bookings_async())
    logger.info(
        f'SYSTEM: {EventType.TASK_FINISHED} for bookings cleanup '
        f'Expired: {result["expired_count"]}, '
    )
    return result


async def _cleanup_expired_bookings_async() -> Dict[str, Any]:
    """Асинхронная очистка истёкших бронирований.

    Returns:
        dict: Статистика выполнения

    """
    # заготовка функции
    now = datetime.now(timezone.utc)
    expired_count = 0

    return {'expired_count': expired_count, 'timestamp': now.isoformat()}


async def _send_telegram_message(
    telegram_id: str,
    text: str,
) -> None:
    """Отправка сообщения в Telegram пользователя.

    Args:
        telegram_id: ID пользователя в Telegram
        text: текст сообщения

    """
    url = (
        f'{settings.TELEGRAM_API_URL}/bot'
        f'{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    )

    payload = {
        'chat_id': telegram_id,
        'text': text,
        'parse_mode': 'HTML',
    }

    timeout = aiohttp.ClientTimeout(
        total=Times.TELEGRAM_REQUEST_TIMEOUT, connect=10
    )

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            response_data = await response.json()

            if response.status != HTTPStatus.OK or not response_data.get('ok'):
                error_description = response_data.get(
                    'description', 'Unknown error'
                )
                logger.error(
                    f'Telegram API error: {error_description} '
                    f'(status: {response.status})'
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f'Telegram API error: {error_description}',
                    headers=response.headers,
                )
