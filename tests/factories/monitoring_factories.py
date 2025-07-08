"""
Comprehensive Monitoring Factories for Quiz App Testing.

This module provides polyfactory-based factories for all monitoring-related data:
- Metrics and performance data
- Alerts and notifications
- Dashboard configurations
- System health data
- User analytics

All factories follow best practices:
- Proper polyfactory syntax with BaseFactory[Model]
- Faker integration for realistic data
- UUID for unique identifiers
- Probabilistic distributions for realistic scenarios
- Generate fixtures for test convenience
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker
from polyfactory.factories import BaseFactory
from polyfactory.fields import Use, PostGenerated, Require
from polyfactory.pytest_plugin import register_fixture

from src.schemas.monitoring import (
    MetricCreate,
    MetricResponse,
    MetricBatch,
    AlertCreate,
    AlertResponse,
    DashboardCreate,
    DashboardResponse,
    SystemHealthResponse,
    ComponentHealth,
    UserAnalyticsResponse,
    PerformanceData,
    MetricType,
    AlertLevel,
    SystemStatus,
    ComponentStatus,
)

# Global faker instance
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


# ============================================================================
# METRIC FACTORIES
# ============================================================================


class MetricCreateFactory(BaseFactory[MetricCreate]):
    """Factory for creating metric data."""

    __model__ = MetricCreate

    @classmethod
    def name(cls) -> str:
        """Generate unique metric name."""
        return f"metric_{uuid.uuid4().hex[:8]}_{fake.random_int(min=1000, max=9999)}"

    @classmethod
    def value(cls) -> float:
        """Generate realistic metric value."""
        return fake.random.uniform(1.0, 1000.0)

    @classmethod
    def type(cls) -> MetricType:
        """Generate metric type."""
        return fake.random_element(list(MetricType))

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate metric tags."""
        if fake.boolean(chance_of_getting_true=70):
            return {
                "environment": fake.random_element(["production", "staging", "test"]),
                "service": fake.random_element(["api", "web", "worker", "bot"]),
                "version": f"v{fake.random_int(min=1, max=10)}.{fake.random_int(min=0, max=99)}",
            }
        return None


