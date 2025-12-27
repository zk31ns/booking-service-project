from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.users.dependencies import get_user_repository
from app.api.v1.users.repository import UserRepository
from app.db.session import get_session
from app.repositories import (
    BookingRepository,
    CafeRepository,
    TableRepository,
)
from app.repositories.slot import SlotRepository
from app.services.booking import BookingService


async def get_cafe_repository(
    session: AsyncSession = Depends(get_session),
) -> CafeRepository:
    """Получить репозиторий для работы с кафе.

    Args:
        session: Асинхронная сессия SQLAlchemy

    Returns:
        Инициализированный репозиторий кафе

    """
    return CafeRepository(session)


async def get_table_repository(
    session: AsyncSession = Depends(get_session),
) -> TableRepository:
    """Получить репозиторий для работы со столиками.

    Args:
        session: Асинхронная сессия SQLAlchemy

    Returns:
        Инициализированный репозиторий столиков

    """
    return TableRepository(session)


async def get_slot_repository(
    session: AsyncSession = Depends(get_session),
) -> SlotRepository:
    """Получить репозиторий для работы со временными слотами.

    Args:
        session: Асинхронная сессия SQLAlchemy

    Returns:
        Инициализированный репозиторий слотов времени

    """
    return SlotRepository(session)


async def get_booking_repository(
    session: AsyncSession = Depends(get_session),
) -> BookingRepository:
    """Получить репозиторий для работы с бронированиями.

    Args:
        session: Асинхронная сессия SQLAlchemy

    Returns:
        Инициализированный репозиторий бронирований

    """
    return BookingRepository(session)


async def get_booking_service(
    booking_repo: BookingRepository = Depends(get_booking_repository),
    cafe_repo: CafeRepository = Depends(get_cafe_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    table_repo: TableRepository = Depends(get_table_repository),
    slot_repo: SlotRepository = Depends(get_slot_repository),
) -> BookingService:
    """Получить сервис для работы с бронированиями.

    Инициализирует и возвращает BookingService со всеми необходимыми
    репозиториями через dependency injection.

    Args:
        booking_repo: Репозиторий бронирований
        cafe_repo: Репозиторий кафе
        user_repo: Репозиторий пользователей
        table_repo: Репозиторий столиков
        slot_repo: Репозиторий слотов времени

    Returns:
        Инициализированный сервис бронирований

    """
    return BookingService(
        booking_repo=booking_repo,
        cafe_repo=cafe_repo,
        user_repo=user_repo,
        table_repo=table_repo,
        slot_repo=slot_repo,
    )
