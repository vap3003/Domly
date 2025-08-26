"""
Интеграция с Yandex Cloud Monitoring
Отправка кастомных метрик в Yandex Cloud Monitoring API
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
import os
import jwt
import structlog
from dataclasses import dataclass, asdict

logger = structlog.get_logger(__name__)


@dataclass
class MetricPoint:
    """Точка метрики для отправки в YC Monitoring"""
    timestamp: int
    value: float


@dataclass
class Metric:
    """Метрика для отправки в YC Monitoring"""
    name: str
    labels: Dict[str, str]
    type: str  # DGAUGE, IGAUGE, COUNTER, RATE
    points: List[MetricPoint]


class YandexCloudMonitoring:
    """Клиент для работы с Yandex Cloud Monitoring API"""
    
    def __init__(
        self,
        service_account_key_path: Optional[str] = None,
        folder_id: Optional[str] = None,
        service_name: str = "property-management"
    ):
        self.service_account_key_path = service_account_key_path or os.getenv("YC_SERVICE_ACCOUNT_KEY_PATH")
        self.folder_id = folder_id or os.getenv("YC_FOLDER_ID")
        self.service_name = service_name
        self.base_url = "https://monitoring.api.cloud.yandex.net/monitoring/v2/data/write"
        self._iam_token = None
        self._token_expires_at = 0
        
        # Базовые лейблы для всех метрик
        self.base_labels = {
            "service": self.service_name,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": os.getenv("SERVICE_VERSION", "1.0.0")
        }
        
    async def _get_iam_token(self) -> str:
        """Получение IAM токена для аутентификации"""
        current_time = time.time()
        
        # Проверяем, не истек ли токен
        if self._iam_token and current_time < self._token_expires_at:
            return self._iam_token
            
        if not self.service_account_key_path:
            raise ValueError("Service account key path is required")
            
        try:
            # Читаем ключ сервисного аккаунта
            with open(self.service_account_key_path, 'r') as f:
                service_account_key = json.load(f)
                
            # Создаем JWT токен
            now = int(current_time)
            payload = {
                'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                'iss': service_account_key['service_account_id'],
                'iat': now,
                'exp': now + 3600  # Токен действует 1 час
            }
            
            jwt_token = jwt.encode(
                payload,
                service_account_key['private_key'],
                algorithm='PS256',
                headers={'kid': service_account_key['id']}
            )
            
            # Обмениваем JWT на IAM токен
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                    json={'jwt': jwt_token}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self._iam_token = token_data['iamToken']
                    # Токен действует час, обновляем за 5 минут до истечения
                    self._token_expires_at = current_time + 3300
                    return self._iam_token
                else:
                    raise Exception(f"Failed to get IAM token: {response.text}")
                    
        except Exception as e:
            logger.error("Failed to get IAM token", error=str(e))
            raise
            
    async def send_metrics(self, metrics: List[Metric]) -> bool:
        """Отправка метрик в Yandex Cloud Monitoring"""
        if not metrics:
            return True
            
        try:
            iam_token = await self._get_iam_token()
            
            # Подготавливаем данные для отправки
            payload = {
                "metrics": []
            }
            
            for metric in metrics:
                # Добавляем базовые лейблы к лейблам метрики
                combined_labels = {**self.base_labels, **metric.labels}
                
                metric_data = {
                    "name": metric.name,
                    "labels": combined_labels,
                    "type": metric.type,
                    "ts": [point.timestamp for point in metric.points],
                    "values": [point.value for point in metric.points]
                }
                payload["metrics"].append(metric_data)
            
            # Отправляем метрики
            headers = {
                "Authorization": f"Bearer {iam_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "folderId": self.folder_id
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    logger.info(
                        "Metrics sent successfully",
                        metrics_count=len(metrics),
                        folder_id=self.folder_id
                    )
                    return True
                else:
                    logger.error(
                        "Failed to send metrics",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return False
                    
        except Exception as e:
            logger.error("Error sending metrics to YC Monitoring", error=str(e))
            return False
    
    async def send_single_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metric_type: str = "DGAUGE",
        timestamp: Optional[int] = None
    ) -> bool:
        """Отправка одной метрики"""
        if timestamp is None:
            timestamp = int(time.time())
            
        metric = Metric(
            name=name,
            labels=labels or {},
            type=metric_type,
            points=[MetricPoint(timestamp=timestamp, value=value)]
        )
        
        return await self.send_metrics([metric])
    
    def create_business_metrics(self, properties_count: int, vacancy_rate: float, revenue: float) -> List[Metric]:
        """Создание бизнес-метрик для недвижимости"""
        timestamp = int(time.time())
        
        return [
            Metric(
                name="property_management.properties.total",
                labels={"metric_type": "business"},
                type="IGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=properties_count)]
            ),
            Metric(
                name="property_management.vacancy.rate_percentage",
                labels={"metric_type": "business"},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=vacancy_rate)]
            ),
            Metric(
                name="property_management.revenue.monthly_rub",
                labels={"metric_type": "business", "currency": "RUB"},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=revenue)]
            )
        ]
    
    def create_technical_metrics(self, request_count: int, response_time: float, error_rate: float) -> List[Metric]:
        """Создание технических метрик"""
        timestamp = int(time.time())
        
        return [
            Metric(
                name="property_management.http.requests_total",
                labels={"metric_type": "technical"},
                type="COUNTER",
                points=[MetricPoint(timestamp=timestamp, value=request_count)]
            ),
            Metric(
                name="property_management.http.response_time_seconds",
                labels={"metric_type": "technical"},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=response_time)]
            ),
            Metric(
                name="property_management.http.error_rate_percentage",
                labels={"metric_type": "technical"},
                type="DGAUGE",
                points=[MetricPoint(timestamp=timestamp, value=error_rate)]
            )
        ]


class MetricsCollector:
    """Сборщик метрик для отправки в YC Monitoring"""
    
    def __init__(self, yc_monitoring: YandexCloudMonitoring):
        self.yc_monitoring = yc_monitoring
        self.metrics_buffer: List[Metric] = []
        self.buffer_size = 50
        self.flush_interval = 60  # секунд
        self._last_flush = time.time()
        
    def add_metric(self, metric: Metric):
        """Добавление метрики в буфер"""
        self.metrics_buffer.append(metric)
        
        # Автоматическая отправка при заполнении буфера
        if len(self.metrics_buffer) >= self.buffer_size:
            asyncio.create_task(self.flush_metrics())
    
    async def flush_metrics(self):
        """Отправка накопленных метрик"""
        if not self.metrics_buffer:
            return
            
        metrics_to_send = self.metrics_buffer.copy()
        self.metrics_buffer.clear()
        self._last_flush = time.time()
        
        success = await self.yc_monitoring.send_metrics(metrics_to_send)
        
        if not success:
            # При ошибке возвращаем метрики обратно в буфер
            self.metrics_buffer.extend(metrics_to_send)
            logger.warning("Metrics returned to buffer due to send failure")
    
    async def periodic_flush(self):
        """Периодическая отправка метрик"""
        while True:
            await asyncio.sleep(self.flush_interval)
            
            if time.time() - self._last_flush >= self.flush_interval:
                await self.flush_metrics()


# Глобальный экземпляр для использования в приложении
_yc_monitoring = None
_metrics_collector = None


def get_yc_monitoring() -> Optional[YandexCloudMonitoring]:
    """Получение глобального экземпляра YC Monitoring"""
    global _yc_monitoring
    
    if _yc_monitoring is None and os.getenv("YC_MONITORING_ENABLED", "false").lower() == "true":
        _yc_monitoring = YandexCloudMonitoring()
        
    return _yc_monitoring


def get_metrics_collector() -> Optional[MetricsCollector]:
    """Получение глобального экземпляра сборщика метрик"""
    global _metrics_collector
    
    yc_monitoring = get_yc_monitoring()
    if yc_monitoring and _metrics_collector is None:
        _metrics_collector = MetricsCollector(yc_monitoring)
        
    return _metrics_collector
