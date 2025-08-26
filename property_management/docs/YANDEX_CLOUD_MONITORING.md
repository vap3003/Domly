# Интеграция с Yandex Cloud Monitoring

Данный документ описывает, как настроить и использовать Yandex Cloud Monitoring для мониторинга системы управления недвижимостью.

## Обзор

Yandex Cloud Monitoring позволяет:
- 📊 Собирать и хранить метрики приложений
- 📈 Создавать дашборды для визуализации
- 🚨 Настраивать алерты на основе метрик
- 🔍 Анализировать производительность и бизнес-показатели

## Настройка

### 1. Создание сервисного аккаунта в Yandex Cloud

1. Перейдите в [консоль Yandex Cloud](https://console.cloud.yandex.ru/)
2. Выберите ваш каталог (folder)
3. Перейдите в раздел "Сервисные аккаунты"
4. Создайте новый сервисный аккаунт с ролью `monitoring.editor`
5. Создайте авторизованный ключ для сервисного аккаунта
6. Скачайте JSON файл с ключом

### 2. Настройка проекта

1. Скопируйте JSON файл с ключом в `config/yandex-cloud/service-account-key.json`
2. Настройте переменные окружения в `.env`:

```bash
# Yandex Cloud Monitoring
YC_MONITORING_ENABLED=true
YC_FOLDER_ID=your-yandex-cloud-folder-id
YC_SERVICE_ACCOUNT_KEY_PATH=./config/yandex-cloud/service-account-key.json
```

3. Получите ID вашего каталога:
   - В консоли Yandex Cloud перейдите в раздел "Обзор"
   - Скопируйте "Идентификатор каталога"

### 3. Запуск с Yandex Cloud Monitoring

```bash
# Запуск только базовых сервисов
docker-compose up -d postgres redis

# Запуск с приложениями и YC Monitoring
docker-compose -f docker-compose.yandex.yml --profile app --profile yandex-monitoring up -d
```

## Архитектура мониторинга

### Компоненты

1. **YandexCloudMonitoring** - основной клиент для отправки метрик
2. **MetricsCollector** - буферизация и пакетная отправка метрик
3. **YandexCloudMonitoringMiddleware** - автоматический сбор HTTP метрик
4. **BusinessMetricsCollector** - сбор бизнес-метрик
5. **Unified Agent** - сбор системных метрик и метрик Prometheus

### Типы метрик

#### Технические метрики
- `property_management.http.requests_total` - общее количество HTTP запросов
- `property_management.http.request_duration_seconds` - время обработки запросов
- `property_management.http.response_size_bytes` - размер ответов
- `property_management.service.started/stopped` - события запуска/остановки

#### Бизнес-метрики
- `property_management.properties.total_count` - общее количество недвижимости
- `property_management.properties.vacancy_rate_percentage` - коэффициент вакантности
- `property_management.contracts.signed_total` - количество подписанных договоров
- `property_management.payments.received_total` - количество полученных платежей
- `property_management.revenue.monthly_rub` - месячная выручка

## Использование в коде

### Автоматический сбор HTTP метрик

```python
from fastapi import FastAPI
from shared.monitoring.middleware import YandexCloudMonitoringMiddleware

app = FastAPI()

# Добавляем middleware для автоматического сбора метрик
app.add_middleware(YandexCloudMonitoringMiddleware, service_name="property-service")
```

### Отправка бизнес-метрик

```python
from shared.monitoring.middleware import get_business_metrics_collector

@app.post("/properties/")
async def create_property(property_data: dict):
    # Бизнес-логика
    # ...
    
    # Отправка метрик
    business_metrics = get_business_metrics_collector()
    await business_metrics.track_property_created(
        property_type=property_data["property_type"],
        monthly_rent=property_data["monthly_rent"]
    )
    
    return {"status": "created"}
```

### Отправка кастомных метрик

```python
from shared.monitoring.yandex_cloud import get_yc_monitoring

@app.get("/custom-metric")
async def send_custom_metric():
    yc_monitoring = get_yc_monitoring()
    
    if yc_monitoring:
        await yc_monitoring.send_single_metric(
            name="custom.metric.name",
            value=42.0,
            labels={"type": "custom"},
            metric_type="DGAUGE"
        )
    
    return {"status": "sent"}
```

## Дашборды в Yandex Cloud

### Создание дашборда

1. Перейдите в раздел "Monitoring" в консоли Yandex Cloud
2. Создайте новый дашборд
3. Добавьте виджеты для отображения метрик

### Рекомендуемые виджеты

#### Технические метрики
- **RPS (Requests Per Second)**: `rate(property_management.http.requests_total[5m])`
- **Время ответа**: `property_management.http.request_duration_seconds`
- **Коды ответов**: `property_management.http.requests_total` (группировка по `status_code`)

#### Бизнес-метрики
- **Общее количество недвижимости**: `property_management.properties.total_count`
- **Коэффициент вакантности**: `property_management.properties.vacancy_rate_percentage`
- **Месячная выручка**: `property_management.revenue.monthly_rub`

### Примеры запросов

```
# Средний RPS за последний час
rate(property_management.http.requests_total[1h])

# 95-й перцентиль времени ответа
histogram_quantile(0.95, property_management.http.request_duration_seconds)

# Количество ошибок 5xx
rate(property_management.http.requests_total{status_class="5xx"}[5m])
```

## Алерты

### Настройка алертов

1. В разделе "Monitoring" создайте новый алерт
2. Настройте условия срабатывания
3. Добавьте каналы уведомлений (email, Telegram, Slack)

### Рекомендуемые алерты

#### Технические алерты
- **Высокое время ответа**: `property_management.http.request_duration_seconds > 5`
- **Много ошибок 5xx**: `rate(property_management.http.requests_total{status_class="5xx"}[5m]) > 0.1`
- **Низкий RPS**: `rate(property_management.http.requests_total[5m]) < 1`

#### Бизнес-алерты
- **Высокий коэффициент вакантности**: `property_management.properties.vacancy_rate_percentage > 20`
- **Падение выручки**: `decrease(property_management.revenue.monthly_rub[1d]) > 0.1`

## Troubleshooting

### Метрики не отправляются

1. Проверьте переменные окружения:
   ```bash
   echo $YC_MONITORING_ENABLED
   echo $YC_FOLDER_ID
   ```

2. Проверьте валидность сервисного аккаунта:
   ```bash
   # В контейнере
   cat /app/config/service-account-key.json
   ```

3. Проверьте логи приложения:
   ```bash
   docker-compose logs property-service | grep -i monitoring
   ```

### Ошибки аутентификации

1. Убедитесь, что сервисный аккаунт имеет роль `monitoring.editor`
2. Проверьте, что JSON файл с ключом не поврежден
3. Убедитесь, что указан правильный `folder_id`

### Проблемы с Unified Agent

1. Проверьте статус контейнера:
   ```bash
   docker-compose ps unified-agent
   ```

2. Проверьте логи агента:
   ```bash
   docker-compose logs unified-agent
   ```

3. Убедитесь, что все сервисы доступны для агента

## Производительность

### Оптимизация отправки метрик

1. **Буферизация**: Метрики буферизуются и отправляются пакетами
2. **Асинхронность**: Отправка не блокирует основной поток
3. **Retry логика**: Автоматические повторы при ошибках

### Настройка буфера

```python
# В коде приложения
from shared.monitoring.yandex_cloud import MetricsCollector

collector = MetricsCollector(yc_monitoring)
collector.buffer_size = 100  # Размер буфера
collector.flush_interval = 30  # Интервал отправки в секундах
```

## Безопасность

1. **Ключи сервисного аккаунта** должны храниться в безопасном месте
2. **Не коммитьте** реальные ключи в репозиторий
3. **Используйте** принцип минимальных привилегий для сервисных аккаунтов
4. **Регулярно ротируйте** ключи сервисных аккаунтов

## Стоимость

Yandex Cloud Monitoring тарифицируется по количеству:
- Записанных точек данных
- API запросов
- Времени хранения метрик

Для оптимизации затрат:
- Настройте разумные интервалы отправки
- Используйте агрегацию метрик
- Настройте retention policy для метрик
