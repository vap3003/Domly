# Архитектура сервиса управления и мониторинга недвижимости

## Обзор системы

Сервис предназначен для арендодателей и управляющих компаний для эффективного управления портфелем недвижимости, мониторинга состояния объектов, взаимодействия с арендаторами и автоматизации бизнес-процессов.

## Высокоуровневая архитектура

### Основные компоненты системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  Mobile Apps    │    │  Admin Panel    │
│   (React/Next)  │    │ (React Native)  │    │   (React/Vue)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      API Gateway         │
                    │    (Kong/AWS ALB)        │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌─────────┴─────────┐
│  Property Service │   │  Tenant Service   │   │ Monitoring Service│
│   (Node.js/Go)    │   │   (Node.js/Go)    │   │   (Node.js/Go)    │
└─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     Message Queue        │
                    │    (Redis/RabbitMQ)      │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌─────────┴─────────┐
│   PostgreSQL      │   │      Redis        │   │   File Storage    │
│   (Primary DB)    │   │     (Cache)       │   │   (AWS S3/MinIO)  │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

## Детальная архитектура микросервисов

### 1. Property Management Service (FastAPI)
**Ответственность:** Управление объектами недвижимости
- CRUD операции с объектами недвижимости
- Управление характеристиками и метаданными
- Категоризация и классификация объектов
- Интеграция с картографическими сервисами
- Автоматическая валидация данных через Pydantic
- Автогенерация OpenAPI документации

**Структура сервиса:**
```python
# app/models/property.py
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    property_type = Column(Enum('apartment', 'house', 'commercial', 'office'))
    # ... остальные поля

# app/schemas/property.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class PropertyType(str, Enum):
    apartment = "apartment"
    house = "house"
    commercial = "commercial"
    office = "office"

class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    property_type: PropertyType
    monthly_rent: float = Field(..., gt=0)
    # ... валидация полей

# app/api/endpoints/properties.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.property_service import PropertyService

router = APIRouter()

@router.get("/", response_model=List[PropertyResponse])
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await PropertyService.get_properties(db, skip, limit)
```

**API Endpoints:**
```
GET    /api/v1/properties          # Список объектов с фильтрацией
POST   /api/v1/properties          # Создание нового объекта
GET    /api/v1/properties/{id}     # Детали объекта
PUT    /api/v1/properties/{id}     # Обновление объекта
DELETE /api/v1/properties/{id}     # Удаление объекта
GET    /api/v1/properties/{id}/analytics # Аналитика по объекту
GET    /docs                       # Автогенерированная документация
```

### 2. Tenant Management Service (FastAPI)
**Ответственность:** Управление арендаторами и договорами
- Профили арендаторов
- Управление договорами аренды
- История платежей
- Коммуникации с арендаторами
- Интеграция с платежными системами
- Автоматические уведомления о платежах

**Ключевые особенности FastAPI:**
```python
# app/schemas/tenant.py
from pydantic import BaseModel, EmailStr, validator
from datetime import date
from typing import Optional

class TenantCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., regex=r'^\+?[1-9]\d{1,14}$')
    birth_date: date
    
    @validator('birth_date')
    def validate_age(cls, v):
        from datetime import date
        age = (date.today() - v).days / 365.25
        if age < 18:
            raise ValueError('Арендатор должен быть совершеннолетним')
        return v

# app/services/payment_service.py
from celery import Celery
from app.core.config import settings

celery_app = Celery("payment_service")

@celery_app.task
async def send_payment_reminder(tenant_id: str, amount: float):
    # Асинхронная отправка напоминания о платеже
    pass

@celery_app.task
async def process_payment(payment_data: dict):
    # Обработка платежа через внешний API
    pass
```

