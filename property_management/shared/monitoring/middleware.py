"""
Middleware для автоматического сбора и отправки метрик в Yandex Cloud Monitoring
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from .yandex_cloud import get_metrics_collector, Metric, MetricPoint

logger = structlog.get_logger(__name__)


class YandexCloudMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора HTTP метрик и отправки в YC Monitoring"""
    
    def __init__(self, app, service_name: str = "property-management"):
        super().__init__(app)
        self.service_name = service_name
        self.metrics_collector = get_metrics_collector()
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Обработка запроса
        response = await call_next(request)
        
        # Вычисление времени обработки
        process_time = time.time() - start_time
        
        # Отправка метрик в YC Monitoring (если включено)
        if self.metrics_collector:
            await self._send_request_metrics(request, response, process_time)
        
        return response
    
    async def _send_request_metrics(self, request: Request, response: Response, process_time: float):
        """Отправка метрик HTTP запроса"""
        try:
            timestamp = int(time.time())
            
            # Базовые лейблы для метрик
            base_labels = {
                "method": request.method,
                "endpoint": self._normalize_path(request.url.path),
                "status_code": str(response.status_code),
                "status_class": f"{response.status_code // 100}xx"
            }
            
            # Метрики для отправки
            metrics = [
                # Счетчик запросов
                Metric(
                    name=f"{self.service_name}.http.requests_total",
                    labels=base_labels,
                    type="COUNTER",
                    points=[MetricPoint(timestamp=timestamp, value=1)]
                ),
                
                # Время обработки запроса
                Metric(
                    name=f"{self.service_name}.http.request_duration_seconds",
                    labels=base_labels,
                    type="DGAUGE",
                    points=[MetricPoint(timestamp=timestamp, value=process_time)]
                ),
                
                # Размер ответа (если доступен)
                Metric(
                    name=f"{self.service_name}.http.response_size_bytes",
                    labels=base_labels,
                    type="DGAUGE",
                    points=[MetricPoint(
                        timestamp=timestamp, 
                        value=len(response.body) if hasattr(response, 'body') else 0
                    )]
                )
            ]
            
            # Добавляем метрики в буфер для отправки
            for metric in metrics:
                self.metrics_collector.add_metric(metric)
                
        except Exception as e:
            logger.error("Error sending HTTP metrics to YC Monitoring", error=str(e))
    
    def _normalize_path(self, path: str) -> str:
        """Нормализация пути для группировки метрик"""
        # Заменяем UUID и числовые ID на placeholder
        import re
        
        # UUID pattern
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        
        # Числовые ID
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path


class BusinessMetricsCollector:
    """Сборщик бизнес-метрик для недвижимости"""
    
    def __init__(self, service_name: str = "property-management"):
        self.service_name = service_name
        self.metrics_collector = get_metrics_collector()
    
    async def track_property_created(self, property_type: str, monthly_rent: float):
        """Отслеживание создания новой недвижимости"""
        if not self.metrics_collector:
            return
            
        timestamp = int(time.time())
        
        metrics = [
            Metric(
                name=f"{self.service_name}.properties.created_total",
                labels={"property_type": property_type},
                type="COUNTER",
                points=[MetricPoint(timestamp=timestamp, value=1)]
            ),
            Metric(
                name=f"{self.service_name}.properties.rent_amount_rub",
                labels={"property_type": property_type, "action": "created"},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=monthly_rent)]
            )
        ]
        
        for metric in metrics:
            self.metrics_collector.add_metric(metric)
    
    async def track_contract_signed(self, property_type: str, monthly_rent: float, contract_duration_months: int):
        """Отслеживание подписания договора"""
        if not self.metrics_collector:
            return
            
        timestamp = int(time.time())
        
        metrics = [
            Metric(
                name=f"{self.service_name}.contracts.signed_total",
                labels={"property_type": property_type},
                type="COUNTER",
                points=[MetricPoint(timestamp=timestamp, value=1)]
            ),
            Metric(
                name=f"{self.service_name}.contracts.monthly_rent_rub",
                labels={"property_type": property_type},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=monthly_rent)]
            ),
            Metric(
                name=f"{self.service_name}.contracts.duration_months",
                labels={"property_type": property_type},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=contract_duration_months)]
            )
        ]
        
        for metric in metrics:
            self.metrics_collector.add_metric(metric)
    
    async def track_payment_received(self, payment_type: str, amount: float, is_overdue: bool = False):
        """Отслеживание получения платежа"""
        if not self.metrics_collector:
            return
            
        timestamp = int(time.time())
        
        metrics = [
            Metric(
                name=f"{self.service_name}.payments.received_total",
                labels={
                    "payment_type": payment_type,
                    "is_overdue": str(is_overdue).lower()
                },
                type="COUNTER",
                points=[MetricPoint(timestamp=timestamp, value=1)]
            ),
            Metric(
                name=f"{self.service_name}.payments.amount_rub",
                labels={
                    "payment_type": payment_type,
                    "is_overdue": str(is_overdue).lower()
                },
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=amount)]
            )
        ]
        
        for metric in metrics:
            self.metrics_collector.add_metric(metric)
    
    async def track_vacancy_rate(self, total_properties: int, vacant_properties: int):
        """Отслеживание коэффициента вакантности"""
        if not self.metrics_collector:
            return
            
        timestamp = int(time.time())
        vacancy_rate = (vacant_properties / total_properties * 100) if total_properties > 0 else 0
        
        metrics = [
            Metric(
                name=f"{self.service_name}.properties.total_count",
                labels={},
                type="IGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=total_properties)]
            ),
            Metric(
                name=f"{self.service_name}.properties.vacant_count",
                labels={},
                type="IGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=vacant_properties)]
            ),
            Metric(
                name=f"{self.service_name}.properties.vacancy_rate_percentage",
                labels={},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=vacancy_rate)]
            )
        ]
        
        for metric in metrics:
            self.metrics_collector.add_metric(metric)


# Глобальный экземпляр для использования в приложениях
_business_metrics_collector = None


def get_business_metrics_collector() -> BusinessMetricsCollector:
    """Получение глобального экземпляра сборщика бизнес-метрик"""
    global _business_metrics_collector
    
    if _business_metrics_collector is None:
        _business_metrics_collector = BusinessMetricsCollector()
        
    return _business_metrics_collector
