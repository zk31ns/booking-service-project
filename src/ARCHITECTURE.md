# ARCHITECTURE.md

## Проект: «Бронирование мест в кафе»

**Версия Python:** 3.11.9
**Рабочая ветка:** develop

---

## 1. Цели архитектуры

Архитектура проекта разработана с учётом:

- Полностью асинхронного стека
- Модульности — возможность параллельной работы всей команды из 6 разработчиков.
- Простоты расширения функционала
- Разделения ответственности (слои: API → Service → Repository → DB)
- Чистоты кода (ruff + pre-commit)
- Требований учебного проекта

---

## 2. Основная структура проекта

Проект располагается в директории `/src`.

```
src/
│   main.py
│   requirements.txt            (Dependencies for Docker and local dev)
│   ARCHITECTURE.md
│   alembic.ini                (Alembic configuration)
│
├───app/
│   ├───api/
│   │   └───v1/
│   │        ├───users/
│   │        │       router.py
│   │        │       schemas.py
│   │        │       service.py
│   │        │       repository.py
│   │        │       models.py
│   │        │
│   │        ├───cafes/
│   │        ├───tables/
│   │        ├───slots/
│   │        ├───booking/
│   │        ├───dishes/      (опционально)
│   │        ├───actions/     (опционально)
│   │        └───media/
│   │
│   ├───core/
│   │       config.py          (pydantic-settings)
│   │       security.py        (JWT, хеширование)
│   │       logging.py         (loguru)
│   │       celery_app.py      (Celery init)
│   │       celery_tasks.py    (планы задач)
│   │       exceptions.py
│   │       dependencies.py
│   │
│   ├───db/
│   │       base.py            (Declarative Base)
│   │       session.py         (async engine + sessionmaker)
│   │       init_db.py
│   │
│   ├───models/                (общие модели при необходимости)
│   ├───schemas/               (общие схемы)
│   ├───services/              (логика без привязки к FastAPI)
│   ├───utils/                 (uuid, validators, file utils)
│   └───media/                 (папка хранения изображений)
│
├───alembic/                   (Database migrations)
│       env.py                 (Alembic runtime configuration)
│       script.py.mako         (Migration script template)
│       versions/              (Migration files - auto-generated)
│       README                 (Alembic documentation)
```

**Проект также содержит:**

```
/                              (Project Root)
├── tests/                      (Unit & integration tests)
│   ├── api/                   (API endpoint tests)
│   ├── services/              (Business logic tests)
│   ├── repositories/          (Database tests)
│   ├── utils/                 (Utility function tests)
│   ├── conftest.py           (Pytest fixtures)
│   └── README.md             (Testing guide)
├── infra/                      (Infrastructure)
│   ├── docker-compose.yml
│   └── .env.example
├── pytest.ini                  (Pytest configuration)
├── ARCHITECTURE.md             (This file)
├── DATABASE_SCHEMA.md
├── CONSTANTS_GUIDE.md
├── TEAM_MEMBERS.md
├── ISSUES_CHECKLIST.md
└── README.md
```

---

## 3. Принципы проектирования

### 3.1. Полная модульность

Каждый модуль — независим и изолирован.

Каждый модуль содержит:

- `router.py`
- `schemas.py`
- `models.py`
- `repository.py`
- `service.py`

**Примерная ответственность:**

- `router.py` – обработка HTTP-запросов
- `schemas.py` – pydantic-модели запросов/ответов
- `models.py` – ORM-модели SQLAlchemy 2.0
- `repository.py` – запросы к БД (CRUD)
- `service.py` – бизнес-правила (логика)

### 3.2. Разделение слоёв
API не содержит бизнес-логики.
Сервисы не содержат SQL.
Repository не содержит ни API, ни хендлеров.

### 3.3. Асинхронность
Все запросы к базе выполняются через async SQLAlchemy 2.0:

async_sessionmaker(engine, expire_on_commit=False)

### 3.4. Безопасность

**Аутентификация и авторизация:**
- JWT токены для аутентификации пользователей
- Срок действия токена: 1 час (access), 7 дней (refresh)
- Хеширование паролей: bcrypt (passlib)
- Проверка прав доступа на уровне роутера (Depends)

**Валидация:**
- Pydantic 2.0 для валидации всех входных данных
- Проверка размера загружаемых файлов (max 5МБ)
- Проверка типов файлов (только JPG/PNG)
- SQL injection защита через SQLAlchemy ORM

**CORS:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 4. Database Architecture

**Реляционная БД:** PostgreSQL

**Общие поля (по требованию ТЗ):**

