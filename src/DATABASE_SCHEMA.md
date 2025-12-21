# DATABASE_SCHEMA.md

## Проект: «Бронирование мест в кафе»

### 📌 Полная ERD-схема (Entity Relationship Diagram)

Схема основана на:
- ТЗ разработчиков
- OpenAPI спецификации
- Требованиях к полям: id, created_at, updated_at, active
- Модульной архитектуре
- Асинхронном SQLAlchemy 2.0

---

## 1. Общая концепция базы данных

### Основные сущности (Entities)

| Сущность | Описание |
|----------|---------|
| **Users** | Пользователи сервиса (клиенты и менеджеры) |
| **Cafes** | Кафе/рестораны |
| **Tables** | Столики в кафе |
| **Slots** | Доступные временные интервалы для бронирования |
| **Booking** | Бронирования пользователей |
| **Dishes** | Блюда в меню (обязательно) |
| **Actions** | Акции и специальные предложения (обязательно) |
| **Media** | Изображения, привязанные к сущностям |

### Связующие таблицы (Many-to-Many)

- `cafe_managers` — менеджеры кафе (Users ↔ Cafes)
- `cafe_dishes` — меню кафе (Cafes ↔ Dishes)
- `cafe_actions` — акции кафе (Cafes ↔ Actions)
- `booking_dishes` — предзаказ блюд (Booking ↔ Dishes) *опционально*

---

## 2. Подробное описание моделей

### 🧑 Users (Пользователи)

**Назначение:** Хранит информацию о пользователях системы (клиентах и менеджерах).

```
id: int (PK)
username: str (unique)
email: str | None
phone: str | None
tg_id: str | None (для уведомлений в Telegram)
password_hash: str (bcrypt)
is_blocked: bool = False
is_superuser: bool = False
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True
```

**Связи:**
- 1 → Many: `booking.user_id` (пользователь может забронировать много мест)
- Many ↔ Many: `cafes` (менеджеры кафе через `cafe_managers`)

**Бизнес-правила:**
- username и email должны быть уникальными
- Пароль хранится в виде bcrypt хеша
- is_superuser = True для администраторов системы

---

### ☕ Cafes (Кафе)

**Назначение:** Информация о кафе/ресторанах.

```
id: int (PK)
name: str
address: str
phone: str
description: str | None
photo_id: uuid | None (FK → Media.id)
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True
```

**Связи:**
- 1 → Many: `tables` (столики в кафе)
- 1 → Many: `slots` (доступные слоты)
- 1 → Many: `booking` (бронирования)
- Many ↔ Many: `dishes` (меню через `cafe_dishes`)
- Many ↔ Many: `actions` (акции через `cafe_actions`)
- Many ↔ Many: `managers` (менеджеры через `cafe_managers`)
- 1 → 1: `media` (фотография кафе)

**Бизнес-правила:**
- name должен быть уникальным
- Удаление кафе (active = False) — логическое удаление
- При deactivate кафе все связанные бронирования становятся cancelled

---

### 🍽 Tables (Столики)

**Назначение:** Столики в кафе.

```
id: int (PK)
cafe_id: int (FK → Cafes.id)
seats: int (количество мест)
description: str | None (например, "VIP стол", "у окна")
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True

Уникальное ограничение: (cafe_id, id)
```

**Связи:**
- Many → 1: `cafe_id` (столик принадлежит кафе)
- 1 → Many: `booking` (столик забронирован много раз)

**Бизнес-правила:**
- Один столик может быть забронирован только на один слот в один день
- seats > 0
- Удаление столика — логическое (active = False)

---

### 🕒 Slots (Временные интервалы)

**Назначение:** Доступные времени бронирования в кафе.

```
id: int (PK)
cafe_id: int (FK → Cafes.id)
start_time: time (время начала, например 10:00)
end_time: time (время окончания, например 12:00)
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True

Уникальное ограничение: (cafe_id, start_time, end_time)
```

**Связи:**
- Many → 1: `cafe_id` (слот в кафе)
- 1 → Many: `booking.slot_id` (слот забронирован много раз)

