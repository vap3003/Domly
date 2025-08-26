"""
Кастомные валидаторы для системы управления недвижимостью
"""

import re
from typing import Any, List, Optional
from datetime import datetime, date
from pydantic import validator
from email_validator import validate_email, EmailNotValidError


def validate_phone_number(phone: str) -> str:
    """
    Валидация номера телефона
    Поддерживает российские номера в различных форматах
    
    Args:
        phone: Номер телефона
    
    Returns:
        str: Нормализованный номер телефона
    
    Raises:
        ValueError: При неверном формате номера
    """
    if not phone:
        raise ValueError("Phone number is required")
    
    # Убираем все символы кроме цифр и +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Паттерны для российских номеров
    patterns = [
        r'^\+7\d{10}$',      # +7XXXXXXXXXX
        r'^8\d{10}$',        # 8XXXXXXXXXX
        r'^7\d{10}$',        # 7XXXXXXXXXX
        r'^\d{10}$',         # XXXXXXXXXX (московские номера)
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean_phone):
            # Нормализуем к формату +7XXXXXXXXXX
            if clean_phone.startswith('8'):
                return '+7' + clean_phone[1:]
            elif clean_phone.startswith('7'):
                return '+' + clean_phone
            elif clean_phone.startswith('+7'):
                return clean_phone
            else:
                return '+7' + clean_phone
    
    raise ValueError("Invalid phone number format")


def validate_email_address(email: str) -> str:
    """
    Валидация email адреса
    
    Args:
        email: Email адрес
    
    Returns:
        str: Нормализованный email
    
    Raises:
        ValueError: При неверном формате email
    """
    if not email:
        raise ValueError("Email is required")
    
    try:
        # Используем email-validator для проверки
        validation_result = validate_email(email)
        return validation_result.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email format: {str(e)}")


def validate_postal_code(postal_code: str, country: str = "Russia") -> str:
    """
    Валидация почтового индекса
    
    Args:
        postal_code: Почтовый индекс
        country: Страна (по умолчанию Россия)
    
    Returns:
        str: Нормализованный почтовый индекс
    
    Raises:
        ValueError: При неверном формате индекса
    """
    if not postal_code:
        raise ValueError("Postal code is required")
    
    # Убираем пробелы
    clean_code = postal_code.strip().replace(' ', '')
    
    if country.lower() in ['russia', 'россия', 'ru']:
        # Российские индексы: 6 цифр
        if not re.match(r'^\d{6}$', clean_code):
            raise ValueError("Russian postal code must be 6 digits")
        return clean_code
    
    # Для других стран можно добавить дополнительную логику
    return clean_code


def validate_inn(inn: str) -> str:
    """
    Валидация ИНН (Идентификационный номер налогоплательщика)
    
    Args:
        inn: ИНН
    
    Returns:
        str: Валидный ИНН
    
    Raises:
        ValueError: При неверном ИНН
    """
    if not inn:
        raise ValueError("INN is required")
    
    # Убираем пробелы и дефисы
    clean_inn = re.sub(r'[\s\-]', '', inn)
    
    # ИНН может быть 10 или 12 цифр
    if not re.match(r'^\d{10}$|^\d{12}$', clean_inn):
        raise ValueError("INN must be 10 or 12 digits")
    
    # Проверка контрольных сумм для ИНН
    def check_inn_10(inn_digits):
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn_digits[i]) * coefficients[i] for i in range(9)) % 11 % 10
        return checksum == int(inn_digits[9])
    
    def check_inn_12(inn_digits):
        coefficients_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        coefficients_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        
        checksum_11 = sum(int(inn_digits[i]) * coefficients_11[i] for i in range(10)) % 11 % 10
        checksum_12 = sum(int(inn_digits[i]) * coefficients_12[i] for i in range(11)) % 11 % 10
        
        return checksum_11 == int(inn_digits[10]) and checksum_12 == int(inn_digits[11])
    
    if len(clean_inn) == 10:
        if not check_inn_10(clean_inn):
            raise ValueError("Invalid INN checksum")
    else:  # 12 digits
        if not check_inn_12(clean_inn):
            raise ValueError("Invalid INN checksum")
    
    return clean_inn


def validate_passport_series(series: str) -> str:
    """
    Валидация серии паспорта РФ
    
    Args:
        series: Серия паспорта
    
    Returns:
        str: Валидная серия паспорта
    
    Raises:
        ValueError: При неверной серии
    """
    if not series:
        raise ValueError("Passport series is required")
    
    # Убираем пробелы
    clean_series = series.strip().replace(' ', '')
    
    # Серия паспорта РФ: 4 цифры
    if not re.match(r'^\d{4}$', clean_series):
        raise ValueError("Passport series must be 4 digits")
    
    return clean_series


def validate_passport_number(number: str) -> str:
    """
    Валидация номера паспорта РФ
    
    Args:
        number: Номер паспорта
    
    Returns:
        str: Валидный номер паспорта
    
    Raises:
        ValueError: При неверном номере
    """
    if not number:
        raise ValueError("Passport number is required")
    
    # Убираем пробелы
    clean_number = number.strip().replace(' ', '')
    
    # Номер паспорта РФ: 6 цифр
    if not re.match(r'^\d{6}$', clean_number):
        raise ValueError("Passport number must be 6 digits")
    
    return clean_number


def validate_date_range(start_date: date, end_date: date) -> None:
    """
    Валидация диапазона дат
    
    Args:
        start_date: Начальная дата
        end_date: Конечная дата
    
    Raises:
        ValueError: При неверном диапазоне дат
    """
    if start_date >= end_date:
        raise ValueError("Start date must be before end date")
    
    if start_date < date.today():
        raise ValueError("Start date cannot be in the past")


def validate_positive_amount(amount: float, field_name: str = "amount") -> float:
    """
    Валидация положительной суммы
    
    Args:
        amount: Сумма
        field_name: Название поля для ошибки
    
    Returns:
        float: Валидная сумма
    
    Raises:
        ValueError: При неверной сумме
    """
    if amount is None:
        raise ValueError(f"{field_name} is required")
    
    if amount <= 0:
        raise ValueError(f"{field_name} must be positive")
    
    # Ограничение на максимальную сумму (100 миллионов)
    if amount > 100_000_000:
        raise ValueError(f"{field_name} is too large")
    
    return round(amount, 2)


def validate_coordinates(lat: float, lng: float) -> tuple[float, float]:
    """
    Валидация географических координат
    
    Args:
        lat: Широта
        lng: Долгота
    
    Returns:
        tuple: Валидные координаты (lat, lng)
    
    Raises:
        ValueError: При неверных координатах
    """
    if lat is None or lng is None:
        raise ValueError("Both latitude and longitude are required")
    
    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    
    if not (-180 <= lng <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    
    return lat, lng


# Pydantic валидаторы для использования в схемах

@validator('phone', pre=True, always=True)
def validate_phone_field(cls, v):
    """Pydantic валидатор для телефона"""
    if v:
        return validate_phone_number(v)
    return v


@validator('email', pre=True, always=True)
def validate_email_field(cls, v):
    """Pydantic валидатор для email"""
    if v:
        return validate_email_address(v)
    return v


@validator('postal_code', pre=True, always=True)
def validate_postal_code_field(cls, v):
    """Pydantic валидатор для почтового индекса"""
    if v:
        return validate_postal_code(v)
    return v
