"""Настройка логирования с использованием Loguru.

Логирует в консоль и в файл с ротацией.
"""

import sys

from loguru import logger as _logger

from app.core.config import settings


def setup_logging() -> None:
    """Инициализировать логирование."""
    # Удалить стандартный обработчик
    _logger.remove()

    # Добавить логирование в консоль
    console_format = (
        '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | '
        '<level>{level: <8}</level> | '
        '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
        '<level>{message}</level>'
    )
    _logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=console_format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Добавить логирование в файл
    file_format = (
        '{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | '
        '{name}:{function}:{line} - {message}'
    )
    _logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        format=file_format,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression='zip',
        backtrace=True,
        diagnose=False,  # Без диагностики в файлах для экономии места
    )

    log_msg = (
        f'Logging initialized | Level: {settings.LOG_LEVEL} | '
        f'File: {settings.LOG_FILE}'
    )
    _logger.info(log_msg)


# Глобальный объект логгера
logger = _logger

# Инициализировать логирование при импорте модуля
setup_logging()

__all__ = ['logger', 'setup_logging']
