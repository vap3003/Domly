"""
Базовые модели для всех сервисов
Общие поля и миксины
"""

from sqlalchemy import Column, String, DateTime, Boolean, UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
import uuid


class TimestampMixin:
    """
    Mixin для добавления временных меток
    """
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="Время создания записи"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Время последнего обновления записи"
    )


class UUIDMixin:
    """
    Mixin для добавления UUID первичного ключа
    """
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор записи"
    )


class SoftDeleteMixin:
    """
    Mixin для мягкого удаления записей
    """
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Флаг мягкого удаления"
    )
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время мягкого удаления"
    )


class UserTrackingMixin:
    """
    Mixin для отслеживания пользователей, создавших/изменивших запись
    """
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID пользователя, создавшего запись"
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID пользователя, последним изменившего запись"
    )


class BaseModel(UUIDMixin, TimestampMixin):
    """
    Базовая модель со стандартными полями
    """
    
    @declared_attr
    def __tablename__(cls):
        # Автоматическое создание имени таблицы из имени класса
        return cls.__name__.lower() + 's'
    
    def to_dict(self):
        """
        Преобразование модели в словарь
        
        Returns:
            dict: Словарь с данными модели
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        """Строковое представление модели"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class AuditableModel(BaseModel, UserTrackingMixin, SoftDeleteMixin):
    """
    Модель с полным аудитом (временные метки, пользователи, мягкое удаление)
    """
    pass
