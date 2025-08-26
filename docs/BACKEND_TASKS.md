# План реализации Backend для системы управления недвижимостью

## Общая информация
- **Технологии:** Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0+, PostgreSQL, Redis, Celery
- **Архитектура:** Микросервисная
- **Время реализации:** 8-10 недель
- **Команда:** 2-3 backend разработчика

## Фаза 1: Базовая инфраструктура (Неделя 1-2)

### Задача 1.1: Настройка проектной структуры
**Приоритет:** Критический
**Время:** 2 дня
**Исполнитель:** Senior Backend Developer

**Детальные шаги:**
1. Создать корневую структуру проекта:
```bash
mkdir -p property_management/{services,shared,docs,scripts}
cd property_management
```

2. Создать структуру для каждого сервиса:
```bash
# Property Management Service
mkdir -p services/property-service/app/{api/endpoints,core,models,schemas,services,tests}

# Tenant Management Service  
mkdir -p services/tenant-service/app/{api/endpoints,core,models,schemas,services,tests}

# Monitoring Service
mkdir -p services/monitoring-service/app/{api/endpoints,core,models,schemas,services,tests}

# API Gateway
mkdir -p services/api-gateway/app/{api,core,middleware,tests}

# Shared modules
mkdir -p shared/{database,auth,utils,schemas}
```

3. Создать базовые файлы конфигурации:
```bash
# В каждом сервисе
touch services/*/requirements.txt
touch services/*/Dockerfile
touch services/*/.env.example
touch services/*/app/main.py
touch services/*/app/__init__.py
```

**Критерии приемки:**
- ✅ Создана полная структура проекта
- ✅ Все необходимые директории существуют
- ✅ Базовые конфигурационные файлы созданы

### Задача 1.2: Docker и окружение разработки
**Приоритет:** Критический
**Время:** 1 день
**Исполнитель:** DevOps/Backend Developer

**Детальные шаги:**
1. Создать `docker-compose.yml` в корне проекта:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: property_management
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

2. Создать базовый Dockerfile для сервисов:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

3. Создать `.env.example` файлы для каждого сервиса

**Критерии приемки:**
- ✅ Docker Compose успешно поднимает PostgreSQL и Redis
- ✅ Dockerfile'ы работают для всех сервисов
- ✅ Переменные окружения настроены

### Задача 1.3: Базовые core модули
**Приоритет:** Критический  
**Время:** 2 дня
**Исполнитель:** Senior Backend Developer

**Детальные шаги:**
1. Создать `shared/database/base.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os

DATABASE_URL = os.getenv("DATABASE_URL")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

2. Создать `shared/auth/security.py`:
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

3. Создать базовые конфигурационные классы для каждого сервиса

**Критерии приемки:**
- ✅ База данных подключается корректно
- ✅ Аутентификация работает
- ✅ Конфигурация загружается из переменных окружения

## Фаза 2: Property Management Service (Неделя 2-3)

### Задача 2.1: SQLAlchemy модели для недвижимости
**Приоритет:** Высокий
**Время:** 2 дня
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Создать `services/property-service/app/models/property.py`:
```python
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid
import enum

