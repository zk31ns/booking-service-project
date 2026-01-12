"""Задачи Celery и уведомления для бронирований."""

import asyncio
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from http import HTTPStatus
from typing import Any

import aiohttp
from celery import Task
from pydantic import BaseModel
from sqlalchemy.pool import NullPool

from app.core.celery_app import celery_app
from app.core.celery_base import BaseTask
from app.core.config import settings
from app.core.constants import CeleryTasks, ErrorCode, EventType, Times
from app.core.exceptions import TelegramApiException
from app.core.logging import logger


class TelegramAPIResponse(BaseModel):
    """Ответ Telegram Bot API."""

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
    telegram_id: str | None,
    email: str | None,
    cafe_name: str,
    cafe_address: str,
    booking_date: str,
    start_time: str,
) -> None:
    """Отправить напоминание о бронировании пользователю.

    Уведомление отправляется параллельно в Telegram и на email (если есть).

    Args:
        self: Экземпляр задачи Celery.
        booking_id: Идентификатор бронирования.
        telegram_id: Telegram ID пользователя.
        email: Email пользователя.
        cafe_name: Название кафе.
        cafe_address: Адрес кафе.
        booking_date: Дата бронирования (ISO-строка).
        start_time: Время начала (HH:MM).

    Returns:
        None

    """
    booking_date_obj = date.fromisoformat(booking_date)
    if telegram_id:
        try:
            asyncio.run(
                _send_reminder_async(
                    booking_id,
                    telegram_id,
                    cafe_name,
                    cafe_address,
                    booking_date_obj,
                    start_time,
                )
            )
        except TelegramApiException:
            logger.exception(
                'SYSTEM: Telegram reminder failed for booking %s',
                booking_id,
            )
    _send_email_reminder(
        booking_id=booking_id,
        email=email,
        cafe_name=cafe_name,
        cafe_address=cafe_address,
        booking_date=booking_date_obj,
        start_time=start_time,
    )


