"""Глобальные константы приложения.

Используются в разных частях проекта для избежания магических
чисел и дублирования. Константы организованы в классы для
лучшей структурации и типизации.

Использование:
    from src.app.core.constants import (
        API, Limits, Times, Messages, ErrorCode
    )

    print(API.V1_PREFIX)  # "/api/v1"
    print(Limits.MAX_USERNAME_LENGTH)  # 50
    print(Times.ACCESS_TOKEN_MINUTES)  # 60

Обратная совместимость:
    from src.app.core.constants import (
        API_V1_PREFIX, TAGS_HEALTH
    )  # Старые имена всё ещё работают
"""

import re
from enum import Enum

# ========== API и Таги ==========


class API:
    """API константы и версии."""

    V1_PREFIX = '/api/v1'

    # Таги для OpenAPI документации
    HEALTH = ['health']
    USERS = ['users']
    AUTH = ['auth']
    CAFES = ['cafes']
    TABLES = ['tables']
    SLOTS = ['slots']
    BOOKING = ['booking']
    MEDIA = ['media']


# ========== Размеры и Лимиты ==========


class Limits:
    """Ограничения размеров, длин и количеств."""

    # Загрузка файлов
    MAX_UPLOAD_SIZE_MB = 5
    MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
    ALLOWED_IMAGE_MIMETYPES = {'image/jpeg', 'image/png'}

    # Пагинация
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    # Username
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50

    # Password
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 255

    # Email
    MAX_EMAIL_LENGTH = 255

    # Telegram
    MAX_TG_ID_LENGTH = 100

    # Cafe name
    MIN_CAFE_NAME_LENGTH = 3
    MAX_CAFE_NAME_LENGTH = 255

    # Description
    MIN_DESCRIPTION_LENGTH = 0
    MAX_DESCRIPTION_LENGTH = 1000

    # Phone
    MIN_PHONE_LENGTH = 10
    MAX_PHONE_LENGTH = 20

    # Seats
    MIN_SEATS = 1
    MAX_SEATS = 100

    # Prices
    MIN_PRICE = 0.0
    MAX_PRICE = 999999.99

    # Минимальная длина строки поиска
    MIN_SEARCH_QUERY_LENGTH = 2


# ========== Времена (в минутах/днях) ==========


class Times:
    """Временные константы для токенов, бронирования и задач."""

    # Временная зона
    TIME_ZONE = 'Europe/Moscow'

    # JWT токены
    ACCESS_TOKEN_MINUTES = 60  # 1 час
    REFRESH_TOKEN_DAYS = 7

    # Бронирование
    BOOKING_REMINDER_MINUTES = 60  # Напомнить за 1 час до бронирования
    MIN_BOOKING_ADVANCE_MINUTES = 30  # Минимум за 30 минут до слота
    MAX_BOOKING_DAYS_AHEAD = 90  # Максимум на 90 дней вперёд

    # Celery задачи
    CELERY_TASK_TIMEOUT = 300  # 5 минут

    # Время хранения кэща Redis
    REDIS_CACHE_EXPIRE_TIME = 300

    # Время хранения результатов в RabbitMQ
    RABBITMQ_RESULT_EXPIRE = 86400

    # Telegram request timeout
    TELEGRAM_REQUEST_TIMEOUT = 30


# ========== Enum классы ==========


class BookingStatus(str, Enum):
    """Статусы бронирования."""

    NEW = 'new'  # Новая бронь
    CONFIRMED = 'confirmed'  # Подтверждённая бронь
    CANCELLED = 'cancelled'  # Отменённая бронь
    FINISHED = 'finished'  # Завершённая бронь


class UserRole(str, Enum):
    """Роли пользователей."""

    CUSTOMER = 'customer'  # Клиент
    MANAGER = 'manager'  # Менеджер кафе
    ADMIN = 'admin'  # Администратор


