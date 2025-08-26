"""
Конфигурация API Gateway
"""

from shared.core.config import APIGatewayConfig

# Создание экземпляра конфигурации
settings = APIGatewayConfig()

# Экспорт для удобного импорта
__all__ = ["settings"]
