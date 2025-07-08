"""
Comprehensive Monitoring Test Configuration.

This module provides fixtures, parametrized data, and test utilities for monitoring tests.
Includes fixtures for all monitoring components with realistic data scenarios.

All fixtures follow best practices:
- Async/await for database operations
- Proper cleanup and isolation
- Realistic data scenarios
- Performance-focused configurations
- Context7 integration ready
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator, Generator

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.monitoring_factories import (
    MetricCreateFactory,
    MetricResponseFactory,
    MetricBatchFactory,
    AlertCreateFactory,
    AlertResponseFactory,
    ComponentHealthFactory,
    SystemHealthResponseFactory,
    PerformanceMetricFactory,
    PerformanceSummaryFactory,
    PerformanceReportFactory,
    UserActionDataFactory,
    TopSurveyFactory,
    UserAnalyticsResponseFactory,
    DashboardMetricFactory,
    DashboardCreateFactory,
    DashboardResponseFactory,
    MonitoringConfigFactory,
    RealTimeMetricsResponseFactory,
    BulkMetricsCreateFactory,
    BulkOperationResponseFactory,
    HighPerformanceMetricFactory,
    ErrorMetricFactory,
    MemoryMetricFactory,
    PredictableMetricFactory,
    CriticalAlertFactory,
)
from src.services.monitoring_service import MonitoringService, get_monitoring_service
from src.schemas.monitoring import (
    MetricType,
    AlertLevel,
    SystemStatus,
    ComponentStatus,
)

# Global faker for consistent data generation
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


# ============================================================================
# CORE MONITORING FIXTURES
# ============================================================================


@pytest.fixture
async def monitoring_service() -> AsyncGenerator[MonitoringService, None]:
    """
    Provides a fresh MonitoringService instance for each test.

    Ensures test isolation by creating new service instances.
    """
    service = MonitoringService()
    yield service
    # Cleanup
    service.metrics.clear()
    service.alerts.clear()
    service.performance_data.clear()


@pytest.fixture
def monitoring_config():
    """Generate monitoring configuration."""
    return MonitoringConfigFactory.build()


# ============================================================================
# METRIC FIXTURES
# ============================================================================


@pytest.fixture
def metric_create_data():
    """Generate metric creation data."""
    return MetricCreateFactory.build()


@pytest.fixture
def metric_response_data():
    """Generate metric response data."""
    return MetricResponseFactory.build()


@pytest.fixture
def metric_batch_data():
    """Generate batch metric data."""
    return MetricBatchFactory.build()


@pytest.fixture
def predictable_metric_data():
    """Generate predictable metric data for deterministic tests."""
    return PredictableMetricFactory.build()


@pytest.fixture
def high_performance_metric_data():
    """Generate high-performance metric data."""
    return HighPerformanceMetricFactory.build()


@pytest.fixture
def error_metric_data():
    """Generate error metric data."""
    return ErrorMetricFactory.build()


@pytest.fixture
def memory_metric_data():
    """Generate memory metric data."""
    return MemoryMetricFactory.build()


@pytest.fixture
def multiple_metrics_data():
    """Generate multiple metrics for batch operations."""
    return [MetricCreateFactory.build() for _ in range(10)]


# ============================================================================
# ALERT FIXTURES
# ============================================================================


@pytest.fixture
def alert_create_data():
    """Generate alert creation data."""
    return AlertCreateFactory.build()


@pytest.fixture
def alert_response_data():
    """Generate alert response data."""
    return AlertResponseFactory.build()


@pytest.fixture
def critical_alert_data():
    """Generate critical alert data."""
    return CriticalAlertFactory.build()


@pytest.fixture
def resolved_alert_data():
    """Generate resolved alert data."""
    return AlertResponseFactory.build(resolved=True)


@pytest.fixture
def unresolved_alert_data():
    """Generate unresolved alert data."""
    return AlertResponseFactory.build(resolved=False)


@pytest.fixture
def multiple_alerts_data():
    """Generate multiple alerts for testing."""
    return [AlertCreateFactory.build() for _ in range(5)]


# ============================================================================
# SYSTEM HEALTH FIXTURES
# ============================================================================


@pytest.fixture
def component_health_data():
    """Generate component health data."""
    return ComponentHealthFactory.build()


@pytest.fixture
def healthy_component_data():
    """Generate healthy component data."""
    return ComponentHealthFactory.build(
        status=ComponentStatus.HEALTHY, connected=True, error=None
    )


@pytest.fixture
def unhealthy_component_data():
    """Generate unhealthy component data."""
    return ComponentHealthFactory.build(
        status=ComponentStatus.UNHEALTHY, connected=False, error="Connection failed"
    )


@pytest.fixture
def system_health_response_data():
    """Generate system health response data."""
    return SystemHealthResponseFactory.build()


@pytest.fixture
def healthy_system_data():
    """Generate healthy system data."""
    return SystemHealthResponseFactory.build(status=SystemStatus.HEALTHY, issues=[])


@pytest.fixture
def degraded_system_data():
    """Generate degraded system data."""
    return SystemHealthResponseFactory.build(
        status=SystemStatus.DEGRADED,
        issues=["Database connection slow", "High memory usage"],
    )


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================


@pytest.fixture
def performance_metric_data():
    """Generate performance metric data."""
    return PerformanceMetricFactory.build()


@pytest.fixture
def slow_performance_data():
    """Generate slow performance data."""
    return PerformanceMetricFactory.build(
        duration_ms=fake.random.uniform(2000, 5000), status="slow"
    )


@pytest.fixture
def fast_performance_data():
    """Generate fast performance data."""
    return PerformanceMetricFactory.build(
        duration_ms=fake.random.uniform(10, 100), status="success"
    )


@pytest.fixture
def performance_summary_data():
    """Generate performance summary data."""
    return PerformanceSummaryFactory.build()


@pytest.fixture
def performance_report_data():
    """Generate performance report data."""
    return PerformanceReportFactory.build()


@pytest.fixture
def multiple_performance_data():
    """Generate multiple performance metrics."""
    return [PerformanceMetricFactory.build() for _ in range(20)]


# ============================================================================
# USER ANALYTICS FIXTURES
# ============================================================================


@pytest.fixture
def user_action_data():
    """Generate user action data."""
    return UserActionDataFactory.build()


@pytest.fixture
def top_survey_data():
    """Generate top survey data."""
    return TopSurveyFactory.build()


@pytest.fixture
def user_analytics_response_data():
    """Generate user analytics response data."""
    return UserAnalyticsResponseFactory.build()


@pytest.fixture
def weekly_analytics_data():
    """Generate weekly analytics data."""
    return UserAnalyticsResponseFactory.build(period_days=7)


@pytest.fixture
def monthly_analytics_data():
    """Generate monthly analytics data."""
    return UserAnalyticsResponseFactory.build(period_days=30)


# ============================================================================
# DASHBOARD FIXTURES
# ============================================================================


@pytest.fixture
def dashboard_metric_data():
    """Generate dashboard metric data."""
    return DashboardMetricFactory.build()


@pytest.fixture
def dashboard_create_data():
    """Generate dashboard creation data."""
    return DashboardCreateFactory.build()


@pytest.fixture
def dashboard_response_data():
    """Generate dashboard response data."""
    return DashboardResponseFactory.build()


@pytest.fixture
def multiple_dashboard_metrics():
    """Generate multiple dashboard metrics."""
    return [DashboardMetricFactory.build() for _ in range(8)]


# ============================================================================
# REAL-TIME FIXTURES
# ============================================================================


@pytest.fixture
def real_time_metrics_data():
    """Generate real-time metrics data."""
    return RealTimeMetricsResponseFactory.build()


@pytest.fixture
def high_load_metrics_data():
    """Generate high-load metrics data."""
    return RealTimeMetricsResponseFactory.build(
        active_connections=fake.random_int(800, 1500),
        error_rate_last_hour=fake.random_int(10, 25),
        active_alerts=fake.random_int(3, 8),
    )


@pytest.fixture
def low_load_metrics_data():
    """Generate low-load metrics data."""
    return RealTimeMetricsResponseFactory.build(
        active_connections=fake.random_int(10, 100),
        error_rate_last_hour=fake.random_int(0, 2),
        active_alerts=0,
    )


# ============================================================================
# BULK OPERATIONS FIXTURES
# ============================================================================


@pytest.fixture
def bulk_metrics_create_data():
    """Generate bulk metrics creation data."""
    return BulkMetricsCreateFactory.build()


@pytest.fixture
def bulk_operation_response_data():
    """Generate bulk operation response data."""
    return BulkOperationResponseFactory.build()


@pytest.fixture
def successful_bulk_operation_data():
    """Generate successful bulk operation data."""
    total_items = fake.random_int(50, 100)
    return BulkOperationResponseFactory.build(
        total_items=total_items, successful=total_items, failed=0, errors=[]
    )


@pytest.fixture
def failed_bulk_operation_data():
    """Generate failed bulk operation data."""
    total_items = fake.random_int(50, 100)
    failed_count = fake.random_int(10, 30)
    return BulkOperationResponseFactory.build(
        total_items=total_items,
        successful=total_items - failed_count,
        failed=failed_count,
        errors=["Connection timeout", "Invalid data format"],
    )


# ============================================================================
# PARAMETRIZED FIXTURES
# ============================================================================


@pytest.fixture(
    params=[
        MetricType.COUNTER,
        MetricType.GAUGE,
        MetricType.TIMER,
        MetricType.HISTOGRAM,
    ]
)
def metric_type(request) -> MetricType:
    """Parametrized metric type fixture."""
    return request.param


@pytest.fixture(
    params=[
        AlertLevel.INFO,
        AlertLevel.WARNING,
        AlertLevel.ERROR,
        AlertLevel.CRITICAL,
    ]
)
def alert_level(request) -> AlertLevel:
    """Parametrized alert level fixture."""
    return request.param


@pytest.fixture(
    params=[
        SystemStatus.HEALTHY,
        SystemStatus.DEGRADED,
        SystemStatus.UNHEALTHY,
        SystemStatus.ERROR,
    ]
)
def system_status(request) -> SystemStatus:
    """Parametrized system status fixture."""
    return request.param


@pytest.fixture(
    params=[
        ComponentStatus.HEALTHY,
        ComponentStatus.SLOW,
        ComponentStatus.UNHEALTHY,
        ComponentStatus.ERROR,
    ]
)
def component_status(request) -> ComponentStatus:
    """Parametrized component status fixture."""
    return request.param


@pytest.fixture(params=[1, 7, 30, 90])
def analytics_period(request) -> int:
    """Parametrized analytics period fixture."""
    return request.param


@pytest.fixture(params=[10, 50, 100, 500])
def batch_size(request) -> int:
    """Parametrized batch size fixture."""
    return request.param


@pytest.fixture(
    params=[
        "api_request",
        "database_query",
        "cache_lookup",
        "file_upload",
        "email_send",
    ]
)
def operation_name(request) -> str:
    """Parametrized operation name fixture."""
    return request.param


# ============================================================================
# SCENARIO-BASED FIXTURES
# ============================================================================


@pytest.fixture
def high_performance_scenario():
    """Generate high-performance scenario data."""
    return {
        "metrics": [HighPerformanceMetricFactory.build() for _ in range(5)],
        "alerts": [],
        "performance_data": [
            PerformanceMetricFactory.build(duration_ms=fake.random.uniform(10, 100))
            for _ in range(10)
        ],
        "system_health": SystemHealthResponseFactory.build(
            status=SystemStatus.HEALTHY, issues=[]
        ),
    }


@pytest.fixture
def high_load_scenario():
    """Generate high-load scenario data."""
    return {
        "metrics": [
            ErrorMetricFactory.build(value=fake.random.uniform(8, 15)) for _ in range(3)
        ],
        "alerts": [
            AlertCreateFactory.build(level=AlertLevel.WARNING) for _ in range(2)
        ],
        "performance_data": [
            PerformanceMetricFactory.build(duration_ms=fake.random.uniform(1000, 3000))
            for _ in range(15)
        ],
        "system_health": SystemHealthResponseFactory.build(
            status=SystemStatus.DEGRADED,
            issues=["High response time", "Memory usage high"],
        ),
    }


@pytest.fixture
def system_failure_scenario():
    """Generate system failure scenario data."""
    return {
        "metrics": [
            ErrorMetricFactory.build(value=fake.random.uniform(20, 50))
            for _ in range(5)
        ],
        "alerts": [
            AlertCreateFactory.build(level=AlertLevel.CRITICAL) for _ in range(3)
        ],
        "performance_data": [
            PerformanceMetricFactory.build(
                duration_ms=fake.random.uniform(5000, 10000), status="error"
            )
            for _ in range(10)
        ],
        "system_health": SystemHealthResponseFactory.build(
            status=SystemStatus.UNHEALTHY,
            issues=[
                "Database connection failed",
                "Redis unavailable",
                "High error rate",
                "Critical memory usage",
            ],
        ),
    }


# ============================================================================
# GENERATE FIXTURES
# ============================================================================


@pytest.fixture
def generate_metrics():
    """Generate fixture for creating multiple metrics."""

    def _generate(count: int = 10, **kwargs) -> List[Any]:
        return [MetricCreateFactory.build(**kwargs) for _ in range(count)]

    return _generate


@pytest.fixture
def generate_alerts():
    """Generate fixture for creating multiple alerts."""

    def _generate(count: int = 5, **kwargs) -> List[Any]:
        return [AlertCreateFactory.build(**kwargs) for _ in range(count)]

    return _generate


@pytest.fixture
def generate_performance_data():
    """Generate fixture for creating performance data."""

    def _generate(count: int = 20, **kwargs) -> List[Any]:
        return [PerformanceMetricFactory.build(**kwargs) for _ in range(count)]

    return _generate


@pytest.fixture
def generate_dashboard_metrics():
    """Generate fixture for creating dashboard metrics."""

    def _generate(count: int = 8, **kwargs) -> List[Any]:
        return [DashboardMetricFactory.build(**kwargs) for _ in range(count)]

    return _generate


# ============================================================================
# HELPER FIXTURES
# ============================================================================


@pytest.fixture
def unique_metric_names():
    """Generate unique metric names for testing."""
    return [f"test_metric_{uuid.uuid4().hex[:8]}" for _ in range(10)]


@pytest.fixture
def unique_alert_ids():
    """Generate unique alert IDs for testing."""
    return [f"alert_{uuid.uuid4().hex[:8]}" for _ in range(5)]


@pytest.fixture
def time_ranges():
    """Generate time ranges for testing."""
    now = datetime.now()
    return {
        "last_hour": (now - timedelta(hours=1), now),
        "last_day": (now - timedelta(days=1), now),
        "last_week": (now - timedelta(weeks=1), now),
        "last_month": (now - timedelta(days=30), now),
    }


@pytest.fixture
def sample_tags():
    """Generate sample tags for testing."""
    return {
        "environment": fake.random_element(["production", "staging", "development"]),
        "service": fake.random_element(["api", "web", "worker", "database"]),
        "region": fake.random_element(["us-east-1", "eu-west-1", "ap-southeast-1"]),
        "version": fake.random_element(["1.0.0", "1.1.0", "1.2.0"]),
        "instance": f"instance-{fake.random_int(1, 10)}",
    }


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================


@pytest.fixture
def performance_test_data():
    """Generate data for performance testing."""
    return {
        "large_metric_batch": [MetricCreateFactory.build() for _ in range(1000)],
        "concurrent_alerts": [AlertCreateFactory.build() for _ in range(100)],
        "heavy_performance_data": [
            PerformanceMetricFactory.build() for _ in range(5000)
        ],
    }


@pytest.fixture
async def concurrent_monitoring_services():
    """Generate multiple monitoring services for concurrency testing."""
    services = [MonitoringService() for _ in range(5)]
    yield services
    # Cleanup
    for service in services:
        service.metrics.clear()
        service.alerts.clear()
        service.performance_data.clear()


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================


@pytest.fixture
async def monitoring_integration_data(async_session: AsyncSession):
    """Generate integration test data with database persistence."""
    # This fixture would create actual database records
    # for integration testing scenarios
    data = {
        "metrics": [],
        "alerts": [],
        "performance_records": [],
    }

    # Create some test records in the database
    # (This would use actual ORM models when they exist)

    yield data

    # Cleanup database records
    # (This would clean up test data from the database)


# ============================================================================
# CONTEXT7 INTEGRATION FIXTURES
# ============================================================================


@pytest.fixture
def context7_monitoring_examples():
    """Generate examples for Context7 documentation."""
    return {
        "basic_metric": MetricCreateFactory.build(
            name="response_time",
            value=250.5,
            type=MetricType.TIMER,
            tags={"service": "api", "endpoint": "/users"},
        ),
        "critical_alert": AlertCreateFactory.build(
            name="Database Connection Failed",
            level=AlertLevel.CRITICAL,
            message="Unable to connect to primary database",
            metadata={"database": "primary", "error_code": "CONNECTION_REFUSED"},
        ),
        "performance_report": PerformanceReportFactory.build(
            period_minutes=60, total_operations=5000, overall_avg_ms=180.5
        ),
    }


# ============================================================================
# EDGE CASE FIXTURES
# ============================================================================


@pytest.fixture
def edge_case_data():
    """Generate edge case data for testing."""
    return {
        "zero_value_metric": MetricCreateFactory.build(value=0.0),
        "negative_value_metric": MetricCreateFactory.build(value=-100.0),
        "very_large_value_metric": MetricCreateFactory.build(value=1e12),
        "empty_tags_metric": MetricCreateFactory.build(tags={}),
        "very_long_name_metric": MetricCreateFactory.build(
            name="a" * 200  # Very long name
        ),
        "empty_alert_message": AlertCreateFactory.build(message=""),
        "very_long_alert_message": AlertCreateFactory.build(
            message="x" * 2000  # Very long message
        ),
    }


@pytest.fixture
def boundary_values():
    """Generate boundary values for testing."""
    return {
        "min_float": float("-inf"),
        "max_float": float("inf"),
        "zero": 0.0,
        "negative_zero": -0.0,
        "small_positive": 1e-10,
        "small_negative": -1e-10,
        "large_positive": 1e10,
        "large_negative": -1e10,
    }
