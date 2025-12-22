from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import get_session
from src.app.api.v1.users.dependencies import (
    get_current_active_user
)
from src.app.models.models import User
from .schemas import BookingDB, BookingCreate, BookingUpdate
from .service import BookingService
from .dependencies import get_booking_service

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
    session: AsyncSession = Depends(get_session),
    service: BookingService = Depends(get_booking_service)
):
    """
    Для суперюзеров и менеджеров:
        - Получить все бронирование
        - сортировать по кафе
        - сортировать по пользователю
        - получить свои бронирования
    Для пользователей:
        - получить свои бронирования
    """
    return await service.get_all_bookings(
        current_user=current_user,
        session=session,
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
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_active_user),
    service: BookingService = Depends(get_booking_service)
):
    """Создать бронирование."""
    booking = await service.create_booking(
        booking_in=booking_in,
        session=session,
        user=user,
    )
    return booking


@router.get(
    '/{booking_id}',
    response_model=BookingDB,
)
async def get_booking(
    current_user: Annotated[User, Depends(get_current_active_user)],
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    service: BookingService = Depends(get_booking_service)
):
    """
    Для суперюзеров и менеджеров:
        - получить любое бронирование по id
    Для пользователей
        - получить свое бронирование по id
    """
    return await service.get_booking(
        current_user=current_user,
        booking_id=booking_id,
        session=session
    )


@router.patch(
    '/{booking_id}',
    response_model=BookingDB,
)
async def update_booking(
    booking_in: BookingUpdate,
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_active_user),
    service: BookingService = Depends(get_booking_service)
):
    """Изменить бронирование."""
    return await service.modify_booking(
        booking_update=booking_in,
        current_user=user,
        booking_id=booking_id,
        session=session
    )
