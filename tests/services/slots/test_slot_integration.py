from datetime import time
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.models.cafes import Cafe
from app.services.slot import SlotService


@pytest.fixture
async def cafe(db_session: AsyncSession) -> Cafe:
    """Создаёт тестовое кафе в БД."""
    cafe = Cafe(
        name=f'Test Cafe {uuid4()}',
        address='Test Address 1',
        phone='+79001234567',
    )
    db_session.add(cafe)
    await db_session.flush()
    return cafe


@pytest.fixture
def slot_service(db_session: AsyncSession) -> SlotService:
    """Создаёт экземпляр SlotService."""
    return SlotService(db_session)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_slot_integration(
    cafe: Cafe, slot_service: SlotService
) -> None:
    """Успешное создание слота в реальной БД."""
    slot = await slot_service.create_slot(
        cafe_id=cafe.id, start_time=time(9, 0), end_time=time(10, 0)
    )

    assert slot.cafe_id == cafe.id
    assert slot.start_time == time(9, 0)
    assert slot.end_time == time(10, 0)
    assert slot.active is True

    retrieved_slot = await slot_service.get_slot(slot.id)
    assert retrieved_slot is not None
    assert retrieved_slot.id == slot.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_slot_with_overlap_raises_error(
    cafe: Cafe, slot_service: SlotService
) -> None:
    """Ошибка при попытке создать пересекающийся слот."""
    await slot_service.create_slot(
        cafe_id=cafe.id, start_time=time(9, 0), end_time=time(10, 0)
    )

    with pytest.raises(ConflictException):
        await slot_service.create_slot(
            cafe_id=cafe.id, start_time=time(9, 30), end_time=time(10, 30)
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_cafe_slots_integration(
    cafe: Cafe, slot_service: SlotService
) -> None:
    """Получение всех слотов кафе."""
    await slot_service.create_slot(cafe.id, time(9, 0), time(10, 0))
    await slot_service.create_slot(cafe.id, time(11, 0), time(12, 0))

    slots = await slot_service.get_cafe_slots(cafe.id)

    assert len(slots) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_slot_integration(
    cafe: Cafe, slot_service: SlotService
) -> None:
    """Обновление времени слота."""
    slot = await slot_service.create_slot(cafe.id, time(9, 0), time(10, 0))

    updated = await slot_service.update_slot(
        slot.id, cafe.id, start_time=time(14, 0), end_time=time(15, 0)
    )

    assert updated.start_time == time(14, 0)
    assert updated.end_time == time(15, 0)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_slot_integration(
    cafe: Cafe, slot_service: SlotService
) -> None:
    """Деактивация слота."""
    slot = await slot_service.create_slot(cafe.id, time(9, 0), time(10, 0))

    result = await slot_service.delete_slot(slot.id, cafe.id)

    assert result is True

    retrieved = await slot_service.get_slot(slot.id)
    assert retrieved is not None
    assert retrieved.active is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_slot_with_overlap_raises_error(
    cafe: Cafe, slot_service: SlotService
) -> None:
    """Ошибка при обновлении слота с пересечением."""
    await slot_service.create_slot(cafe.id, time(9, 0), time(10, 0))
    slot2 = await slot_service.create_slot(cafe.id, time(11, 0), time(12, 0))

    with pytest.raises(ConflictException):
        await slot_service.update_slot(
            slot2.id, cafe.id, start_time=time(9, 30), end_time=time(10, 30)
        )
