from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import BookingRepository
from .service import BookingService
from src.app.api.v1.slots.repository import SlotRepository
from src.app.api.v1.users.dependencies import get_user_repository
from src.app.api.v1.users.repository import UserRepository
from src.app.db.session import get_session
from src.app.repositories import CafeRepository, TableRepository


async def get_cafe_repository(
    session: AsyncSession = Depends(get_session),
) -> CafeRepository:
    """Получить репозиторий кафе."""
    return CafeRepository(session)


async def get_table_repository(
    session: AsyncSession = Depends(get_session),
) -> TableRepository:
    """Получить репозиторий столиков."""
    return TableRepository(session)


async def get_slot_repository(
    session: AsyncSession = Depends(get_session),
) -> SlotRepository:
    """Получить репозиторий слотов."""
    return SlotRepository(session)


async def get_booking_repository(
    session: AsyncSession = Depends(get_session),
) -> BookingRepository:
    """Получить репозиторий бронирований."""
    return BookingRepository()


async def get_booking_service(
    booking_repo: BookingRepository = Depends(get_booking_repository),
    cafe_repo: CafeRepository = Depends(get_cafe_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    table_repo: TableRepository = Depends(get_table_repository),
    slot_repo: SlotRepository = Depends(get_slot_repository),
) -> BookingService:
    """Получить сервис бронирований."""
    return BookingService(
        booking_repo=booking_repo,
        cafe_repo=cafe_repo,
        user_repo=user_repo,
        table_repo=table_repo,
        slot_repo=slot_repo,
    )
