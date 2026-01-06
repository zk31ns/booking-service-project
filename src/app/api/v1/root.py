"""Корневой endpoint для проверки статуса приложения."""

from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel

from ...core.config import settings
from ...core.constants import API, EventType, Messages
from ...core.logging import logger

router = APIRouter(tags=API.ROOT)


class RootResponse(BaseModel):
    """Response для корневого эндпоинта."""

    answer: str
    timestamp: datetime
    version: str
    environment: str


@router.get(
    '/',
    response_model=RootResponse,
    status_code=status.HTTP_200_OK,
    summary='Send greeting message',
    description='Приветственное сообщение',
)
async def root_message() -> RootResponse:
    """Проверить, что приложение работает.

    Returns:
        RootResponse: Приветственное сообщение и статус сервиса

    """
    logger.info(f'SYSTEM: {EventType.GREETING_SENT}')

    return RootResponse(
        answer=Messages.success_messages[EventType.GREETING_SENT],
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
    )


__all__ = ['router']
