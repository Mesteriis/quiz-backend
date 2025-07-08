"""
Comprehensive Positive Tests for System Health Monitoring.

This module tests successful scenarios for system health functionality:
- Component health monitoring
- System status aggregation
- Health check operations
- Status reporting
- Thresholds validation

All tests use best practices:
- Polyfactory factories for realistic data
- Parametrized tests for different scenarios
- Async/await for all operations
- Component isolation testing
- Context7 integration ready
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from faker import Faker

from src.services.monitoring_service import MonitoringService
from src.schemas.monitoring import (
    SystemStatus,
    ComponentStatus,
    ComponentHealth,
    SystemHealthResponse,
)

# Initialize faker
fake = Faker(["en_US", "ru_RU"])


# ============================================================================
# BASIC SYSTEM HEALTH TESTS
# ============================================================================


class TestBasicSystemHealth:
    """Test basic system health functionality."""

    async def test_get_system_health_basic_structure(
        self, monitoring_service: MonitoringService
    ):
        """Test that system health returns proper basic structure."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert basic structure
        assert isinstance(health_data, dict)
        assert "timestamp" in health_data
        assert "status" in health_data
        assert "components" in health_data

        # Verify timestamp format
        timestamp_str = health_data["timestamp"]
        assert isinstance(timestamp_str, str)
        # Should be able to parse ISO format
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        # Verify status is valid
        valid_statuses = ["healthy", "degraded", "unhealthy", "error"]
        assert health_data["status"] in valid_statuses

        # Verify components structure
        assert isinstance(health_data["components"], dict)
        assert len(health_data["components"]) > 0

    async def test_system_health_required_components(
        self, monitoring_service: MonitoringService
    ):
        """Test that all required components are included in health check."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert required components exist
        required_components = ["database", "redis", "application", "telegram_bot"]
        components = health_data["components"]

        for component in required_components:
            assert component in components, (
                f"Component {component} missing from health check"
            )

            # Verify component structure
            component_data = components[component]
            assert "status" in component_data
            assert isinstance(component_data["status"], str)

    async def test_system_health_component_details(
        self, monitoring_service: MonitoringService
    ):
        """Test detailed component health information."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert each component has detailed information
        for component_name, component_data in health_data["components"].items():
            # Basic fields
            assert "status" in component_data
            assert "connected" in component_data

            # Status should be valid
            valid_statuses = ["healthy", "slow", "unhealthy", "error"]
            assert component_data["status"] in valid_statuses

            # Connected should be boolean
            assert isinstance(component_data["connected"], bool)

            # If unhealthy, should have error information
            if component_data["status"] in ["unhealthy", "error"]:
                # May have error field
                if "error" in component_data:
                    assert isinstance(component_data["error"], str)

    @pytest.mark.parametrize(
        "component_name", ["database", "redis", "application", "telegram_bot"]
    )
    async def test_individual_component_health(
        self, monitoring_service: MonitoringService, component_name: str
    ):
        """Test individual component health monitoring."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert component exists and has proper data
        assert component_name in health_data["components"]
        component = health_data["components"][component_name]

        # Verify component-specific requirements
        if component_name == "database":
            # Database should have response time and user count
            if component["status"] == "healthy":
                assert "response_time_ms" in component
                assert "total_users" in component
                assert isinstance(component["response_time_ms"], (int, float))
                assert isinstance(component["total_users"], int)

        elif component_name == "redis":
            # Redis should have connection and possibly cache stats
            assert "connected" in component
            if component["connected"]:
                # May have additional cache statistics
                pass

        elif component_name == "application":
            # Application should have basic metrics
            assert "status" in component
            if component["status"] == "healthy":
                # Should have application-specific metrics
                pass

        elif component_name == "telegram_bot":
            # Telegram bot should have bot info
            if component["status"] == "healthy":
                assert "connected" in component
                if component["connected"]:
                    # May have bot username and response time
                    if "bot_username" in component:
                        assert isinstance(component["bot_username"], str)


# ============================================================================
# SYSTEM STATUS AGGREGATION TESTS
# ============================================================================


class TestSystemStatusAggregation:
    """Test system status aggregation logic."""

    async def test_healthy_system_status(self, monitoring_service: MonitoringService):
        """Test system status when all components are healthy."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert - if all components are healthy, system should be healthy
        component_statuses = [
            comp["status"] for comp in health_data["components"].values()
        ]

        if all(status == "healthy" for status in component_statuses):
            assert health_data["status"] == "healthy"
            # Should have no issues
            if "issues" in health_data:
                assert len(health_data["issues"]) == 0

    async def test_system_status_with_issues_detection(
        self, monitoring_service: MonitoringService
    ):
        """Test system status calculation with potential issues."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert status logic
        component_statuses = [
            comp["status"] for comp in health_data["components"].values()
        ]

        unhealthy_count = sum(
            1 for status in component_statuses if status in ["unhealthy", "error"]
        )

        if unhealthy_count == 0:
            # All components are healthy or slow
            slow_count = sum(1 for status in component_statuses if status == "slow")
            if slow_count == 0:
                assert health_data["status"] == "healthy"
            else:
                assert health_data["status"] in ["healthy", "degraded"]
        elif unhealthy_count < 2:
            assert health_data["status"] in ["degraded", "unhealthy"]
        else:
            assert health_data["status"] in ["unhealthy", "error"]

    async def test_system_issues_reporting(self, monitoring_service: MonitoringService):
        """Test system issues are properly reported."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert issues reporting
        if "issues" in health_data:
            issues = health_data["issues"]
            assert isinstance(issues, list)

            # If there are issues, system shouldn't be healthy
            if len(issues) > 0:
                assert health_data["status"] != "healthy"

            # Each issue should be a string
            for issue in issues:
                assert isinstance(issue, str)
                assert len(issue) > 0


