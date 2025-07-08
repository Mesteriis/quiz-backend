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

import pytest
from faker import Faker
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

from tests.factories.monitoring_factories import (
    MetricCreateFactory,
    AlertCreateFactory,
    SystemHealthResponseFactory,
    UserAnalyticsResponseFactory,
    PerformanceDataFactory,
    DashboardCreateFactory,
    HighLoadMetricFactory,
    ErrorMetricFactory,
    PerformanceMetricFactory,
)

# Global faker for consistent data generation
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


@pytest.fixture
def monitoring_service():
    """
    Provides a fresh MonitoringService instance for each test.
    """
    from src.services.monitoring_service import MonitoringService

    service = MonitoringService()
    yield service
    # Cleanup
    service.metrics.clear()
    service.alerts.clear()
    service.performance_data.clear()


@pytest.fixture
def metric_create_data():
    """Generate metric creation data."""
    return MetricCreateFactory.build()


@pytest.fixture
def alert_create_data():
    """Generate alert creation data."""
    return AlertCreateFactory.build()


@pytest.fixture
def system_health_response_data():
    """Generate system health response data."""
    return SystemHealthResponseFactory.build()


@pytest.fixture
def user_analytics_response_data():
    """Generate user analytics response data."""
    return UserAnalyticsResponseFactory.build()


@pytest.fixture
def performance_data():
    """Generate performance data."""
    return PerformanceDataFactory.build()


@pytest.fixture
def dashboard_create_data():
    """Generate dashboard creation data."""
    return DashboardCreateFactory.build()


@pytest.fixture
def high_load_metric_data():
    """Generate high load metric data."""
    return HighLoadMetricFactory.build()


@pytest.fixture
def error_metric_data():
    """Generate error metric data."""
    return ErrorMetricFactory.build()


@pytest.fixture
def performance_metric_data():
    """Generate performance metric data."""
    return PerformanceMetricFactory.build()


@pytest.fixture
def multiple_metrics_data():
    """Generate multiple metrics for batch operations."""
    return [MetricCreateFactory.build() for _ in range(5)]


@pytest.fixture
def multiple_alerts_data():
    """Generate multiple alerts for testing."""
    return [AlertCreateFactory.build() for _ in range(3)]


# Mock external dependencies
@pytest.fixture
def mock_redis_service():
    """Mock Redis service."""
    mock = AsyncMock()
    mock.get_hash.return_value = {}
    mock.set_hash.return_value = True
    mock.increment_counter.return_value = 1
    mock.get_counter.return_value = 100
    mock.ping.return_value = True
    mock.is_connected.return_value = True
    return mock


@pytest.fixture
def mock_telegram_service():
    """Mock Telegram service."""
    mock = MagicMock()
    mock.bot = MagicMock()
    mock.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))
    return mock


@pytest.fixture
def mock_database_session():
    """Mock database session."""
    mock = AsyncMock()
    mock.execute.return_value = MagicMock()
    mock.scalar.return_value = 100
    return mock


@pytest.fixture
def mock_get_redis_service():
    """Mock get_redis_service function."""
    mock = AsyncMock()
    mock.return_value = AsyncMock()
    mock.return_value.set_hash = AsyncMock()
    mock.return_value.get_hash = AsyncMock(return_value={})
    mock.return_value.increment_counter = AsyncMock(return_value=1)
    mock.return_value.get_counter = AsyncMock(return_value=100)
    mock.return_value.ping = AsyncMock(return_value=True)
    mock.return_value.is_connected = AsyncMock(return_value=True)
    return mock