**API Endpoints:**
```
GET    /api/v1/tenants             # Список арендаторов
POST   /api/v1/tenants             # Регистрация арендатора
GET    /api/v1/tenants/{id}        # Профиль арендатора
PUT    /api/v1/tenants/{id}        # Обновление профиля
GET    /api/v1/tenants/{id}/contracts # Договоры арендатора
POST   /api/v1/contracts           # Создание договора
PUT    /api/v1/contracts/{id}      # Обновление договора
GET    /api/v1/payments            # История платежей
POST   /api/v1/payments            # Регистрация платежа
POST   /api/v1/payments/webhook    # Webhook для платежных систем
```

### 3. Monitoring & Analytics Service (FastAPI)
**Ответственность:** Мониторинг состояния и аналитика
- Сбор метрик состояния объектов
- Аналитические отчеты
- Уведомления и алерты
- Прогнозирование и рекомендации
- Real-time мониторинг через WebSocket
- Машинное обучение для прогнозов

**Особенности реализации:**
```python
# app/services/analytics_service.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from fastapi import WebSocket
import asyncio

class AnalyticsService:
    @staticmethod
    async def calculate_property_roi(property_id: str) -> dict:
        # Расчет ROI недвижимости
        pass
    
    @staticmethod
    async def predict_vacancy_rate(property_data: dict) -> float:
        # ML прогноз вакантности
        model = LinearRegression()
        # ... логика ML
        return predicted_rate

# app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast_metrics(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

@router.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Отправка real-time метрик
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**API Endpoints:**
```
GET    /api/v1/monitoring/dashboard    # Дашборд мониторинга
GET    /api/v1/monitoring/alerts       # Активные алерты
POST   /api/v1/monitoring/metrics      # Отправка метрик
GET    /api/v1/analytics/revenue       # Анализ доходности
GET    /api/v1/analytics/occupancy     # Анализ заполняемости
GET    /api/v1/analytics/predictions   # ML прогнозы
GET    /api/v1/reports/{type}          # Генерация отчетов
WS     /ws/monitoring                  # Real-time мониторинг
```

### 4. Notification Service
**Ответственность:** Система уведомлений
- Email уведомления
- Push уведомления
- SMS уведомления
- In-app уведомления

### 5. File Management Service
**Ответственность:** Управление файлами и документами
- Загрузка и хранение документов
- Обработка изображений
- Версионирование документов
- Интеграция с облачными хранилищами

## База данных

### Основные сущности и их связи

```sql
-- Объекты недвижимости
Properties {
  id: UUID PRIMARY KEY
  owner_id: UUID NOT NULL
  title: VARCHAR(255) NOT NULL
  description: TEXT
  property_type: ENUM('apartment', 'house', 'commercial', 'office')
  address: JSONB NOT NULL
  coordinates: POINT
  total_area: DECIMAL(10,2)
  rooms_count: INTEGER
  floor: INTEGER
  total_floors: INTEGER
  year_built: INTEGER
  amenities: JSONB
  photos: JSONB
  status: ENUM('available', 'rented', 'maintenance', 'inactive')
  monthly_rent: DECIMAL(10,2)
  currency: VARCHAR(3) DEFAULT 'RUB'
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
}

-- Арендаторы
Tenants {
  id: UUID PRIMARY KEY
  first_name: VARCHAR(100) NOT NULL
  last_name: VARCHAR(100) NOT NULL
  email: VARCHAR(255) UNIQUE NOT NULL
  phone: VARCHAR(20)
  birth_date: DATE
  passport_data: JSONB
  employment_info: JSONB
  emergency_contact: JSONB
  rating: DECIMAL(3,2)
  status: ENUM('active', 'inactive', 'blacklisted')
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
}

-- Договоры аренды
Contracts {
  id: UUID PRIMARY KEY
  property_id: UUID REFERENCES Properties(id)
  tenant_id: UUID REFERENCES Tenants(id)
  start_date: DATE NOT NULL
  end_date: DATE NOT NULL
  monthly_rent: DECIMAL(10,2) NOT NULL
  security_deposit: DECIMAL(10,2)
  payment_due_day: INTEGER DEFAULT 1
  terms: TEXT
  status: ENUM('draft', 'active', 'expired', 'terminated')
  signed_at: TIMESTAMP
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
}

