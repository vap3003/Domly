"""
Property Management Service Models
Импорт всех моделей для правильной инициализации SQLAlchemy
"""

# Импортируем все модели для регистрации в SQLAlchemy
from .property import (
    Property,
    PropertyType,
    PropertyStatus,
    PropertyCondition,
    HeatingType
)

from .photo import (
    PropertyPhoto,
    PhotoType
)

from .feature import (
    PropertyFeature,
    PropertyFeatureAssignment,
    PropertyAmenity,
    FeatureCategory
)

from .owner import (
    PropertyOwner,
    OwnerType
)

from .interaction import (
    PropertyView,
    PropertyFavorite,
    PropertyInquiry,
    SearchQuery,
    InteractionType
)

# Экспортируем все модели
__all__ = [
    # Основная модель недвижимости
    "Property",
    "PropertyType", 
    "PropertyStatus",
    "PropertyCondition",
    "HeatingType",
    
    # Модели фотографий
    "PropertyPhoto",
    "PhotoType",
    
    # Модели характеристик
    "PropertyFeature",
    "PropertyFeatureAssignment", 
    "PropertyAmenity",
    "FeatureCategory",
    
    # Модели владельцев
    "PropertyOwner",
    "OwnerType",
    
    # Модели взаимодействий
    "PropertyView",
    "PropertyFavorite", 
    "PropertyInquiry",
    "SearchQuery",
    "InteractionType",
]