class ErrorCode(str, Enum):
    """Коды ошибок API."""

    # Auth
    INVALID_CREDENTIALS = 'invalid_credentials'
    TOKEN_EXPIRED = 'token_expired'
    INVALID_TOKEN = 'invalid_token'
    USER_NOT_FOUND = 'user_not_found'
    USER_ALREADY_EXISTS = 'user_already_exists'
    USER_BLOCKED = 'user_blocked'
    USER_DEACTIVATED = 'user_deactivated'
    CONFIRMATION_REQUIRED = 'confirmation_required'
    PASSWORD_CHANGE_FAILED = 'password_change_failed'
    DATA_CONFLICT = 'data_conflict'
    TOKEN_REFRESH_FAILED = 'token_refresh_failed'
    AUTHENTICATION_REQUIRED = 'authentication_required'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    INVALID_REFRESH_TOKEN = 'invalid_refresh_token'
    PHONE_ALREADY_REGISTERED = 'phone_already_registered'
    PASSWORD_SAME_AS_OLD = 'password_same_as_old'
    CANNOT_DELETE_OWN_ACCOUNT = 'cannot_delete_own_account'
    INCORRECT_CURRENT_PASSWORD = 'incorrect_current_password'

    # Cafe
    CAFE_NOT_FOUND = 'cafe_not_found'
    CAFE_INACTIVE = 'cafe_inactive'
    NOT_CAFE_MANAGER = 'not_cafe_manager'

    # Table
    TABLE_NOT_FOUND = 'table_not_found'
    TABLE_INACTIVE = 'table_inactive'
    INVALID_SEATS_COUNT = 'invalid_seats_count'

    # Slot
    SLOT_NOT_FOUND = 'slot_not_found'
    SLOT_INACTIVE = 'slot_inactive'
    SLOT_OVERLAP = 'slot_overlap'
    INVALID_TIME_RANGE = 'invalid_time_range'
    CONFLICT = 409

    # Booking
    BOOKING_NOT_FOUND = 'booking_not_found'
    BOOKING_PAST_DATE = 'booking_past_date'
    TABLE_ALREADY_BOOKED = 'table_already_booked'
    USER_ALREADY_BOOKED = 'user_already_booked'
    INSUFFICIENT_PERMISSIONS = 'insufficient_permissions'
    INVALID_STATUS_TRANSITION = 'invalid_status_transition'

    # Media
    FILE_TOO_LARGE = 'file_too_large'
    INVALID_FILE_TYPE = 'invalid_file_type'
    MEDIA_NOT_FOUND = 'media_not_found'

    # General
    VALIDATION_ERROR = 'validation_error'
    INTERNAL_SERVER_ERROR = 'internal_server_error'


class EventType(str, Enum):
    """Типы событий для логирования."""

    # Auth
    USER_REGISTERED = 'user_registered'
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    USER_BLOCKED = 'user_blocked'
    USER_UNBLOCKED = 'user_unblocked'

    # Cafe
    CAFE_CREATED = 'cafe_created'
    CAFE_UPDATED = 'cafe_updated'
    CAFE_DELETED = 'cafe_deleted'

    # Booking
    BOOKING_CREATED = 'booking_created'
    BOOKING_CONFIRMED = 'booking_confirmed'
    BOOKING_CANCELLED = 'booking_cancelled'
    BOOKING_FINISHED = 'booking_finished'
    BOOKING_REMINDER_SENT = 'booking_reminder_sent'

    # Media
    FILE_UPLOADED = 'file_uploaded'
    FILE_DELETED = 'file_deleted'

    # Celery tasks
    TASK_STARTED = 'task_started'
    TASK_FINISHED = 'task_finished'
    REMINDER_SENT = 'reminder_sent'


# ========== Сообщения об ошибках ==========


