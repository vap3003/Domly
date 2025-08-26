"""
Кастомные исключения для системы управления недвижимостью
"""

from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class PropertyManagementException(Exception):
    """Базовое исключение для системы управления недвижимостью"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(PropertyManagementException):
    """Исключения связанные с базой данных"""
    pass


class AuthenticationException(PropertyManagementException):
    """Исключения аутентификации"""
    pass


class AuthorizationException(PropertyManagementException):
    """Исключения авторизации"""
    pass


class ValidationException(PropertyManagementException):
    """Исключения валидации данных"""
    pass


class ExternalServiceException(PropertyManagementException):
    """Исключения при работе с внешними сервисами"""
    pass


class PropertyNotFoundException(PropertyManagementException):
    """Недвижимость не найдена"""
    
    def __init__(self, property_id: str):
        super().__init__(f"Property with ID {property_id} not found")
        self.property_id = property_id


class TenantNotFoundException(PropertyManagementException):
    """Арендатор не найден"""
    
    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant with ID {tenant_id} not found")
        self.tenant_id = tenant_id


class ContractNotFoundException(PropertyManagementException):
    """Договор не найден"""
    
    def __init__(self, contract_id: str):
        super().__init__(f"Contract with ID {contract_id} not found")
        self.contract_id = contract_id


class PaymentException(PropertyManagementException):
    """Исключения связанные с платежами"""
    pass


class InsufficientPermissionsException(AuthorizationException):
    """Недостаточно прав доступа"""
    
    def __init__(self, required_permission: str):
        super().__init__(f"Insufficient permissions. Required: {required_permission}")
        self.required_permission = required_permission


class PropertyAlreadyRentedException(PropertyManagementException):
    """Недвижимость уже сдана в аренду"""
    
    def __init__(self, property_id: str):
        super().__init__(f"Property {property_id} is already rented")
        self.property_id = property_id


class InvalidPropertyStatusException(PropertyManagementException):
    """Неверный статус недвижимости для операции"""
    
    def __init__(self, property_id: str, current_status: str, required_status: str):
        super().__init__(
            f"Property {property_id} has status '{current_status}', but '{required_status}' is required"
        )
        self.property_id = property_id
        self.current_status = current_status
        self.required_status = required_status


# Функции для преобразования исключений в HTTP ответы

def to_http_exception(exc: PropertyManagementException) -> HTTPException:
    """
    Преобразование кастомного исключения в HTTPException
    
    Args:
        exc: Кастомное исключение
    
    Returns:
        HTTPException: HTTP исключение для FastAPI
    """
    
    # Маппинг типов исключений на HTTP статусы
    status_map = {
        PropertyNotFoundException: status.HTTP_404_NOT_FOUND,
        TenantNotFoundException: status.HTTP_404_NOT_FOUND,
        ContractNotFoundException: status.HTTP_404_NOT_FOUND,
        
        AuthenticationException: status.HTTP_401_UNAUTHORIZED,
        AuthorizationException: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsException: status.HTTP_403_FORBIDDEN,
        
        ValidationException: status.HTTP_422_UNPROCESSABLE_ENTITY,
        PropertyAlreadyRentedException: status.HTTP_409_CONFLICT,
        InvalidPropertyStatusException: status.HTTP_409_CONFLICT,
        
        PaymentException: status.HTTP_400_BAD_REQUEST,
        ExternalServiceException: status.HTTP_503_SERVICE_UNAVAILABLE,
        DatabaseException: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    # Определение HTTP статуса
    http_status = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Создание детального сообщения
    detail = {
        "message": exc.message,
        "type": type(exc).__name__,
        "details": exc.details
    }
    
    return HTTPException(status_code=http_status, detail=detail)


def exception_handler(exc: Exception) -> HTTPException:
    """
    Общий обработчик исключений
    
    Args:
        exc: Любое исключение
    
    Returns:
        HTTPException: HTTP исключение для FastAPI
    """
    
    # Если это уже наше кастомное исключение
    if isinstance(exc, PropertyManagementException):
        return to_http_exception(exc)
    
    # Если это уже HTTPException
    if isinstance(exc, HTTPException):
        return exc
    
    # Для всех остальных исключений
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "message": "Internal server error",
            "type": type(exc).__name__,
            "details": {"original_error": str(exc)}
        }
    )