- `id` (int или UUID4)
- `created_at` — datetime (server_default func.now)
- `updated_at` — datetime (onupdate)
- `active` — bool

**Асинхронный движок:**

```python
engine = create_async_engine(settings.db_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)
```

Alembic используется для миграций.
---

## 5. Celery + RabbitMQ

**Стек фоновых задач:**

- Celery worker (выполнение задач)
- Celery beat (периодические задачи (опционально))
- RabbitMQ (брокер)
- Flower (мониторинг)

**Пример инициализации:**

```python
from celery import Celery

celery_app = Celery(
    "booking",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["app.core.celery_tasks"])
```

**Примеры задач:**

- `send_booking_reminder` — напоминание пользователю за 1 час до времени бронирования
- `notify_manager` — уведомление менеджеру о новом бронировании
- `send_cancellation_notification` — уведомление об отмене бронирования
- `cleanup_expired_bookings` — периодическое удаление истёкших бронирований (celery beat)

---

## 6. Logging (loguru)

**Логи пишутся:**

- в консоль
- в файл с ротацией

**Логируются:**
- запросы;
- ошибки;
- действия пользователей;
- события системы.

**Формат содержимого лога:**

- timestamp
- уровень
- user/id (если есть, если нет SYSTEM)
- действие (описание)

**Пример конфигурации:**

```python
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)
```

---

## 7. Работа с изображениями

**ТЗ:**

- загрузка только JPG и PNG
- при загрузке — конвертация в JPG
- размер не более 5МБ
- UUID4 как идентификатор изображения;
- хранение в директории `/app/media/`

**В БД хранится:**

- uuid
- путь к файлу
- mime-type
- размер
- created_at


**Выдача изображений**

— бинарный JPG.

---

## 8. Требуемые технологии (обязательные)

| Технология | Статус | Использование |
|-----------|--------|---------------|
| Python 3.11.9 | Обязательно | основа проекта |
| FastAPI | Обязательно | API |
| SQLAlchemy 2.0 async | Обязательно | ORM |
| Pydantic 2.0 | Обязательно | схемы |
| Pydantic-settings | Обязательно | конфигурация |
| Docker | Обязательно | запуск сервисов |
| RabbitMQ | Обязательно | очереди задач |
| Celery | Обязательно | уведомления/напоминания |
| Redis | Опционально | кеширование меню/акций |
| Loguru | Обязательно | логирование |
| Ruff | Обязательно | стиль + форматирование |
| Pre-commit | Рекомендуется | автоматизация стиля |
| Alembic | Обязательно | миграции |
| Git-flow | Обязательно | процесс разработки |
| Python-multipart | Обязательно | загрузка файлов |
| PyJWT / python-jose | Обязательно | JWT токены |
| Passlib + bcrypt | Обязательно | хеширование паролей |
| Pillow | Обязательно | обработка и конвертация изображений |
| Pytest | Опционально | модульное тестирование |
| pytest-asyncio | Опционально | тестирование async кода |

---

## 9. Git-flow (требование курса + лучший практический опыт)

### 9.1. Основные ветки

- `main` — только финальный стабильный код
- `develop` — основная рабочая ветка

### 9.2. Ветки разработчиков

- `feature/<описание>`
- `fix/<описание>`

**Примеры имён:**

- `feature/27_users_create` *(задача №27 — создание функционала для пользователей)
- `feature/14_booking_logic` *(задача №14 — логика бронирования)
- `fix/38_slots_overlap` * (задача №38 — исправление перекрытия временных слотов)

### 9.3. Правила

**1. Работаем только из develop**

Перед созданием ветки:

```bash
git checkout develop
git pull
```

**2. PR обязателен**

Слияние выполняется только после review тимлида.

**3. Нельзя пушить файлы:**

- БД
- картинки
- временные файлы
- IDE configs

**4. Проверка перед PR:**

- проект поднимается через docker-compose
- ruff check
- функционал работает

---

## 10. API-структура

**Префикс всех эндпоинтов:**

```
/api/v1/
```

**Группы:**

- `/auth` — аутентификация и авторизация
- `/users` — управление пользователями
- `/cafes` — список кафе
- `/cafes/{id}/tables` — столы в кафе
- `/cafes/{id}/slots` — временные слоты
- `/booking` — бронирования
- `/dishes` (опционально) — меню
- `/actions` (опционально) — акции и предложения
- `/media` — загрузка и выдача изображений

**Точка входа:**

```
src/main.py
```

### 10.1. Стандартные HTTP статус коды

