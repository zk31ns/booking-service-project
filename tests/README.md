# Tests

Тестирование API Booking Seats.

## Структура

```
tests/
├── api/              # API endpoint tests
├── services/         # Business logic tests
├── repositories/     # Database tests
├── utils/            # Utility function tests
├── conftest.py       # Pytest fixtures and configuration
└── __init__.py
```

## Запуск тестов

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/api/test_health.py

# Run tests with markers
pytest -m unit
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

## Требования

Для запуска тестов нужны дополнительные зависимости:

```bash
pip install pytest pytest-asyncio httpx aiosqlite
```

## Написание тестов

### Unit тесты

```python
@pytest.mark.unit
def test_function():
    assert True
```

### Async тесты

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### API тесты

```python
def test_endpoint(client: TestClient):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
```

## Notes

- Тесты используют in-memory SQLite для изоляции
- Fixtures определены в `conftest.py`
- Используется `pytest-asyncio` для async/await поддержки
- Pre-commit автоматически проверяет тесты перед commit