-- Платежи
Payments {
  id: UUID PRIMARY KEY
  contract_id: UUID REFERENCES Contracts(id)
  amount: DECIMAL(10,2) NOT NULL
  payment_date: DATE NOT NULL
  due_date: DATE NOT NULL
  payment_type: ENUM('rent', 'deposit', 'utilities', 'penalty')
  status: ENUM('pending', 'paid', 'overdue', 'partial')
  payment_method: VARCHAR(50)
  transaction_id: VARCHAR(255)
  notes: TEXT
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
}

-- Метрики мониторинга
Monitoring_Metrics {
  id: UUID PRIMARY KEY
  property_id: UUID REFERENCES Properties(id)
  metric_type: VARCHAR(50) NOT NULL
  metric_value: JSONB NOT NULL
  timestamp: TIMESTAMP NOT NULL
  source: VARCHAR(100)
  created_at: TIMESTAMP DEFAULT NOW()
}

-- Уведомления
Notifications {
  id: UUID PRIMARY KEY
  recipient_id: UUID NOT NULL
  recipient_type: ENUM('owner', 'tenant', 'admin')
  title: VARCHAR(255) NOT NULL
  message: TEXT NOT NULL
  type: ENUM('payment_reminder', 'contract_expiry', 'maintenance', 'alert')
  status: ENUM('pending', 'sent', 'delivered', 'read')
  channels: JSONB
  scheduled_at: TIMESTAMP
  sent_at: TIMESTAMP
  created_at: TIMESTAMP DEFAULT NOW()
}
```

## План реализации MVP

### Этап 1: Базовая инфраструктура (2-3 недели)
**Цели:**
- Настройка базовой инфраструктуры
- Развертывание основных сервисов
- Реализация аутентификации и авторизации

**Задачи:**
1. Настройка CI/CD пайплайна (GitHub Actions/GitLab CI)
2. Развертывание PostgreSQL и Redis
3. Создание базовой структуры микросервисов
4. Реализация API Gateway
5. Настройка системы логирования и мониторинга
6. Реализация JWT-аутентификации
7. Базовая настройка RBAC (Role-Based Access Control)

**Результат:** Работающая инфраструктура с базовой аутентификацией

### Этап 2: Управление недвижимостью (3-4 недели)
**Цели:**
- Реализация CRUD операций для объектов недвижимости
- Базовый веб-интерфейс для управления

**Задачи:**
1. Property Management Service:
   - CRUD API для объектов недвижимости
   - Загрузка и управление фотографиями
   - Геокодирование адресов
2. Веб-интерфейс:
   - Список объектов с фильтрацией и поиском
   - Форма добавления/редактирования объекта
   - Детальная страница объекта
   - Галерея фотографий
3. File Management Service:
   - Загрузка файлов в S3/MinIO
   - Генерация превью изображений

**Результат:** Функциональная система управления объектами недвижимости

### Этап 3: Управление арендаторами (2-3 недели)
**Цели:**
- Система управления арендаторами и договорами
- Базовая система платежей

**Задачи:**
1. Tenant Management Service:
   - CRUD API для арендаторов
   - Управление договорами аренды
   - Регистрация платежей
2. Веб-интерфейс:
   - Реестр арендаторов
   - Форма создания договора
   - Календарь платежей
   - История транзакций

**Результат:** Полнофункциональная система управления арендой

### Этап 4: Базовый мониторинг и уведомления (2 недели)
**Цели:**
- Простая система уведомлений
- Базовые аналитические отчеты

**Задачи:**
1. Notification Service:
   - Email уведомления (просрочка платежей, истечение договоров)
   - In-app уведомления
2. Monitoring Service:
   - Дашборд с ключевыми метриками
   - Базовые отчеты (доходность, заполняемость)
   - Алерты по просрочкам

**Результат:** Базовая система мониторинга и уведомлений

### Этап 5: Мобильное приложение (3-4 недели)
**Цели:**
- Мобильное приложение для арендодателей
- Базовое приложение для арендаторов

**Задачи:**
1. React Native приложение для арендодателей:
   - Просмотр объектов и арендаторов
   - Push уведомления
   - Базовая аналитика
2. Веб-портал для арендаторов:
   - Личный кабинет
   - История платежей
   - Подача заявок на обслуживание

**Результат:** Мобильные решения для всех участников

## Технологический стек

### Backend
- **Язык:** Python 3.11+
- **Фреймворк:** FastAPI 0.104+
- **ASGI сервер:** Uvicorn
- **База данных:** PostgreSQL 14+
- **Кэширование:** Redis 6+
- **Очереди:** Celery + Redis/RabbitMQ
- **ORM:** SQLAlchemy 2.0+ с Alembic для миграций
- **Валидация:** Pydantic 2.0+

### Frontend
- **Web:** React 18+ с Next.js 13+
- **Mobile:** React Native 0.72+
- **State Management:** Redux Toolkit или Zustand
- **UI Library:** Material-UI или Ant Design
- **Карты:** Mapbox или Google Maps

### DevOps & Infrastructure
- **Контейнеризация:** Docker + Docker Compose
- **Оркестрация:** Kubernetes (для продакшн)
- **CI/CD:** GitHub Actions или GitLab CI
- **Мониторинг:** Prometheus + Grafana
- **Логирование:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Облако:** AWS/GCP/Azure или on-premise

### Интеграции
- **Платежи:** Stripe, PayPal, или локальные платежные системы
- **Карты:** Google Maps API, Mapbox
- **Уведомления:** Firebase Cloud Messaging, SendGrid
- **Файлы:** AWS S3, Google Cloud Storage, MinIO

## Безопасность

### Аутентификация и авторизация
- JWT токены с refresh механизмом
- OAuth 2.0 для внешних интеграций
- Role-Based Access Control (RBAC)
- Multi-factor authentication (2FA)

### Защита данных
- Шифрование данных в покое (AES-256)
- TLS 1.3 для передачи данных
- Хеширование паролей (bcrypt/scrypt)
- Регулярные backup'ы с шифрованием

### API Security
- Rate limiting
- Input validation и sanitization
- CORS настройки
- API versioning
- Request/Response logging

## Масштабирование

### Горизонтальное масштабирование
- Stateless микросервисы
- Load balancing (Nginx, HAProxy)
- Database sharding по owner_id
- CDN для статических файлов

### Производительность
- Database indexing стратегия
- Query optimization
- Кэширование на разных уровнях
- Асинхронная обработка тяжелых операций

### Мониторинг производительности
- APM инструменты (New Relic, DataDog)
- Database performance monitoring
- Real User Monitoring (RUM)
- Synthetic monitoring

## Развертывание MVP

### Минимальные требования к серверу
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Storage:** 100 GB SSD
- **Network:** 1 Gbps

### Docker Compose для разработки
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
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  # API Gateway (FastAPI)
  api-gateway:
    build: 
      context: ./services/api-gateway
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://admin:password@postgres:5432/property_management
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Property Management Service
  property-service:
    build: ./services/property-service
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://admin:password@postgres:5432/property_management
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Tenant Management Service  
  tenant-service:
    build: ./services/tenant-service
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql://admin:password@postgres:5432/property_management
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Monitoring Service
  monitoring-service:
    build: ./services/monitoring-service
    ports:
      - "8003:8000"
    environment:
      - DATABASE_URL=postgresql://admin:password@postgres:5432/property_management
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker для фоновых задач
  celery-worker:
    build: ./services/tenant-service
    command: celery -A app.core.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://admin:password@postgres:5432/property_management
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  # Celery Beat для периодических задач
  celery-beat:
    build: ./services/tenant-service
    command: celery -A app.core.celery beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://admin:password@postgres:5432/property_management
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

### Структура FastAPI проекта
```
property_management/
├── services/
│   ├── api-gateway/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── api.py
│   │   │   │   └── deps.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py
│   │   │   │   └── database.py
│   │   │   └── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── property-service/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── endpoints/
│   │   │   │       └── properties.py
│   │   │   ├── models/
│   │   │   │   └── property.py
│   │   │   ├── schemas/
│   │   │   │   └── property.py
│   │   │   ├── services/
│   │   │   │   └── property_service.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   └── database.py
│   │   │   └── main.py
│   │   └── requirements.txt
│   └── tenant-service/
│       ├── app/
│       │   ├── api/endpoints/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── core/
│       │   │   ├── celery.py
│       │   │   └── config.py
│       │   └── main.py
│       └── requirements.txt
├── requirements.txt
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

