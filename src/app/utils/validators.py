import re

from phonenumbers import NumberParseException, is_valid_number, parse


def validate_phone_format(phone: str | None) -> str | None:
    """Валидирует формат телефонного номера и автоматически заменяет 8 на +7.

    Требования:
    - Номер должен начинаться с +7.
    - Разрешены только цифры, скобки и дефисы (например, +7(916)123-45-67).
    - Если номер начинается с 8, он автоматически заменяется на +7.

    Args:
        phone (str | None): Номер телефона.

    Returns:
        str | None: Валидированный номер телефона в формате +7XXXXXXXXXX.
                   Возвращает None, если входное значение None.

    Raises:
        ValueError: Если номер телефона не соответствует требованиям.

    """
    if phone is None:
        return phone

    if phone.startswith('8'):
        phone = '+7' + phone[1:]

    if not re.fullmatch(r'\+7\(\d{3}\)\d{3}-\d{2}-\d{2}|\+7\d{10}', phone):
        error_msg = (
            'Неверный формат телефона. '
            'Пример: +79161234567 или +7(916)123-45-67'
        )
        raise ValueError(error_msg)

    try:
        phone_number = parse(phone, None)
        if not is_valid_number(phone_number):
            raise ValueError('Неверный номер телефона')

    except NumberParseException:
        error_msg = (
            'Неверный формат телефона. '
            'Пример: +79161234567 или +7(916)123-45-67'
        )
        raise ValueError(error_msg)

    return phone
