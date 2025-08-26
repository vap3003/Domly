"""
Конфигурация Tenant Service
"""

from shared.core.config import TenantServiceConfig

# Создание экземпляра конфигурации
settings = TenantServiceConfig()

# Экспорт для удобного импорта
__all__ = ["settings"]