# ============================================================================
# HEALTH CHECK PERFORMANCE TESTS
# ============================================================================


class TestHealthCheckPerformance:
    """Test health check performance and timing."""

    async def test_health_check_response_time(
        self, monitoring_service: MonitoringService
    ):
        """Test that health check completes in reasonable time."""
        # Arrange
        start_time = datetime.now()

        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Health check should complete within 10 seconds
        assert duration < 10.0

        # Should have timestamp close to actual time
        health_timestamp = datetime.fromisoformat(
            health_data["timestamp"].replace("Z", "+00:00")
        )
        time_diff = abs((health_timestamp - end_time).total_seconds())
        assert time_diff < 5.0  # Within 5 seconds

    async def test_concurrent_health_checks(
        self, monitoring_service: MonitoringService
    ):
        """Test multiple concurrent health checks."""
        # Arrange
        concurrent_checks = 5

        # Act
        tasks = [
            monitoring_service.get_system_health() for _ in range(concurrent_checks)
        ]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == concurrent_checks

        # All results should be valid
        for health_data in results:
            assert "timestamp" in health_data
            assert "status" in health_data
            assert "components" in health_data

        # Timestamps should be close to each other
        timestamps = [
            datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
            for result in results
        ]

        time_spread = max(timestamps) - min(timestamps)
        assert time_spread.total_seconds() < 5.0  # Within 5 seconds

    async def test_health_check_consistency(
        self, monitoring_service: MonitoringService
    ):
        """Test health check results are consistent across calls."""
        # Act
        health_check1 = await monitoring_service.get_system_health()
        await asyncio.sleep(0.1)  # Small delay
        health_check2 = await monitoring_service.get_system_health()

        # Assert structure consistency
        assert set(health_check1.keys()) == set(health_check2.keys())
        assert set(health_check1["components"].keys()) == set(
            health_check2["components"].keys()
        )

        # Component structure should be consistent
        for component_name in health_check1["components"]:
            comp1 = health_check1["components"][component_name]
            comp2 = health_check2["components"][component_name]

            # Should have same basic structure
            assert "status" in comp1 and "status" in comp2
            assert "connected" in comp1 and "connected" in comp2


