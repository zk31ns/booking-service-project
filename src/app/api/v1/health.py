"""Health-check endpoints для проверки здоровья приложения."""

from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel

from ...core.config import settings
from ...core.constants import TAGS_HEALTH
from ...core.logging import logger

router = APIRouter(tags=TAGS_HEALTH)


class HealthResponse(BaseModel):
    """Response для health-check эндпоинта."""

    status: str = 'ok'
    timestamp: datetime
    version: str
    environment: str


@router.get(
    '/health',
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary='Health Check',
    description='Проверить здоровье приложения',
)
async def health_check() -> HealthResponse:
    """Проверить, что приложение работает.

    Returns:
        HealthResponse: Статус приложения

    """
    logger.info('Health check requested')

    return HealthResponse(
        status='ok',
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
    )


__all__ = ['router']