async def _send_reminder_async(
    booking_id: int,
    telegram_id: str,
    cafe_name: str,
    cafe_address: str,
    booking_date: date,
    start_time: str,
) -> None:
    """Асинхронно отправить напоминание в Telegram.

    Args:
        booking_id: Идентификатор бронирования.
        telegram_id: Telegram ID пользователя.
        cafe_name: Название кафе.
        cafe_address: Адрес кафе.
        booking_date: Дата бронирования.
        start_time: Время начала.

    Returns:
        None

    """
    date_formatted = booking_date.strftime(Times.DATE_FORMAT)
    message_text = f"""<b>Напоминание о бронировании</b>
<b>Дата:</b> {date_formatted}
<b>Кафе:</b> {cafe_name}
<b>Адрес:</b> {cafe_address}
<b>Время:</b> {start_time}
"""

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
    telegram_id: str | None,
    email: str | None,
    cafe_name: str,
    user_name: str,
    table_seats: int,
    table_description: str,
    start_time: str,
    end_time: str,
    cancellation: bool,
) -> None:
    """Уведомить менеджера о бронировании или отмене.

    Уведомление отправляется параллельно в Telegram и на email (если есть).

    Args:
        self: Экземпляр задачи Celery.
        booking_id: Идентификатор бронирования.
        telegram_id: Telegram ID менеджера.
        email: Email менеджера.
        cafe_name: Название кафе.
        user_name: Имя пользователя.
        table_seats: Количество мест за столом.
        table_description: Описание столика.
        start_time: Время начала.
        end_time: Время окончания.
        cancellation: Признак отмены бронирования.

    Returns:
        None

    """
    if telegram_id:
        try:
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
        except TelegramApiException:
            logger.exception(
                'SYSTEM: Telegram manager notify failed for booking %s',
                booking_id,
            )
    _send_email_manager_notification(
        booking_id=booking_id,
        email=email,
        cafe_name=cafe_name,
        user_name=user_name,
        table_seats=table_seats,
        table_description=table_description,
        start_time=start_time,
        end_time=end_time,
        cancellation=cancellation,
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
    """Асинхронно отправить уведомление менеджеру в Telegram.

    Args:
        booking_id: Идентификатор бронирования.
        telegram_id: Telegram ID менеджера.
        cafe_name: Название кафе.
        user_name: Имя пользователя.
        table_seats: Количество мест за столом.
        table_description: Описание столика.
        start_time: Время начала.
        end_time: Время окончания.
        cancellation: Признак отмены бронирования.

    Returns:
        None

    """
    message_type = '<b>Новое бронирование</b>'
    if cancellation:
        message_type = '<b>Отмена бронирования</b>'
    message_text = f"""{message_type}
<b>Кафе:</b> {cafe_name}
<b>Пользователь:</b> {user_name}
<b>Мест:</b> {table_seats}
<b>Описание столика:</b> {table_description}
<b>Начало:</b> {start_time}
<b>Окончание:</b> {end_time}
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
def cleanup_expired_bookings(self: Task) -> dict[str, Any]:
    """Очистить просроченные бронирования.

    Меняет статус активных бронирований со статусом PENDING/CONFIRMED
    на COMPLETED и деактивирует их.

    Returns:
        dict: Количество обработанных записей и время выполнения.

    """
    logger.info(f'SYSTEM: {EventType.TASK_STARTED} for bookings cleanup ')
    expired_count = asyncio.run(_cleanup_expired_bookings_async())
    cleanup_date = datetime.now()
    logger.info(
        f'SYSTEM: {EventType.TASK_FINISHED} for bookings cleanup at '
        f'{cleanup_date.isoformat()} Expired: {expired_count}'
    )
    return {'Expired count': expired_count, 'Cleanup date': cleanup_date}


async def _cleanup_expired_bookings_async() -> int:
    """Очистить просроченные бронирования в отдельной сессии БД.

    Используется NullPool, чтобы избежать проблем с соединениями
    внутри Celery worker.

    Returns:
        int: Количество просроченных бронирований.

    """
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from app.repositories import (
        BookingRepository,
        CafeRepository,
        TableRepository,
    )
    from app.repositories.slot import SlotRepository
    from app.repositories.users import UserRepository
    from app.services.booking import BookingService

    engine = create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        future=True,
        poolclass=NullPool,
    )
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        booking_repo = BookingRepository(session)
        cafe_repo = CafeRepository(session)
        user_repo = UserRepository(session)
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
    await engine.dispose()
    return expired_count


async def _send_telegram_message(
    telegram_id: str,
    text: str,
) -> None:
    """Отправить сообщение в Telegram.

    Args:
        telegram_id: Telegram ID пользователя.
        text: Текст сообщения.

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


def _send_email_message(
    to_email: str | None,
    subject: str,
    body: str,
) -> None:
    """Отправить email уведомление, если настроен SMTP.

    Args:
        to_email: Email получателя.
        subject: Тема письма.
        body: Текст письма.

    Returns:
        None

    """
    if not to_email:
        return
    if not settings.smtp_server:
        logger.info('SYSTEM: Email skipped: SMTP is not configured.')
        return

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = settings.smtp_user or 'no-reply@booking.local'
    message['To'] = to_email
    message.set_content(body)

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(
                settings.smtp_server, settings.smtp_port
            ) as smtp:
                if settings.smtp_user and settings.smtp_password:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(
                settings.smtp_server, settings.smtp_port
            ) as smtp:
                smtp.ehlo()
                if settings.smtp_user and settings.smtp_password:
                    smtp.starttls()
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
    except Exception:
        logger.exception(
            'SYSTEM: Email send failed for recipient: %s', to_email
        )


def _send_email_reminder(
    booking_id: int,
    email: str | None,
    cafe_name: str,
    cafe_address: str,
    booking_date: date,
    start_time: str,
) -> None:
    """Отправить email-напоминание пользователю о бронировании.

    Args:
        booking_id: Идентификатор бронирования.
        email: Email пользователя.
        cafe_name: Название кафе.
        cafe_address: Адрес кафе.
        booking_date: Дата бронирования.
        start_time: Время начала.

    Returns:
        None

    """
    date_formatted = booking_date.strftime(Times.DATE_FORMAT)
    subject = f'Напоминание о бронировании #{booking_id}'
    body = (
        'Напоминание о бронировании\n'
        f'Дата: {date_formatted}\n'
        f'Кафе: {cafe_name}\n'
        f'Адрес: {cafe_address}\n'
        f'Время: {start_time}\n'
    )
    _send_email_message(email, subject, body)


def _send_email_manager_notification(
    booking_id: int,
    email: str | None,
    cafe_name: str,
    user_name: str,
    table_seats: int,
    table_description: str,
    start_time: str,
    end_time: str,
    cancellation: bool,
) -> None:
    """Отправить email менеджеру о бронировании или отмене.

    Args:
        booking_id: Идентификатор бронирования.
        email: Email менеджера.
        cafe_name: Название кафе.
        user_name: Имя пользователя.
        table_seats: Количество мест за столом.
        table_description: Описание столика.
        start_time: Время начала.
        end_time: Время окончания.
        cancellation: Признак отмены бронирования.

    Returns:
        None

    """
    if cancellation:
        subject = f'Отмена бронирования #{booking_id}'
        header = 'Отмена бронирования'
    else:
        subject = f'Новое бронирование #{booking_id}'
        header = 'Новое бронирование'
    body = (
        f'{header}\n'
        f'Кафе: {cafe_name}\n'
        f'Пользователь: {user_name}\n'
        f'Мест: {table_seats}\n'
        f'Описание столика: {table_description}\n'
        f'Начало: {start_time}\n'
        f'Окончание: {end_time}\n'
    )
    _send_email_message(email, subject, body)