**Бизнес-правила:**
- start_time < end_time
- Слоты не должны пересекаться в одном кафе
- Один слот может быть использован несколько раз в разные дни, но **только один раз в день за один столик**

---

### 📅 Booking (Бронирования)

**Назначение:** Информация о забронированных местах пользователями.

```
id: int (PK)
user_id: int (FK → Users.id)
cafe_id: int (FK → Cafes.id)
table_id: int (FK → Tables.id)
slot_id: int (FK → Slots.id)
date: date (дата бронирования)
status: str (enum: 'new', 'confirmed', 'cancelled', 'finished')
note: str | None (комментарий пользователя)
remind_at: datetime | None (когда отправить напоминание Celery)
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True

Уникальное ограничение: (cafe_id, table_id, slot_id, date)
```

**Связи:**
- Many → 1: `user_id` (пользователь)
- Many → 1: `cafe_id` (кафе)
- Many → 1: `table_id` (столик)
- Many → 1: `slot_id` (временной интервал)
- Many ↔ Many: `dishes` (блюда в заказе через `booking_dishes`) *опционально*

**Бизнес-правила:**
- Пользователь **не может** забронировать на прошедшую дату
- Пользователь **не может** иметь две активные брони на одно время в один день
- Бронь привязана к: кафе + дате + слоту + столику
- Только активный (active=True) столик и слот могут быть забронированы
- Статус может переходить: new → confirmed → finished или new/confirmed → cancelled
- Поле `remind_at` используется для Celery Beat для отправки напоминаний

---

### 🍲 Dishes (Блюда) — **обязательно**

**Назначение:** Меню блюд.

```
id: int (PK)
name: str
description: str
price: decimal (Numeric(10, 2))
photo_id: uuid | None (FK → Media.id)
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True
```

**Связи:**
- Many ↔ Many: `cafes` (меню через `cafe_dishes`)
- Many ↔ Many: `bookings` (блюда в брони через `booking_dishes`)
- 1 → 1: `media` (фото блюда)

**Бизнес-правила:**
- Блюдо может быть активным в одном кафе и неактивным в другом
- price >= 0

---

### 🎉 Actions (Акции) — **обязательно**

**Назначение:** Специальные предложения и скидки.

```
id: int (PK)
name: str
description: str
photo_id: uuid | None (FK → Media.id)
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True
```

**Связи:**
- Many ↔ Many: `cafes` (через `cafe_actions`)
- 1 → 1: `media` (фото акции)

**Бизнес-правила:**
- Акция привязана к определённым кафе
- Акция может быть активной/неактивной

---

### 🖼 Media (Изображения)

**Назначение:** Хранение информации о загруженных изображениях.

```
id: UUID4 (PK, default=uuid.uuid4)
file_path: str (путь к файлу: /app/media/{uuid}.jpg)
mime_type: str (например, image/jpeg)
file_size: int (размер в байтах)
created_at: datetime (server_default=func.now())
updated_at: datetime (onupdate=func.now())
active: bool = True
```

**Связи:**
- Используется в: Cafes.photo_id, Dishes.photo_id, Actions.photo_id

**Бизнес-правила:**
- Только JPG и PNG при загрузке (конвертируется в JPG)
- Размер ≤ 5MB
- Путь к файлу уникален
- Файлы хранятся в `/app/media/`

---

## 3. Мостовые таблицы (Many-to-Many)

### 👥 cafe_managers

**Назначение:** Связь между менеджерами (Users) и кафе.

```
id: int (PK)
cafe_id: int (FK → Cafes.id)
user_id: int (FK → Users.id)

Уникальное ограничение: (cafe_id, user_id)
```

**Использование:** Определение, кто может управлять кафе.

---

### 🍽 cafe_dishes

**Назначение:** Меню кафе.

```
id: int (PK)
cafe_id: int (FK → Cafes.id)
dish_id: int (FK → Dishes.id)

Уникальное ограничение: (cafe_id, dish_id)
```

**Использование:** Какие блюда доступны в каком кафе.

---

### 🎉 cafe_actions