| Код | Описание | Использование |
|-----|---------|---------------|
| 200 | OK | Успешный GET запрос |
| 201 | Created | Успешное создание ресурса (POST) |
| 204 | No Content | Успешное удаление (DELETE) |
| 400 | Bad Request | Ошибка валидации входных данных |
| 401 | Unauthorized | Отсутствует или неверен JWT токен |
| 403 | Forbidden | Недостаточно прав доступа |
| 404 | Not Found | Ресурс не найден |
| 409 | Conflict | Конфликт данных (например, пересечение слотов) |
| 422 | Unprocessable Entity | Ошибка обработки данных |
| 500 | Internal Server Error | Внутренняя ошибка сервера |

---

## 11. Переменные окружения (.env)

Для работы проекта необходимы следующие переменные окружения (пример в `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/booking_db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Message Broker
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
REDIS_URL=redis://localhost:6379/0

# App settings
APP_TITLE=Booking Seats API
APP_VERSION=1.0.0
DEBUG=False
FRONTEND_URL=http://localhost:3000

# File upload
MAX_UPLOAD_SIZE=5242880  # 5MB in bytes
ALLOWED_IMAGE_TYPES=image/jpeg,image/png
```

**Правила:**
- Никогда не коммитить `.env` файл в репозиторий
- Коммитить `.env.example` как шаблон
- Добавить `.env` в `.gitignore`

---

## 12. Миграции БД (Alembic)

**Alembic уже инициализирован и настроен для работы с async SQLAlchemy 2.0.**

Структура:
```
alembic/
├── env.py              (настроен для async операций)
├── script.py.mako      (шаблон миграций)
├── versions/           (папка с миграциями)
└── alembic.ini         (конфигурация с DATABASE_URL)
```

**Основные команды:**

```bash
# Применить все миграции
alembic upgrade head

# Создать новую миграцию после изменения моделей
alembic revision --autogenerate -m "описание изменений"
alembic upgrade head

# Проверка версии БД и истории
alembic current  # текущая версия
alembic history  # история миграций
```

**Рекомендации для команды:**

- Каждый разработчик создаёт миграции в своей feature-ветке
- Миграции имеют уникальные имена (timestamp-based), конфликты маловероятны
- Перед merge в develop убедитесь что `alembic upgrade head` выполняется без ошибок
- В локальном окружении используйте настоящую PostgreSQL (не SQLite)

---

## 13. Pre-commit конфигурация

Файл `.pre-commit-config.yaml` в корне проекта:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]
        additional_dependencies: [types-all]
```

**Установка:**
```bash
pip install pre-commit
pre-commit install
```

Теперь перед каждым `git commit` будут автоматически проверяться стиль кода и форматирование.

---

## 14. Декомпозиция ответственности в команде

| Модуль | Ответственный |
|--------|--------------|
| Users/Auth | Александр |
| Cafes | Павел |
| Tables | Павел |
| Slots | Лев |
| Booking | Анастасия |
| Celery Tasks | Андрей |
| Images | Лев / Данил |
| Logging | Данил |
| Docker / CI/CD | Данил + Лев |
| Code Review | Данил |

---

## 15. Минимальный порядок запуска проекта

**Шаг 1: Подготовка окружения**

```bash
cd booking_seats_team_project
cp .env.example .env
# Отредактировать .env при необходимости
```

**Шаг 2: Запуск сервисов через Docker**

```bash
docker-compose up --build
```

**Шаг 3: Применить миграции БД (в отдельном терминале)**

```bash
docker-compose exec api alembic upgrade head
```

**Шаг 4: Проверка здоровья приложения**

```bash
curl http://localhost:8000/api/v1/health
```

**Доступные сервисы:**

- **FastAPI** — http://localhost:8000
- **API Docs (Swagger)** — http://localhost:8000/docs
- **ReDoc** — http://localhost:8000/redoc
- **Postgres** — localhost:5432
- **Redis** — localhost:6379
- **RabbitMQ** — http://localhost:15672 (guest:guest)
- **Flower (Celery monitor)** — http://localhost:5555

**Docker сервисы:**

- api (FastAPI приложение)
- postgres (база данных)
- redis (кэш и backend для Celery)
- rabbitmq (message broker)
- celery_worker (обработчик задач)
- celery_beat (планировщик задач)
- flower (веб-интерфейс для мониторинга Celery)

---

## 16. Дальнейшее улучшение архитектуры (опционально)

Если останется время:

- кеширование меню и акций через Redis;
- дополнительные уведомления;
- вынести бизнес-логику в отдельные сервисы
- добавить S3-хранилище изображений.
- оптимизация SQL-запросов;
- сделать автотесты
- система ролей и расширенные права доступа.