# ============================================================================
# COMPONENT-SPECIFIC HEALTH TESTS
# ============================================================================


class TestComponentSpecificHealth:
    """Test health checks for specific components."""

    async def test_database_health_check(self, monitoring_service: MonitoringService):
        """Test database component health check."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert database component
        assert "database" in health_data["components"]
        db_health = health_data["components"]["database"]

        # Basic fields
        assert "status" in db_health
        assert "connected" in db_health

        # If connected and healthy, should have performance metrics
        if db_health["connected"] and db_health["status"] == "healthy":
            assert "response_time_ms" in db_health
            assert "total_users" in db_health

            # Validate response time
            response_time = db_health["response_time_ms"]
            assert isinstance(response_time, (int, float))
            assert response_time >= 0

            # Validate user count
            user_count = db_health["total_users"]
            assert isinstance(user_count, int)
            assert user_count >= 0

    async def test_redis_health_check(self, monitoring_service: MonitoringService):
        """Test Redis component health check."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert Redis component
        assert "redis" in health_data["components"]
        redis_health = health_data["components"]["redis"]

        # Basic fields
        assert "status" in redis_health
        assert "connected" in redis_health

        # If not connected, should have error information
        if not redis_health["connected"]:
            assert redis_health["status"] == "unhealthy"
            # Should have error message
            if "error" in redis_health:
                assert isinstance(redis_health["error"], str)

    async def test_application_health_check(
        self, monitoring_service: MonitoringService
    ):
        """Test application component health check."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert application component
        assert "application" in health_data["components"]
        app_health = health_data["components"]["application"]

        # Should always have status
        assert "status" in app_health

        # If healthy, should have basic metrics
        if app_health["status"] == "healthy":
            # May have additional application metrics
            pass

    async def test_telegram_bot_health_check(
        self, monitoring_service: MonitoringService
    ):
        """Test Telegram bot component health check."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert Telegram bot component
        assert "telegram_bot" in health_data["components"]
        bot_health = health_data["components"]["telegram_bot"]

        # Basic fields
        assert "status" in bot_health
        assert "connected" in bot_health

        # If connected and healthy, may have bot information
        if bot_health["connected"] and bot_health["status"] == "healthy":
            if "bot_username" in bot_health:
                assert isinstance(bot_health["bot_username"], str)
                assert len(bot_health["bot_username"]) > 0

            if "response_time_ms" in bot_health:
                response_time = bot_health["response_time_ms"]
                assert isinstance(response_time, (int, float))
                assert response_time >= 0


# ============================================================================
# HEALTH STATUS VALIDATION TESTS
# ============================================================================