class MetricResponseFactory(BaseFactory[MetricResponse]):
    """Factory for metric response data."""

    __model__ = MetricResponse

    @classmethod
    def id(cls) -> str:
        """Generate unique metric ID."""
        return str(uuid.uuid4())

    @classmethod
    def name(cls) -> str:
        """Generate metric name."""
        return f"response_metric_{uuid.uuid4().hex[:8]}"

    @classmethod
    def value(cls) -> float:
        """Generate metric value."""
        return fake.random.uniform(1.0, 1000.0)

    @classmethod
    def type(cls) -> MetricType:
        """Generate metric type."""
        return fake.random_element(list(MetricType))

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate metric tags."""
        return {
            "source": fake.random_element(["api", "web", "worker"]),
            "component": fake.random_element(["auth", "surveys", "notifications"]),
        }

    @classmethod
    def timestamp(cls) -> datetime:
        """Generate timestamp."""
        return fake.date_time_between(start_date="-1d", end_date="now")


class MetricBatchFactory(BaseFactory[MetricBatch]):
    """Factory for batch metric operations."""

    __model__ = MetricBatch

    @classmethod
    def batch_id(cls) -> Optional[str]:
        """Generate batch ID."""
        return f"batch_{uuid.uuid4().hex[:12]}"

    @classmethod
    def metrics(cls) -> List[MetricCreate]:
        """Generate batch of metrics."""
        count = fake.random_int(min=5, max=20)
        return [MetricCreateFactory.build() for _ in range(count)]

    @classmethod
    def metadata(cls) -> Optional[Dict[str, Any]]:
        """Generate batch metadata."""
        return {
            "source": fake.random_element(["api", "collector", "agent"]),
            "timestamp": datetime.now().isoformat(),
            "total_metrics": fake.random_int(min=5, max=20),
        }


# ============================================================================
# ALERT FACTORIES
# ============================================================================


class AlertCreateFactory(BaseFactory[AlertCreate]):
    """Factory for creating alert data."""

    __model__ = AlertCreate

    @classmethod
    def name(cls) -> str:
        """Generate unique alert name."""
        return f"alert_{uuid.uuid4().hex[:8]}_{fake.random_int(min=1000, max=9999)}"

    @classmethod
    def description(cls) -> str:
        """Generate alert description."""
        return fake.text(max_nb_chars=200)

    @classmethod
    def metric_name(cls) -> str:
        """Generate metric name for alert."""
        return f"alert_metric_{uuid.uuid4().hex[:6]}"

    @classmethod
    def threshold(cls) -> float:
        """Generate alert threshold."""
        return fake.random.uniform(10.0, 1000.0)

    @classmethod
    def level(cls) -> AlertLevel:
        """Generate alert level."""
        return fake.random_element(list(AlertLevel))

    @classmethod
    def conditions(cls) -> Dict[str, Any]:
        """Generate alert conditions."""
        return {
            "operator": fake.random_element(["gt", "lt", "eq", "ge", "le"]),
            "duration": fake.random_int(min=60, max=3600),  # seconds
            "evaluation_window": fake.random_int(min=300, max=1800),  # seconds
        }


class AlertResponseFactory(BaseFactory[AlertResponse]):
    """Factory for alert response data."""

    __model__ = AlertResponse

    @classmethod
    def id(cls) -> str:
        """Generate alert ID."""
        return str(uuid.uuid4())

    @classmethod
    def name(cls) -> str:
        """Generate alert name."""
        return f"response_alert_{uuid.uuid4().hex[:8]}"

    @classmethod
    def description(cls) -> str:
        """Generate alert description."""
        return fake.text(max_nb_chars=200)

    @classmethod
    def level(cls) -> AlertLevel:
        """Generate alert level."""
        return fake.random_element(list(AlertLevel))

    @classmethod
    def is_active(cls) -> bool:
        """Generate alert active status."""
        return fake.boolean(chance_of_getting_true=70)

    @classmethod
    def triggered_count(cls) -> int:
        """Generate triggered count."""
        return fake.random_int(min=0, max=100)

    @classmethod
    def last_triggered(cls) -> Optional[datetime]:
        """Generate last triggered time."""
        if fake.boolean(chance_of_getting_true=60):
            return fake.date_time_between(start_date="-7d", end_date="now")
        return None

    @classmethod
    def created_at(cls) -> datetime:
        """Generate creation time."""
        return fake.date_time_between(start_date="-30d", end_date="now")


# ============================================================================
# DASHBOARD FACTORIES
# ============================================================================


class DashboardCreateFactory(BaseFactory[DashboardCreate]):
    """Factory for creating dashboard data."""

    __model__ = DashboardCreate

    @classmethod
    def name(cls) -> str:
        """Generate unique dashboard name."""
        return f"dashboard_{uuid.uuid4().hex[:8]}_{fake.random_int(min=1000, max=9999)}"

    @classmethod
    def description(cls) -> Optional[str]:
        """Generate dashboard description."""
        if fake.boolean(chance_of_getting_true=70):
            return fake.text(max_nb_chars=300)
        return None

    @classmethod
    def metrics(cls) -> List[str]:
        """Generate list of metrics for dashboard."""
        count = fake.random_int(min=3, max=10)
        return [f"dashboard_metric_{uuid.uuid4().hex[:6]}" for _ in range(count)]

    @classmethod
    def layout(cls) -> Optional[Dict[str, Any]]:
        """Generate dashboard layout."""
        return {
            "columns": fake.random_int(min=2, max=4),
            "rows": fake.random_int(min=2, max=6),
            "refresh_interval": fake.random_element([30, 60, 300, 600]),  # seconds
        }


class DashboardResponseFactory(BaseFactory[DashboardResponse]):
    """Factory for dashboard response data."""

    __model__ = DashboardResponse

    @classmethod
    def id(cls) -> str:
        """Generate dashboard ID."""
        return str(uuid.uuid4())

    @classmethod
    def name(cls) -> str:
        """Generate dashboard name."""
        return f"response_dashboard_{uuid.uuid4().hex[:8]}"

    @classmethod
    def description(cls) -> Optional[str]:
        """Generate dashboard description."""
        if fake.boolean(chance_of_getting_true=70):
            return fake.text(max_nb_chars=300)
        return None

    @classmethod
    def metrics(cls) -> List[str]:
        """Generate metrics list."""
        count = fake.random_int(min=3, max=10)
        return [f"metric_{uuid.uuid4().hex[:6]}" for _ in range(count)]

    @classmethod
    def created_at(cls) -> datetime:
        """Generate creation time."""
        return fake.date_time_between(start_date="-90d", end_date="now")

    @classmethod
    def updated_at(cls) -> datetime:
        """Generate update time."""
        return fake.date_time_between(start_date="-7d", end_date="now")


# ============================================================================
# SYSTEM HEALTH FACTORIES
# ============================================================================


class ComponentHealthFactory(BaseFactory[ComponentHealth]):
    """Factory for component health data."""

    __model__ = ComponentHealth

    @classmethod
    def name(cls) -> str:
        """Generate component name."""
        return fake.random_element(["database", "redis", "application", "telegram_bot"])

    @classmethod
    def status(cls) -> ComponentStatus:
        """Generate component status."""
        return fake.random_element(list(ComponentStatus))

    @classmethod
    def connected(cls) -> bool:
        """Generate connection status."""
        return fake.boolean(chance_of_getting_true=85)

    @classmethod
    def response_time_ms(cls) -> Optional[float]:
        """Generate response time."""
        if fake.boolean(chance_of_getting_true=80):
            return fake.random.uniform(1.0, 500.0)
        return None

    @classmethod
    def error_message(cls) -> Optional[str]:
        """Generate error message."""
        if fake.boolean(chance_of_getting_true=20):
            return fake.text(max_nb_chars=100)
        return None

    @classmethod
    def metadata(cls) -> Optional[Dict[str, Any]]:
        """Generate component metadata."""
        return {
            "version": f"v{fake.random_int(min=1, max=5)}.{fake.random_int(min=0, max=99)}",
            "uptime": fake.random_int(min=3600, max=86400),  # seconds
            "last_check": datetime.now().isoformat(),
        }


class SystemHealthResponseFactory(BaseFactory[SystemHealthResponse]):
    """Factory for system health response data."""

    __model__ = SystemHealthResponse

    @classmethod
    def status(cls) -> SystemStatus:
        """Generate system status."""
        return fake.random_element(list(SystemStatus))

    @classmethod
    def timestamp(cls) -> datetime:
        """Generate timestamp."""
        return datetime.now()

    @classmethod
    def components(cls) -> Dict[str, ComponentHealth]:
        """Generate components health."""
        components = ["database", "redis", "application", "telegram_bot"]
        return {
            component: ComponentHealthFactory.build(name=component)
            for component in components
        }

    @classmethod
    def issues(cls) -> Optional[List[str]]:
        """Generate system issues."""
        if fake.boolean(chance_of_getting_true=30):
            count = fake.random_int(min=1, max=3)
            return [fake.text(max_nb_chars=100) for _ in range(count)]
        return None


# ============================================================================
# USER ANALYTICS FACTORIES
# ============================================================================


class UserAnalyticsResponseFactory(BaseFactory[UserAnalyticsResponse]):
    """Factory for user analytics response data."""

    __model__ = UserAnalyticsResponse

    @classmethod
    def period_days(cls) -> int:
        """Generate analytics period."""
        return fake.random_element([1, 7, 30, 90])

    @classmethod
    def timestamp(cls) -> datetime:
        """Generate timestamp."""
        return datetime.now()

    @classmethod
    def users(cls) -> Dict[str, Any]:
        """Generate user analytics."""
        return {
            "new_registrations": fake.random_int(min=0, max=100),
            "active_users": fake.random_int(min=50, max=1000),
            "verified_users": fake.random_int(min=30, max=500),
            "telegram_users": fake.random_int(min=20, max=300),
        }

    @classmethod
    def surveys(cls) -> Dict[str, Any]:
        """Generate survey analytics."""
        return {
            "completions": fake.random_int(min=0, max=500),
            "new_surveys": fake.random_int(min=0, max=50),
            "top_surveys": [
                {
                    "title": fake.text(max_nb_chars=50),
                    "responses": fake.random_int(min=10, max=100),
                }
                for _ in range(fake.random_int(min=3, max=8))
            ],
        }

    @classmethod
    def actions(cls) -> Dict[str, Any]:
        """Generate action analytics."""
        return {
            "total_actions": fake.random_int(min=100, max=5000),
            "unique_users": fake.random_int(min=50, max=1000),
            "top_actions": [
                {
                    "action": fake.random_element(
                        ["survey_start", "survey_complete", "login", "telegram_auth"]
                    ),
                    "count": fake.random_int(min=10, max=200),
                }
                for _ in range(5)
            ],
        }

    @classmethod
    def performance(cls) -> Dict[str, Any]:
        """Generate performance analytics."""
        operations = ["api_request", "survey_load", "auth_check", "telegram_message"]
        return {
            operation: {
                "avg_ms": fake.random.uniform(10.0, 500.0),
                "min_ms": fake.random.uniform(1.0, 50.0),
                "max_ms": fake.random.uniform(100.0, 2000.0),
                "count": fake.random_int(min=100, max=10000),
            }
            for operation in operations
        }


# ============================================================================
# PERFORMANCE FACTORIES
# ============================================================================


class PerformanceDataFactory(BaseFactory[PerformanceData]):
    """Factory for performance data."""

    __model__ = PerformanceData

    @classmethod
    def operation(cls) -> str:
        """Generate operation name."""
        return fake.random_element(
            [
                "api_request",
                "database_query",
                "redis_operation",
                "file_upload",
                "survey_load",
                "auth_check",
                "telegram_message",
            ]
        )

    @classmethod
    def duration_ms(cls) -> float:
        """Generate duration in milliseconds."""
        return fake.random.uniform(1.0, 5000.0)

    @classmethod
    def status(cls) -> str:
        """Generate operation status."""
        return fake.random_element(["success", "error", "timeout", "cancelled"])

    @classmethod
    def timestamp(cls) -> Optional[datetime]:
        """Generate timestamp."""
        return fake.date_time_between(start_date="-1h", end_date="now")


# ============================================================================
# SPECIALIZED FACTORIES
# ============================================================================


class HighLoadMetricFactory(MetricCreateFactory):
    """Factory for high-load metrics."""

    @classmethod
    def name(cls) -> str:
        """Generate high-load metric name."""
        return f"high_load_{uuid.uuid4().hex[:8]}"

    @classmethod
    def value(cls) -> float:
        """Generate high values."""
        return fake.random.uniform(1000.0, 10000.0)

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate high-load tags."""
        return {
            "environment": "production",
            "priority": "high",
            "load_type": fake.random_element(["cpu", "memory", "disk", "network"]),
        }


