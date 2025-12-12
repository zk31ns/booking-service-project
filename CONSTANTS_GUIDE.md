# 📚 Руководство по использованию констант

Полное руководство по работе с глобальными константами в проекте `booking_seats_team_project`.

**Файл:** `src/app/core/constants.py` (в папке `src/app/core/`)

## Оглавление

1. [Обзор](#обзор)
2. [API константы](#api-константы)
3. [Лимиты и размеры](#лимиты-и-размеры)
4. [Времена и таймауты](#времена-и-таймауты)
5. [Перечисления (Enums)](#перечисления-enums)
6. [Сообщения](#сообщения)
7. [Валидация (Regex)](#валидация-regex)
8. [Celery задачи](#celery-задачи)
9. [Примеры использования](#примеры-использования)
10. [Миграция со старых имён](#миграция-со-старых-имён)

---

## Обзор

Константы организованы в **6 основных классов** для лучшей структурации и типизации:

| Класс | Назначение | Примеры |
|-------|-----------|---------|
| `API` | Версии API и таги для документации | `V1_PREFIX`, `HEALTH`, `USERS` |
| `Limits` | Размеры, длины, диапазоны | `MAX_USERNAME_LENGTH`, `MAX_UPLOAD_SIZE_MB` |
| `Times` | Временные константы | `ACCESS_TOKEN_MINUTES`, `BOOKING_REMINDER_MINUTES` |
| `Messages` | Ошибки и успешные сообщения | `errors`, `success_messages` |
| `CeleryTasks` | Пути к Celery задачам | `SEND_BOOKING_REMINDER`, `NOTIFY_MANAGER` |
| `Patterns` | Regex паттерны для валидации | `EMAIL`, `USERNAME`, `PHONE` |

**Enums:**
- `BookingStatus` - статусы броней
- `UserRole` - роли пользователей
- `ErrorCode` - коды ошибок
- `EventType` - типы событий

---

## API константы

### Использование в маршрутах

```python
from fastapi import APIRouter
from app.core.constants import API

# ✅ Правильно (новый способ)
router = APIRouter(prefix=API.V1_PREFIX, tags=API.USERS)

@router.get("/profile", tags=API.AUTH)
async def get_profile():
    """Получить профиль пользователя."""
    pass
```

### Все доступные значения

```python
from app.core.constants import API

API.V1_PREFIX         # "/api/v1"
API.HEALTH            # ["health"]
API.USERS             # ["users"]
API.AUTH              # ["auth"]
API.CAFES             # ["cafes"]
API.TABLES            # ["tables"]
API.SLOTS             # ["slots"]
API.BOOKING           # ["booking"]
API.MEDIA             # ["media"]
```

### Обратная совместимость (старый способ - скоро устаревает)

```python
# ⚠️ Используется, но не рекомендуется
from app.core.constants import API_V1_PREFIX, TAGS_USERS

router = APIRouter(prefix=API_V1_PREFIX, tags=TAGS_USERS)
```

---

## Лимиты и размеры

### Использование в Pydantic схемах

```python
from pydantic import BaseModel, Field
from app.core.constants import Limits

class UserCreate(BaseModel):
    username: str = Field(
        min_length=Limits.MIN_USERNAME_LENGTH,
        max_length=Limits.MAX_USERNAME_LENGTH,
        description=f"Username от {Limits.MIN_USERNAME_LENGTH} до {Limits.MAX_USERNAME_LENGTH} символов"
    )
    password: str = Field(
        min_length=Limits.MIN_PASSWORD_LENGTH,
        max_length=Limits.MAX_PASSWORD_LENGTH,
        description=f"Пароль от {Limits.MIN_PASSWORD_LENGTH} символов"
    )
    email: str

class CafeCreate(BaseModel):
    name: str = Field(
        min_length=Limits.MIN_CAFE_NAME_LENGTH,
        max_length=Limits.MAX_CAFE_NAME_LENGTH
    )
    description: str = Field(
        max_length=Limits.MAX_DESCRIPTION_LENGTH
    )
```

### Использование в валидации

```python
from app.core.constants import Limits

# Проверка размера файла
def validate_file_size(file_size: int) -> bool:
    return file_size <= Limits.MAX_UPLOAD_SIZE_BYTES

# Пример
if file_size > Limits.MAX_UPLOAD_SIZE_BYTES:
    raise ValueError(f"Максимальный размер: {Limits.MAX_UPLOAD_SIZE_MB}MB")
```

### Использование в пагинации

```python
from fastapi import Query
from app.core.constants import Limits

async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(Limits.DEFAULT_PAGE_SIZE, ge=1, le=Limits.MAX_PAGE_SIZE)
):
    """
    `size` может быть от 1 до {Limits.MAX_PAGE_SIZE}.
    По умолчанию: {Limits.DEFAULT_PAGE_SIZE}
    """
    skip = (page - 1) * size
    # ... выполнить запрос
```

### Все доступные значения

```python
from app.core.constants import Limits

# Загрузка файлов
Limits.MAX_UPLOAD_SIZE_MB          # 5
Limits.MAX_UPLOAD_SIZE_BYTES        # 5242880
Limits.ALLOWED_IMAGE_EXTENSIONS    # {".jpg", ".jpeg", ".png"}
Limits.ALLOWED_IMAGE_MIMETYPES     # {"image/jpeg", "image/png"}

# Пагинация
Limits.DEFAULT_PAGE_SIZE            # 10
Limits.MAX_PAGE_SIZE                # 100

# Username
Limits.MIN_USERNAME_LENGTH          # 3
Limits.MAX_USERNAME_LENGTH          # 50

# Password
Limits.MIN_PASSWORD_LENGTH          # 8
Limits.MAX_PASSWORD_LENGTH          # 255

# Cafe name
Limits.MIN_CAFE_NAME_LENGTH         # 3
Limits.MAX_CAFE_NAME_LENGTH         # 255

# Description
Limits.MIN_DESCRIPTION_LENGTH       # 0
Limits.MAX_DESCRIPTION_LENGTH       # 1000

# Phone
Limits.MIN_PHONE_LENGTH             # 10
Limits.MAX_PHONE_LENGTH             # 20

# Seats
Limits.MIN_SEATS                    # 1
Limits.MAX_SEATS                    # 100

# Prices
Limits.MIN_PRICE                    # 0.0
Limits.MAX_PRICE                    # 999999.99
```

---

## Времена и таймауты

### Использование в конфигурации

```python
from app.core.constants import Times

# JWT token expiry (из config.py)
ACCESS_TOKEN_EXPIRE_MINUTES = Times.ACCESS_TOKEN_MINUTES  # 60 минут

# Расчёт времени напоминания
from datetime import datetime, timedelta

booking_time = datetime.utcnow()
remind_at = booking_time + timedelta(minutes=Times.BOOKING_REMINDER_MINUTES)
```

### Использование в бизнес-логике

```python
from app.core.constants import Times
from datetime import datetime, timedelta

async def validate_booking_date(booking_date: datetime) -> bool:
    """Проверить, можно ли забронировать на эту дату."""
    now = datetime.utcnow()
    min_advance = now + timedelta(minutes=Times.MIN_BOOKING_ADVANCE_MINUTES)
    max_future = now + timedelta(days=Times.MAX_BOOKING_DAYS_AHEAD)
    
    return min_advance <= booking_date <= max_future
```

### Все доступные значения

```python
from app.core.constants import Times

# JWT токены
Times.ACCESS_TOKEN_MINUTES          # 60 (1 час)
Times.REFRESH_TOKEN_DAYS            # 7

# Бронирование
Times.BOOKING_REMINDER_MINUTES      # 60 (напомнить за 1 час)
Times.MIN_BOOKING_ADVANCE_MINUTES   # 30 (минимум за 30 минут)
Times.MAX_BOOKING_DAYS_AHEAD        # 90 (максимум на 90 дней)

# Celery
Times.CELERY_TASK_TIMEOUT           # 300 (5 минут)
```

---

## Перечисления (Enums)

### BookingStatus

```python
from app.core.constants import BookingStatus

class Booking(Base):
    status: str = Column(String, default=BookingStatus.NEW.value)

# Использование в коде
def update_booking_status(booking_id: int, new_status: BookingStatus):
    # Валидация: статус должен быть из enum
    if new_status not in BookingStatus:
        raise ValueError("Неверный статус")
    
    # Переход только из допустимых статусов
    allowed_transitions = {
        BookingStatus.NEW: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
        BookingStatus.CONFIRMED: [BookingStatus.CANCELLED, BookingStatus.FINISHED],
        BookingStatus.CANCELLED: [],
        BookingStatus.FINISHED: [],
    }
```

**Значения:**
- `NEW` - новая бронь
- `CONFIRMED` - подтверждённая бронь
- `CANCELLED` - отменённая бронь
- `FINISHED` - завершённая бронь

### UserRole

```python
from app.core.constants import UserRole

class User(Base):
    role: str = Column(String, default=UserRole.CUSTOMER.value)

# Проверка прав
def require_role(*allowed_roles: UserRole):
    def decorator(func):
        async def wrapper(current_user: User, *args, **kwargs):
            if UserRole(current_user.role) not in allowed_roles:
                raise HTTPException(status_code=403)
            return await func(current_user, *args, **kwargs)
        return wrapper
    return decorator

@require_role(UserRole.MANAGER, UserRole.ADMIN)
async def update_cafe(cafe_id: int, ...):
    """Только менеджер или администратор."""
    pass
```

**Значения:**
- `CUSTOMER` - клиент
- `MANAGER` - менеджер кафе
- `ADMIN` - администратор

### ErrorCode

```python
from app.core.constants import ErrorCode
from fastapi import HTTPException

async def get_user(user_id: int) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": ErrorCode.USER_NOT_FOUND.value,
                "message": Messages.error(ErrorCode.USER_NOT_FOUND)
            }
        )
    return user
```

**Основные коды:**
- Auth: `INVALID_CREDENTIALS`, `TOKEN_EXPIRED`, `INVALID_TOKEN`, `USER_NOT_FOUND`
- Cafe: `CAFE_NOT_FOUND`, `CAFE_INACTIVE`
- Table: `TABLE_NOT_FOUND`, `TABLE_INACTIVE`
- Booking: `BOOKING_NOT_FOUND`, `TABLE_ALREADY_BOOKED`
- Media: `FILE_TOO_LARGE`, `INVALID_FILE_TYPE`

### EventType

```python
from app.core.constants import EventType
from app.services.event_service import log_event

async def register_user(user: UserCreate) -> User:
    # ... создание пользователя
    
    # Логировать событие
    await log_event(
        event_type=EventType.USER_REGISTERED.value,
        user_id=user.id,
        details={"username": user.username}
    )
```

---

## Сообщения

### Использование класса Messages

```python
from app.core.constants import Messages, ErrorCode, BookingStatus

# Получить сообщение об ошибке
error_msg = Messages.error(ErrorCode.USER_NOT_FOUND)
# "Пользователь не найден"

# Получить успешное сообщение
success_msg = Messages.success("user_created")
# "Пользователь успешно создан"
```

### В API ответах

```python
from fastapi import HTTPException
from app.core.constants import ErrorCode, Messages

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.USER_NOT_FOUND.value,
                "message": Messages.error(ErrorCode.USER_NOT_FOUND),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return {
        "data": user,
        "message": Messages.success("user_retrieved")
    }
```

### Все доступные сообщения об ошибках

```python
from app.core.constants import Messages

Messages.errors[ErrorCode.INVALID_CREDENTIALS]
Messages.errors[ErrorCode.TOKEN_EXPIRED]
Messages.errors[ErrorCode.USER_NOT_FOUND]
Messages.errors[ErrorCode.USER_ALREADY_EXISTS]
Messages.errors[ErrorCode.CAFE_NOT_FOUND]
Messages.errors[ErrorCode.TABLE_ALREADY_BOOKED]
Messages.errors[ErrorCode.FILE_TOO_LARGE]
# ... и 20+ других
```

---

## Валидация (Regex)

### Использование в Pydantic

```python
from pydantic import BaseModel, Field, field_validator
from app.core.constants import Patterns, Limits

class UserCreate(BaseModel):
    username: str = Field(
        min_length=Limits.MIN_USERNAME_LENGTH,
        max_length=Limits.MAX_USERNAME_LENGTH
    )
    email: str
    phone: str = Field(min_length=Limits.MIN_PHONE_LENGTH)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not Patterns.USERNAME.match(v):
            raise ValueError("Username должен содержать буквы, цифры, подчеркивание и дефис")
        return v
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not Patterns.EMAIL.match(v):
            raise ValueError("Неверный формат email")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not Patterns.PHONE.match(v):
            raise ValueError("Телефон должен быть в формате +7 999 999 9999")
        return v
```

### Использование в сервисах

```python
from app.core.constants import Patterns

def is_valid_email(email: str) -> bool:
    return bool(Patterns.EMAIL.match(email))

def is_valid_username(username: str) -> bool:
    return bool(Patterns.USERNAME.match(username))

def is_valid_phone(phone: str) -> bool:
    return bool(Patterns.PHONE.match(phone))

# Примеры телефонов, которые проходят валидацию:
# +7 999 999 9999
# +7(999)999-9999
# +79999999999
# 79999999999
```

### Все доступные паттерны

```python
from app.core.constants import Patterns

Patterns.EMAIL      # Email валидация
Patterns.USERNAME   # Username: буквы, цифры, _, - (3-50 символов)
Patterns.PHONE      # Телефон: +7 и цифры, скобки, дефисы
```

---

## Celery задачи

### Использование в сервисах

```python
from celery import Celery
from app.core.constants import CeleryTasks
from app.core.config import settings

celery_app = Celery(__name__, broker=settings.CELERY_BROKER_URL)

# Регистрация задач
@celery_app.task(name=CeleryTasks.SEND_BOOKING_REMINDER)
def send_booking_reminder(booking_id: int):
    """Отправить напоминание о бронировании."""
    pass

@celery_app.task(name=CeleryTasks.NOTIFY_MANAGER)
def notify_manager(cafe_id: int, message: str):
    """Уведомить менеджера кафе."""
    pass
```

### Запуск задач из сервисов

```python
from app.core.constants import CeleryTasks, Times
from app.core.celery import celery_app

async def create_booking(booking: BookingCreate) -> Booking:
    booking_obj = await booking_repository.create(booking)
    
    # Запланировать напоминание за 1 час до времени
    celery_app.send_task(
        CeleryTasks.SEND_BOOKING_REMINDER,
        args=[booking_obj.id],
        countdown=Times.BOOKING_REMINDER_MINUTES * 60  # в секунды
    )
    
    return booking_obj
```

### Все доступные задачи

```python
from app.core.constants import CeleryTasks

CeleryTasks.SEND_BOOKING_REMINDER           # Отправить напоминание
CeleryTasks.NOTIFY_MANAGER                  # Уведомить менеджера
CeleryTasks.SEND_CANCELLATION_NOTIFICATION  # Уведомить об отмене
CeleryTasks.CLEANUP_EXPIRED_BOOKINGS        # Очистить устаревшие брони
```

---

## Примеры использования

### Полный пример: создание пользователя

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from app.core.constants import (
    API, Limits, Patterns, Messages, ErrorCode, EventType
)

router = APIRouter(prefix=API.V1_PREFIX, tags=API.USERS)

class UserCreate(BaseModel):
    username: str = Field(
        min_length=Limits.MIN_USERNAME_LENGTH,
        max_length=Limits.MAX_USERNAME_LENGTH,
        description="Имя пользователя"
    )
    email: str = Field(description="Email адрес")
    phone: str = Field(
        min_length=Limits.MIN_PHONE_LENGTH,
        max_length=Limits.MAX_PHONE_LENGTH,
        description="Номер телефона"
    )
    password: str = Field(
        min_length=Limits.MIN_PASSWORD_LENGTH,
        max_length=Limits.MAX_PASSWORD_LENGTH,
        description="Пароль"
    )
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not Patterns.USERNAME.match(v):
            raise ValueError("Неверный формат username")
        return v
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not Patterns.EMAIL.match(v):
            raise ValueError("Неверный email")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not Patterns.PHONE.match(v):
            raise ValueError("Телефон должен быть в формате +7 999 999 9999")
        return v

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    # Проверить существование пользователя
    existing_user = await user_repository.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": ErrorCode.USER_ALREADY_EXISTS.value,
                "message": Messages.error(ErrorCode.USER_ALREADY_EXISTS)
            }
        )
    
    # Создать пользователя
    user = await user_service.create_user(user_data)
    
    # Логировать событие
    await event_service.log_event(
        event_type=EventType.USER_REGISTERED.value,
        user_id=user.id,
        details={"username": user.username}
    )
    
    return {
        "data": user,
        "message": Messages.success("user_created")
    }
```

### Пример: валидация броней

```python
from datetime import datetime
from app.core.constants import Times, BookingStatus, Messages, ErrorCode
from fastapi import HTTPException, status

async def create_booking(booking_data: BookingCreate, current_user: User):
    # Проверить, что бронь на будущее
    now = datetime.utcnow()
    min_advance = now + timedelta(minutes=Times.MIN_BOOKING_ADVANCE_MINUTES)
    
    if booking_data.booking_date < min_advance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.BOOKING_PAST_DATE.value,
                "message": Messages.error(ErrorCode.BOOKING_PAST_DATE)
            }
        )
    
    # Проверить, не забронирована ли уже таблица
    existing = await booking_repository.get_by_table_date(
        table_id=booking_data.table_id,
        booking_date=booking_data.booking_date
    )
    if existing and existing.status != BookingStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": ErrorCode.TABLE_ALREADY_BOOKED.value,
                "message": Messages.error(ErrorCode.TABLE_ALREADY_BOOKED)
            }
        )
    
    # Создать бронь
    booking = await booking_service.create_booking(booking_data, current_user)
    
    return {
        "data": booking,
        "message": Messages.success("booking_created")
    }
```

---

## Миграция со старых имён

### Постепенный переход

На данный момент **обе системы имён работают**:

```python
# ❌ Старый способ (скоро устаревает)
from app.core.constants import API_V1_PREFIX, TAGS_USERS, MAX_USERNAME_LENGTH

# ✅ Новый способ (рекомендуется)
from app.core.constants import API, Limits

API.V1_PREFIX              # "/api/v1"
Limits.MAX_USERNAME_LENGTH # 50
```

### Чек-лист миграции

При написании **нового кода**:

- [ ] Используете `API` вместо отдельных `API_V1_PREFIX` и `TAGS_*`
- [ ] Используете `Limits` вместо отдельных `MIN_*/MAX_*`
- [ ] Используете `Times` вместо отдельных временных констант
- [ ] Используете `Patterns` для валидации вместо отдельных regex
- [ ] Используете `Messages` для получения сообщений об ошибках
- [ ] Используете `CeleryTasks` для имён задач

### Окончательное удаление (в будущем)

Когда все файлы будут обновлены, можно удалить раздел "Обратная совместимость" из `constants.py`:

```python
# Удалить эти строки (когда все файлы мигрированы):
API_V1_PREFIX = API.V1_PREFIX
TAGS_HEALTH = API.HEALTH
# ... и все остальные alias'ы
```

---

## ❓ FAQ

**Q: Как выбрать между новым и старым способом?**
A: Используйте **новый способ** во всём новом коде. Старый способ сохраняется для обратной совместимости и будет удалён в будущем.

**Q: Где найти все доступные коды ошибок?**
A: В классе `ErrorCode` в `constants.py`. Все коды синхронизированы с `Messages.errors`.

**Q: Как добавить новую константу?**
A: Добавьте в соответствующий класс (`API`, `Limits`, `Times` и т.д.) и обновите `__all__`.

**Q: Почему классы вместо модуля с переменными?**
A: Классы обеспечивают лучшую организацию, типизацию и IDE autocomplete.

**Q: Что делать, если нужна новая роль пользователя?**
A: Добавьте значение в `UserRole` enum и обновите документацию.

---

## 📞 Контакты

Вопросы по константам? Обратитесь к Данилу Мордовину (Team Lead) в TG.

Последнее обновление: **11 декабря 2025**