class PropertyType(enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    OFFICE = "office"

class PropertyStatus(enum.Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"

class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    property_type = Column(Enum(PropertyType), nullable=False)
    address = Column(JSONB, nullable=False)  # {street, city, postal_code, country}
    coordinates = Column(JSONB)  # {lat, lng}
    total_area = Column(Numeric(10, 2))
    rooms_count = Column(Integer)
    floor = Column(Integer)
    total_floors = Column(Integer)
    year_built = Column(Integer)
    amenities = Column(JSONB)  # ["parking", "elevator", "balcony"]
    photos = Column(JSONB)  # [{"url": "...", "caption": "..."}]
    status = Column(Enum(PropertyStatus), default=PropertyStatus.AVAILABLE)
    monthly_rent = Column(Numeric(10, 2))
    currency = Column(String(3), default="RUB")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Property(id={self.id}, title={self.title})>"
```

2. Создать дополнительные модели:
```python
class PropertyPhoto(Base):
    __tablename__ = "property_photos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    url = Column(String(500), nullable=False)
    caption = Column(String(255))
    is_main = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PropertyFeature(Base):
    __tablename__ = "property_features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # "amenity", "utility", "security"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Критерии приемки:**
- ✅ Все модели созданы и соответствуют схеме БД
- ✅ Enum типы корректно работают
- ✅ JSONB поля настроены для PostgreSQL
- ✅ Связи между таблицами настроены

### Задача 2.2: Pydantic схемы для валидации
**Приоритет:** Высокий
**Время:** 1 день
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Создать `services/property-service/app/schemas/property.py`:
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PropertyType(str, Enum):
    apartment = "apartment"
    house = "house"
    commercial = "commercial"
    office = "office"

class PropertyStatus(str, Enum):
    available = "available"
    rented = "rented"
    maintenance = "maintenance"
    inactive = "inactive"

class AddressSchema(BaseModel):
    street: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., regex=r'^\d{6}$')
    country: str = Field(default="Russia", max_length=50)

class CoordinatesSchema(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

class PropertyPhotoSchema(BaseModel):
    url: str = Field(..., max_length=500)
    caption: Optional[str] = Field(None, max_length=255)
    is_main: bool = False

class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    property_type: PropertyType
    address: AddressSchema
    coordinates: Optional[CoordinatesSchema] = None
    total_area: Optional[float] = Field(None, gt=0, le=10000)
    rooms_count: Optional[int] = Field(None, ge=1, le=20)
    floor: Optional[int] = Field(None, ge=1, le=100)
    total_floors: Optional[int] = Field(None, ge=1, le=100)
    year_built: Optional[int] = Field(None, ge=1800, le=2030)
    amenities: Optional[List[str]] = []
    monthly_rent: float = Field(..., gt=0)
    currency: str = Field(default="RUB", regex=r'^[A-Z]{3}$')

    @validator('total_floors')
    def validate_floors(cls, v, values):
        if 'floor' in values and values['floor'] and v:
            if values['floor'] > v:
                raise ValueError('Floor cannot be greater than total floors')
        return v

class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[PropertyStatus] = None
    monthly_rent: Optional[float] = Field(None, gt=0)
    # ... остальные поля как Optional

class PropertyResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    property_type: PropertyType
    address: Dict[str, Any]
    status: PropertyStatus
    monthly_rent: float
    currency: str
    photos: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

**Критерии приемки:**
- ✅ Все схемы валидации работают корректно
- ✅ Кастомные валидаторы функционируют
- ✅ Схемы покрывают все CRUD операции

### Задача 2.3: CRUD API endpoints
**Приоритет:** Высокий
**Время:** 2 дня
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Создать `services/property-service/app/services/property_service.py`:
```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.models.property import Property, PropertyPhoto
from app.schemas.property import PropertyCreate, PropertyUpdate
import uuid

class PropertyService:
    @staticmethod
    async def create_property(db: AsyncSession, property_data: PropertyCreate, owner_id: str) -> Property:
        property_dict = property_data.dict()
        property_dict['owner_id'] = uuid.UUID(owner_id)
        
        db_property = Property(**property_dict)
        db.add(db_property)
        await db.commit()
        await db.refresh(db_property)
        return db_property

    @staticmethod
    async def get_property(db: AsyncSession, property_id: str) -> Optional[Property]:
        result = await db.execute(
            select(Property)
            .options(selectinload(Property.photos))
            .where(Property.id == uuid.UUID(property_id))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_properties(
        db: AsyncSession, 
        owner_id: Optional[str] = None,
        property_type: Optional[str] = None,
        city: Optional[str] = None,
        min_rent: Optional[float] = None,
        max_rent: Optional[float] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Property]:
        query = select(Property)
        
        conditions = []
        if owner_id:
            conditions.append(Property.owner_id == uuid.UUID(owner_id))
        if property_type:
            conditions.append(Property.property_type == property_type)
        if city:
            conditions.append(Property.address['city'].astext == city)
        if min_rent:
            conditions.append(Property.monthly_rent >= min_rent)
        if max_rent:
            conditions.append(Property.monthly_rent <= max_rent)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_property(
        db: AsyncSession, 
        property_id: str, 
        property_update: PropertyUpdate
    ) -> Optional[Property]:
        result = await db.execute(
            select(Property).where(Property.id == uuid.UUID(property_id))
        )
        db_property = result.scalar_one_or_none()
        
        if not db_property:
            return None
            
        update_data = property_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_property, field, value)
            
        await db.commit()
        await db.refresh(db_property)
        return db_property

    @staticmethod
    async def delete_property(db: AsyncSession, property_id: str) -> bool:
        result = await db.execute(
            select(Property).where(Property.id == uuid.UUID(property_id))
        )
        db_property = result.scalar_one_or_none()
        
        if not db_property:
            return False
            
        await db.delete(db_property)
        await db.commit()
        return True
```

2. Создать `services/property-service/app/api/endpoints/properties.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.services.property_service import PropertyService
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from shared.database.base import get_db
from shared.auth.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Создание новой недвижимости"""
    try:
        property_obj = await PropertyService.create_property(
            db=db, 
            property_data=property_data, 
            owner_id=current_user["user_id"]
        )
        return property_obj
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating property: {str(e)}"
        )

@router.get("/", response_model=List[PropertyResponse])
async def get_properties(
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_rent: Optional[float] = Query(None, description="Minimum monthly rent"),
    max_rent: Optional[float] = Query(None, description="Maximum monthly rent"),
    skip: int = Query(0, ge=0, description="Number of properties to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of properties to return"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получение списка недвижимости с фильтрацией"""
    properties = await PropertyService.get_properties(
        db=db,
        owner_id=current_user["user_id"],
        property_type=property_type,
        city=city,
        min_rent=min_rent,
        max_rent=max_rent,
        skip=skip,
        limit=limit
    )
    return properties

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получение детальной информации о недвижимости"""
    property_obj = await PropertyService.get_property(db=db, property_id=property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    return property_obj

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: str,
    property_update: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновление информации о недвижимости"""
    property_obj = await PropertyService.update_property(
        db=db, 
        property_id=property_id, 
        property_update=property_update
    )
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    return property_obj

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Удаление недвижимости"""
    success = await PropertyService.delete_property(db=db, property_id=property_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
```

**Критерии приемки:**
- ✅ Все CRUD операции работают корректно
- ✅ Фильтрация и пагинация реализованы
- ✅ Обработка ошибок настроена
- ✅ Авторизация интегрирована

## Фаза 3: Tenant Management Service (Неделя 3-4)

### Задача 3.1: SQLAlchemy модели для арендаторов
**Приоритет:** Высокий
**Время:** 2 дня
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Создать модели в `services/tenant-service/app/models/`:

```python
# tenant.py
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    birth_date = Column(Date)
    passport_data = Column(JSONB)  # {series, number, issued_by, issued_date}
    employment_info = Column(JSONB)  # {company, position, salary, work_experience}
    emergency_contact = Column(JSONB)  # {name, phone, relationship}
    rating = Column(Numeric(3, 2), default=5.0)
    status = Column(Enum(TenantStatus), default=TenantStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# contract.py
class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to Property service
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    monthly_rent = Column(Numeric(10, 2), nullable=False)
    security_deposit = Column(Numeric(10, 2))
    payment_due_day = Column(Integer, default=1)
    terms = Column(Text)
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    signed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# payment.py
class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(50))
    transaction_id = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Критерии приемки:**
- ✅ Все модели созданы с правильными связями
- ✅ Enum типы определены для статусов
- ✅ JSONB поля настроены для сложных данных

### Задача 3.2: Celery для асинхронных задач
**Приоритет:** Средний
**Время:** 1 день
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Создать `services/tenant-service/app/core/celery_app.py`:
```python
from celery import Celery
import os

celery_app = Celery(
    "tenant_service",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379"),
    include=["app.tasks.payment_tasks", "app.tasks.notification_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-overdue-payments": {
            "task": "app.tasks.payment_tasks.check_overdue_payments",
            "schedule": 3600.0,  # Every hour
        },
        "send-payment-reminders": {
            "task": "app.tasks.payment_tasks.send_payment_reminders", 
            "schedule": 86400.0,  # Every day
        },
    },
)
```

2. Создать задачи в `services/tenant-service/app/tasks/`:
```python
# payment_tasks.py
from celery import current_app
from app.core.celery_app import celery_app
from app.services.payment_service import PaymentService
from shared.database.base import AsyncSessionLocal
import asyncio

@celery_app.task
def check_overdue_payments():
    """Проверка просроченных платежей"""
    async def _check_overdue():
        async with AsyncSessionLocal() as db:
            overdue_payments = await PaymentService.get_overdue_payments(db)
            for payment in overdue_payments:
                # Отправить уведомление
                send_overdue_notification.delay(str(payment.id))
    
    asyncio.run(_check_overdue())
    return f"Checked overdue payments"

@celery_app.task
def send_payment_reminders():
    """Отправка напоминаний о платежах"""
    async def _send_reminders():
        async with AsyncSessionLocal() as db:
            upcoming_payments = await PaymentService.get_upcoming_payments(db)
            for payment in upcoming_payments:
                send_payment_reminder_email.delay(str(payment.id))
    
    asyncio.run(_send_reminders())
    return f"Sent payment reminders"

@celery_app.task
def send_overdue_notification(payment_id: str):
    """Отправка уведомления о просрочке"""
    # Логика отправки уведомления
    return f"Sent overdue notification for payment {payment_id}"

@celery_app.task
def send_payment_reminder_email(payment_id: str):
    """Отправка напоминания по email"""
    # Логика отправки email
    return f"Sent reminder email for payment {payment_id}"
```

**Критерии приемки:**
- ✅ Celery настроен и работает с Redis
- ✅ Периодические задачи настроены
- ✅ Асинхронные задачи выполняются корректно

## Фаза 4: Monitoring & Analytics Service (Неделя 4-5)

### Задача 4.1: WebSocket для real-time мониторинга
**Приоритет:** Средний
**Время:** 2 дня
**Исполнитель:** Senior Backend Developer

**Детальные шаги:**
1. Создать `services/monitoring-service/app/api/websocket.py`:
```python
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(websocket)

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                await connection.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_metrics(self, metrics_data: dict):
        message = json.dumps({
            "type": "metrics_update",
            "data": metrics_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        await self.broadcast(message)

manager = ConnectionManager()

@router.websocket("/ws/monitoring/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Периодическая отправка метрик
            await asyncio.sleep(5)
            
            # Получить текущие метрики
            metrics = await get_current_metrics(user_id)
            await manager.send_personal_message(
                json.dumps({
                    "type": "metrics",
                    "data": metrics,
                    "timestamp": datetime.utcnow().isoformat()
                }), 
                user_id
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

2. Создать сервис аналитики:
```python
# services/analytics_service.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, List
from datetime import datetime, timedelta

class AnalyticsService:
    @staticmethod
    async def calculate_property_roi(property_id: str, db: AsyncSession) -> Dict:
        """Расчет ROI недвижимости"""
        # Получить данные о доходах и расходах
        revenue_data = await get_property_revenue(db, property_id)
        expenses_data = await get_property_expenses(db, property_id)
        
        total_revenue = sum(revenue_data)
        total_expenses = sum(expenses_data)
        roi = ((total_revenue - total_expenses) / total_expenses) * 100 if total_expenses > 0 else 0
        
        return {
            "property_id": property_id,
            "roi_percentage": round(roi, 2),
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": total_revenue - total_expenses
        }

    @staticmethod
    async def predict_vacancy_rate(property_data: Dict) -> float:
        """ML прогноз вакантности"""
        # Подготовка данных для модели
        features = np.array([[
            property_data.get('monthly_rent', 0),
            property_data.get('total_area', 0),
            property_data.get('rooms_count', 0),
            property_data.get('floor', 0),
        ]])
        
        # Простая модель (в реальности нужно обучить на исторических данных)
        model = LinearRegression()
        # model.fit(training_data, target_data)  # Обучение на исторических данных
        
        # Заглушка для демонстрации
        predicted_rate = np.random.uniform(0.05, 0.25)  # 5-25% вакантности
        
        return round(predicted_rate, 3)

    @staticmethod
    async def generate_occupancy_report(owner_id: str, db: AsyncSession) -> Dict:
        """Генерация отчета по заполняемости"""
        properties = await get_owner_properties(db, owner_id)
        
        total_properties = len(properties)
        occupied_properties = len([p for p in properties if p.status == "rented"])
        vacancy_rate = (total_properties - occupied_properties) / total_properties * 100 if total_properties > 0 else 0
        
        return {
            "total_properties": total_properties,
            "occupied_properties": occupied_properties,
            "vacant_properties": total_properties - occupied_properties,
            "occupancy_rate": round(100 - vacancy_rate, 2),
            "vacancy_rate": round(vacancy_rate, 2)
        }
```

**Критерии приемки:**
- ✅ WebSocket соединения работают стабильно
- ✅ Real-time метрики отправляются клиентам
- ✅ Базовая аналитика реализована

## Фаза 5: API Gateway и интеграции (Неделя 5-6)

### Задача 5.1: Создание API Gateway
**Приоритет:** Высокий
**Время:** 2 дня
**Исполнитель:** Senior Backend Developer

**Детальные шаги:**
1. Создать `services/api-gateway/app/main.py`:
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(title="Property Management API Gateway", version="1.0.0")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшн указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URLs микросервисов
PROPERTY_SERVICE_URL = os.getenv("PROPERTY_SERVICE_URL", "http://property-service:8000")
TENANT_SERVICE_URL = os.getenv("TENANT_SERVICE_URL", "http://tenant-service:8000")
MONITORING_SERVICE_URL = os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8000")

async def proxy_request(request: Request, service_url: str, path: str):
    """Проксирование запроса к микросервису"""
    url = f"{service_url}{path}"
    
    # Подготовка заголовков
    headers = dict(request.headers)
    headers.pop("host", None)
    
    async with httpx.AsyncClient() as client:
        if request.method == "GET":
            response = await client.get(url, headers=headers, params=request.query_params)
        elif request.method == "POST":
            body = await request.body()
            response = await client.post(url, headers=headers, content=body)
        elif request.method == "PUT":
            body = await request.body()
            response = await client.put(url, headers=headers, content=body)
        elif request.method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

# Роуты для Property Service
@app.api_route("/api/v1/properties/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def property_proxy(request: Request, path: str):
    return await proxy_request(request, PROPERTY_SERVICE_URL, f"/api/v1/properties/{path}")

# Роуты для Tenant Service
@app.api_route("/api/v1/tenants/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def tenant_proxy(request: Request, path: str):
    return await proxy_request(request, TENANT_SERVICE_URL, f"/api/v1/tenants/{path}")

# Роуты для Monitoring Service
@app.api_route("/api/v1/monitoring/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def monitoring_proxy(request: Request, path: str):
    return await proxy_request(request, MONITORING_SERVICE_URL, f"/api/v1/monitoring/{path}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services_health = {}
    
    async with httpx.AsyncClient() as client:
        # Проверка здоровья всех сервисов
        for service_name, service_url in [
            ("property", PROPERTY_SERVICE_URL),
            ("tenant", TENANT_SERVICE_URL), 
            ("monitoring", MONITORING_SERVICE_URL)
        ]:
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                services_health[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                services_health[service_name] = "unhealthy"
    
    return {
        "status": "healthy",
        "services": services_health
    }
```

**Критерии приемки:**
- ✅ API Gateway корректно проксирует запросы
- ✅ Health check работает для всех сервисов
- ✅ CORS настроен корректно

### Задача 5.2: Интеграция с внешними сервисами
**Приоритет:** Средний
**Время:** 2 дня
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Создать интеграцию с картами:
```python
# shared/integrations/maps_service.py
import httpx
import os
from typing import Dict, Optional

class MapsService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api"

    async def geocode_address(self, address: str) -> Optional[Dict]:
        """Получение координат по адресу"""
        url = f"{self.base_url}/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return {
                        "lat": location["lat"],
                        "lng": location["lng"]
                    }
        return None

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """Получение адреса по координатам"""
        url = f"{self.base_url}/geocode/json"
        params = {
            "latlng": f"{lat},{lng}",
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    return data["results"][0]["formatted_address"]
        return None
```

2. Создать интеграцию с платежными системами:
```python
# shared/integrations/payment_service.py
import httpx
import os
from typing import Dict
import uuid

class PaymentService:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.base_url = "https://api.stripe.com/v1"

    async def create_payment_intent(self, amount: float, currency: str = "rub") -> Dict:
        """Создание платежного намерения"""
        url = f"{self.base_url}/payment_intents"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "amount": int(amount * 100),  # Stripe использует копейки
            "currency": currency.lower(),
            "metadata": {
                "integration_check": "accept_a_payment"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)
            return response.json()

    async def confirm_payment(self, payment_intent_id: str) -> Dict:
        """Подтверждение платежа"""
        url = f"{self.base_url}/payment_intents/{payment_intent_id}/confirm"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            return response.json()
```

**Критерии приемки:**
- ✅ Интеграция с картами работает
- ✅ Платежная система интегрирована
- ✅ Обработка ошибок настроена

## Фаза 6: Тестирование и документация (Неделя 6-7)

### Задача 6.1: Unit и Integration тесты
**Приоритет:** Высокий
**Время:** 3 дня
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Создать базовую конфигурацию тестов:
```python
# conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from shared.database.base import Base, get_db

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5433/test_property_db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def test_db(test_engine):
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
async def client(test_db):
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

2. Создать тесты для Property Service:
```python
# tests/test_property_service.py
import pytest
from app.services.property_service import PropertyService
from app.schemas.property import PropertyCreate, PropertyUpdate

@pytest.mark.asyncio
async def test_create_property(test_db):
    """Тест создания недвижимости"""
    property_data = PropertyCreate(
        title="Test Apartment",
        property_type="apartment",
        address={
            "street": "Test Street 123",
            "city": "Moscow",
            "postal_code": "123456",
            "country": "Russia"
        },
        monthly_rent=50000.0,
        total_area=75.5,
        rooms_count=3
    )
    
    property_obj = await PropertyService.create_property(
        db=test_db,
        property_data=property_data,
        owner_id="550e8400-e29b-41d4-a716-446655440000"
    )
    
    assert property_obj.title == "Test Apartment"
    assert property_obj.property_type.value == "apartment"
    assert property_obj.monthly_rent == 50000.0

@pytest.mark.asyncio
async def test_get_properties_with_filters(test_db):
    """Тест получения недвижимости с фильтрами"""
    # Создать тестовые данные
    properties = await PropertyService.get_properties(
        db=test_db,
        property_type="apartment",
        city="Moscow",
        min_rent=40000.0,
        max_rent=60000.0
    )
    
    assert isinstance(properties, list)
    for prop in properties:
        assert prop.property_type.value == "apartment"
        assert 40000.0 <= prop.monthly_rent <= 60000.0

@pytest.mark.asyncio
async def test_update_property(test_db):
    """Тест обновления недвижимости"""
    # Сначала создать недвижимость
    property_data = PropertyCreate(
        title="Original Title",
        property_type="apartment",
        address={
            "street": "Test Street 123",
            "city": "Moscow",
            "postal_code": "123456"
        },
        monthly_rent=50000.0
    )
    
    created_property = await PropertyService.create_property(
        db=test_db,
        property_data=property_data,
        owner_id="550e8400-e29b-41d4-a716-446655440000"
    )
    
    # Обновить недвижимость
    update_data = PropertyUpdate(title="Updated Title", monthly_rent=55000.0)
    updated_property = await PropertyService.update_property(
        db=test_db,
        property_id=str(created_property.id),
        property_update=update_data
    )
    
    assert updated_property.title == "Updated Title"
    assert updated_property.monthly_rent == 55000.0
```

3. Создать API тесты:
```python
# tests/test_property_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_property_api(client: AsyncClient):
    """Тест API создания недвижимости"""
    property_data = {
        "title": "API Test Apartment",
        "property_type": "apartment",
        "address": {
            "street": "API Test Street 456",
            "city": "Moscow",
            "postal_code": "654321"
        },
        "monthly_rent": 45000.0,
        "total_area": 65.0,
        "rooms_count": 2
    }
    
    response = await client.post("/api/v1/properties/", json=property_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "API Test Apartment"
    assert data["property_type"] == "apartment"

@pytest.mark.asyncio
async def test_get_properties_api(client: AsyncClient):
    """Тест API получения списка недвижимости"""
    response = await client.get("/api/v1/properties/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_property_validation_error(client: AsyncClient):
    """Тест валидации данных недвижимости"""
    invalid_data = {
        "title": "",  # Пустой title
        "property_type": "invalid_type",
        "monthly_rent": -1000  # Отрицательная аренда
    }
    
    response = await client.post("/api/v1/properties/", json=invalid_data)
    
    assert response.status_code == 422
    error_data = response.json()
    assert "detail" in error_data
```

**Критерии приемки:**
- ✅ Unit тесты покрывают основную логику
- ✅ Integration тесты проверяют API endpoints
- ✅ Тесты валидации данных работают
- ✅ Покрытие тестами не менее 80%

### Задача 6.2: Настройка автодокументации
**Приоритет:** Средний
**Время:** 1 день
**Исполнитель:** Backend Developer

**Детальные шаги:**
1. Настроить OpenAPI документацию в каждом сервисе:
```python
# В каждом main.py сервиса
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Property Management Service",
    description="Микросервис для управления недвижимостью",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Property Management API",
        version="1.0.0",
        description="REST API для управления недвижимостью",
        routes=app.routes,
    )
    
    # Добавить дополнительную информацию
    openapi_schema["info"]["contact"] = {
        "name": "Property Management Team",
        "email": "dev@property-management.com"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

2. Добавить подробные описания к endpoints:
```python
@router.post("/", 
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой недвижимости",
    description="Создает новый объект недвижимости с валидацией данных",
    responses={
        201: {"description": "Недвижимость успешно создана"},
        400: {"description": "Ошибка валидации данных"},
        401: {"description": "Не авторизован"}
    }
)
async def create_property(
    property_data: PropertyCreate = Body(..., description="Данные для создания недвижимости"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Создание нового объекта недвижимости.
    
    - **title**: Название недвижимости (обязательно)
    - **property_type**: Тип недвижимости (apartment, house, commercial, office)
    - **address**: Полный адрес объекта
    - **monthly_rent**: Месячная арендная плата в рублях
    - **total_area**: Общая площадь в квадратных метрах
    - **rooms_count**: Количество комнат
    """
    # ... логика создания
```

**Критерии приемки:**
- ✅ Swagger UI доступен для всех сервисов
- ✅ Все endpoints документированы
- ✅ Схемы данных описаны подробно

## Фаза 7: Финализация и деплой (Неделя 7-8)

### Задача 7.1: Настройка мониторинга и логирования
**Приоритет:** Высокий
**Время:** 2 дня
**Исполнитель:** DevOps/Backend Developer

**Детальные шаги:**
1. Настроить структурированное логирование:
```python
# shared/utils/logging.py
import structlog
import logging
import sys

def configure_logging():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
```

2. Добавить middleware для логирования запросов:
```python
# shared/middleware/logging_middleware.py
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent")
        )
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            process_time=round(process_time, 4)
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
```

3. Настроить Prometheus метрики:
```python
# shared/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Метрики HTTP запросов
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Метрики базы данных
DB_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections'
)

# Метрики недвижимости
PROPERTIES_TOTAL = Gauge(
    'properties_total',
    'Total number of properties'
)

VACANCY_RATE = Gauge(
    'vacancy_rate_percentage',
    'Current vacancy rate percentage'
)

async def track_request_metrics(request: Request, response: Response, process_time: float):
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
```

**Критерии приемки:**
- ✅ Структурированные логи настроены
- ✅ Prometheus метрики собираются
- ✅ Request ID трекинг работает

### Задача 7.2: Финальная настройка Docker Compose
**Приоритет:** Высокий
**Время:** 1 день
**Исполнитель:** DevOps Developer

**Детальные шаги:**
1. Создать production-ready docker-compose.yml:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-property_management}
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-admin}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:6-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  api-gateway:
    build: 
      context: ./services/api-gateway
      dockerfile: Dockerfile
    ports:
      - "${API_GATEWAY_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-password}@postgres:5432/${POSTGRES_DB:-property_management}
      - REDIS_URL=redis://redis:6379
      - PROPERTY_SERVICE_URL=http://property-service:8000
      - TENANT_SERVICE_URL=http://tenant-service:8000
      - MONITORING_SERVICE_URL=http://monitoring-service:8000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  property-service:
    build: ./services/property-service
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-password}@postgres:5432/${POSTGRES_DB:-property_management}
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  tenant-service:
    build: ./services/tenant-service
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-password}@postgres:5432/${POSTGRES_DB:-property_management}
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  monitoring-service:
    build: ./services/monitoring-service
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-password}@postgres:5432/${POSTGRES_DB:-property_management}
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-worker:
    build: ./services/tenant-service
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-password}@postgres:5432/${POSTGRES_DB:-property_management}
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-beat:
    build: ./services/tenant-service
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-password}@postgres:5432/${POSTGRES_DB:-property_management}
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

2. Создать скрипты для управления:
```bash
#!/bin/bash
# scripts/start.sh
echo "Starting Property Management System..."

# Проверить наличие .env файла
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Запустить сервисы
docker-compose up -d

echo "Waiting for services to start..."
sleep 30

# Проверить здоровье сервисов
echo "Checking services health..."
docker-compose ps

echo "Property Management System started!"
echo "API Gateway: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "Prometheus: http://localhost:9090"
```

**Критерии приемки:**
- ✅ Docker Compose настроен для продакшн
- ✅ Health checks работают для всех сервисов
- ✅ Мониторинг (Prometheus + Grafana) настроен
- ✅ Скрипты управления созданы

## Критерии готовности MVP Backend

### Функциональные требования:
- ✅ Property Management Service полностью функционален
- ✅ Tenant Management Service с Celery задачами
- ✅ Monitoring Service с WebSocket и аналитикой
- ✅ API Gateway для маршрутизации
- ✅ Система аутентификации и авторизации
- ✅ Интеграции с внешними сервисами (карты, платежи)
- ✅ Файловый сервис для загрузки изображений

### Нефункциональные требования:
- ✅ Автодокументация API (Swagger/OpenAPI)
- ✅ Unit и Integration тесты (покрытие >80%)
- ✅ Структурированное логирование
- ✅ Мониторинг и метрики (Prometheus)
- ✅ Containerization (Docker)
- ✅ Database миграции (Alembic)
- ✅ Асинхронная обработка задач (Celery)

### Производительность:
- ✅ Асинхронные API endpoints
- ✅ Database connection pooling
- ✅ Redis кэширование
- ✅ Оптимизированные SQL запросы

### Безопасность:
- ✅ JWT аутентификация
- ✅ Валидация входных данных (Pydantic)
- ✅ SQL injection защита (SQLAlchemy)
- ✅ CORS настройки

## Команды для запуска

```bash
# Клонирование и настройка
git clone <repository>
cd property_management

# Настройка окружения
cp .env.example .env
# Отредактировать .env файл

# Запуск системы
./scripts/start.sh

# Или вручную
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка системы
docker-compose down
```

## Следующие шаги для продакшн

1. **CI/CD Pipeline** - настройка автоматического тестирования и деплоя
2. **Kubernetes** - оркестрация для продакшн среды
3. **Database Backup** - автоматическое резервное копирование
4. **SSL Certificates** - HTTPS для всех endpoints
5. **Rate Limiting** - защита от DDoS атак
6. **Advanced Monitoring** - APM инструменты (New Relic, DataDog)
7. **Caching Strategy** - Redis кэширование на уровне приложения
8. **Database Optimization** - индексы, партиционирование
9. **Load Balancing** - распределение нагрузки между инстансами
10. **Security Audit** - проверка безопасности кода и инфраструктуры
