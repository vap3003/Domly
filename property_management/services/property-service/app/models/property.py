"""
SQLAlchemy модели для Property Management Service
Основные модели для работы с недвижимостью
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database.base import Base
from shared.database.models import TimestampMixin, UUIDMixin
import uuid
import enum
from typing import Dict, List, Any, Optional
from datetime import datetime


class PropertyType(enum.Enum):
    """Типы недвижимости"""
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    STUDIO = "studio"
    PENTHOUSE = "penthouse"
    TOWNHOUSE = "townhouse"
    WAREHOUSE = "warehouse"
    RETAIL = "retail"
    LAND = "land"


class PropertyStatus(enum.Enum):
    """Статусы недвижимости"""
    AVAILABLE = "available"        # Доступна для аренды
    RENTED = "rented"             # Сдана в аренду
    MAINTENANCE = "maintenance"    # На обслуживании
    INACTIVE = "inactive"         # Неактивна
    RESERVED = "reserved"         # Зарезервирована
    SOLD = "sold"                # Продана


class PropertyCondition(enum.Enum):
    """Состояние недвижимости"""
    EXCELLENT = "excellent"       # Отличное
    GOOD = "good"                # Хорошее
    FAIR = "fair"                # Удовлетворительное
    POOR = "poor"                # Плохое
    RENOVATION_REQUIRED = "renovation_required"  # Требует ремонта


class HeatingType(enum.Enum):
    """Типы отопления"""
    CENTRAL = "central"           # Центральное
    INDIVIDUAL = "individual"     # Индивидуальное
    GAS = "gas"                  # Газовое
    ELECTRIC = "electric"        # Электрическое
    NONE = "none"                # Отсутствует


class Property(Base, UUIDMixin, TimestampMixin):
    """
    Основная модель недвижимости
    """
    __tablename__ = "properties"
    
    # Основная информация
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="ID владельца недвижимости")
    title = Column(String(255), nullable=False, comment="Название/заголовок недвижимости")
    description = Column(Text, comment="Подробное описание недвижимости")
    
    # Тип и статус
    property_type = Column(Enum(PropertyType), nullable=False, index=True, comment="Тип недвижимости")
    status = Column(
        Enum(PropertyStatus), 
        default=PropertyStatus.AVAILABLE, 
        nullable=False,
        index=True,
        comment="Статус недвижимости"
    )
    condition = Column(Enum(PropertyCondition), comment="Состояние недвижимости")
    
    # Адрес и местоположение
    address = Column(
        JSONB, 
        nullable=False,
        comment="Адрес в формате JSON: {street, city, postal_code, country, district, region}"
    )
    coordinates = Column(
        JSONB,
        comment="Координаты в формате JSON: {lat, lng, accuracy}"
    )
    
    # Характеристики
    total_area = Column(Numeric(10, 2), comment="Общая площадь в кв.м")
    living_area = Column(Numeric(10, 2), comment="Жилая площадь в кв.м")
    kitchen_area = Column(Numeric(8, 2), comment="Площадь кухни в кв.м")
    
    rooms_count = Column(Integer, comment="Количество комнат")
    bedrooms_count = Column(Integer, comment="Количество спален")
    bathrooms_count = Column(Integer, comment="Количество санузлов")
    
    floor = Column(Integer, comment="Этаж")
    total_floors = Column(Integer, comment="Общее количество этажей в здании")
    
    # Дополнительные характеристики
    year_built = Column(Integer, comment="Год постройки")
    ceiling_height = Column(Numeric(4, 2), comment="Высота потолков в метрах")
    
    # Коммуникации и удобства
    heating_type = Column(Enum(HeatingType), comment="Тип отопления")
    has_elevator = Column(Boolean, default=False, comment="Наличие лифта")
    has_parking = Column(Boolean, default=False, comment="Наличие парковки")
    has_balcony = Column(Boolean, default=False, comment="Наличие балкона/лоджии")
    has_furniture = Column(Boolean, default=False, comment="Меблирована")
    
    # Удобства в формате JSON массива
    amenities = Column(
        JSONB,
        comment="Удобства в формате JSON массива: ['parking', 'elevator', 'balcony', 'gym', 'pool']"
    )
    
    # Фотографии в формате JSON массива
    photos = Column(
        JSONB,
        comment="Фотографии в формате JSON: [{'url': '...', 'caption': '...', 'is_main': bool, 'order': int}]"
    )
    
    # Финансовая информация
    monthly_rent = Column(Numeric(12, 2), comment="Месячная арендная плата")
    security_deposit = Column(Numeric(12, 2), comment="Залог")
    utility_cost = Column(Numeric(10, 2), comment="Коммунальные платежи")
    currency = Column(String(3), default="RUB", nullable=False, comment="Валюта (ISO код)")
    
    # Дополнительная информация
    is_featured = Column(Boolean, default=False, comment="Рекомендуемая недвижимость")
    views_count = Column(Integer, default=0, comment="Количество просмотров")
    
    # Метаданные
    metadata_info = Column(
        JSONB,
        comment="Дополнительные метаданные в формате JSON"
    )
    
    # Связи
    photos_rel = relationship(
        "PropertyPhoto",
        back_populates="property",
        cascade="all, delete-orphan",
        order_by="PropertyPhoto.order_index"
    )
    
    features_rel = relationship(
        "PropertyFeatureAssignment",
        back_populates="property",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Property(id={self.id}, title='{self.title}', type={self.property_type.value})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "owner_id": str(self.owner_id),
            "title": self.title,
            "description": self.description,
            "property_type": self.property_type.value,
            "status": self.status.value,
            "condition": self.condition.value if self.condition else None,
            "address": self.address,
            "coordinates": self.coordinates,
            "total_area": float(self.total_area) if self.total_area else None,
            "living_area": float(self.living_area) if self.living_area else None,
            "kitchen_area": float(self.kitchen_area) if self.kitchen_area else None,
            "rooms_count": self.rooms_count,
            "bedrooms_count": self.bedrooms_count,
            "bathrooms_count": self.bathrooms_count,
            "floor": self.floor,
            "total_floors": self.total_floors,
            "year_built": self.year_built,
            "ceiling_height": float(self.ceiling_height) if self.ceiling_height else None,
            "heating_type": self.heating_type.value if self.heating_type else None,
            "has_elevator": self.has_elevator,
            "has_parking": self.has_parking,
            "has_balcony": self.has_balcony,
            "has_furniture": self.has_furniture,
            "amenities": self.amenities,
            "photos": self.photos,
            "monthly_rent": float(self.monthly_rent) if self.monthly_rent else None,
            "security_deposit": float(self.security_deposit) if self.security_deposit else None,
            "utility_cost": float(self.utility_cost) if self.utility_cost else None,
            "currency": self.currency,
            "is_featured": self.is_featured,
            "views_count": self.views_count,
            "metadata_info": self.metadata_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def full_address(self) -> str:
        """Полный адрес в текстовом формате"""
        if not self.address:
            return ""
        
        parts = []
        if self.address.get("street"):
            parts.append(self.address["street"])
        if self.address.get("city"):
            parts.append(self.address["city"])
        if self.address.get("postal_code"):
            parts.append(self.address["postal_code"])
        if self.address.get("country"):
            parts.append(self.address["country"])
        
        return ", ".join(parts)
    
    @property
    def price_per_sqm(self) -> Optional[float]:
        """Цена за квадратный метр"""
        if self.monthly_rent and self.total_area and self.total_area > 0:
            return float(self.monthly_rent / self.total_area)
        return None
    
    @property
    def is_available(self) -> bool:
        """Доступна ли недвижимость для аренды"""
        return self.status == PropertyStatus.AVAILABLE
    
    def increment_views(self):
        """Увеличить счетчик просмотров"""
        if self.views_count is None:
            self.views_count = 0
        self.views_count += 1


# Индексы для оптимизации запросов
Index('idx_property_owner_status', Property.owner_id, Property.status)
Index('idx_property_type_status', Property.property_type, Property.status)
Index('idx_property_rent_range', Property.monthly_rent)
Index('idx_property_area_range', Property.total_area)
Index('idx_property_location', Property.address.op('->>')('city'), Property.address.op('->>')('district'))
Index('idx_property_created_at', Property.created_at.desc())
Index('idx_property_featured', Property.is_featured, Property.status)
