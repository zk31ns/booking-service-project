# tests/services/slots/test_slot_service.py
"""Unit-тесты для SlotService."""
from datetime import time
from typing import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.app.api.v1.slots.service import SlotService
from src.app.core.exceptions import ConflictException, ValidationException


class TestSlotsOverlap:
    """Тесты проверки пересечения временных интервалов."""

    @pytest.mark.unit
    def test_slots_overlap_true(self) -> None:
        """Интервалы пересекаются: 9:00-10:00 и 9:30-10:30."""
        service = SlotService(session=None)

        result = service._slots_overlap(
            time(9, 0), time(10, 0),
            time(9, 30), time(10, 30)
        )

        assert result is True

    @pytest.mark.unit
    def test_slots_no_overlap_after(self) -> None:
        """Интервалы НЕ пересекаются: 9:00-10:00 и 10:00-11:00."""
        service = SlotService(session=None)

        result = service._slots_overlap(
            time(9, 0), time(10, 0),
            time(10, 0), time(11, 0)
        )

        assert result is False

    @pytest.mark.unit
    def test_slots_no_overlap_before(self) -> None:
        """Интервалы НЕ пересекаются: 10:00-11:00 и 9:00-10:00."""
        service = SlotService(session=None)

        result = service._slots_overlap(
            time(10, 0), time(11, 0),
            time(9, 0), time(10, 0)
        )

        assert result is False

    @pytest.mark.unit
    def test_slots_overlap_contained(self) -> None:
        """Один интервал внутри другого: 8:00-12:00 и 9:00-10:00."""
        service = SlotService(session=None)

        result = service._slots_overlap(
            time(8, 0), time(12, 0),
            time(9, 0), time(10, 0)
        )

        assert result is True


class TestCreateSlot:
    """Тесты создания слота."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_slot_invalid_time_range(self) -> None:
        """Ошибка если start_time >= end_time."""
        session = AsyncMock()
        service = SlotService(session)

        service._validate_cafe_exists = AsyncMock()

        with pytest.raises(ValidationException) as exc:
            await service.create_slot(
                cafe_id=1,
                start_time=time(10, 0),
                end_time=time(9, 0)
            )
        service._validate_cafe_exists.assert_called_once_with(1)

        assert 'Время начала должно быть раньше' in str(exc.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_slot_equal_times(self) -> None:
        """Ошибка если start_time == end_time."""
        session = AsyncMock()
        service = SlotService(session)

        service._validate_cafe_exists = AsyncMock()

        with pytest.raises(ValidationException):
            await service.create_slot(
                cafe_id=1,
                start_time=time(10, 0),
                end_time=time(10, 0)
            )


class TestGetSlot:
    """Тесты получения слота."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_slot_success(
            self,
            mock_slot_factory: Callable[..., MagicMock]
    ) -> None:
        """Успешное получение слота по ID."""
        service = SlotService(session=None)
        mock_slot = mock_slot_factory(id_=1, cafe_id=1)

        service.repo.get_by_id = AsyncMock(return_value=mock_slot)

        result = await service.get_slot(1)

        assert result.id == 1
        assert result.cafe_id == 1
        service.repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_slot_not_found(self) -> None:
        """Слот не найден - возвращает None."""
        session = AsyncMock()
        service = SlotService(session)

        service.repo = AsyncMock()
        service.repo.get_by_id = AsyncMock(return_value=None)

        result = await service.get_slot(999)
        assert result is None


