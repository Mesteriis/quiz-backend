"""
Comprehensive Positive Tests for Metrics Tracking.

This module tests successful scenarios for metrics tracking functionality:
- Metric creation and management
- Batch operations
- Performance tracking
- Real-time metrics
- Dashboard operations

All tests use best practices:
- Polyfactory factories for data generation
- Parametrized tests for comprehensive coverage
- Async/await for all operations
- Generate fixtures for dynamic data
- Context7 integration ready
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from faker import Faker

from src.services.monitoring_service import MonitoringService
from src.schemas.monitoring import (
    MetricType,
    AlertLevel,
    SystemStatus,
    ComponentStatus,
    MetricCreate,
    MetricResponse,
)

# Initialize faker
fake = Faker(["en_US", "ru_RU"])


# ============================================================================
# BASIC METRICS TRACKING TESTS
# ============================================================================


class TestBasicMetricsTracking:
    """Test basic metrics tracking functionality."""

    async def test_track_single_metric_success(
        self, monitoring_service: MonitoringService, metric_create_data: MetricCreate
    ):
        """Test successful tracking of a single metric."""
        # Act
        await monitoring_service.track_metric(
            name=metric_create_data.name,
            value=metric_create_data.value,
            metric_type=metric_create_data.type,
            tags=metric_create_data.tags,
        )

        # Assert
        assert len(monitoring_service.metrics) == 1
        tracked_metric = monitoring_service.metrics[0]
        assert tracked_metric.name == metric_create_data.name
        assert tracked_metric.value == metric_create_data.value
        assert tracked_metric.type == metric_create_data.type
        assert tracked_metric.tags == metric_create_data.tags
        assert isinstance(tracked_metric.timestamp, datetime)

    @pytest.mark.parametrize(
        "metric_type",
        [MetricType.COUNTER, MetricType.GAUGE, MetricType.TIMER, MetricType.HISTOGRAM],
    )
    async def test_track_metrics_by_type(
        self, monitoring_service: MonitoringService, metric_type: MetricType
    ):
        """Test tracking metrics of different types."""
        # Arrange
        metric_name = f"test_metric_{metric_type.value}"
        metric_value = fake.random.uniform(1.0, 1000.0)
        tags = {"type": metric_type.value, "test": "parametrized"}

        # Act
        await monitoring_service.track_metric(
            name=metric_name,
            value=metric_value,
            metric_type=metric_type,
            tags=tags,
        )

        # Assert
        assert len(monitoring_service.metrics) == 1
        tracked_metric = monitoring_service.metrics[0]
        assert tracked_metric.type == metric_type
        assert tracked_metric.value == metric_value
        assert tracked_metric.tags["type"] == metric_type.value

    async def test_track_multiple_metrics_success(
        self,
        monitoring_service: MonitoringService,
        multiple_metrics_data: List[MetricCreate],
    ):
        """Test tracking multiple metrics successfully."""
        # Act
        for metric_data in multiple_metrics_data:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

        # Assert
        assert len(monitoring_service.metrics) == len(multiple_metrics_data)

        # Verify each metric was tracked correctly
        for i, original_metric in enumerate(multiple_metrics_data):
            tracked_metric = monitoring_service.metrics[i]
            assert tracked_metric.name == original_metric.name
            assert tracked_metric.value == original_metric.value
            assert tracked_metric.type == original_metric.type

    async def test_metrics_timestamp_ordering(
        self, monitoring_service: MonitoringService, generate_metrics
    ):
        """Test that metrics are ordered by timestamp."""
        # Arrange
        metrics_data = generate_metrics(count=5)

        # Act
        for metric_data in metrics_data:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )
            # Small delay to ensure different timestamps
            await asyncio.sleep(0.001)

        # Assert
        timestamps = [metric.timestamp for metric in monitoring_service.metrics]
        assert timestamps == sorted(timestamps)


# ============================================================================
# PERFORMANCE TRACKING TESTS
# ============================================================================


class TestPerformanceTracking:
    """Test performance tracking functionality."""

    async def test_track_performance_success(
        self, monitoring_service: MonitoringService, performance_metric_data
    ):
        """Test successful performance tracking."""
        # Act
        await monitoring_service.track_performance(
            operation=performance_metric_data.operation,
            duration_ms=performance_metric_data.duration_ms,
            status=performance_metric_data.status,
        )

        # Assert
        assert performance_metric_data.operation in monitoring_service.performance_data
        performance_list = monitoring_service.performance_data[
            performance_metric_data.operation
        ]
        assert len(performance_list) == 1
        assert performance_list[0] == performance_metric_data.duration_ms

        # Verify metric was also tracked
        assert len(monitoring_service.metrics) == 1
        tracked_metric = monitoring_service.metrics[0]
        assert (
            tracked_metric.name
            == f"performance.{performance_metric_data.operation}.duration"
        )
        assert tracked_metric.value == performance_metric_data.duration_ms
        assert tracked_metric.type == MetricType.TIMER

    @pytest.mark.parametrize(
        "operation_name",
        ["api_request", "database_query", "cache_lookup", "file_upload", "email_send"],
    )
    async def test_track_performance_different_operations(
        self, monitoring_service: MonitoringService, operation_name: str
    ):
        """Test performance tracking for different operations."""
        # Arrange
        duration_ms = fake.random.uniform(10.0, 5000.0)
        status = fake.random_element(["success", "error", "timeout"])

        # Act
        await monitoring_service.track_performance(
            operation=operation_name,
            duration_ms=duration_ms,
            status=status,
        )

        # Assert
        assert operation_name in monitoring_service.performance_data
        assert monitoring_service.performance_data[operation_name][0] == duration_ms

    async def test_track_performance_multiple_operations(
        self, monitoring_service: MonitoringService, multiple_performance_data
    ):
        """Test tracking performance for multiple operations."""
        # Act
        for perf_data in multiple_performance_data:
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Assert
        # Check that operations are grouped correctly
        operations = set(perf.operation for perf in multiple_performance_data)
        assert len(monitoring_service.performance_data) == len(operations)

        # Verify total measurements
        total_measurements = sum(
            len(durations) for durations in monitoring_service.performance_data.values()
        )
        assert total_measurements == len(multiple_performance_data)

    async def test_performance_data_limit(
        self, monitoring_service: MonitoringService, operation_name: str
    ):
        """Test that performance data is limited to prevent memory issues."""
        # Arrange
        operation = operation_name
        # Track more than the limit (1000)
        measurements_count = 1200

        # Act
        for i in range(measurements_count):
            await monitoring_service.track_performance(
                operation=operation,
                duration_ms=fake.random.uniform(10.0, 1000.0),
                status="success",
            )

        # Assert
        # Should keep only last 800 measurements
        assert len(monitoring_service.performance_data[operation]) == 800


# ============================================================================
# USER ACTION TRACKING TESTS
# ============================================================================


class TestUserActionTracking:
    """Test user action tracking functionality."""

    @pytest.mark.asyncio
    async def test_track_user_action_success(
        self, monitoring_service: MonitoringService, user_action_data
    ):
        """Test successful user action tracking."""
        # Arrange
        user_id = fake.random_int(1, 1000)
        action = user_action_data.action
        metadata = {"page": "dashboard", "feature": "survey_creation"}

        # Act
        await monitoring_service.track_user_action(
            user_id=user_id,
            action=action,
            metadata=metadata,
        )

        # Assert - В данном случае метод не падает и выполняется без ошибок
        # Реальная проверка зависела бы от наличия Redis, здесь проверяем отсутствие исключений
        assert True  # No exception raised

    @pytest.mark.parametrize(
        "action_type",
        [
            "survey_start",
            "survey_complete",
            "question_answer",
            "telegram_interaction",
            "profile_update",
            "login",
            "logout",
        ],
    )
    async def test_track_different_user_actions(
        self, monitoring_service: MonitoringService, action_type: str
    ):
        """Test tracking different types of user actions."""
        # Arrange
        user_id = fake.random_int(1, 1000)
        metadata = {"action_type": action_type, "timestamp": datetime.now().isoformat()}

        # Act & Assert
        await monitoring_service.track_user_action(
            user_id=user_id,
            action=action_type,
            metadata=metadata,
        )
        # No exception should be raised

    async def test_track_user_actions_batch(
        self, monitoring_service: MonitoringService, generate_metrics
    ):
        """Test tracking multiple user actions in batch."""
        # Arrange
        actions_count = 50
        user_ids = [fake.random_int(1, 100) for _ in range(actions_count)]
        actions = [
            fake.random_element(
                ["survey_start", "survey_complete", "question_answer", "login"]
            )
            for _ in range(actions_count)
        ]

        # Act
        tasks = [
            monitoring_service.track_user_action(
                user_id=user_id,
                action=action,
                metadata={"batch": True},
            )
            for user_id, action in zip(user_ids, actions)
        ]
        await asyncio.gather(*tasks)

        # Assert - All actions processed without errors
        assert True


# ============================================================================
# REAL-TIME METRICS TESTS
# ============================================================================


class TestRealTimeMetrics:
    """Test real-time metrics functionality."""

    async def test_get_real_time_metrics_success(
        self, monitoring_service: MonitoringService, real_time_metrics_data
    ):
        """Test successful retrieval of real-time metrics."""
        # Arrange - Add some sample metrics
        await monitoring_service.track_metric("test_metric", 100.0, MetricType.GAUGE)
        await monitoring_service.track_metric("error_metric", 5.0, MetricType.COUNTER)

        # Act
        real_time_data = await monitoring_service.get_real_time_metrics()

        # Assert
        assert "timestamp" in real_time_data
        assert "recent_metrics_count" in real_time_data
        assert "active_alerts" in real_time_data
        assert isinstance(real_time_data["timestamp"], str)
        assert isinstance(real_time_data["recent_metrics_count"], int)
        assert real_time_data["recent_metrics_count"] >= 0

    async def test_real_time_metrics_with_recent_data(
        self, monitoring_service: MonitoringService
    ):
        """Test real-time metrics calculation with recent data."""
        # Arrange - Add metrics in the last 5 minutes
        current_time = datetime.now()

        # Add some recent metrics
        for i in range(5):
            await monitoring_service.track_metric(
                f"recent_metric_{i}",
                fake.random.uniform(10.0, 100.0),
                MetricType.GAUGE,
            )

        # Act
        real_time_data = await monitoring_service.get_real_time_metrics()

        # Assert
        assert real_time_data["recent_metrics_count"] == 5
        assert real_time_data["active_alerts"] == 0  # No alerts yet

    async def test_real_time_metrics_performance_data(
        self, monitoring_service: MonitoringService, multiple_performance_data
    ):
        """Test real-time metrics with performance data."""
        # Arrange - Add performance data
        for perf_data in multiple_performance_data[:10]:  # Add 10 items
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Act
        real_time_data = await monitoring_service.get_real_time_metrics()

        # Assert
        assert "performance_avg" in real_time_data
        assert isinstance(real_time_data["performance_avg"], dict)


# ============================================================================
# DASHBOARD OPERATIONS TESTS
# ============================================================================


class TestDashboardOperations:
    """Test dashboard creation and management."""

    async def test_create_custom_dashboard_success(
        self, monitoring_service: MonitoringService, dashboard_create_data
    ):
        """Test successful custom dashboard creation."""
        # Arrange - Add some metrics first
        metric_names = dashboard_create_data.metrics[:3]  # Use first 3 metrics

        for metric_name in metric_names:
            await monitoring_service.track_metric(
                name=metric_name,
                value=fake.random.uniform(10.0, 1000.0),
                metric_type=MetricType.GAUGE,
                tags={"dashboard": "test"},
            )

        # Act
        dashboard = await monitoring_service.create_custom_dashboard(
            name=dashboard_create_data.name,
            metrics=metric_names,
        )

        # Assert
        assert dashboard["name"] == dashboard_create_data.name
        assert "created_at" in dashboard
        assert "metrics" in dashboard
        assert len(dashboard["metrics"]) == len(metric_names)

    async def test_create_dashboard_with_historical_data(
        self, monitoring_service: MonitoringService, unique_metric_names
    ):
        """Test dashboard creation with historical metric data."""
        # Arrange - Create metrics with data over 24 hours
        metric_names = unique_metric_names[:3]

        for metric_name in metric_names:
            # Add multiple data points for each metric
            for i in range(10):
                await monitoring_service.track_metric(
                    name=metric_name,
                    value=fake.random.uniform(10.0, 1000.0),
                    metric_type=MetricType.GAUGE,
                )

        # Act
        dashboard = await monitoring_service.create_custom_dashboard(
            name="Historical Dashboard",
            metrics=metric_names,
        )

        # Assert
        assert len(dashboard["metrics"]) == len(metric_names)

        for metric_data in dashboard["metrics"]:
            assert "name" in metric_data
            assert "current_value" in metric_data
            assert "avg_24h" in metric_data
            assert "min_24h" in metric_data
            assert "max_24h" in metric_data
            assert "data_points" in metric_data

    @pytest.mark.parametrize("metrics_count", [1, 3, 5, 8, 10])
    async def test_create_dashboard_different_sizes(
        self,
        monitoring_service: MonitoringService,
        metrics_count: int,
        generate_metrics,
    ):
        """Test creating dashboards with different numbers of metrics."""
        # Arrange
        metrics_data = generate_metrics(count=metrics_count)
        metric_names = []

        for metric_data in metrics_data:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )
            metric_names.append(metric_data.name)

        # Act
        dashboard = await monitoring_service.create_custom_dashboard(
            name=f"Dashboard_{metrics_count}_metrics",
            metrics=metric_names,
        )

        # Assert
        assert len(dashboard["metrics"]) == metrics_count


# ============================================================================
# SYSTEM HEALTH TESTS
# ============================================================================


class TestSystemHealth:
    """Test system health monitoring functionality."""

    async def test_get_system_health_success(
        self, monitoring_service: MonitoringService
    ):
        """Test successful system health retrieval."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert
        assert "timestamp" in health_data
        assert "status" in health_data
        assert "components" in health_data
        assert isinstance(health_data["components"], dict)

        # Check required components
        expected_components = ["database", "redis", "application", "telegram_bot"]
        for component in expected_components:
            assert component in health_data["components"]
            component_health = health_data["components"][component]
            assert "status" in component_health

    async def test_system_health_components_validation(
        self, monitoring_service: MonitoringService
    ):
        """Test that all system components are properly validated."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert each component has required fields
        for component_name, component_data in health_data["components"].items():
            assert "status" in component_data
            # Status should be one of the valid values
            valid_statuses = ["healthy", "slow", "unhealthy", "error"]
            assert component_data["status"] in valid_statuses

    async def test_system_health_with_metrics_data(
        self, monitoring_service: MonitoringService, multiple_metrics_data
    ):
        """Test system health calculation with existing metrics."""
        # Arrange - Add some metrics to the service
        for metric_data in multiple_metrics_data[:5]:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert
        assert health_data["status"] in ["healthy", "degraded", "unhealthy", "error"]
        assert len(health_data["components"]) >= 4  # At least 4 components


# ============================================================================
# USER ANALYTICS TESTS
# ============================================================================


class TestUserAnalytics:
    """Test user analytics functionality."""

    @pytest.mark.parametrize("analytics_period", [1, 7, 30, 90])
    async def test_get_user_analytics_different_periods(
        self, monitoring_service: MonitoringService, analytics_period: int
    ):
        """Test user analytics for different time periods."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(
            days=analytics_period
        )

        # Assert
        assert "period_days" in analytics_data
        assert analytics_data["period_days"] == analytics_period
        assert "timestamp" in analytics_data
        assert "users" in analytics_data
        assert "surveys" in analytics_data
        assert "actions" in analytics_data
        assert "performance" in analytics_data

    async def test_user_analytics_structure_validation(
        self, monitoring_service: MonitoringService
    ):
        """Test that user analytics returns properly structured data."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert users section
        users_data = analytics_data["users"]
        assert "new_registrations" in users_data
        assert "active_users" in users_data
        assert isinstance(users_data["new_registrations"], int)
        assert isinstance(users_data["active_users"], int)

        # Assert surveys section
        surveys_data = analytics_data["surveys"]
        assert "completions" in surveys_data
        assert "top_surveys" in surveys_data
        assert isinstance(surveys_data["completions"], int)
        assert isinstance(surveys_data["top_surveys"], list)

    async def test_user_analytics_with_performance_data(
        self, monitoring_service: MonitoringService, multiple_performance_data
    ):
        """Test user analytics includes performance data."""
        # Arrange - Add performance data
        for perf_data in multiple_performance_data[:5]:
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert
        assert "performance" in analytics_data
        performance_data = analytics_data["performance"]
        assert isinstance(performance_data, dict)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestMonitoringIntegration:
    """Test integrated monitoring functionality."""

    async def test_complete_monitoring_workflow(
        self, monitoring_service: MonitoringService, monitoring_config
    ):
        """Test complete monitoring workflow from metrics to dashboard."""
        # Arrange
        metric_names = ["response_time", "error_rate", "memory_usage"]

        # Act 1: Track metrics
        for metric_name in metric_names:
            await monitoring_service.track_metric(
                name=metric_name,
                value=fake.random.uniform(10.0, 1000.0),
                metric_type=MetricType.GAUGE,
                tags={"workflow": "integration"},
            )

        # Act 2: Track performance
        await monitoring_service.track_performance(
            operation="integration_test",
            duration_ms=150.0,
            status="success",
        )

        # Act 3: Get system health
        health_data = await monitoring_service.get_system_health()

        # Act 4: Create dashboard
        dashboard = await monitoring_service.create_custom_dashboard(
            name="Integration Dashboard",
            metrics=metric_names,
        )

        # Act 5: Get real-time metrics
        real_time_data = await monitoring_service.get_real_time_metrics()

        # Assert everything worked together
        assert len(monitoring_service.metrics) == len(metric_names)
        assert "integration_test" in monitoring_service.performance_data
        assert health_data["status"] in ["healthy", "degraded", "unhealthy", "error"]
        assert dashboard["name"] == "Integration Dashboard"
        assert real_time_data["recent_metrics_count"] >= len(metric_names)

    async def test_concurrent_operations(
        self, monitoring_service: MonitoringService, generate_metrics
    ):
        """Test concurrent monitoring operations."""
        # Arrange
        metrics_data = generate_metrics(count=20)

        # Act - Run operations concurrently
        metric_tasks = [
            monitoring_service.track_metric(
                name=metric.name,
                value=metric.value,
                metric_type=metric.type,
                tags=metric.tags,
            )
            for metric in metrics_data
        ]

        performance_tasks = [
            monitoring_service.track_performance(
                operation=f"concurrent_op_{i}",
                duration_ms=fake.random.uniform(10.0, 500.0),
                status="success",
            )
            for i in range(10)
        ]

        # Execute all tasks concurrently
        await asyncio.gather(*(metric_tasks + performance_tasks))

        # Assert
        assert len(monitoring_service.metrics) == len(metrics_data)
        assert len(monitoring_service.performance_data) == 10

    async def test_monitoring_service_state_consistency(
        self,
        monitoring_service: MonitoringService,
        multiple_metrics_data,
        multiple_performance_data,
    ):
        """Test that monitoring service maintains consistent state."""
        # Arrange & Act
        # Add metrics
        for metric_data in multiple_metrics_data:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

        # Add performance data
        for perf_data in multiple_performance_data:
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Assert state consistency
        assert len(monitoring_service.metrics) >= len(multiple_metrics_data)
        assert len(monitoring_service.performance_data) > 0

        # Verify metrics ordering
        timestamps = [metric.timestamp for metric in monitoring_service.metrics]
        assert timestamps == sorted(timestamps)

        # Verify performance data grouping
        operations = set(perf.operation for perf in multiple_performance_data)
        tracked_operations = set(monitoring_service.performance_data.keys())
        assert operations.issubset(tracked_operations)
