"""
Модели для отслеживания взаимодействий с недвижимостью
Просмотры, избранное, поиски
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index, DateTime, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database.base import Base
from shared.database.models import TimestampMixin, UUIDMixin
import enum
from typing import Dict, Any, Optional
from datetime import datetime


class InteractionType(enum.Enum):
    """Типы взаимодействий"""
    VIEW = "view"                 # Просмотр
    FAVORITE = "favorite"         # Добавление в избранное
    CONTACT = "contact"           # Запрос контактов
    INQUIRY = "inquiry"           # Запрос информации
    VISIT_REQUEST = "visit_request"  # Запрос на просмотр
    SHARE = "share"               # Поделиться
    REPORT = "report"             # Жалоба


class PropertyView(Base, UUIDMixin, TimestampMixin):
    """
    Модель для отслеживания просмотров недвижимости
    """
    __tablename__ = "property_views"
    
    # Связи
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID недвижимости"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID пользователя (null для анонимных)"
    )
    
    # Информация о сессии
    session_id = Column(String(100), comment="ID сессии")
    ip_address = Column(String(45), comment="IP адрес")
    user_agent = Column(Text, comment="User Agent браузера")
    
    # Геолокация
    country = Column(String(2), comment="Код страны")
    city = Column(String(100), comment="Город")
    
    # Источник перехода
    referrer = Column(String(500), comment="Источник перехода")
    utm_source = Column(String(100), comment="UTM источник")
    utm_medium = Column(String(100), comment="UTM канал")
    utm_campaign = Column(String(100), comment="UTM кампания")
    
    # Детали просмотра
    duration_seconds = Column(Integer, comment="Длительность просмотра в секундах")
    pages_viewed = Column(Integer, default=1, comment="Количество просмотренных страниц")
    photos_viewed = Column(Integer, default=0, comment="Количество просмотренных фото")
    
    # Устройство
    device_type = Column(String(20), comment="Тип устройства (desktop, mobile, tablet)")
    browser = Column(String(50), comment="Браузер")
    os = Column(String(50), comment="Операционная система")
    
    # Связи
    property = relationship("Property")
    
    def __repr__(self):
        return f"<PropertyView(id={self.id}, property_id={self.property_id}, user_id={self.user_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "country": self.country,
            "city": self.city,
            "referrer": self.referrer,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "duration_seconds": self.duration_seconds,
            "pages_viewed": self.pages_viewed,
            "photos_viewed": self.photos_viewed,
            "device_type": self.device_type,
            "browser": self.browser,
            "os": self.os,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PropertyFavorite(Base, UUIDMixin, TimestampMixin):
    """
    Модель избранной недвижимости
    """
    __tablename__ = "property_favorites"
    
    # Связи
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID недвижимости"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="ID пользователя"
    )
    
    # Дополнительная информация
    notes = Column(Text, comment="Заметки пользователя")
    is_active = Column(Boolean, default=True, comment="Активно ли в избранном")
    
    # Уведомления
    notify_price_change = Column(Boolean, default=True, comment="Уведомлять об изменении цены")
    notify_status_change = Column(Boolean, default=True, comment="Уведомлять об изменении статуса")
    
    # Связи
    property = relationship("Property")
    
    # Уникальность
    __table_args__ = (
        UniqueConstraint('property_id', 'user_id', name='uq_property_favorite'),
    )
    
    def __repr__(self):
        return f"<PropertyFavorite(property_id={self.property_id}, user_id={self.user_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "user_id": str(self.user_id),
            "notes": self.notes,
            "is_active": self.is_active,
            "notify_price_change": self.notify_price_change,
            "notify_status_change": self.notify_status_change,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PropertyInquiry(Base, UUIDMixin, TimestampMixin):
    """
    Модель запросов информации о недвижимости
    """
    __tablename__ = "property_inquiries"
    
    # Связи
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID недвижимости"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID пользователя"
    )
    
    # Контактная информация (для анонимных запросов)
    contact_name = Column(String(200), comment="Имя контактного лица")
    contact_email = Column(String(255), comment="Email для связи")
    contact_phone = Column(String(20), comment="Телефон для связи")
    
    # Детали запроса
    inquiry_type = Column(
        String(50),
        default=InteractionType.INQUIRY.value,
        comment="Тип запроса"
    )
    
    subject = Column(String(255), comment="Тема запроса")
    message = Column(Text, comment="Текст запроса")
    
    # Предпочтения
    preferred_contact_method = Column(String(20), comment="Предпочитаемый способ связи")
    preferred_contact_time = Column(String(100), comment="Предпочитаемое время связи")
    
    # Статус обработки
    status = Column(String(20), default="new", comment="Статус обработки")
    processed_at = Column(DateTime(timezone=True), comment="Время обработки")
    processed_by = Column(UUID(as_uuid=True), comment="ID обработавшего сотрудника")
    
    # Ответ
    response = Column(Text, comment="Ответ на запрос")
    response_sent_at = Column(DateTime(timezone=True), comment="Время отправки ответа")
    
    # Связи
    property = relationship("Property")
    
    def __repr__(self):
        return f"<PropertyInquiry(id={self.id}, property_id={self.property_id}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "inquiry_type": self.inquiry_type,
            "subject": self.subject,
            "message": self.message,
            "preferred_contact_method": self.preferred_contact_method,
            "preferred_contact_time": self.preferred_contact_time,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processed_by": str(self.processed_by) if self.processed_by else None,
            "response": self.response,
            "response_sent_at": self.response_sent_at.isoformat() if self.response_sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_processed(self) -> bool:
        """Обработан ли запрос"""
        return self.status != "new"
    
    @property
    def response_time_hours(self) -> Optional[float]:
        """Время ответа в часах"""
        if self.processed_at and self.created_at:
            delta = self.processed_at - self.created_at
            return delta.total_seconds() / 3600
        return None


class SearchQuery(Base, UUIDMixin, TimestampMixin):
    """
    Модель для отслеживания поисковых запросов
    """
    __tablename__ = "search_queries"
    
    # Пользователь
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID пользователя"
    )
    
    session_id = Column(String(100), index=True, comment="ID сессии")
    
    # Параметры поиска
    query_text = Column(String(500), comment="Текст поискового запроса")
    filters = Column(
        JSONB,
        comment="Фильтры поиска в формате JSON"
    )
    
    # Результаты
    results_count = Column(Integer, comment="Количество найденных результатов")
    results_clicked = Column(Integer, default=0, comment="Количество кликов по результатам")
    
    # Геолокация
    location = Column(
        JSONB,
        comment="Геолокация поиска в формате JSON"
    )
    
    def __repr__(self):
        return f"<SearchQuery(id={self.id}, query='{self.query_text}', results={self.results_count})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "query_text": self.query_text,
            "filters": self.filters,
            "results_count": self.results_count,
            "results_clicked": self.results_clicked,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Индексы для оптимизации
Index('idx_property_view_property_date', PropertyView.property_id, PropertyView.created_at.desc())
Index('idx_property_view_user_date', PropertyView.user_id, PropertyView.created_at.desc())
Index('idx_property_view_session', PropertyView.session_id)
Index('idx_property_view_ip', PropertyView.ip_address)

Index('idx_property_favorite_user', PropertyFavorite.user_id, PropertyFavorite.is_active)
Index('idx_property_favorite_property', PropertyFavorite.property_id, PropertyFavorite.is_active)

Index('idx_property_inquiry_status', PropertyInquiry.status, PropertyInquiry.created_at.desc())
Index('idx_property_inquiry_property', PropertyInquiry.property_id, PropertyInquiry.status)
Index('idx_property_inquiry_processed', PropertyInquiry.processed_by, PropertyInquiry.processed_at)

Index('idx_search_query_user', SearchQuery.user_id, SearchQuery.created_at.desc())
Index('idx_search_query_session', SearchQuery.session_id, SearchQuery.created_at.desc())
Index('idx_search_query_text', SearchQuery.query_text)
