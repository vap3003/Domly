"""
Модели для работы с характеристиками и удобствами недвижимости
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.base import Base
from shared.database.models import TimestampMixin, UUIDMixin
import enum
from typing import Dict, Any, List


class FeatureCategory(enum.Enum):
    """Категории характеристик"""
    AMENITY = "amenity"           # Удобства
    UTILITY = "utility"           # Коммуникации
    SECURITY = "security"         # Безопасность
    TRANSPORT = "transport"       # Транспорт
    INFRASTRUCTURE = "infrastructure"  # Инфраструктура
    BUILDING = "building"         # Здание
    INTERIOR = "interior"         # Интерьер
    EXTERIOR = "exterior"         # Экстерьер
    APPLIANCE = "appliance"       # Техника
    OTHER = "other"               # Прочее


class PropertyFeature(Base, UUIDMixin, TimestampMixin):
    """
    Справочник характеристик недвижимости
    """
    __tablename__ = "property_features"
    
    # Основная информация
    name = Column(String(100), nullable=False, unique=True, comment="Название характеристики")
    description = Column(Text, comment="Описание характеристики")
    
    # Категоризация
    category = Column(
        String(50), 
        nullable=False,
        default=FeatureCategory.AMENITY.value,
        index=True,
        comment="Категория характеристики"
    )
    subcategory = Column(String(50), comment="Подкатегория")
    
    # Настройки
    is_active = Column(Boolean, default=True, comment="Активна ли характеристика")
    is_popular = Column(Boolean, default=False, comment="Популярная характеристика")
    
    # Локализация
    name_en = Column(String(100), comment="Название на английском")
    name_ru = Column(String(100), comment="Название на русском")
    
    # Иконка и отображение
    icon = Column(String(100), comment="CSS класс или URL иконки")
    color = Column(String(7), comment="Цвет в формате HEX")
    
    # Связи
    property_assignments = relationship(
        "PropertyFeatureAssignment",
        back_populates="feature",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<PropertyFeature(id={self.id}, name='{self.name}', category={self.category})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "is_active": self.is_active,
            "is_popular": self.is_popular,
            "name_en": self.name_en,
            "name_ru": self.name_ru,
            "icon": self.icon,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PropertyFeatureAssignment(Base, UUIDMixin, TimestampMixin):
    """
    Связь между недвижимостью и характеристиками (многие ко многим)
    """
    __tablename__ = "property_feature_assignments"
    
    # Связи
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID недвижимости"
    )
    
    feature_id = Column(
        UUID(as_uuid=True),
        ForeignKey("property_features.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID характеристики"
    )
    
    # Дополнительные данные для связи
    value = Column(String(255), comment="Значение характеристики (если применимо)")
    notes = Column(Text, comment="Дополнительные заметки")
    
    # Настройки отображения
    is_highlighted = Column(Boolean, default=False, comment="Выделить при отображении")
    display_order = Column(Integer, default=0, comment="Порядок отображения")
    
    # Связи
    property = relationship("Property", back_populates="features_rel")
    feature = relationship("PropertyFeature", back_populates="property_assignments")
    
    # Уникальность связи
    __table_args__ = (
        UniqueConstraint('property_id', 'feature_id', name='uq_property_feature'),
    )
    
    def __repr__(self):
        return f"<PropertyFeatureAssignment(property_id={self.property_id}, feature_id={self.feature_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "feature_id": str(self.feature_id),
            "value": self.value,
            "notes": self.notes,
            "is_highlighted": self.is_highlighted,
            "display_order": self.display_order,
            "feature": self.feature.to_dict() if self.feature else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PropertyAmenity(Base, UUIDMixin, TimestampMixin):
    """
    Дополнительная модель для быстрого доступа к популярным удобствам
    (денормализация для производительности)
    """
    __tablename__ = "property_amenities"
    
    # Связь с недвижимостью
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID недвижимости"
    )
    
    # Популярные удобства (boolean поля для быстрых запросов)
    has_parking = Column(Boolean, default=False, comment="Парковка")
    has_elevator = Column(Boolean, default=False, comment="Лифт")
    has_balcony = Column(Boolean, default=False, comment="Балкон/лоджия")
    has_air_conditioning = Column(Boolean, default=False, comment="Кондиционер")
    has_heating = Column(Boolean, default=False, comment="Отопление")
    has_internet = Column(Boolean, default=False, comment="Интернет")
    has_cable_tv = Column(Boolean, default=False, comment="Кабельное ТВ")
    has_washing_machine = Column(Boolean, default=False, comment="Стиральная машина")
    has_dishwasher = Column(Boolean, default=False, comment="Посудомоечная машина")
    has_refrigerator = Column(Boolean, default=False, comment="Холодильник")
    has_microwave = Column(Boolean, default=False, comment="Микроволновка")
    has_furniture = Column(Boolean, default=False, comment="Мебель")
    has_gym = Column(Boolean, default=False, comment="Спортзал")
    has_pool = Column(Boolean, default=False, comment="Бассейн")
    has_security = Column(Boolean, default=False, comment="Охрана")
    has_concierge = Column(Boolean, default=False, comment="Консьерж")
    has_garden = Column(Boolean, default=False, comment="Сад")
    has_terrace = Column(Boolean, default=False, comment="Терраса")
    pets_allowed = Column(Boolean, default=False, comment="Разрешены животные")
    smoking_allowed = Column(Boolean, default=False, comment="Разрешено курение")
    
    # Связь
    property = relationship("Property")
    
    def __repr__(self):
        return f"<PropertyAmenity(property_id={self.property_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "property_id": str(self.property_id),
            "has_parking": self.has_parking,
            "has_elevator": self.has_elevator,
            "has_balcony": self.has_balcony,
            "has_air_conditioning": self.has_air_conditioning,
            "has_heating": self.has_heating,
            "has_internet": self.has_internet,
            "has_cable_tv": self.has_cable_tv,
            "has_washing_machine": self.has_washing_machine,
            "has_dishwasher": self.has_dishwasher,
            "has_refrigerator": self.has_refrigerator,
            "has_microwave": self.has_microwave,
            "has_furniture": self.has_furniture,
            "has_gym": self.has_gym,
            "has_pool": self.has_pool,
            "has_security": self.has_security,
            "has_concierge": self.has_concierge,
            "has_garden": self.has_garden,
            "has_terrace": self.has_terrace,
            "pets_allowed": self.pets_allowed,
            "smoking_allowed": self.smoking_allowed,
        }
    
    def get_active_amenities(self) -> List[str]:
        """Получить список активных удобств"""
        amenities = []
        amenity_map = {
            "has_parking": "Парковка",
            "has_elevator": "Лифт",
            "has_balcony": "Балкон",
            "has_air_conditioning": "Кондиционер",
            "has_heating": "Отопление",
            "has_internet": "Интернет",
            "has_cable_tv": "Кабельное ТВ",
            "has_washing_machine": "Стиральная машина",
            "has_dishwasher": "Посудомоечная машина",
            "has_refrigerator": "Холодильник",
            "has_microwave": "Микроволновка",
            "has_furniture": "Мебель",
            "has_gym": "Спортзал",
            "has_pool": "Бассейн",
            "has_security": "Охрана",
            "has_concierge": "Консьерж",
            "has_garden": "Сад",
            "has_terrace": "Терраса",
            "pets_allowed": "Разрешены животные",
            "smoking_allowed": "Разрешено курение",
        }
        
        for field, name in amenity_map.items():
            if getattr(self, field, False):
                amenities.append(name)
        
        return amenities


# Индексы для оптимизации
Index('idx_property_feature_category', PropertyFeature.category, PropertyFeature.is_active)
Index('idx_property_feature_popular', PropertyFeature.is_popular, PropertyFeature.is_active)
Index('idx_property_feature_assignment_property', PropertyFeatureAssignment.property_id)
Index('idx_property_feature_assignment_feature', PropertyFeatureAssignment.feature_id)
Index('idx_property_amenity_parking', PropertyAmenity.has_parking)
Index('idx_property_amenity_elevator', PropertyAmenity.has_elevator)
Index('idx_property_amenity_furniture', PropertyAmenity.has_furniture)