**Назначение:** Акции в кафе.

```
id: int (PK)
cafe_id: int (FK → Cafes.id)
action_id: int (FK → Actions.id)

Уникальное ограничение: (cafe_id, action_id)
```

**Использование:** Какие акции действуют в каком кафе.

---

### 🍝 booking_dishes (опционально)

**Назначение:** Предзаказ блюд при бронировании.

```
id: int (PK)
booking_id: int (FK → Booking.id, ondelete=CASCADE)
dish_id: int (FK → Dishes.id)
quantity: int (количество)

Уникальное ограничение: (booking_id, dish_id)
```

**Использование:** Сохранение информации о том, какие блюда заказаны к бронировании.

**Бизнес-правила:**
- quantity > 0
- При удалении брони удаляются и записи о блюдах

---

## 4. Визуальная ERD-диаграмма (ASCII)

```
                                    ┌──────────────┐
                                    │    Users     │
                                    │              │
                                    │ id (PK)      │
                                    │ username     │
                                    │ password     │
                                    │ created_at   │
                                    │ updated_at   │
                                    │ active       │
                                    └──────┬───────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                        │                  │                  │
                   1:N  │             M:M  │                  │
                        │         cafe_    │                  │
                        ▼        managers  ▼                  ▼
                   ┌──────────┐    │    ┌──────────┐    ┌──────────────┐
                   │ Booking  │◄───┘    │  Cafes   │    │    Media     │
                   │          │         │          │    │ (изображения)│
                   │ id (PK)  │         │ id (PK)  │◄───┤ id (UUID)    │
                   │ user_id  │         │ name     │    │ file_path    │
                   │ cafe_id  │         │ address  │    │ mime_type    │
                   │ table_id │         │ photo_id │    │ created_at   │
                   │ slot_id  │         │ created_ │    │ updated_at   │
                   │ date     │         │   at     │    │ active       │
                   │ status   │         │ updated_ │    └──────────────┘
                   │ created_ │         │   at     │
                   │   at     │         │ active   │
                   │ updated_ │         └────┬─────┘
                   │   at     │              │
                   │ active   │         1:N  │
                   └────┬─────┘         ┌────┴─────┐
                        │              │           │
                    1:N │              ▼           ▼
                   ┌────┴──────┐   ┌────────┐  ┌───────┐
            ◄──────┤ Tables    │   │ Slots  │  │Dishes │
            │      │           │   │        │  │       │
        M:M │      │ id (PK)   │   │id (PK)│  │id(PK) │
booking_    │      │ cafe_id   │   │cafe_id│  │name   │
dishes      │      │ seats     │   │start_ │  │price  │
            │      │ created   │   │time   │  │photo_ │
            │      │ updated   │   │end_   │  │id     │
            │      │ active    │   │time   │  │created│
            │      └───────────┘   │active │  │updated│
            │                      └───────┘  │active │
            │                                 └───────┘
            └─────────────────────────────────────────┘


            Дополнительно:

            Cafes ◄─────────► Dishes    (через cafe_dishes)
            Cafes ◄─────────► Actions   (через cafe_actions)
```

---

## 5. Особенности при реализации SQLAlchemy 2.0

### ✅ Все модели должны наследоваться от Base

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### ✅ Используем только новый стиль (Mapped)

```python
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str | None]
```

### ✅ Обязательные поля в каждой модели

```python
from datetime import datetime
from sqlalchemy import func

class Base(DeclarativeBase):
    pass

# В каждой модели:
created_at: Mapped[datetime] = mapped_column(server_default=func.now())
updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
active: Mapped[bool] = mapped_column(default=True)
```

### ✅ UUID для Media таблицы

```python
import uuid
from uuid import UUID
from sqlalchemy import UUID as UUID_Type

class Media(Base):
    __tablename__ = "media"

    id: Mapped[UUID] = mapped_column(
        UUID_Type(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
```

### ✅ Связи между моделями

```python
from sqlalchemy.orm import Relationship

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")

class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="bookings")
```

### ✅ Many-to-Many связи

