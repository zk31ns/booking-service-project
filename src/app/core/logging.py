"""Настройка логирования с использованием Loguru.

Логирует в консоль и в файл с ротацией.
"""

import sys

from loguru import logger as _logger

from .config import settings


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
        level=settings.log_level,
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
        settings.log_file,
        level=settings.log_level,
        format=file_format,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression='zip',
        backtrace=True,
        diagnose=False,  # Без диагностики в файлах для экономии места
    )

    log_msg = (
        f'Logging initialized | Level: {settings.log_level} | '
        f'File: {settings.log_file}'
    )
    _logger.info(log_msg)


# Глобальный объект логгера
logger = _logger

# Инициализировать логирование при импорте модуля
setup_logging()

__all__ = ['logger', 'setup_logging']
