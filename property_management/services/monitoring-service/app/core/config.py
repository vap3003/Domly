"""
Конфигурация Monitoring Service
"""

from shared.core.config import MonitoringServiceConfig

# Создание экземпляра конфигурации
settings = MonitoringServiceConfig()

# Экспорт для удобного импорта
__all__ = ["settings"]
