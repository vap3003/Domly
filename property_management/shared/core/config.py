"""
Базовые конфигурационные классы для всех сервисов
Использует Pydantic Settings для загрузки конфигурации из переменных окружения
"""

from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import os
from enum import Enum


class Environment(str, Enum):
    """Окружения развертывания"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Уровни логирования"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseConfig(BaseSettings):
    """
    Базовая конфигурация для всех сервисов
    Содержит общие настройки
    """
    
    # Основные настройки
    SERVICE_NAME: str = Field(..., description="Название сервиса")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Версия сервиса")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, description="Окружение")
    DEBUG: bool = Field(default=True, description="Режим отладки")
    
    # Логирование
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Уровень логирования")
    LOG_FORMAT: str = Field(default="json", description="Формат логов (json/text)")
    
    # База данных
    DATABASE_URL: str = Field(..., description="URL подключения к базе данных")
    DATABASE_ECHO: bool = Field(default=False, description="Логирование SQL запросов")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Размер пула соединений")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Максимальное переполнение пула")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", description="URL подключения к Redis")
    REDIS_DB: int = Field(default=0, description="Номер базы данных Redis")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Пароль Redis")
    
    # Безопасность
    SECRET_KEY: str = Field(..., description="Секретный ключ для JWT")
    ALGORITHM: str = Field(default="HS256", description="Алгоритм шифрования JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Время жизни access токена (минуты)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Время жизни refresh токена (дни)")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], description="Разрешенные origins для CORS")
    ALLOWED_METHODS: List[str] = Field(default=["*"], description="Разрешенные HTTP методы")
    ALLOWED_HEADERS: List[str] = Field(default=["*"], description="Разрешенные заголовки")
    
    # Мониторинг
    ENABLE_METRICS: bool = Field(default=True, description="Включить сбор метрик")
    METRICS_PATH: str = Field(default="/metrics", description="Путь для метрик Prometheus")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v or not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        if values.get("ENVIRONMENT") == Environment.PRODUCTION and v == "your-secret-key":
            raise ValueError("SECRET_KEY must be changed in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_METHODS", pre=True)
    def parse_allowed_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @validator("ALLOWED_HEADERS", pre=True)
    def parse_allowed_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v


class PropertyServiceConfig(BaseConfig):
    """Конфигурация для Property Service"""
    
    SERVICE_NAME: str = Field(default="property-service")
    
    # Специфичные настройки для сервиса недвижимости
    MAX_PROPERTY_PHOTOS: int = Field(default=20, description="Максимальное количество фото недвижимости")
    PHOTO_UPLOAD_SIZE_MB: int = Field(default=5, description="Максимальный размер фото в МБ")
    SUPPORTED_PHOTO_FORMATS: List[str] = Field(
        default=["jpg", "jpeg", "png", "webp"], 
        description="Поддерживаемые форматы фото"
    )
    
    # Интеграция с внешними сервисами
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(default=None, description="API ключ Google Maps")
    ENABLE_GEOCODING: bool = Field(default=False, description="Включить геокодирование адресов")


class TenantServiceConfig(BaseConfig):
    """Конфигурация для Tenant Service"""
    
    SERVICE_NAME: str = Field(default="tenant-service")
    
    # Celery настройки
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="URL брокера Celery")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", description="Backend для результатов Celery")
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Сериализатор задач Celery")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Сериализатор результатов Celery")
    
    # Email настройки
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP хост")
    SMTP_PORT: int = Field(default=587, description="SMTP порт")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP пользователь")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP пароль")
    SMTP_TLS: bool = Field(default=True, description="Использовать TLS для SMTP")
    
    # Платежные системы
    STRIPE_API_KEY: Optional[str] = Field(default=None, description="API ключ Stripe")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Webhook секрет Stripe")
    
    # Уведомления
    PAYMENT_REMINDER_DAYS: int = Field(default=3, description="За сколько дней напоминать о платеже")
    CONTRACT_EXPIRY_REMINDER_DAYS: int = Field(default=30, description="За сколько дней напоминать об истечении договора")


class MonitoringServiceConfig(BaseConfig):
    """Конфигурация для Monitoring Service"""
    
    SERVICE_NAME: str = Field(default="monitoring-service")
    
    # WebSocket настройки
    WEBSOCKET_PING_INTERVAL: int = Field(default=30, description="Интервал ping для WebSocket (секунды)")
    WEBSOCKET_PING_TIMEOUT: int = Field(default=10, description="Таймаут ping для WebSocket (секунды)")
    MAX_WEBSOCKET_CONNECTIONS: int = Field(default=100, description="Максимальное количество WebSocket соединений")
    
    # Аналитика
    ANALYTICS_RETENTION_DAYS: int = Field(default=365, description="Срок хранения аналитических данных (дни)")
    ML_MODEL_UPDATE_INTERVAL: int = Field(default=24, description="Интервал обновления ML моделей (часы)")
    ENABLE_ML_PREDICTIONS: bool = Field(default=True, description="Включить ML предсказания")
    
    # Мониторинг других сервисов
    PROPERTY_SERVICE_URL: str = Field(default="http://property-service:8000", description="URL Property Service")
    TENANT_SERVICE_URL: str = Field(default="http://tenant-service:8000", description="URL Tenant Service")
    
    # Метрики
    METRICS_COLLECTION_INTERVAL: int = Field(default=60, description="Интервал сбора метрик (секунды)")
    METRICS_RETENTION_DAYS: int = Field(default=90, description="Срок хранения метрик (дни)")


class APIGatewayConfig(BaseConfig):
    """Конфигурация для API Gateway"""
    
    SERVICE_NAME: str = Field(default="api-gateway")
    
    # URLs сервисов
    PROPERTY_SERVICE_URL: str = Field(default="http://property-service:8000", description="URL Property Service")
    TENANT_SERVICE_URL: str = Field(default="http://tenant-service:8000", description="URL Tenant Service")
    MONITORING_SERVICE_URL: str = Field(default="http://monitoring-service:8000", description="URL Monitoring Service")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, description="Лимит запросов в минуту")
    RATE_LIMIT_BURST: int = Field(default=10, description="Burst лимит для rate limiting")
    ENABLE_RATE_LIMITING: bool = Field(default=True, description="Включить rate limiting")
    
    # Проксирование
    PROXY_TIMEOUT: int = Field(default=30, description="Таймаут проксирования (секунды)")
    MAX_RETRY_ATTEMPTS: int = Field(default=3, description="Максимальное количество повторов")
    RETRY_DELAY: float = Field(default=1.0, description="Задержка между повторами (секунды)")
    
    # Health checks
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Интервал проверки здоровья сервисов (секунды)")
    HEALTH_CHECK_TIMEOUT: int = Field(default=5, description="Таймаут проверки здоровья (секунды)")


def get_config(service_name: str) -> BaseConfig:
    """
    Фабрика для получения конфигурации сервиса
    
    Args:
        service_name: Название сервиса
    
    Returns:
        BaseConfig: Конфигурация сервиса
    """
    config_map = {
        "property-service": PropertyServiceConfig,
        "tenant-service": TenantServiceConfig,
        "monitoring-service": MonitoringServiceConfig,
        "api-gateway": APIGatewayConfig,
    }
    
    config_class = config_map.get(service_name, BaseConfig)
    return config_class()