class Messages:
    """Сообщения для пользователя (локализованы на русском)."""

    errors = {
        ErrorCode.INVALID_CREDENTIALS: 'Неверные учётные данные',
        ErrorCode.TOKEN_EXPIRED: 'Токен истёк',
        ErrorCode.INVALID_TOKEN: 'Неверный токен',
        ErrorCode.USER_NOT_FOUND: 'Пользователь не найден',
        ErrorCode.USER_BLOCKED: 'Пользователь заблокирован',
        ErrorCode.USER_ALREADY_EXISTS: (
            'Пользователь с этим именем/email уже существует'
        ),
        ErrorCode.PHONE_ALREADY_REGISTERED: 'Телефон уже зарегистрирован',
        ErrorCode.USER_DEACTIVATED: 'Пользователь деактивирован',
        ErrorCode.CAFE_NOT_FOUND: 'Кафе не найдено',
        ErrorCode.CAFE_INACTIVE: 'Кафе неактивно',
        ErrorCode.NOT_CAFE_MANAGER: 'Вы не являетесь менеджером этого кафе',
        ErrorCode.TABLE_NOT_FOUND: 'Столик не найден',
        ErrorCode.TABLE_INACTIVE: 'Столик неактивен',
        ErrorCode.INVALID_SEATS_COUNT: 'Некорректное количество мест',
        ErrorCode.SLOT_NOT_FOUND: 'Слот не найден',
        ErrorCode.SLOT_INACTIVE: 'Слот неактивен',
        ErrorCode.SLOT_OVERLAP: 'Слот пересекается с существующим',
        ErrorCode.INVALID_TIME_RANGE: (
            'Время начала должно быть раньше времени окончания'
        ),
        ErrorCode.USER_ALREADY_BOOKED: 'У вас уже есть бронь на это время',
        ErrorCode.BOOKING_NOT_FOUND: 'Бронь не найдена',
        ErrorCode.BOOKING_PAST_DATE: 'Нельзя забронировать на прошедшую дату',
        ErrorCode.TABLE_ALREADY_BOOKED: 'Столик уже забронирован на это время',
        ErrorCode.INSUFFICIENT_PERMISSIONS: 'Недостаточно прав доступа',
        ErrorCode.INVALID_STATUS_TRANSITION: 'Неверный переход статуса',
        ErrorCode.FILE_TOO_LARGE: 'Файл слишком большой (макс. 5MB)',
        ErrorCode.INVALID_FILE_TYPE: (
            'Недопустимый тип файла (разрешены JPG, PNG)'
        ),
        ErrorCode.MEDIA_NOT_FOUND: 'Изображение не найдено',
        ErrorCode.VALIDATION_ERROR: 'Ошибка валидации',
        ErrorCode.INTERNAL_SERVER_ERROR: 'Внутренняя ошибка сервера',
        ErrorCode.CONFIRMATION_REQUIRED: 'Требуется подтверждение действия',
        ErrorCode.PASSWORD_CHANGE_FAILED: 'Ошибка смены пароля',
        ErrorCode.DATA_CONFLICT: 'Конфликт данных',
        ErrorCode.TOKEN_REFRESH_FAILED: 'Ошибка обновления токена',
        ErrorCode.AUTHENTICATION_REQUIRED: 'Требуется аутентификация',
        ErrorCode.SERVICE_UNAVAILABLE: 'Сервис временно недоступен',
        ErrorCode.INVALID_REFRESH_TOKEN: 'Неверный или истёкший refresh токен',
        ErrorCode.PASSWORD_SAME_AS_OLD: (
            'Новый пароль должен отличаться от старого'
        ),
        ErrorCode.CANNOT_DELETE_OWN_ACCOUNT: (
            'Нельзя удалить свой собственный аккаунт'
        ),
        ErrorCode.INCORRECT_CURRENT_PASSWORD: 'Текущий пароль неверен',
    }

    success_messages = {
        'user_created': 'Пользователь успешно создан',
        'user_updated': 'Профиль успешно обновлён',
        'user_deleted': 'Пользователь удалён',
        'cafe_created': 'Кафе успешно создано',
        'cafe_updated': 'Кафе успешно обновлено',
        'cafe_deleted': 'Кафе удалено',
        'booking_created': 'Бронь успешно создана',
        'booking_confirmed': 'Бронь подтверждена',
        'booking_cancelled': 'Бронь отменена',
        'file_uploaded': 'Файл успешно загружен',
        'file_deleted': 'Файл удалён',
    }


# ========== Celery задачи ==========


class CeleryTasks:
    """Имена и пути Celery задач."""

    SEND_BOOKING_REMINDER = 'app.core.celery_tasks.send_booking_reminder'
    NOTIFY_MANAGER = 'app.core.celery_tasks.notify_manager'
    SEND_CANCELLATION_NOTIFICATION = (
        'app.core.celery_tasks.send_cancellation_notification'
    )
    CLEANUP_EXPIRED_BOOKINGS = 'app.core.celery_tasks.cleanup_expired_bookings'


# ========== Регулярные выражения ==========


class Patterns:
    """Regex паттерны для валидации."""

    # Email валидация
    EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # Username валидация (буквы, цифры, подчеркивание, дефис)
    USERNAME = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')

    # Телефон (формат +7 и цифры, допускаются скобки и дефисы)
    # Примеры: +7 999 999 9999, +7(999)999-9999, +79999999999, 79999999999
    PHONE = re.compile(r'^\+?7[\s\-\(\)]*\d[\d\s\-\(\)]*$')


# ========== Обратная совместимость (для постепенного перехода) ==========
# ========== Обратная совместимость (для постепенного перехода) ==========
# Можно удалить после обновления всех файлов

# API
API_V1_PREFIX = API.V1_PREFIX
TAGS_HEALTH = API.HEALTH
TAGS_USERS = API.USERS
TAGS_AUTH = API.AUTH
TAGS_CAFES = API.CAFES
TAGS_TABLES = API.TABLES
TAGS_SLOTS = API.SLOTS
TAGS_BOOKING = API.BOOKING
TAGS_MEDIA = API.MEDIA

