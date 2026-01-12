# Booking Seats API

Backend для бронирования мест в кафе.

## Требования
- Python 3.11
- Docker + Docker Compose (если запускаете в контейнерах)

## Запуск в Docker

### Windows (Git Bash)
```
cp src/.env.example src/.env
docker build -t booking-seats-api:latest -f src/Dockerfile src
DOCKER_IMAGE=booking-seats-api IMAGE_TAG=latest docker compose -f infra/docker-compose.yml up -d
```

### macOS/Linux
```
cp src/.env.example src/.env
docker build -t booking-seats-api:latest -f src/Dockerfile src
DOCKER_IMAGE=booking-seats-api IMAGE_TAG=latest docker compose -f infra/docker-compose.yml up -d
```

## Локальный запуск (без Docker)

### Windows (Git Bash)
```
python -m venv venv
source venv/Scripts/activate
pip install -r src/requirements.txt
cp src/.env.example src/.env
cd src
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### macOS/Linux
```
python3 -m venv venv
source venv/bin/activate
pip install -r src/requirements.txt
cp src/.env.example src/.env
cd src
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Запуск на сервере
```
ssh <USER>@<SERVER_IP>
cd /home/<USER>/booking_seats_team_project
git pull
docker build -t booking-seats-api:latest -f src/Dockerfile src
DOCKER_IMAGE=booking-seats-api IMAGE_TAG=latest docker compose -f infra/docker-compose.yml up -d
```

## Миграции
```
cd src
alembic upgrade head
```

## Полезные адреса
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Mailpit (перехватчик почты): http://localhost:8025

## Файлы окружения
- `src/.env` — локальная конфигурация
- `src/.env.example` — шаблон
- `src/.env.production` — продакшен-конфиг

## Состав команды
- @Mordovin — тимлид, Docker, CI/CD, logging, базовая структура
- @zk31ns — users/auth, JWT
- @PashaDyakonov — cafes/tables
- @al3eon — slots/media, Redis caching
- @Anastasia-Kruglova — booking, бизнес-логика
- @Shtraube — Celery, tasks, RabbitMQ

## Тесты
```
pytest
```