### Requirements.txt для FastAPI сервисов
```python
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Cache & Queue
redis==5.0.1
celery==5.3.4
flower==2.0.1

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# File handling
aiofiles==23.2.1
pillow==10.1.0
boto3==1.34.0

# HTTP client
httpx==0.25.2
aiohttp==3.9.1

# Data processing & ML
pandas==2.1.4
numpy==1.25.2
scikit-learn==1.3.2

# Email & Notifications
emails==0.6
jinja2==3.1.2

# Monitoring & Logging
prometheus-client==0.19.0
structlog==23.2.0

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
mypy==1.7.1

# Documentation
mkdocs==1.5.3
mkdocs-material==9.4.8
```

### Преимущества FastAPI для проекта недвижимости

1. **Автоматическая документация API**
   - Swagger UI из коробки
   - OpenAPI 3.0 спецификация
   - Интерактивное тестирование API

2. **Строгая типизация и валидация**
   - Pydantic модели для валидации данных
   - Автоматическая сериализация/десериализация
   - Защита от некорректных данных

3. **Высокая производительность**
   - Асинхронная обработка запросов
   - Один из самых быстрых Python фреймворков
   - Поддержка WebSocket для real-time обновлений

4. **Современные стандарты разработки**
   - Type hints поддержка
   - Dependency Injection система
   - Middleware для кросс-функциональной логики