class ErrorMetricFactory(MetricCreateFactory):
    """Factory for error metrics."""

    @classmethod
    def name(cls) -> str:
        """Generate error metric name."""
        return f"error_{uuid.uuid4().hex[:8]}"

    @classmethod
    def value(cls) -> float:
        """Generate error count."""
        return fake.random.uniform(1.0, 100.0)

    @classmethod
    def type(cls) -> MetricType:
        """Always counter for errors."""
        return MetricType.COUNTER

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate error tags."""
        return {
            "error_type": fake.random_element(["http_error", "db_error", "auth_error"]),
            "status_code": fake.random_element(
                ["400", "401", "403", "404", "500", "502"]
            ),
            "severity": fake.random_element(["low", "medium", "high", "critical"]),
        }


class PerformanceMetricFactory(MetricCreateFactory):
    """Factory for performance metrics."""

    @classmethod
    def name(cls) -> str:
        """Generate performance metric name."""
        return f"performance_{uuid.uuid4().hex[:8]}"

    @classmethod
    def value(cls) -> float:
        """Generate performance value (duration)."""
        return fake.random.uniform(1.0, 5000.0)

    @classmethod
    def type(cls) -> MetricType:
        """Always timer for performance."""
        return MetricType.TIMER

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate performance tags."""
        return {
            "operation": fake.random_element(
                ["api_request", "database_query", "redis_operation", "file_upload"]
            ),
            "endpoint": fake.random_element(
                ["/api/surveys", "/api/auth", "/api/users", "/api/responses"]
            ),
            "method": fake.random_element(["GET", "POST", "PUT", "DELETE"]),
        }