class TestDeleteSlot:
    """Тесты удаления слота."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_slot_success(
            self,
            mock_slot_factory: Callable[..., MagicMock]
    ) -> None:
        """Успешное удаление (деактивация) слота."""
        session = AsyncMock()
        service = SlotService(session)
        service.repo = AsyncMock()

        mock_slot = mock_slot_factory(id_=1, cafe_id=1, active=True)
        service.repo.get_by_id = AsyncMock(return_value=mock_slot)

        result = await service.delete_slot(slot_id=1, cafe_id=1)

        assert result is True
        assert mock_slot.active is False
        service.repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_slot_not_found(self) -> None:
        """Слот не найден - возвращает False."""
        session = AsyncMock()
        service = SlotService(session)

        service.repo = AsyncMock()
        service.repo.get_by_id = AsyncMock(return_value=None)

        result = await service.delete_slot(slot_id=999, cafe_id=1)
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_slot_wrong_cafe(
            self,
            mock_slot_factory: Callable[..., MagicMock]
    ) -> None:
        """Слот принадлежит другому кафе - возвращает False."""
        service = SlotService(session=None)
        mock_slot = mock_slot_factory(id_=1, cafe_id=999)

        service.repo.get_by_id = AsyncMock(return_value=mock_slot)

        result = await service.delete_slot(slot_id=1, cafe_id=1)
        assert result is False


class TestValidateSlotOverlap:
    """Тесты проверки пересечения с существующими слотами."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_no_overlap(self) -> None:
        """Нет пересечений - валидация проходит."""
        service = SlotService(session=None)

        existing_slot = MagicMock()
        existing_slot.id = 1
        existing_slot.start_time = time(9, 0)
        existing_slot.end_time = time(10, 0)

        service.repo.get_all_by_cafe = AsyncMock(return_value=[existing_slot])

        await service._validate_slot_overlap(
            cafe_id=1,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_overlap_raises_exception(self) -> None:
        """Есть пересечение - выбрасывается ConflictException."""
        session = AsyncMock()
        service = SlotService(session)

        existing_slot = MagicMock()
        existing_slot.id = 1
        existing_slot.start_time = time(9, 0)
        existing_slot.end_time = time(11, 0)

        service.repo.get_all_by_cafe = AsyncMock(return_value=[existing_slot])

        with pytest.raises(ConflictException) as exc:
            await service._validate_slot_overlap(
                cafe_id=1,
                start_time=time(10, 0),
                end_time=time(12, 0)
            )

        assert 'пересекается' in str(exc.value.detail).lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_overlap_exclude_slot(self) -> None:
        """Исключение слота из проверки работает корректно."""
        service = SlotService(session=None)

        existing_slot = MagicMock()
        existing_slot.id = 5
        existing_slot.start_time = time(9, 0)
        existing_slot.end_time = time(11, 0)

        service.repo.get_all_by_cafe = AsyncMock(return_value=[existing_slot])

        await service._validate_slot_overlap(
            cafe_id=1,
            start_time=time(9, 0),
            end_time=time(11, 0),
            exclude_slot_id=5
        )


class TestUpdateSlot:
    """Тесты обновления слота."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_slot_time_success(
            self,
            mock_slot_factory: Callable[..., MagicMock]
    ) -> None:
        """Успешное обновление времени слота."""
        session = AsyncMock()
        service = SlotService(session)
        service.repo = AsyncMock()

        mock_slot = mock_slot_factory(
            id_=1, cafe_id=1, start=time(9, 0),
            end=time(10, 0), active=True
        )
        service.repo.get_by_id = AsyncMock(return_value=mock_slot)
        service._validate_slot_overlap = AsyncMock()

        result = await service.update_slot(
            slot_id=1,
            cafe_id=1,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )

        assert result is not None
        assert mock_slot.start_time == time(10, 0)
        assert mock_slot.end_time == time(11, 0)
        service._validate_slot_overlap.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_slot_invalid_time(
            self,
            mock_slot_factory: Callable[..., MagicMock]
    ) -> None:
        """Ошибка при обновлении с неправильным временем."""
        service = SlotService(session=None)
        mock_slot = mock_slot_factory(
            id_=1, cafe_id=1, start=time(9, 0), end=time(10, 0)
        )

        service.repo.get_by_id = AsyncMock(return_value=mock_slot)

        with pytest.raises(ValidationException):
            await service.update_slot(
                slot_id=1,
                cafe_id=1,
                start_time=time(11, 0),
                end_time=time(10, 0)
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_slot_wrong_cafe(self) -> None:
        """Ошибка при обновлении слота другого кафе."""
        session = AsyncMock()
        service = SlotService(session)

        mock_slot = MagicMock()
        mock_slot.id = 1
        mock_slot.cafe_id = 999

        service.repo.get_by_id = AsyncMock(return_value=mock_slot)

        result = await service.update_slot(
            slot_id=1,
            cafe_id=1,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )

        assert result is None  # Должен вернуть None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_slot_not_found(self) -> None:
        """Ошибка при обновлении несуществующего слота."""
        session = AsyncMock()
        service = SlotService(session)

        service.repo.get_by_id = AsyncMock(return_value=None)

        result = await service.update_slot(
            slot_id=999,
            cafe_id=1,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_slot_active_status(
            self,
            mock_slot_factory: Callable[..., MagicMock]
    ) -> None:
        """Обновление статуса активности слота."""
        session = AsyncMock()
        service = SlotService(session)
        service.repo = AsyncMock()

        mock_slot = mock_slot_factory(id_=1, cafe_id=1, active=True)
        service.repo.get_by_id = AsyncMock(return_value=mock_slot)

        result = await service.update_slot(
            slot_id=1,
            cafe_id=1,
            active=False
        )

        assert result is not None
        assert mock_slot.active is False


class TestGetCafeSlots:
    """Тесты получения списка слотов кафе."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_cafe_slots_only_active(self) -> None:
        """Получение только активных слотов."""
        session = AsyncMock()
        service = SlotService(session)

        mock_slots = [MagicMock(id=1), MagicMock(id=2)]
        service.repo.get_all_by_cafe = AsyncMock(return_value=mock_slots)

        result = await service.get_cafe_slots(cafe_id=1, show_inactive=False)

        assert len(result) == 2
        service.repo.get_all_by_cafe.assert_called_once_with(1, False)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_cafe_slots_with_inactive(self) -> None:
        """Получение всех слотов включая неактивные."""
        session = AsyncMock()
        service = SlotService(session)

        mock_slots = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]
        service.repo.get_all_by_cafe = AsyncMock(return_value=mock_slots)

        result = await service.get_cafe_slots(cafe_id=1, show_inactive=True)

        assert len(result) == 3
        service.repo.get_all_by_cafe.assert_called_once_with(1, True)
