"""
Модели для работы с владельцами недвижимости
"""

from sqlalchemy import Column, String, Text, Boolean, Date, Index, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from shared.database.base import Base
from shared.database.models import TimestampMixin, UUIDMixin
import enum
from typing import Dict, Any, Optional
from datetime import date


class OwnerType(enum.Enum):
    """Типы владельцев"""
    INDIVIDUAL = "individual"     # Физическое лицо
    COMPANY = "company"          # Юридическое лицо
    AGENCY = "agency"            # Агентство недвижимости


class PropertyOwner(Base, UUIDMixin, TimestampMixin):
    """
    Модель владельца недвижимости
    """
    __tablename__ = "property_owners"
    
    # Основная информация
    owner_type = Column(
        String(20),
        nullable=False,
        default=OwnerType.INDIVIDUAL.value,
        index=True,
        comment="Тип владельца"
    )
    
    # Персональные данные (для физлиц)
    first_name = Column(String(100), comment="Имя")
    last_name = Column(String(100), comment="Фамилия")
    middle_name = Column(String(100), comment="Отчество")
    birth_date = Column(Date, comment="Дата рождения")
    
    # Данные организации (для юрлиц)
    company_name = Column(String(255), comment="Название организации")
    company_legal_name = Column(String(255), comment="Полное юридическое название")
    tax_id = Column(String(20), comment="ИНН")
    registration_number = Column(String(50), comment="ОГРН")
    
    # Контактная информация
    email = Column(String(255), index=True, comment="Email")
    phone = Column(String(20), comment="Телефон")
    phone_additional = Column(String(20), comment="Дополнительный телефон")
    
    # Адрес
    address = Column(
        JSONB,
        comment="Адрес владельца в формате JSON"
    )
    
    # Документы
    passport_data = Column(
        JSONB,
        comment="Паспортные данные в формате JSON: {series, number, issued_by, issued_date}"
    )
    
    # Банковские реквизиты
    bank_details = Column(
        JSONB,
        comment="Банковские реквизиты в формате JSON"
    )
    
    # Настройки
    is_active = Column(Boolean, default=True, comment="Активен ли владелец")
    is_verified = Column(Boolean, default=False, comment="Верифицирован ли владелец")
    
    # Предпочтения
    preferred_contact_method = Column(String(20), default="email", comment="Предпочитаемый способ связи")
    notification_settings = Column(
        JSONB,
        comment="Настройки уведомлений"
    )
    
    # Дополнительная информация
    notes = Column(Text, comment="Заметки о владельце")
    rating = Column(Integer, comment="Рейтинг владельца (1-5)")
    
    # Связи
    properties = relationship("Property", foreign_keys="Property.owner_id", lazy="select")
    
    def __repr__(self):
        if self.owner_type == OwnerType.INDIVIDUAL.value:
            return f"<PropertyOwner(id={self.id}, name='{self.full_name}')>"
        else:
            return f"<PropertyOwner(id={self.id}, company='{self.company_name}')>"
    
    @property
    def full_name(self) -> str:
        """Полное имя владельца"""
        if self.owner_type == OwnerType.INDIVIDUAL.value:
            parts = [self.last_name, self.first_name, self.middle_name]
            return " ".join(filter(None, parts))
        return self.company_name or ""
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя"""
        if self.owner_type == OwnerType.INDIVIDUAL.value:
            if self.first_name and self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.full_name
        return self.company_name or ""
    
    @property
    def age(self) -> Optional[int]:
        """Возраст владельца"""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        return {
            "id": str(self.id),
            "owner_type": self.owner_type,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "age": self.age,
            "company_name": self.company_name,
            "company_legal_name": self.company_legal_name,
            "tax_id": self.tax_id,
            "registration_number": self.registration_number,
            "email": self.email,
            "phone": self.phone,
            "phone_additional": self.phone_additional,
            "address": self.address,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "preferred_contact_method": self.preferred_contact_method,
            "notification_settings": self.notification_settings,
            "notes": self.notes,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Индексы для оптимизации
Index('idx_property_owner_type_active', PropertyOwner.owner_type, PropertyOwner.is_active)
Index('idx_property_owner_email', PropertyOwner.email)
Index('idx_property_owner_phone', PropertyOwner.phone)
Index('idx_property_owner_tax_id', PropertyOwner.tax_id)
Index('idx_property_owner_name', PropertyOwner.last_name, PropertyOwner.first_name)
Index('idx_property_owner_company', PropertyOwner.company_name)
