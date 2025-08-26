"""
Пример использования Yandex Cloud Monitoring в FastAPI приложении
"""

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import asyncio

# Импорт наших модулей мониторинга
from shared.monitoring.yandex_cloud import get_yc_monitoring, get_metrics_collector
from shared.monitoring.middleware import YandexCloudMonitoringMiddleware, get_business_metrics_collector


# Lifespan для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: запуск периодической отправки метрик
    metrics_collector = get_metrics_collector()
    if metrics_collector:
        # Запускаем фоновую задачу для периодической отправки метрик
        task = asyncio.create_task(metrics_collector.periodic_flush())
        
        # Отправляем стартовую метрику
        yc_monitoring = get_yc_monitoring()
        if yc_monitoring:
            await yc_monitoring.send_single_metric(
                name="property_management.service.started",
                value=1,
                labels={"service": "property-service"},
                metric_type="COUNTER"
            )
    
    yield
    
    # Shutdown: отправляем финальные метрики
    if metrics_collector:
        await metrics_collector.flush_metrics()
        task.cancel()
        
        # Отправляем метрику остановки
        yc_monitoring = get_yc_monitoring()
        if yc_monitoring:
            await yc_monitoring.send_single_metric(
                name="property_management.service.stopped",
                value=1,
                labels={"service": "property-service"},
                metric_type="COUNTER"
            )


# Создание приложения
app = FastAPI(
    title="Property Service with YC Monitoring",
    lifespan=lifespan
)

# Добавление middleware для автоматического сбора метрик
app.add_middleware(YandexCloudMonitoringMiddleware, service_name="property-service")


# Пример эндпоинта с отправкой бизнес-метрик
@app.post("/properties/")
async def create_property(property_data: dict):
    """Создание недвижимости с отправкой метрик в YC Monitoring"""
    
    # Бизнес-логика создания недвижимости
    # ... код создания недвижимости ...
    
    # Отправка бизнес-метрик
    business_metrics = get_business_metrics_collector()
    await business_metrics.track_property_created(
        property_type=property_data.get("property_type", "unknown"),
        monthly_rent=property_data.get("monthly_rent", 0)
    )
    
    return {"message": "Property created successfully"}


@app.post("/contracts/")
async def create_contract(contract_data: dict):
    """Создание договора с отправкой метрик"""
    
    # Бизнес-логика создания договора
    # ... код создания договора ...
    
    # Отправка бизнес-метрик
    business_metrics = get_business_metrics_collector()
    await business_metrics.track_contract_signed(
        property_type=contract_data.get("property_type", "unknown"),
        monthly_rent=contract_data.get("monthly_rent", 0),
        contract_duration_months=contract_data.get("duration_months", 12)
    )
    
    return {"message": "Contract created successfully"}


@app.post("/payments/")
async def receive_payment(payment_data: dict):
    """Обработка платежа с отправкой метрик"""
    
    # Бизнес-логика обработки платежа
    # ... код обработки платежа ...
    
    # Отправка бизнес-метрик
    business_metrics = get_business_metrics_collector()
    await business_metrics.track_payment_received(
        payment_type=payment_data.get("payment_type", "rent"),
        amount=payment_data.get("amount", 0),
        is_overdue=payment_data.get("is_overdue", False)
    )
    
    return {"message": "Payment processed successfully"}


@app.get("/metrics/business")
async def get_business_metrics():
    """Эндпоинт для получения текущих бизнес-метрик"""
    
    # Пример отправки агрегированных метрик
    business_metrics = get_business_metrics_collector()
    
    # Предположим, у нас есть данные из базы
    total_properties = 150
    vacant_properties = 15
    
    await business_metrics.track_vacancy_rate(
        total_properties=total_properties,
        vacant_properties=vacant_properties
    )
    
    return {
        "total_properties": total_properties,
        "vacant_properties": vacant_properties,
        "vacancy_rate": (vacant_properties / total_properties * 100) if total_properties > 0 else 0
    }


@app.get("/health")
async def health_check():
    """Health check с отправкой метрики здоровья"""
    
    yc_monitoring = get_yc_monitoring()
    if yc_monitoring:
        await yc_monitoring.send_single_metric(
            name="property_management.service.health_check",
            value=1,
            labels={"service": "property-service", "status": "healthy"},
            metric_type="COUNTER"
        )
    
    return {"status": "healthy"}


# Пример отправки кастомных метрик
@app.get("/custom-metrics")
async def send_custom_metrics():
    """Пример отправки кастомных метрик"""
    
    yc_monitoring = get_yc_monitoring()
    if not yc_monitoring:
        return {"message": "YC Monitoring not configured"}
    
    # Создание кастомных метрик
    custom_metrics = yc_monitoring.create_business_metrics(
        properties_count=150,
        vacancy_rate=10.5,
        revenue=750000.0
    )
    
    # Отправка метрик
    success = await yc_monitoring.send_metrics(custom_metrics)
    
    return {
        "message": "Custom metrics sent" if success else "Failed to send metrics",
        "metrics_count": len(custom_metrics)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