```python
from sqlalchemy.orm import Mapped, relationship

cafe_managers = Table(
    "cafe_managers",
    Base.metadata,
    Column("cafe_id", Integer, ForeignKey("cafes.id")),
    Column("user_id", Integer, ForeignKey("users.id")),
)

class Cafe(Base):
    __tablename__ = "cafes"

    managers: Mapped[List["User"]] = relationship(
        secondary=cafe_managers,
        back_populates="managed_cafes"
    )

class User(Base):
    __tablename__ = "users"

    managed_cafes: Mapped[List["Cafe"]] = relationship(
        secondary=cafe_managers,
        back_populates="managers"
    )
```

### ✅ Значения по умолчанию

```python
from datetime import datetime
from sqlalchemy import func, Boolean

class User(Base):
    __tablename__ = "users"

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
```

---

## 6. Индексы и оптимизация запросов

Рекомендуется добавить индексы на часто используемые поля:

```python
class Booking(Base):
    __tablename__ = "booking"

    # ... поля модели ...

    __table_args__ = (
        Index("ix_booking_user_id", "user_id"),
        Index("ix_booking_cafe_id", "cafe_id"),
        Index("ix_booking_date", "date"),
        Index("ix_booking_status", "status"),
        UniqueConstraint("cafe_id", "table_id", "slot_id", "date", name="uq_booking_slot"),
    )
```

---

## 7. Миграции (Alembic)

Каждый разработчик, когда модель готова:

```bash
# После добавления новой модели в models/
alembic revision --autogenerate -m "Add {Model} table"
alembic upgrade head
```

**Важно:** Не коммитить модели с конфликтующими структурами! Согласовывайте со своей командой.

---

## 8. Статусы бронирования (Enum)

```python
from enum import Enum

class BookingStatus(str, Enum):
    NEW = "new"              # Новая бронь
    CONFIRMED = "confirmed"  # Подтверждённая бронь
    CANCELLED = "cancelled"  # Отменённая бронь
    FINISHED = "finished"    # Завершённая бронь
```

**Переходы:**
- new → confirmed (менеджер подтверждает)
- new/confirmed → cancelled (пользователь/менеджер отменяет)
- confirmed → finished (автоматически после даты/времени)

---

## 9. Ограничения целостности данных

| Ограничение | Применение | Цель |
|------------|-----------|------|
| UNIQUE | username, email | Никакие два пользователя не могут иметь один username |
| UNIQUE | (cafe_id, table_id, slot_id, date) | Столик не может быть забронирован дважды на один слот в один день |
| UNIQUE | (cafe_id, start_time, end_time) | Слоты в кафе не дублируются |
| UNIQUE | file_path | Каждое изображение хранится один раз |
| FK | cafe_id в Tables, Slots | Удаление кафе cascades |
| CHECK | seats > 0 | Столик должен иметь хотя бы одно место |
| CHECK | start_time < end_time | Время начала раньше времени окончания |
| CHECK | price >= 0 | Цена не может быть отрицательной |

---

## 10. Рекомендации по распределению работы

| Модуль | Ответственный | Модели |
|--------|--------------|--------|
| Users/Auth | Александр | User, cafe_managers (M2M) |
| Cafes | Павел | Cafe, cafe_dishes (M2M), cafe_actions (M2M) |
| Tables | Павел | Table |
| Slots | Лев | Slot |
| Booking | Анастасия | Booking, booking_dishes (M2M) |
| Media | Лев / Данил | Media |
| DB Init | Данил | Base, init_db.py, миграции |

---

## 11. Порядок создания миграций

1. **Основные сущности** (без FK):
   - Users
   - Cafes
   - Tables
   - Slots
   - Dishes (опционально)
   - Actions (опционально)
   - Media

2. **Основные связи** (FK):
   - Booking (с FK на User, Cafe, Table, Slot)

3. **Связующие таблицы** (M2M):
   - cafe_managers
   - cafe_dishes
   - cafe_actions
   - booking_dishes (опционально)

**Каждый разработчик создаёт миграцию для своих моделей после их реализации!**
