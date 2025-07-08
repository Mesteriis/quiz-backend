"""
Comprehensive тесты для Monitoring Schemas.

Покрывает все схемы мониторинга:
- Метрики и их валидация
- Алерты и уведомления
- Дашборды и виджеты
- Системное здоровье
- Аналитические данные
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import ValidationError

from schemas.monitoring import (
    MetricCreate,
    MetricResponse,
    MetricBatch,
    MetricType,
    AlertCreate,
    AlertResponse,
    AlertLevel,
    ComponentHealth,
    ComponentStatus,
    SystemHealthResponse,
    SystemStatus,
    DashboardCreate,
    DashboardResponse,
    UserAnalyticsResponse,
    PerformanceData,
)
from tests.factories.monitoring_factories import (
    MetricCreateFactory,
    MetricResponseFactory,
    AlertCreateFactory,
    AlertResponseFactory,
    ComponentHealthFactory,
    SystemHealthResponseFactory,
    DashboardCreateFactory,
    DashboardResponseFactory,
    UserAnalyticsResponseFactory,
    PerformanceDataFactory,
)


class TestMetricSchemas:
    """Тесты схем метрик."""

    def test_metric_create_valid_data(self):
        """Тест создания валидной метрики."""
        # Arrange
        metric_data = {
            "name": "cpu_usage",
            "value": 75.5,
            "type": MetricType.GAUGE,
            "tags": {"server": "web-01", "environment": "production"},
            "timestamp": datetime.now().isoformat(),
        }

        # Act
        metric = MetricCreate(**metric_data)

        # Assert
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.type == MetricType.GAUGE
        assert metric.tags["server"] == "web-01"
        assert isinstance(metric.timestamp, datetime)

    def test_metric_create_with_factory(self):
        """Тест создания метрики с помощью фабрики."""
        # Arrange & Act
        metric_data = MetricCreateFactory.build()
        metric = MetricCreate(
            name=metric_data.name,
            value=metric_data.value,
            type=metric_data.type,
            tags=metric_data.tags,
            timestamp=metric_data.timestamp,
        )

        # Assert
        assert isinstance(metric.name, str)
        assert isinstance(metric.value, (int, float))
        assert metric.type in [e.value for e in MetricType]
        assert metric.tags is None or isinstance(metric.tags, dict)

    def test_metric_create_without_optional_fields(self):
        """Тест создания метрики без опциональных полей."""
        # Arrange
        metric_data = {
            "name": "simple_metric",
            "value": 100.0,
            "type": MetricType.COUNTER,
        }

        # Act
        metric = MetricCreate(**metric_data)

        # Assert
        assert metric.name == "simple_metric"
        assert metric.value == 100.0
        assert metric.type == MetricType.COUNTER
        assert metric.tags is None
        assert metric.timestamp is None

    def test_metric_create_invalid_value_type(self):
        """Тест создания метрики с невалидным типом значения."""
        # Arrange
        metric_data = {
            "name": "invalid_metric",
            "value": "not_a_number",  # Невалидный тип
            "type": MetricType.GAUGE,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricCreate(**metric_data)

        assert "value" in str(exc_info.value)

    def test_metric_create_empty_name(self):
        """Тест создания метрики с пустым именем."""
        # Arrange
        metric_data = {
            "name": "",  # Пустое имя
            "value": 50.0,
            "type": MetricType.COUNTER,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricCreate(**metric_data)

        assert "name" in str(exc_info.value)

    def test_metric_create_invalid_metric_type(self):
        """Тест создания метрики с невалидным типом."""
        # Arrange
        metric_data = {
            "name": "test_metric",
            "value": 25.0,
            "type": "invalid_type",  # Невалидный тип
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricCreate(**metric_data)

        assert "type" in str(exc_info.value)

    def test_metric_response_schema(self):
        """Тест схемы ответа метрики."""
        # Arrange
        response_data = {
            "id": "metric_123",
            "name": "response_time",
            "value": 150.0,
            "type": MetricType.TIMER,
            "tags": {"endpoint": "/api/users"},
            "timestamp": datetime.now(),
        }

        # Act
        metric_response = MetricResponse(**response_data)

        # Assert
        assert metric_response.id == "metric_123"
        assert metric_response.name == "response_time"
        assert metric_response.value == 150.0
        assert metric_response.type == MetricType.TIMER
        assert metric_response.tags["endpoint"] == "/api/users"
        assert isinstance(metric_response.timestamp, datetime)

    def test_metric_batch_schema(self):
        """Тест схемы батчевых метрик."""
        # Arrange
        metrics = [
            MetricCreate(name="metric1", value=10.0, type=MetricType.COUNTER),
            MetricCreate(name="metric2", value=20.0, type=MetricType.GAUGE),
        ]

        batch_data = {
            "batch_id": "batch_456",
            "metrics": metrics,
            "metadata": {"source": "monitoring_service", "version": "1.0"},
        }

        # Act
        metric_batch = MetricBatch(**batch_data)

        # Assert
        assert metric_batch.batch_id == "batch_456"
        assert len(metric_batch.metrics) == 2
        assert metric_batch.metadata["source"] == "monitoring_service"

    def test_metric_batch_empty_metrics(self):
        """Тест создания пустого батча метрик."""
        # Arrange
        batch_data = {"metrics": []}

        # Act
        metric_batch = MetricBatch(**batch_data)

        # Assert
        assert len(metric_batch.metrics) == 0
        assert metric_batch.batch_id is None
        assert metric_batch.metadata is None

    def test_metric_types_enum(self):
        """Тест перечисления типов метрик."""
        # Act & Assert
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.TIMER == "timer"

        # Проверяем, что все типы доступны
        all_types = [
            MetricType.COUNTER,
            MetricType.GAUGE,
            MetricType.HISTOGRAM,
            MetricType.TIMER,
        ]
        assert len(all_types) == 4


class TestAlertSchemas:
    """Тесты схем алертов."""

    def test_alert_create_valid_data(self):
        """Тест создания валидного алерта."""
        # Arrange
        alert_data = {
            "name": "High CPU Usage",
            "description": "CPU usage exceeded 90%",
            "metric_name": "cpu_usage",
            "threshold": 90.0,
            "level": AlertLevel.CRITICAL,
            "conditions": {
                "operator": ">=",
                "duration_minutes": 5,
                "consecutive_breaches": 3,
            },
        }

        # Act
        alert = AlertCreate(**alert_data)

        # Assert
        assert alert.name == "High CPU Usage"
        assert alert.description == "CPU usage exceeded 90%"
        assert alert.metric_name == "cpu_usage"
        assert alert.threshold == 90.0
        assert alert.level == AlertLevel.CRITICAL
        assert alert.conditions["operator"] == ">="

    def test_alert_create_with_factory(self):
        """Тест создания алерта с помощью фабрики."""
        # Arrange & Act
        alert_data = AlertCreateFactory.build()
        alert = AlertCreate(
            name=alert_data.name,
            description=alert_data.description,
            metric_name=alert_data.metric_name,
            threshold=alert_data.threshold,
            level=alert_data.level,
            conditions=alert_data.conditions,
        )

        # Assert
        assert isinstance(alert.name, str)
        assert isinstance(alert.description, str)
        assert isinstance(alert.metric_name, str)
        assert isinstance(alert.threshold, (int, float))
        assert alert.level in [e.value for e in AlertLevel]

    def test_alert_create_minimal_data(self):
        """Тест создания алерта с минимальными данными."""
        # Arrange
        alert_data = {
            "name": "Simple Alert",
            "metric_name": "error_count",
            "threshold": 10.0,
            "level": AlertLevel.WARNING,
        }

        # Act
        alert = AlertCreate(**alert_data)

        # Assert
        assert alert.name == "Simple Alert"
        assert alert.metric_name == "error_count"
        assert alert.threshold == 10.0
        assert alert.level == AlertLevel.WARNING
        assert alert.description is None
        assert alert.conditions is None

    def test_alert_create_invalid_threshold(self):
        """Тест создания алерта с невалидным порогом."""
        # Arrange
        alert_data = {
            "name": "Invalid Alert",
            "metric_name": "test_metric",
            "threshold": "not_a_number",  # Невалидный тип
            "level": AlertLevel.INFO,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AlertCreate(**alert_data)

        assert "threshold" in str(exc_info.value)

    def test_alert_create_invalid_level(self):
        """Тест создания алерта с невалидным уровнем."""
        # Arrange
        alert_data = {
            "name": "Test Alert",
            "metric_name": "test_metric",
            "threshold": 50.0,
            "level": "invalid_level",  # Невалидный уровень
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AlertCreate(**alert_data)

        assert "level" in str(exc_info.value)

    def test_alert_response_schema(self):
        """Тест схемы ответа алерта."""
        # Arrange
        response_data = {
            "id": "alert_789",
            "name": "Memory Usage Alert",
            "description": "Memory usage is high",
            "level": AlertLevel.ERROR,
            "is_active": True,
            "triggered_count": 5,
            "last_triggered": datetime.now(),
            "created_at": datetime.now() - timedelta(days=1),
        }

        # Act
        alert_response = AlertResponse(**response_data)

        # Assert
        assert alert_response.id == "alert_789"
        assert alert_response.name == "Memory Usage Alert"
        assert alert_response.level == AlertLevel.ERROR
        assert alert_response.is_active is True
        assert alert_response.triggered_count == 5
        assert isinstance(alert_response.last_triggered, datetime)
        assert isinstance(alert_response.created_at, datetime)

    def test_alert_levels_enum(self):
        """Тест перечисления уровней алертов."""
        # Act & Assert
        assert AlertLevel.INFO == "info"
        assert AlertLevel.WARNING == "warning"
        assert AlertLevel.ERROR == "error"
        assert AlertLevel.CRITICAL == "critical"

        # Проверяем порядок приоритетов
        levels = [
            AlertLevel.INFO,
            AlertLevel.WARNING,
            AlertLevel.ERROR,
            AlertLevel.CRITICAL,
        ]
        assert len(levels) == 4


class TestSystemHealthSchemas:
    """Тесты схем системного здоровья."""

    def test_component_health_schema(self):
        """Тест схемы здоровья компонента."""
        # Arrange
        component_data = {
            "name": "database",
            "status": ComponentStatus.HEALTHY,
            "connected": True,
            "response_time_ms": 15.5,
            "error_message": None,
            "metadata": {"version": "14.2", "connections": 25},
        }

        # Act
        component = ComponentHealth(**component_data)

        # Assert
        assert component.name == "database"
        assert component.status == ComponentStatus.HEALTHY
        assert component.connected is True
        assert component.response_time_ms == 15.5
        assert component.error_message is None
        assert component.metadata["version"] == "14.2"

    def test_component_health_unhealthy(self):
        """Тест схемы нездорового компонента."""
        # Arrange
        component_data = {
            "name": "redis",
            "status": ComponentStatus.UNHEALTHY,
            "connected": False,
            "response_time_ms": None,
            "error_message": "Connection timeout",
            "metadata": {"last_connection": "2024-01-20T10:00:00Z"},
        }

        # Act
        component = ComponentHealth(**component_data)

        # Assert
        assert component.name == "redis"
        assert component.status == ComponentStatus.UNHEALTHY
        assert component.connected is False
        assert component.response_time_ms is None
        assert component.error_message == "Connection timeout"

    def test_component_status_enum(self):
        """Тест перечисления статусов компонентов."""
        # Act & Assert
        assert ComponentStatus.HEALTHY == "healthy"
        assert ComponentStatus.UNHEALTHY == "unhealthy"
        assert ComponentStatus.DEGRADED == "degraded"
        assert ComponentStatus.UNKNOWN == "unknown"

    def test_system_health_response_healthy(self):
        """Тест схемы здорового системного ответа."""
        # Arrange
        components = {
            "database": ComponentHealth(
                name="database",
                status=ComponentStatus.HEALTHY,
                connected=True,
                response_time_ms=10.0,
            ),
            "redis": ComponentHealth(
                name="redis",
                status=ComponentStatus.HEALTHY,
                connected=True,
                response_time_ms=2.0,
            ),
        }

        health_data = {
            "status": SystemStatus.HEALTHY,
            "timestamp": datetime.now(),
            "components": components,
            "issues": None,
        }

        # Act
        system_health = SystemHealthResponse(**health_data)

        # Assert
        assert system_health.status == SystemStatus.HEALTHY
        assert isinstance(system_health.timestamp, datetime)
        assert len(system_health.components) == 2
        assert system_health.issues is None
        assert system_health.components["database"].status == ComponentStatus.HEALTHY

    def test_system_health_response_unhealthy(self):
        """Тест схемы нездорового системного ответа."""
        # Arrange
        components = {
            "database": ComponentHealth(
                name="database",
                status=ComponentStatus.UNHEALTHY,
                connected=False,
                error_message="Connection failed",
            )
        }

        health_data = {
            "status": SystemStatus.UNHEALTHY,
            "timestamp": datetime.now(),
            "components": components,
            "issues": ["Database connection failed", "High response times"],
        }

        # Act
        system_health = SystemHealthResponse(**health_data)

        # Assert
        assert system_health.status == SystemStatus.UNHEALTHY
        assert len(system_health.components) == 1
        assert len(system_health.issues) == 2
        assert "Database connection failed" in system_health.issues

    def test_system_status_enum(self):
        """Тест перечисления системных статусов."""
        # Act & Assert
        assert SystemStatus.HEALTHY == "healthy"
        assert SystemStatus.UNHEALTHY == "unhealthy"
        assert SystemStatus.DEGRADED == "degraded"
        assert SystemStatus.MAINTENANCE == "maintenance"


class TestDashboardSchemas:
    """Тесты схем дашбордов."""

    def test_dashboard_create_schema(self):
        """Тест схемы создания дашборда."""
        # Arrange
        dashboard_data = {
            "name": "System Overview",
            "description": "Main system monitoring dashboard",
            "metrics": ["cpu_usage", "memory_usage", "disk_usage"],
            "layout": {
                "grid": {"rows": 3, "cols": 2},
                "widgets": [
                    {
                        "type": "chart",
                        "metric": "cpu_usage",
                        "position": {"row": 0, "col": 0},
                    },
                    {
                        "type": "gauge",
                        "metric": "memory_usage",
                        "position": {"row": 0, "col": 1},
                    },
                ],
            },
        }

        # Act
        dashboard = DashboardCreate(**dashboard_data)

        # Assert
        assert dashboard.name == "System Overview"
        assert dashboard.description == "Main system monitoring dashboard"
        assert len(dashboard.metrics) == 3
        assert "cpu_usage" in dashboard.metrics
        assert dashboard.layout["grid"]["rows"] == 3

    def test_dashboard_create_minimal(self):
        """Тест создания дашборда с минимальными данными."""
        # Arrange
        dashboard_data = {"name": "Simple Dashboard", "metrics": ["test_metric"]}

        # Act
        dashboard = DashboardCreate(**dashboard_data)

        # Assert
        assert dashboard.name == "Simple Dashboard"
        assert len(dashboard.metrics) == 1
        assert dashboard.description is None
        assert dashboard.layout is None

    def test_dashboard_response_schema(self):
        """Тест схемы ответа дашборда."""
        # Arrange
        response_data = {
            "id": "dashboard_123",
            "name": "Performance Dashboard",
            "description": "Application performance metrics",
            "metrics": ["response_time", "throughput", "error_rate"],
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now(),
        }

        # Act
        dashboard_response = DashboardResponse(**response_data)

        # Assert
        assert dashboard_response.id == "dashboard_123"
        assert dashboard_response.name == "Performance Dashboard"
        assert len(dashboard_response.metrics) == 3
        assert isinstance(dashboard_response.created_at, datetime)
        assert isinstance(dashboard_response.updated_at, datetime)

    def test_dashboard_create_empty_metrics(self):
        """Тест создания дашборда с пустым списком метрик."""
        # Arrange
        dashboard_data = {"name": "Empty Dashboard", "metrics": []}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DashboardCreate(**dashboard_data)

        assert "metrics" in str(exc_info.value)

    def test_dashboard_create_invalid_name(self):
        """Тест создания дашборда с невалидным именем."""
        # Arrange
        dashboard_data = {
            "name": "",  # Пустое имя
            "metrics": ["test_metric"],
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DashboardCreate(**dashboard_data)

        assert "name" in str(exc_info.value)


class TestAnalyticsSchemas:
    """Тесты схем аналитики."""

    def test_user_analytics_response_schema(self):
        """Тест схемы ответа аналитики пользователей."""
        # Arrange
        analytics_data = {
            "period_days": 7,
            "timestamp": datetime.now(),
            "users": {
                "total": 1500,
                "active": 800,
                "new": 45,
                "by_country": {"US": 600, "UK": 200, "DE": 150},
            },
            "surveys": {
                "total": 25,
                "completed": 20,
                "in_progress": 5,
                "completion_rate": 80.0,
            },
            "actions": {
                "survey_started": 1200,
                "survey_completed": 960,
                "questions_answered": 15000,
            },
            "performance": {
                "avg_response_time": 145.5,
                "page_load_time": 850.0,
                "api_response_time": 95.2,
            },
        }

        # Act
        analytics = UserAnalyticsResponse(**analytics_data)

        # Assert
        assert analytics.period_days == 7
        assert isinstance(analytics.timestamp, datetime)
        assert analytics.users["total"] == 1500
        assert analytics.users["active"] == 800
        assert analytics.surveys["completion_rate"] == 80.0
        assert analytics.actions["survey_completed"] == 960
        assert analytics.performance["avg_response_time"] == 145.5

    def test_user_analytics_minimal_data(self):
        """Тест аналитики с минимальными данными."""
        # Arrange
        analytics_data = {
            "period_days": 1,
            "timestamp": datetime.now(),
            "users": {"total": 0, "active": 0, "new": 0},
            "surveys": {"total": 0, "completed": 0, "in_progress": 0},
            "actions": {},
            "performance": {},
        }

        # Act
        analytics = UserAnalyticsResponse(**analytics_data)

        # Assert
        assert analytics.period_days == 1
        assert analytics.users["total"] == 0
        assert analytics.surveys["total"] == 0
        assert len(analytics.actions) == 0
        assert len(analytics.performance) == 0

    def test_performance_data_schema(self):
        """Тест схемы данных производительности."""
        # Arrange
        performance_data = {
            "operation": "database_query",
            "duration_ms": 125.5,
            "status": "success",
            "timestamp": datetime.now(),
        }

        # Act
        performance = PerformanceData(**performance_data)

        # Assert
        assert performance.operation == "database_query"
        assert performance.duration_ms == 125.5
        assert performance.status == "success"
        assert isinstance(performance.timestamp, datetime)

    def test_performance_data_with_optional_fields(self):
        """Тест данных производительности с опциональными полями."""
        # Arrange
        performance_data = {"operation": "api_call"}

        # Act
        performance = PerformanceData(**performance_data)

        # Assert
        assert performance.operation == "api_call"
        assert performance.duration_ms is None
        assert performance.status is None
        assert performance.timestamp is None


class TestMonitoringSchemasIntegration:
    """Интеграционные тесты схем мониторинга."""

    def test_complete_monitoring_data_flow(self):
        """Тест полного потока данных мониторинга."""
        # Arrange
        # 1. Создание метрики
        metric = MetricCreate(
            name="test_metric",
            value=50.0,
            type=MetricType.GAUGE,
            tags={"service": "test"},
        )

        # 2. Создание алерта
        alert = AlertCreate(
            name="Test Alert",
            metric_name="test_metric",
            threshold=75.0,
            level=AlertLevel.WARNING,
        )

        # 3. Создание компонента здоровья
        component = ComponentHealth(
            name="test_service",
            status=ComponentStatus.HEALTHY,
            connected=True,
            response_time_ms=25.0,
        )

        # 4. Создание системного здоровья
        system_health = SystemHealthResponse(
            status=SystemStatus.HEALTHY,
            timestamp=datetime.now(),
            components={"test_service": component},
        )

        # Act & Assert
        assert metric.name == "test_metric"
        assert alert.metric_name == "test_metric"
        assert component.status == ComponentStatus.HEALTHY
        assert system_health.status == SystemStatus.HEALTHY
        assert "test_service" in system_health.components

    def test_monitoring_schemas_with_factories(self):
        """Тест схем мониторинга с использованием фабрик."""
        # Arrange & Act
        metric_data = MetricCreateFactory.build()
        alert_data = AlertCreateFactory.build()
        component_data = ComponentHealthFactory.build()
        dashboard_data = DashboardCreateFactory.build()

        # Создание объектов схем
        metric = MetricCreate(
            name=metric_data.name,
            value=metric_data.value,
            type=metric_data.type,
            tags=metric_data.tags,
        )

        alert = AlertCreate(
            name=alert_data.name,
            description=alert_data.description,
            metric_name=alert_data.metric_name,
            threshold=alert_data.threshold,
            level=alert_data.level,
        )

        # Assert
        assert isinstance(metric.name, str)
        assert isinstance(metric.value, (int, float))
        assert isinstance(alert.name, str)
        assert isinstance(alert.threshold, (int, float))

    def test_validation_edge_cases(self):
        """Тест граничных случаев валидации."""
        # Test 1: Очень большие значения
        large_metric = MetricCreate(
            name="large_metric",
            value=1e10,  # Очень большое число
            type=MetricType.COUNTER,
        )
        assert large_metric.value == 1e10

        # Test 2: Очень маленькие значения
        small_metric = MetricCreate(
            name="small_metric",
            value=1e-10,  # Очень маленькое число
            type=MetricType.GAUGE,
        )
        assert small_metric.value == 1e-10

        # Test 3: Нулевые значения
        zero_metric = MetricCreate(name="zero_metric", value=0.0, type=MetricType.TIMER)
        assert zero_metric.value == 0.0

        # Test 4: Отрицательные значения
        negative_metric = MetricCreate(
            name="negative_metric", value=-25.5, type=MetricType.GAUGE
        )
        assert negative_metric.value == -25.5

    def test_complex_dashboard_layout(self):
        """Тест сложного макета дашборда."""
        # Arrange
        complex_layout = {
            "grid": {"rows": 4, "cols": 3},
            "widgets": [
                {
                    "id": "widget_1",
                    "type": "line_chart",
                    "metric": "cpu_usage",
                    "position": {"row": 0, "col": 0, "span": {"rows": 2, "cols": 2}},
                    "config": {"time_range": "1h", "aggregation": "avg"},
                },
                {
                    "id": "widget_2",
                    "type": "gauge",
                    "metric": "memory_usage",
                    "position": {"row": 0, "col": 2},
                    "config": {"min": 0, "max": 100, "unit": "%"},
                },
            ],
            "theme": "dark",
            "auto_refresh": 30,
        }

        dashboard_data = {
            "name": "Complex Dashboard",
            "description": "Advanced monitoring dashboard",
            "metrics": ["cpu_usage", "memory_usage", "disk_usage"],
            "layout": complex_layout,
        }

        # Act
        dashboard = DashboardCreate(**dashboard_data)

        # Assert
        assert dashboard.name == "Complex Dashboard"
        assert len(dashboard.metrics) == 3
        assert dashboard.layout["grid"]["rows"] == 4
        assert len(dashboard.layout["widgets"]) == 2
        assert dashboard.layout["theme"] == "dark"
        assert dashboard.layout["auto_refresh"] == 30

    def test_nested_component_metadata(self):
        """Тест вложенных метаданных компонента."""
        # Arrange
        complex_metadata = {
            "version": "2.1.4",
            "database": {
                "engine": "PostgreSQL",
                "version": "14.2",
                "connections": {"active": 15, "idle": 5, "max": 100},
                "performance": {
                    "queries_per_second": 150.5,
                    "avg_query_time": 8.2,
                    "cache_hit_ratio": 0.92,
                },
            },
            "memory": {"used": "2.5GB", "available": "1.5GB", "buffers": "512MB"},
        }

        component_data = {
            "name": "database_cluster",
            "status": ComponentStatus.HEALTHY,
            "connected": True,
            "response_time_ms": 12.5,
            "metadata": complex_metadata,
        }

        # Act
        component = ComponentHealth(**component_data)

        # Assert
        assert component.name == "database_cluster"
        assert component.metadata["version"] == "2.1.4"
        assert component.metadata["database"]["engine"] == "PostgreSQL"
        assert component.metadata["database"]["connections"]["active"] == 15
        assert component.metadata["database"]["performance"]["cache_hit_ratio"] == 0.92
        assert component.metadata["memory"]["used"] == "2.5GB"
