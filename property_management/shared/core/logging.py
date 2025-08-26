"""
Настройка структурированного логирования для всех сервисов
Использует structlog для создания структурированных логов
"""

import structlog
import logging
import sys
import json
from typing import Dict, Any
from .config import BaseConfig


def configure_logging(config: BaseConfig) -> None:
    """
    Настройка логирования для сервиса
    
    Args:
        config: Конфигурация сервиса
    """
    
    # Настройка стандартного logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.LOG_LEVEL.value),
    )
    
    # Процессоры для structlog
    processors = [
        # Фильтрация по уровню
        structlog.stdlib.filter_by_level,
        
        # Добавление имени логгера
        structlog.stdlib.add_logger_name,
        
        # Добавление уровня логирования
        structlog.stdlib.add_log_level,
        
        # Обработка позиционных аргументов
        structlog.stdlib.PositionalArgumentsFormatter(),
        
        # Добавление времени
        structlog.processors.TimeStamper(fmt="iso"),
        
        # Информация о стеке
        structlog.processors.StackInfoRenderer(),
        
        # Форматирование исключений
        structlog.processors.format_exc_info,
        
        # Декодирование Unicode
        structlog.processors.UnicodeDecoder(),
        
        # Добавление контекста сервиса
        add_service_context(config),
    ]
    
    # Добавление финального рендерера в зависимости от формата
    if config.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Конфигурация structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def add_service_context(config: BaseConfig):
    """
    Процессор для добавления контекста сервиса в каждое сообщение лога
    
    Args:
        config: Конфигурация сервиса
    
    Returns:
        function: Процессор structlog
    """
    def processor(logger, method_name, event_dict):
        event_dict.update({
            "service": config.SERVICE_NAME,
            "version": config.SERVICE_VERSION,
            "environment": config.ENVIRONMENT.value,
        })
        return event_dict
    
    return processor


class LoggerMixin:
    """
    Mixin для добавления логгера в классы
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = structlog.get_logger(self.__class__.__name__)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Получение структурированного логгера
    
    Args:
        name: Имя логгера
    
    Returns:
        structlog.BoundLogger: Настроенный логгер
    """
    return structlog.get_logger(name)


class RequestLoggingMiddleware:
    """
    Middleware для логирования HTTP запросов
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("http")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request_id = scope.get("request_id", "unknown")
        method = scope.get("method", "unknown")
        path = scope.get("path", "unknown")
        
        # Логирование начала запроса
        self.logger.info(
            "Request started",
            request_id=request_id,
            method=method,
            path=path,
            client=scope.get("client", ["unknown", 0])[0]
        )
        
        # Обработка запроса
        await self.app(scope, receive, send)


def log_function_call(logger_name: str = None):
    """
    Декоратор для логирования вызовов функций
    
    Args:
        logger_name: Имя логгера
    
    Returns:
        function: Декоратор
    """
    def decorator(func):
        logger = get_logger(logger_name or func.__module__)
        
        async def async_wrapper(*args, **kwargs):
            logger.debug(
                "Function called",
                function=func.__name__,
                args=len(args),
                kwargs=list(kwargs.keys())
            )
            
            try:
                result = await func(*args, **kwargs)
                logger.debug("Function completed", function=func.__name__)
                return result
            except Exception as e:
                logger.error(
                    "Function failed",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger.debug(
                "Function called",
                function=func.__name__,
                args=len(args),
                kwargs=list(kwargs.keys())
            )
            
            try:
                result = func(*args, **kwargs)
                logger.debug("Function completed", function=func.__name__)
                return result
            except Exception as e:
                logger.error(
                    "Function failed",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        # Возвращаем соответствующий wrapper в зависимости от типа функции
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