# ============================================================================
# REGISTER FIXTURES
# ============================================================================


@register_fixture(name="metric_create_data")
def metric_create_fixture():
    """Fixture for metric creation data."""
    return MetricCreateFactory.build()


@register_fixture(name="multiple_metrics_data")
def multiple_metrics_fixture():
    """Fixture for multiple metrics data."""
    return MetricCreateFactory.build_batch(size=10)


@register_fixture(name="alert_create_data")
def alert_create_fixture():
    """Fixture for alert creation data."""
    return AlertCreateFactory.build()


@register_fixture(name="dashboard_create_data")
def dashboard_create_fixture():
    """Fixture for dashboard creation data."""
    return DashboardCreateFactory.build()


@register_fixture(name="system_health_data")
def system_health_fixture():
    """Fixture for system health data."""
    return SystemHealthResponseFactory.build()


@register_fixture(name="user_analytics_data")
def user_analytics_fixture():
    """Fixture for user analytics data."""
    return UserAnalyticsResponseFactory.build()


@register_fixture(name="performance_metric_data")
def performance_metric_fixture():
    """Fixture for performance metric data."""
    return PerformanceMetricFactory.build()


@register_fixture(name="multiple_performance_data")
def multiple_performance_fixture():
    """Fixture for multiple performance data."""
    return PerformanceDataFactory.build_batch(size=15)