class TestHealthStatusValidation:
    """Test health status validation and logic."""

    @pytest.mark.parametrize(
        "component_status",
        [
            ComponentStatus.HEALTHY,
            ComponentStatus.SLOW,
            ComponentStatus.UNHEALTHY,
            ComponentStatus.ERROR,
        ],
    )
    async def test_component_status_validation(
        self, monitoring_service: MonitoringService, component_status: ComponentStatus
    ):
        """Test component status validation."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert all component statuses are valid
        for component_name, component_data in health_data["components"].items():
            status = component_data["status"]
            valid_statuses = ["healthy", "slow", "unhealthy", "error"]
            assert status in valid_statuses

    async def test_system_status_logic_validation(
        self, monitoring_service: MonitoringService
    ):
        """Test system-wide status aggregation logic."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Get component statuses
        component_statuses = [
            comp["status"] for comp in health_data["components"].values()
        ]

        system_status = health_data["status"]

        # Validate status logic
        error_count = component_statuses.count("error")
        unhealthy_count = component_statuses.count("unhealthy")
        slow_count = component_statuses.count("slow")
        healthy_count = component_statuses.count("healthy")

        # System status should reflect component states
        total_problematic = error_count + unhealthy_count

        if total_problematic == 0:
            if slow_count == 0:
                # All healthy
                assert system_status == "healthy"
            else:
                # Some slow, but no critical issues
                assert system_status in ["healthy", "degraded"]
        elif total_problematic == 1:
            # One component has issues
            assert system_status in ["degraded", "unhealthy"]
        else:
            # Multiple components have issues
            assert system_status in ["unhealthy", "error"]

    async def test_health_data_completeness(
        self, monitoring_service: MonitoringService
    ):
        """Test that health data is complete and well-formed."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert top-level completeness
        required_fields = ["timestamp", "status", "components"]
        for field in required_fields:
            assert field in health_data

        # Assert components completeness
        for component_name, component_data in health_data["components"].items():
            # Each component should have status
            assert "status" in component_data
            assert isinstance(component_data["status"], str)

            # Each component should have connected field
            assert "connected" in component_data
            assert isinstance(component_data["connected"], bool)

            # If there's an error, it should be a string
            if "error" in component_data:
                assert component_data["error"] is None or isinstance(
                    component_data["error"], str
                )


# ============================================================================
# HEALTH MONITORING INTEGRATION TESTS
# ============================================================================


class TestHealthMonitoringIntegration:
    """Test health monitoring integration with other systems."""

    async def test_health_check_with_existing_metrics(
        self, monitoring_service: MonitoringService, multiple_metrics_data
    ):
        """Test health check when monitoring service has existing metrics."""
        # Arrange - Add some metrics
        for metric_data in multiple_metrics_data[:5]:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert health check works with existing data
        assert "timestamp" in health_data
        assert "status" in health_data
        assert "components" in health_data

        # Should still have all required components
        required_components = ["database", "redis", "application", "telegram_bot"]
        for component in required_components:
            assert component in health_data["components"]

    async def test_health_check_with_performance_data(
        self, monitoring_service: MonitoringService, multiple_performance_data
    ):
        """Test health check with existing performance data."""
        # Arrange - Add performance data
        for perf_data in multiple_performance_data[:3]:
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert health check is not affected by performance data
        assert "status" in health_data
        assert "components" in health_data

        # Application component might reflect performance data
        app_component = health_data["components"]["application"]
        assert "status" in app_component

    async def test_health_check_system_coherence(
        self, monitoring_service: MonitoringService
    ):
        """Test that health check maintains system coherence."""
        # Act - Multiple health checks
        health_checks = []
        for _ in range(3):
            health_data = await monitoring_service.get_system_health()
            health_checks.append(health_data)
            await asyncio.sleep(0.1)

        # Assert coherence across checks
        for health_data in health_checks:
            # All should have same component set
            component_names = set(health_data["components"].keys())
            expected_components = {"database", "redis", "application", "telegram_bot"}
            assert component_names == expected_components

            # Status should be valid
            assert health_data["status"] in [
                "healthy",
                "degraded",
                "unhealthy",
                "error",
            ]

        # Component availability should be consistent
        first_check_components = set(health_checks[0]["components"].keys())
        for health_data in health_checks[1:]:
            current_components = set(health_data["components"].keys())
            assert current_components == first_check_components

    async def test_health_check_error_handling(
        self, monitoring_service: MonitoringService
    ):
        """Test health check error handling and graceful degradation."""
        # Act
        health_data = await monitoring_service.get_system_health()

        # Assert graceful handling
        assert isinstance(health_data, dict)
        assert "status" in health_data

        # Even if some components fail, should still return structure
        assert "components" in health_data
        assert len(health_data["components"]) > 0

        # Each component should handle errors gracefully
        for component_name, component_data in health_data["components"].items():
            assert "status" in component_data

            # Error states should be properly handled
            if component_data["status"] in ["unhealthy", "error"]:
                # Should have connected field indicating failure
                assert "connected" in component_data
                # Connected should be False for error states
                if component_data["status"] == "error":
                    assert component_data["connected"] is False
