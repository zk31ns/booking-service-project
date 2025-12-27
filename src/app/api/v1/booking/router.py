from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends

from .dependencies import get_booking_service
from .schemas import BookingCreate, BookingDB, BookingUpdate
from src.app.api.v1.users.dependencies import get_current_active_user
from src.app.models import Booking, User
from src.app.services.booking import BookingService

router = APIRouter()


@router.get(
    '/',
    response_model=list[BookingDB],
)
async def get_all_bookings(
    current_user: Annotated[User, Depends(get_current_active_user)],
    show_all: bool = True,
    cafe_id: Optional[int] = None,
    user_id: Optional[int] = None,
    service: BookingService = Depends(get_booking_service),
) -> List[Booking]:
    """Получить все доступные бронирования."""
    return await service.get_all_bookings(
        current_user=current_user,
        show_all=show_all,
        cafe_id=cafe_id,
        user_id=user_id,
    )


@router.post(
    '/',
    response_model=BookingDB,
)
async def create_booking(
    booking_in: BookingCreate,
    user: User = Depends(get_current_active_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    """Создать бронирование."""
    return await service.create_booking(
        booking_in=booking_in,
        user=user,
    )


@router.get(
    '/{booking_id}',
    response_model=BookingDB,
)
async def get_booking(
    current_user: Annotated[User, Depends(get_current_active_user)],
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    """Получить бронирование."""
    return await service.get_booking(
        current_user=current_user,
        booking_id=booking_id
    )


@router.patch(
    '/{booking_id}',
    response_model=BookingDB,
)
async def update_booking(
    booking_in: BookingUpdate,
    booking_id: int,
    user: User = Depends(get_current_active_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    """Изменить бронирование."""
    return await service.update_booking(
        update_booking=booking_in,
        current_user=user,
        booking_id=booking_id
    )
