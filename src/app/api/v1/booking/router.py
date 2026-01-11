from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_booking_service, get_current_user
from app.core.constants import API
from app.models import Booking, User
from app.schemas import BookingCreate, BookingDB, BookingUpdate
from app.services.booking import BookingService

router = APIRouter(prefix='/booking', tags=API.BOOKING)


@router.get(
    '/',
    response_model=list[BookingDB],
)
async def get_all_bookings(
    current_user: Annotated[User, Depends(get_current_user)],
    show_all: bool = True,
    cafe_id: int | None = None,
    user_id: int | None = None,
    service: BookingService = Depends(get_booking_service),
) -> list[Booking]:
    """Получить список доступных бронирований.

    В зависимости от прав пользователя возвращает:
    - Для суперюзеров и менеджеров: все бронирования с фильтрацией
    - Для обычных пользователей: только свои бронирования

    Args:
        current_user: Текущий аутентифицированный пользователь
        show_all: Показывать все бронирования или только свои
        cafe_id: ID кафе для фильтрации
        user_id: ID пользователя для фильтрации
        service: Сервис для работы с бронированиями

    Returns:
        Список бронирований

    """
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
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    """Создать новое бронирование.

    Args:
        booking_in: Данные для создания бронирования
        user: Текущий аутентифицированный пользователь
        service: Сервис для работы с бронированиями

    Returns:
        Созданное бронирование

    Raises:
        HTTPException: Если данные невалидны или недостаточно прав

    """
    return await service.create_booking(
        booking_in=booking_in,
        user=user,
    )


@router.get(
    '/{booking_id}',
    response_model=BookingDB,
)
async def get_booking(
    current_user: Annotated[User, Depends(get_current_user)],
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    """Получить бронирование по ID.

    Args:
        current_user: Текущий аутентифицированный пользователь
        booking_id: ID запрашиваемого бронирования
        service: Сервис для работы с бронированиями

    Returns:
        Найденное бронирование

    Raises:
        HTTPException: Если бронирование не найдено или недостаточно прав

    """
    return await service.get_booking(
        current_user=current_user, booking_id=booking_id
    )


@router.patch(
    '/{booking_id}',
    response_model=BookingDB,
)
async def update_booking(
    booking_in: BookingUpdate,
    booking_id: int,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    """Обновить существующее бронирование.

    Поддерживает частичное обновление полей бронирования.

    Args:
        booking_in: Данные для обновления бронирования
        booking_id: ID обновляемого бронирования
        user: Текущий аутентифицированный пользователь
        service: Сервис для работы с бронированиями

    Returns:
        Обновленное бронирование

    Raises:
        HTTPException: Если бронирование не найдено, недостаточно прав
                     или данные невалидны

    """
    return await service.update_booking(
        update_booking=booking_in, current_user=user, booking_id=booking_id
    )
