"""Создание задач Celery."""

import asyncio
from datetime import date, datetime
from http import HTTPStatus
from typing import Any, Dict

import aiohttp
from celery import Task
from pydantic import BaseModel

from app.api.v1.users.repository import UserRepository
from app.core.celery_app import celery_app
from app.core.celery_base import BaseTask
from app.core.config import settings
from app.core.constants import CeleryTasks, ErrorCode, EventType, Times
from app.core.exceptions import TelegramApiException
from app.core.logging import logger
from app.db.session import async_session_maker
from app.repositories import (
    BookingRepository,
    CafeRepository,
    TableRepository,
)
from app.repositories.slot import SlotRepository


class TelegramAPIResponse(BaseModel):
    """Схема ответа Telegram Bot API."""

    ok: bool
    description: str | None = None
    result: dict | None = None


@celery_app.task(
    name=CeleryTasks.BOOKING_REMINDER_TASK_NAME,
    bind=True,
    base=BaseTask,
)
def send_booking_reminder(
    self: Task,
    booking_id: int,
    telegram_id: str,
    cafe_name: str,
    cafe_address: str,
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
        cafe_address: адрес кафе
        booking_date: дата бронирования
        start_time: дата начала слота бронирования

    Returns:
        None

    """
    asyncio.run(
        _send_reminder_async(
            booking_id,
            telegram_id,
            cafe_name,
            cafe_address,
            booking_date,
            start_time,
        )
    )


async def _send_reminder_async(
    booking_id: int,
    telegram_id: str,
    cafe_name: str,
    cafe_address: str,
    booking_date: datetime,
    start_time: str,
) -> None:
    """Асинхронная отправка напоминания.

    Args:
        booking_id: ID бронирования
        telegram_id: ID пользователя в Telegram
        cafe_name: название кафе
        cafe_address: адрес кафе
        booking_date: дата бронирования
        start_time: дата начала слота бронирования

    Returns:
        None

    """
    date_formatted = booking_date.strftime('%d.%m.%Y')
    message_text = f"""🔔 <b>Напоминание о бронировании</b>
    📅 <b>Дата:</b> {date_formatted}
    🏠 <b>Заведение:</b> {cafe_name}
    🗺️ <b>Адрес:</b> {cafe_address}
    ⏰ <b>Время бронирования:</b> {start_time}
    Ждём вас!"""

    await _send_telegram_message(telegram_id=telegram_id, text=message_text)

    logger.info(
        f'SYSTEM: {EventType.REMINDER_SENT} for booking {booking_id} '
        f'(telegram_id: {telegram_id})'
    )


@celery_app.task(
    name=CeleryTasks.NOTIFY_MANAGER_TASK_NAME,
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

    Returns:
        None

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

    Returns:
        None

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
        f'booking: {booking_id} telegram_id: {telegram_id}'
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
    expired_count = asyncio.run(_cleanup_expired_bookings_async())
    cleanup_date = datetime.now()
    logger.info(
        f'SYSTEM: {EventType.TASK_FINISHED} for bookings cleanup at '
        f'{cleanup_date.isoformat()} Expired: {expired_count}'
    )
    return {
        'Expired count': expired_count,
        'Cleanup date': cleanup_date
    }


async def _cleanup_expired_bookings_async() -> int:
    """Асинхронная очистка истёкших бронирований.

    Returns:
        Количество обработанных записей

    """
    from app.services.booking import BookingService

    async with async_session_maker() as session:
        booking_repo = BookingRepository(session)
        cafe_repo = CafeRepository(session)
        user_repo = UserRepository()
        table_repo = TableRepository(session)
        slot_repo = SlotRepository(session)
        booking_service = BookingService(
            booking_repo=booking_repo,
            cafe_repo=cafe_repo,
            user_repo=user_repo,
            table_repo=table_repo,
            slot_repo=slot_repo,
        )
        now = date.today()
        expired_count = await booking_service.cleanup_expired_bookings(now=now)
        await session.commit()
    return {'expired_count': expired_count, 'timestamp': now.isoformat()}


async def _send_telegram_message(
    telegram_id: str,
    text: str,
) -> None:
    """Отправка сообщения в Telegram пользователя.

    Args:
        telegram_id: ID пользователя в Telegram
        text: текст сообщения

    Returns:
        None

    """
    url = (
        f'{settings.telegram_api_url}/bot'
        f'{settings.telegram_bot_token}/sendMessage'
    )

    payload = {
        'chat_id': telegram_id,
        'text': text,
        'parse_mode': 'HTML',
    }

    timeout = aiohttp.ClientTimeout(
        total=Times.TELEGRAM_REQUEST_TIMEOUT,
        connect=Times.TELEGRAM_CONNECT_TIMEOUT,
    )

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            response_json_data = await response.json()
            response_data = TelegramAPIResponse(**response_json_data)

            if response.status != HTTPStatus.OK or not response_data.ok:
                error_description = response_data.description
                logger.error(
                    f'Telegram API error: {error_description} '
                    f'status: {response.status}'
                )
                raise TelegramApiException(
                    detail=ErrorCode.BAD_GATEWAY,
                )