@register_fixture(name="error_metric_data")
def error_metric_fixture():
    """Fixture for error metric data."""
    return ErrorMetricFactory.build()


@register_fixture(name="high_load_metric_data")
def high_load_metric_fixture():
    """Fixture for high load metric data."""
    return HighLoadMetricFactory.build()


# ============================================================================
# GENERATE FIXTURES
# ============================================================================


@register_fixture(name="generate_metrics")
def generate_metrics_fixture():
    """Generate fixture for dynamic metrics creation."""

    def _generate_metrics(count: int = 5, **kwargs) -> List[MetricCreate]:
        """Generate metrics with custom parameters."""
        return [MetricCreateFactory.build(**kwargs) for _ in range(count)]

    return _generate_metrics


@register_fixture(name="generate_alerts")
def generate_alerts_fixture():
    """Generate fixture for dynamic alerts creation."""

    def _generate_alerts(count: int = 3, **kwargs) -> List[AlertCreate]:
        """Generate alerts with custom parameters."""
        return [AlertCreateFactory.build(**kwargs) for _ in range(count)]

    return _generate_alerts


@register_fixture(name="generate_dashboards")
def generate_dashboards_fixture():
    """Generate fixture for dynamic dashboards creation."""

    def _generate_dashboards(count: int = 2, **kwargs) -> List[DashboardCreate]:
        """Generate dashboards with custom parameters."""
        return [DashboardCreateFactory.build(**kwargs) for _ in range(count)]

    return _generate_dashboards
