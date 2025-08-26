"""
Конфигурация Property Service
"""

from shared.core.config import PropertyServiceConfig

# Создание экземпляра конфигурации
settings = PropertyServiceConfig()

# Экспорт для удобного импорта
__all__ = ["settings"]