# Sizes/Limits
MAX_UPLOAD_SIZE_MB = Limits.MAX_UPLOAD_SIZE_MB
MAX_UPLOAD_SIZE_BYTES = Limits.MAX_UPLOAD_SIZE_BYTES
ALLOWED_IMAGE_EXTENSIONS = Limits.ALLOWED_IMAGE_EXTENSIONS
ALLOWED_IMAGE_MIMETYPES = Limits.ALLOWED_IMAGE_MIMETYPES
DEFAULT_PAGE_SIZE = Limits.DEFAULT_PAGE_SIZE
MAX_PAGE_SIZE = Limits.MAX_PAGE_SIZE
MIN_USERNAME_LENGTH = Limits.MIN_USERNAME_LENGTH
MAX_USERNAME_LENGTH = Limits.MAX_USERNAME_LENGTH
MIN_PASSWORD_LENGTH = Limits.MIN_PASSWORD_LENGTH
MAX_PASSWORD_LENGTH = Limits.MAX_PASSWORD_LENGTH
MIN_CAFE_NAME_LENGTH = Limits.MIN_CAFE_NAME_LENGTH
MAX_CAFE_NAME_LENGTH = Limits.MAX_CAFE_NAME_LENGTH
PHONE_MIN_LENGTH = Limits.MIN_PHONE_LENGTH
PHONE_MAX_LENGTH = Limits.MAX_PHONE_LENGTH
MIN_SEATS = Limits.MIN_SEATS
MAX_SEATS = Limits.MAX_SEATS
MIN_PRICE = Limits.MIN_PRICE
MAX_PRICE = Limits.MAX_PRICE

# Times
ACCESS_TOKEN_EXPIRE_MINUTES = Times.ACCESS_TOKEN_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = Times.REFRESH_TOKEN_DAYS
BOOKING_REMINDER_MINUTES = Times.BOOKING_REMINDER_MINUTES
MIN_BOOKING_ADVANCE_MINUTES = Times.MIN_BOOKING_ADVANCE_MINUTES
MAX_BOOKING_DAYS_AHEAD = Times.MAX_BOOKING_DAYS_AHEAD
CELERY_TASK_TIMEOUT = Times.CELERY_TASK_TIMEOUT
REDIS_CACHE_EXPIRE_TIME = Times.REDIS_CACHE_EXPIRE_TIME

# Messages
ERROR_MESSAGES = Messages.errors
SUCCESS_MESSAGES = Messages.success_messages

# Celery
CELERY_TASKS = {
    'send_booking_reminder': CeleryTasks.SEND_BOOKING_REMINDER,
    'notify_manager': CeleryTasks.NOTIFY_MANAGER,
    'send_cancellation_notification': (
        CeleryTasks.SEND_CANCELLATION_NOTIFICATION
    ),
    'cleanup_expired_bookings': CeleryTasks.CLEANUP_EXPIRED_BOOKINGS,
}

# Regex
EMAIL_REGEX = Patterns.EMAIL
USERNAME_REGEX = Patterns.USERNAME
PHONE_REGEX = Patterns.PHONE


__all__ = [
    # Новые классы (рекомендуется использовать)
    'API',
    'Limits',
    'Times',
    'Messages',
    'CeleryTasks',
    'Patterns',
    # Enums
    'BookingStatus',
    'UserRole',
    'ErrorCode',
    'EventType',
    # Обратная совместимость (старые имена - скоро устаревшие)
    'API_V1_PREFIX',
    'TAGS_HEALTH',
    'TAGS_USERS',
    'TAGS_AUTH',
    'TAGS_CAFES',
    'TAGS_TABLES',
    'TAGS_SLOTS',
    'TAGS_BOOKING',
    'TAGS_MEDIA',
    'MAX_UPLOAD_SIZE_MB',
    'MAX_UPLOAD_SIZE_BYTES',
    'ALLOWED_IMAGE_EXTENSIONS',
    'ALLOWED_IMAGE_MIMETYPES',
    'DEFAULT_PAGE_SIZE',
    'MAX_PAGE_SIZE',
    'MIN_USERNAME_LENGTH',
    'MAX_USERNAME_LENGTH',
    'MIN_PASSWORD_LENGTH',
    'MAX_PASSWORD_LENGTH',
    'MIN_CAFE_NAME_LENGTH',
    'MAX_CAFE_NAME_LENGTH',
    'PHONE_MIN_LENGTH',
    'PHONE_MAX_LENGTH',
    'MIN_SEATS',
    'MAX_SEATS',
    'MIN_PRICE',
    'MAX_PRICE',
    'ACCESS_TOKEN_EXPIRE_MINUTES',
    'REFRESH_TOKEN_EXPIRE_DAYS',
    'BOOKING_REMINDER_MINUTES',
    'MIN_BOOKING_ADVANCE_MINUTES',
    'MAX_BOOKING_DAYS_AHEAD',
    'CELERY_TASK_TIMEOUT',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'CELERY_TASKS',
    'EMAIL_REGEX',
    'USERNAME_REGEX',
    'PHONE_REGEX',
]