5. **Интеграция с экосистемой Python**
   - SQLAlchemy для работы с БД
   - Celery для фоновых задач
   - Pandas/NumPy для аналитики
   - Scikit-learn для ML прогнозов

## Заключение

Данная архитектура на базе **FastAPI** обеспечивает:

### Технические преимущества:
- **Масштабируемость:** Микросервисная архитектура позволяет независимо масштабировать компоненты
- **Производительность:** Асинхронная обработка запросов FastAPI + эффективное кэширование Redis
- **Надежность:** Отказоустойчивость через репликацию и мониторинг
- **Безопасность:** Многоуровневая защита данных и API с автоматической валидацией
- **Расширяемость:** Модульная архитектура для добавления новых функций

### Бизнес преимущества:
- **Быстрая разработка:** Автогенерация документации и валидация данных ускоряют разработку
- **Низкие затраты на поддержку:** Строгая типизация снижает количество багов
- **Простота интеграций:** OpenAPI документация упрощает интеграцию с внешними системами
- **ML возможности:** Встроенная поддержка Python ML библиотек для аналитики и прогнозов

### План развертывания MVP:
**Команда:** 4-5 разработчиков (2 backend, 1 frontend, 1 mobile, 1 DevOps)
**Время:** 10-12 недель
**Результат:** Полнофункциональная система управления недвижимостью с современным tech stack

**Ключевые возможности MVP:**
- Управление портфелем недвижимости
- Система арендаторов и договоров
- Автоматизация платежей и уведомлений
- Аналитика и отчетность
- Мобильные приложения для всех участников
- Real-time мониторинг через WebSocket
- Интеграция с внешними сервисами (карты, платежи)
