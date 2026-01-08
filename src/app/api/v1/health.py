"""Health check endpoint для мониторинга статуса приложения."""

from fastapi import APIRouter

router = APIRouter(prefix='/health', tags=['health'])


@router.get('')
async def health_check() -> dict[str, str]:
    """Простая проверка здоровья приложения.

    Returns:
        dict: Статус приложения

    """
    return {'status': 'ok'}
