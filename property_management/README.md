# Property Management System

Микросервисная система управления недвижимостью на базе FastAPI, PostgreSQL и Redis.

## Архитектура

Система состоит из следующих микросервисов:

- **API Gateway** - точка входа для всех запросов
- **Property Service** - управление недвижимостью
- **Tenant Service** - управление арендаторами и договорами
- **Monitoring Service** - аналитика и мониторинг

## Технологический стек

- **Backend**: Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0+
- **База данных**: PostgreSQL 14+
- **Кэширование**: Redis 6+
- **Очереди**: Celery
- **Контейнеризация**: Docker, Docker Compose

## Структура проекта

```
property_management/
├── services/           # Микросервисы
│   ├── api-gateway/    # API Gateway
│   ├── property-service/    # Сервис недвижимости
│   ├── tenant-service/      # Сервис арендаторов
│   └── monitoring-service/  # Сервис мониторинга
├── shared/            # Общие модули
│   ├── database/      # Настройки БД
│   ├── auth/          # Аутентификация
│   ├── utils/         # Утилиты
│   └── schemas/       # Общие схемы
├── docs/              # Документация
└── scripts/           # Скрипты управления
```

## Установка и запуск

### Предварительные требования

- Docker и Docker Compose
- Python 3.11+
- PostgreSQL 14+ (для разработки)
- Redis 6+ (для разработки)

### Быстрый старт

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd property_management
```

2. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл под ваши нужды
```

3. Запустите систему:
```bash
docker-compose up -d
```

4. Проверьте статус сервисов:
```bash
docker-compose ps
```

### Доступные эндпоинты

- API Gateway: http://localhost:8000
- API Документация: http://localhost:8000/docs
- Мониторинг (Grafana): http://localhost:3000
- Метрики (Prometheus): http://localhost:9090

## Разработка

### Локальная разработка

Для разработки отдельного сервиса:

```bash
cd services/property-service
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Тестирование

Запуск тестов:
```bash
pytest services/property-service/app/tests/
```

## Статус проекта

- ✅ Базовая структура проекта
- ⏳ Docker конфигурация
- ⏳ Базовые core модули
- ⏳ Property Management Service
- ⏳ Tenant Management Service
- ⏳ Monitoring Service
- ⏳ API Gateway
- ⏳ Тестирование
- ⏳ Документация

## Контакты

Property Management Team - dev@property-management.com
