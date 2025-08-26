"""
Модели для работы с фотографиями недвижимости
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.base import Base
from shared.database.models import TimestampMixin, UUIDMixin
import enum
from typing import Dict, Any, Optional


class PhotoType(enum.Enum):
    """Типы фотографий"""
    EXTERIOR = "exterior"         # Внешний вид
    INTERIOR = "interior"         # Интерьер
    KITCHEN = "kitchen"           # Кухня
    BATHROOM = "bathroom"         # Ванная комната
    BEDROOM = "bedroom"           # Спальня
    LIVING_ROOM = "living_room"   # Гостиная
    BALCONY = "balcony"          # Балкон/лоджия
    VIEW = "view"                # Вид из окна
    FLOOR_PLAN = "floor_plan"    # План этажа
    DOCUMENT = "document"        # Документы
    OTHER = "other"              # Прочее


class PropertyPhoto(Base, UUIDMixin, TimestampMixin):
    """
    Модель фотографий недвижимости
    """
    __tablename__ = "property_photos"
    
    # Связь с недвижимостью
    property_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("properties.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID недвижимости"
    )
    
    # Основная информация о фото
    url = Column(String(500), nullable=False, comment="URL фотографии")
    thumbnail_url = Column(String(500), comment="URL миниатюры")
    original_filename = Column(String(255), comment="Оригинальное имя файла")
    
    # Метаданные
    caption = Column(String(255), comment="Подпись к фотографии")
    alt_text = Column(String(255), comment="Альтернативный текст для accessibility")
    description = Column(Text, comment="Подробное описание фотографии")
    
    # Классификация
    photo_type = Column(
        String(50), 
        default=PhotoType.INTERIOR.value,
        comment="Тип фотографии"
    )
    room_name = Column(String(100), comment="Название комнаты")
    
    # Настройки отображения
    is_main = Column(Boolean, default=False, comment="Главная фотография")
    is_featured = Column(Boolean, default=False, comment="Рекомендуемая фотография")
    is_active = Column(Boolean, default=True, comment="Активна ли фотография")
    order_index = Column(Integer, default=0, comment="Порядок отображения")
    
    # Технические параметры
    width = Column(Integer, comment="Ширина изображения в пикселях")
    height = Column(Integer, comment="Высота изображения в пикселях")
    file_size = Column(Integer, comment="Размер файла в байтах")
    mime_type = Column(String(100), comment="MIME тип файла")
    
    # Связи
    property = relationship("Property", back_populates="photos_rel")
    
    def __repr__(self):
        return f"<PropertyPhoto(id={self.id}, property_id={self.property_id}, is_main={self.is_main})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "original_filename": self.original_filename,
            "caption": self.caption,
            "alt_text": self.alt_text,
            "description": self.description,
            "photo_type": self.photo_type,
            "room_name": self.room_name,
            "is_main": self.is_main,
            "is_featured": self.is_featured,
            "is_active": self.is_active,
            "order_index": self.order_index,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def aspect_ratio(self) -> Optional[float]:
        """Соотношение сторон изображения"""
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return None
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Размер файла в мегабайтах"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
    
    def is_landscape(self) -> bool:
        """Горизонтальная ориентация"""
        aspect_ratio = self.aspect_ratio
        return aspect_ratio is not None and aspect_ratio > 1.0
    
    def is_portrait(self) -> bool:
        """Вертикальная ориентация"""
        aspect_ratio = self.aspect_ratio
        return aspect_ratio is not None and aspect_ratio < 1.0
    
    def is_square(self) -> bool:
        """Квадратная ориентация"""
        aspect_ratio = self.aspect_ratio
        return aspect_ratio is not None and abs(aspect_ratio - 1.0) < 0.1


# Индексы для оптимизации
Index('idx_property_photo_property_main', PropertyPhoto.property_id, PropertyPhoto.is_main)
Index('idx_property_photo_property_active', PropertyPhoto.property_id, PropertyPhoto.is_active)
Index('idx_property_photo_order', PropertyPhoto.property_id, PropertyPhoto.order_index)
Index('idx_property_photo_type', PropertyPhoto.photo_type)
Index('idx_property_photo_featured', PropertyPhoto.is_featured, PropertyPhoto.is_active)
