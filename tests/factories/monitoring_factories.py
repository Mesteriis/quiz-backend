"""
Comprehensive Monitoring Factories for Quiz App Testing.

This module provides polyfactory-based factories for all monitoring-related data:
- Metrics and performance data
- Alerts and notifications
- Dashboard configurations
- System health data
- User analytics

All factories follow best practices:
- Proper polyfactory syntax with ModelFactory[PydanticModel]
- Faker integration for realistic data
- UUID for unique identifiers
- Probabilistic distributions for realistic scenarios
- Generate fixtures for test convenience
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory
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


class MetricCreateFactory(ModelFactory[MetricCreate]):
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


class MetricResponseFactory(ModelFactory[MetricResponse]):
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


class MetricBatchFactory(ModelFactory[MetricBatch]):
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


class AlertCreateFactory(ModelFactory[AlertCreate]):
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


class AlertResponseFactory(ModelFactory[AlertResponse]):
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


class DashboardCreateFactory(ModelFactory[DashboardCreate]):
    """Factory for creating dashboard data."""

    __model__ = DashboardCreate

    @classmethod
    def name(cls) -> str:
        """Generate unique dashboard name."""
        return f"dashboard_{uuid.uuid4().hex[:8]}"

    @classmethod
    def description(cls) -> Optional[str]:
        """Generate dashboard description."""
        if fake.boolean(chance_of_getting_true=80):
            return fake.text(max_nb_chars=200)
        return None

    @classmethod
    def metrics(cls) -> List[str]:
        """Generate metrics list."""
        count = fake.random_int(min=3, max=10)
        return [f"metric_{uuid.uuid4().hex[:6]}" for _ in range(count)]

    @classmethod
    def layout(cls) -> Optional[Dict[str, Any]]:
        """Generate dashboard layout."""
        return {
            "grid": {
                "rows": fake.random_int(min=2, max=6),
                "cols": fake.random_int(min=2, max=4),
            },
            "widgets": [
                {
                    "type": "chart",
                    "position": {"x": 0, "y": 0},
                    "size": {"w": 2, "h": 2},
                },
                {
                    "type": "table",
                    "position": {"x": 2, "y": 0},
                    "size": {"w": 2, "h": 1},
                },
            ],
        }


class DashboardResponseFactory(ModelFactory[DashboardResponse]):
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
        if fake.boolean(chance_of_getting_true=80):
            return fake.text(max_nb_chars=200)
        return None

    @classmethod
    def metrics(cls) -> List[str]:
        """Generate metrics list."""
        count = fake.random_int(min=3, max=10)
        return [f"metric_{uuid.uuid4().hex[:6]}" for _ in range(count)]

    @classmethod
    def created_at(cls) -> datetime:
        """Generate creation time."""
        return fake.date_time_between(start_date="-30d", end_date="now")

    @classmethod
    def updated_at(cls) -> datetime:
        """Generate update time."""
        return fake.date_time_between(start_date="-7d", end_date="now")


# ============================================================================
# SYSTEM HEALTH FACTORIES
# ============================================================================


class ComponentHealthFactory(ModelFactory[ComponentHealth]):
    """Factory for component health data."""

    __model__ = ComponentHealth

    @classmethod
    def name(cls) -> str:
        """Generate component name."""
        return fake.random_element(["database", "redis", "api", "worker", "telegram"])

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
            return fake.random.uniform(1.0, 1000.0)
        return None

    @classmethod
    def error_message(cls) -> Optional[str]:
        """Generate error message."""
        if fake.boolean(chance_of_getting_true=20):
            return fake.sentence()
        return None

    @classmethod
    def metadata(cls) -> Optional[Dict[str, Any]]:
        """Generate component metadata."""
        return {
            "version": f"v{fake.random_int(min=1, max=5)}.{fake.random_int(min=0, max=20)}",
            "uptime": fake.random_int(min=3600, max=86400),  # seconds
            "memory_usage": fake.random.uniform(0.1, 0.9),
        }


class SystemHealthResponseFactory(ModelFactory[SystemHealthResponse]):
    """Factory for system health response data."""

    __model__ = SystemHealthResponse

    @classmethod
    def status(cls) -> SystemStatus:
        """Generate system status."""
        return fake.random_element(list(SystemStatus))

    @classmethod
    def timestamp(cls) -> datetime:
        """Generate timestamp."""
        return fake.date_time_between(start_date="-1h", end_date="now")

    @classmethod
    def components(cls) -> Dict[str, ComponentHealth]:
        """Generate components health."""
        components = ["database", "redis", "api", "worker", "telegram"]
        return {
            component: ComponentHealthFactory.build(name=component)
            for component in components
        }

    @classmethod
    def issues(cls) -> Optional[List[str]]:
        """Generate issues list."""
        if fake.boolean(chance_of_getting_true=30):
            count = fake.random_int(min=1, max=3)
            return [fake.sentence() for _ in range(count)]
        return None


# ============================================================================
# USER ANALYTICS FACTORIES
# ============================================================================


class UserAnalyticsResponseFactory(ModelFactory[UserAnalyticsResponse]):
    """Factory for user analytics response data."""

    __model__ = UserAnalyticsResponse

    @classmethod
    def period_days(cls) -> int:
        """Generate period days."""
        return fake.random_element([1, 7, 30, 90])

    @classmethod
    def timestamp(cls) -> datetime:
        """Generate timestamp."""
        return fake.date_time_between(start_date="-1d", end_date="now")

    @classmethod
    def users(cls) -> Dict[str, Any]:
        """Generate user statistics."""
        return {
            "total": fake.random_int(min=100, max=10000),
            "active": fake.random_int(min=50, max=5000),
            "new": fake.random_int(min=10, max=500),
            "verified": fake.random_int(min=80, max=8000),
            "retention_rate": fake.random.uniform(0.3, 0.9),
        }

    @classmethod
    def surveys(cls) -> Dict[str, Any]:
        """Generate survey statistics."""
        return {
            "total": fake.random_int(min=10, max=1000),
            "active": fake.random_int(min=5, max=500),
            "completed": fake.random_int(min=50, max=5000),
            "avg_completion_time": fake.random.uniform(120.0, 1800.0),  # seconds
            "completion_rate": fake.random.uniform(0.4, 0.9),
        }

    @classmethod
    def actions(cls) -> Dict[str, Any]:
        """Generate action statistics."""
        return {
            "total": fake.random_int(min=1000, max=100000),
            "logins": fake.random_int(min=100, max=10000),
            "registrations": fake.random_int(min=10, max=1000),
            "survey_starts": fake.random_int(min=50, max=5000),
            "survey_completions": fake.random_int(min=30, max=3000),
        }

    @classmethod
    def performance(cls) -> Dict[str, Any]:
        """Generate performance statistics."""
        return {
            "avg_response_time": fake.random.uniform(50.0, 500.0),  # ms
            "error_rate": fake.random.uniform(0.01, 0.1),
            "throughput": fake.random.uniform(100.0, 1000.0),  # requests/second
            "uptime": fake.random.uniform(0.95, 1.0),
        }


# ============================================================================
# PERFORMANCE FACTORIES
# ============================================================================


class PerformanceDataFactory(ModelFactory[PerformanceData]):
    """Factory for performance data."""

    __model__ = PerformanceData

    @classmethod
    def operation(cls) -> str:
        """Generate operation name."""
        operations = [
            "user_login",
            "survey_create",
            "survey_complete",
            "response_save",
            "profile_update",
            "auth_validate",
            "database_query",
            "cache_access",
        ]
        return fake.random_element(operations)

    @classmethod
    def duration_ms(cls) -> float:
        """Generate duration in milliseconds."""
        return fake.random.uniform(1.0, 2000.0)

    @classmethod
    def status(cls) -> str:
        """Generate operation status."""
        return fake.random_element(["success", "error", "timeout", "cancelled"])

    @classmethod
    def timestamp(cls) -> Optional[datetime]:
        """Generate timestamp."""
        if fake.boolean(chance_of_getting_true=90):
            return fake.date_time_between(start_date="-1d", end_date="now")
        return None


# ============================================================================
# SPECIALIZED FACTORIES
# ============================================================================


class HighLoadMetricFactory(MetricCreateFactory):
    """Factory for high load metrics."""

    @classmethod
    def name(cls) -> str:
        """Generate high load metric name."""
        return f"high_load_{uuid.uuid4().hex[:8]}"

    @classmethod
    def value(cls) -> float:
        """Generate high load metric value."""
        return fake.random.uniform(800.0, 1000.0)

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate high load tags."""
        return {
            "environment": "production",
            "severity": "high",
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
        """Generate error metric value."""
        return fake.random.uniform(1.0, 100.0)

    @classmethod
    def type(cls) -> MetricType:
        """Generate error metric type."""
        return MetricType.COUNTER

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate error tags."""
        return {
            "error_type": fake.random_element(
                ["validation", "auth", "database", "network"]
            ),
            "service": fake.random_element(["api", "worker", "bot"]),
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
        """Generate performance metric value."""
        return fake.random.uniform(10.0, 500.0)

    @classmethod
    def type(cls) -> MetricType:
        """Generate performance metric type."""
        return fake.random_element([MetricType.TIMER, MetricType.HISTOGRAM])

    @classmethod
    def tags(cls) -> Optional[Dict[str, str]]:
        """Generate performance tags."""
        return {
            "operation": fake.random_element(["query", "insert", "update", "delete"]),
            "table": fake.random_element(["users", "surveys", "responses", "profiles"]),
            "optimization": fake.random_element(["enabled", "disabled"]),
        }


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


def metric_create_fixture():
    """Fixture for metric creation data."""
    return MetricCreateFactory.build()


def multiple_metrics_fixture():
    """Fixture for multiple metrics data."""
    return MetricCreateFactory.batch(5)


def alert_create_fixture():
    """Fixture for alert creation data."""
    return AlertCreateFactory.build()


def dashboard_create_fixture():
    """Fixture for dashboard creation data."""
    return DashboardCreateFactory.build()


def system_health_fixture():
    """Fixture for system health data."""
    return SystemHealthResponseFactory.build()


def user_analytics_fixture():
    """Fixture for user analytics data."""
    return UserAnalyticsResponseFactory.build()


def performance_metric_fixture():
    """Fixture for performance metric data."""
    return PerformanceMetricFactory.build()


def multiple_performance_fixture():
    """Fixture for multiple performance data."""
    return PerformanceDataFactory.batch(10)


def error_metric_fixture():
    """Fixture for error metric data."""
    return ErrorMetricFactory.build()


def high_load_metric_fixture():
    """Fixture for high load metric data."""
    return HighLoadMetricFactory.build()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def generate_metrics_fixture():
    """Fixture for generating metrics."""

    def _generate_metrics(count: int = 5, **kwargs) -> List[MetricCreate]:
        """Generate metrics with custom parameters."""
        return MetricCreateFactory.batch(count, **kwargs)

    return _generate_metrics


def generate_alerts_fixture():
    """Fixture for generating alerts."""

    def _generate_alerts(count: int = 3, **kwargs) -> List[AlertCreate]:
        """Generate alerts with custom parameters."""
        return AlertCreateFactory.batch(count, **kwargs)

    return _generate_alerts


def generate_dashboards_fixture():
    """Fixture for generating dashboards."""

    def _generate_dashboards(count: int = 2, **kwargs) -> List[DashboardCreate]:
        """Generate dashboards with custom parameters."""
        return DashboardCreateFactory.batch(count, **kwargs)

    return _generate_dashboards
