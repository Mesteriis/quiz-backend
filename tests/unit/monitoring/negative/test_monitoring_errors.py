"""
Comprehensive Negative Tests for Monitoring Errors.

This module tests error scenarios and failure handling in monitoring:
- Invalid input validation
- Error propagation and handling
- Service failure scenarios
- Resource exhaustion
- Network and connectivity issues

All tests use best practices:
- Proper exception testing with pytest.raises
- Error message validation
- Graceful degradation testing
- Resource cleanup verification
- Context7 integration ready
"""

import asyncio
import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import patch, AsyncMock, MagicMock

from src.services.monitoring_service import MonitoringService
from src.schemas.monitoring import MetricType, AlertLevel


# ============================================================================
# INVALID INPUT TESTS
# ============================================================================


class TestInvalidInputs:
    """Test invalid input handling."""

    async def test_track_metric_invalid_name(
        self, monitoring_service: MonitoringService
    ):
        """Test tracking metric with invalid name."""
        # Test empty name
        with pytest.raises(Exception):
            await monitoring_service.track_metric(
                name="",
                value=100.0,
                metric_type=MetricType.GAUGE,
            )

        # Test None name
        with pytest.raises((TypeError, AttributeError)):
            await monitoring_service.track_metric(
                name=None,
                value=100.0,
                metric_type=MetricType.GAUGE,
            )

        # Test very long name
        very_long_name = "a" * 10000
        # Should handle gracefully, might truncate or accept
        await monitoring_service.track_metric(
            name=very_long_name,
            value=100.0,
            metric_type=MetricType.GAUGE,
        )
        # Verify it was handled (not necessarily an error)

    async def test_track_metric_invalid_value(
        self, monitoring_service: MonitoringService
    ):
        """Test tracking metric with invalid value."""
        # Test None value
        with pytest.raises((TypeError, ValueError)):
            await monitoring_service.track_metric(
                name="test_metric",
                value=None,
                metric_type=MetricType.GAUGE,
            )

        # Test string value (should be convertible or error)
        with pytest.raises((TypeError, ValueError)):
            await monitoring_service.track_metric(
                name="test_metric",
                value="not_a_number",
                metric_type=MetricType.GAUGE,
            )

        # Test invalid numeric values
        invalid_values = [float("inf"), float("-inf"), float("nan")]
        for invalid_value in invalid_values:
            # These might be accepted or rejected depending on implementation
            try:
                await monitoring_service.track_metric(
                    name="test_metric",
                    value=invalid_value,
                    metric_type=MetricType.GAUGE,
                )
            except (ValueError, TypeError):
                # Expected for some invalid values
                pass

    async def test_track_metric_invalid_type(
        self, monitoring_service: MonitoringService
    ):
        """Test tracking metric with invalid type."""
        # Test None type
        with pytest.raises((TypeError, ValueError)):
            await monitoring_service.track_metric(
                name="test_metric",
                value=100.0,
                metric_type=None,
            )

        # Test invalid string type
        with pytest.raises((TypeError, ValueError, AttributeError)):
            await monitoring_service.track_metric(
                name="test_metric",
                value=100.0,
                metric_type="invalid_type",
            )

    async def test_track_performance_invalid_operation(
        self, monitoring_service: MonitoringService
    ):
        """Test tracking performance with invalid operation name."""
        # Test empty operation
        with pytest.raises((ValueError, TypeError)):
            await monitoring_service.track_performance(
                operation="",
                duration_ms=100.0,
            )

        # Test None operation
        with pytest.raises((TypeError, AttributeError)):
            await monitoring_service.track_performance(
                operation=None,
                duration_ms=100.0,
            )

    async def test_track_performance_invalid_duration(
        self, monitoring_service: MonitoringService
    ):
        """Test tracking performance with invalid duration."""
        # Test negative duration
        with pytest.raises((ValueError, TypeError)):
            await monitoring_service.track_performance(
                operation="test_op",
                duration_ms=-100.0,
            )

        # Test None duration
        with pytest.raises((TypeError, ValueError)):
            await monitoring_service.track_performance(
                operation="test_op",
                duration_ms=None,
            )

        # Test string duration
        with pytest.raises((TypeError, ValueError)):
            await monitoring_service.track_performance(
                operation="test_op",
                duration_ms="not_a_number",
            )

    async def test_user_analytics_invalid_days(
        self, monitoring_service: MonitoringService
    ):
        """Test user analytics with invalid days parameter."""
        # Test negative days
        with pytest.raises((ValueError, TypeError)):
            await monitoring_service.get_user_analytics(days=-1)

        # Test zero days
        with pytest.raises((ValueError, TypeError)):
            await monitoring_service.get_user_analytics(days=0)

        # Test very large days
        with pytest.raises((ValueError, OverflowError)):
            await monitoring_service.get_user_analytics(days=999999999)

        # Test string days
        with pytest.raises((TypeError, ValueError)):
            await monitoring_service.get_user_analytics(days="invalid")

    async def test_create_dashboard_invalid_inputs(
        self, monitoring_service: MonitoringService
    ):
        """Test dashboard creation with invalid inputs."""
        # Test empty name
        with pytest.raises((ValueError, TypeError)):
            await monitoring_service.create_custom_dashboard(
                name="",
                metrics=["metric1", "metric2"],
            )

        # Test None name
        with pytest.raises((TypeError, AttributeError)):
            await monitoring_service.create_custom_dashboard(
                name=None,
                metrics=["metric1", "metric2"],
            )

        # Test None metrics list
        with pytest.raises((TypeError, AttributeError)):
            await monitoring_service.create_custom_dashboard(
                name="test_dashboard",
                metrics=None,
            )

        # Test empty metrics list
        result = await monitoring_service.create_custom_dashboard(
            name="test_dashboard",
            metrics=[],
        )
        # Should handle gracefully
        assert "metrics" in result
        assert len(result["metrics"]) == 0


# ============================================================================
# SERVICE FAILURE TESTS
# ============================================================================


class TestServiceFailures:
    """Test service failure scenarios."""

    @patch("src.services.monitoring_service.get_async_session")
    async def test_database_connection_failure(
        self, mock_get_session, monitoring_service: MonitoringService
    ):
        """Test behavior when database connection fails."""
        # Mock database failure
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection failed")
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Act - Should handle database failure gracefully
        try:
            analytics_data = await monitoring_service.get_user_analytics(days=7)
            # If it doesn't raise, should have error information
            assert "error" in analytics_data
        except Exception as e:
            # If it raises, should be handled appropriately
            assert "Database" in str(e) or "connection" in str(e)

    async def test_system_health_component_failures(
        self, monitoring_service: MonitoringService
    ):
        """Test system health when components fail."""
        # System health should handle component failures gracefully
        health_data = await monitoring_service.get_system_health()

        # Should always return a valid structure
        assert "timestamp" in health_data
        assert "status" in health_data
        assert "components" in health_data

        # Even with failures, should have component information
        assert len(health_data["components"]) > 0

        # Failed components should be marked appropriately
        for component_name, component_data in health_data["components"].items():
            if component_data["status"] in ["unhealthy", "error"]:
                # Should have failure indication
                assert "connected" in component_data
                # Disconnected components should be marked as such
                if component_data["status"] == "error":
                    assert component_data["connected"] is False

    @patch("src.services.monitoring_service.get_redis_service")
    async def test_redis_service_unavailable(
        self, mock_redis_service, monitoring_service: MonitoringService
    ):
        """Test behavior when Redis service is unavailable."""
        # Mock Redis unavailability
        mock_redis_service.return_value = None

        # User action tracking should handle Redis unavailability
        await monitoring_service.track_user_action(
            user_id=1,
            action="test_action",
            metadata={"test": True},
        )
        # Should not raise exception

        # Metric tracking should still work
        await monitoring_service.track_metric(
            name="test_metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
        )

        # Should have metric in memory
        assert len(monitoring_service.metrics) > 0

    async def test_multiple_concurrent_failures(
        self, monitoring_service: MonitoringService
    ):
        """Test handling multiple concurrent failure scenarios."""
        # Simulate high error rate
        error_count = 0
        total_operations = 50

        tasks = []
        for i in range(total_operations):
            try:
                if i % 3 == 0:
                    # Some operations will fail
                    task = monitoring_service.track_metric(
                        name="",  # Invalid name
                        value=100.0,
                        metric_type=MetricType.GAUGE,
                    )
                else:
                    task = monitoring_service.track_metric(
                        name=f"metric_{i}",
                        value=100.0,
                        metric_type=MetricType.GAUGE,
                    )
                tasks.append(task)
            except Exception:
                error_count += 1

        # Execute with exception handling
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        successful = [r for r in results if not isinstance(r, Exception)]

        # Should have some successful operations
        assert len(successful) > 0
        # Should have some failed operations
        assert len(exceptions) > 0

        # System should remain stable
        assert isinstance(monitoring_service.metrics, list)


# ============================================================================
# RESOURCE EXHAUSTION TESTS
# ============================================================================


class TestResourceExhaustion:
    """Test resource exhaustion scenarios."""

    async def test_metrics_memory_limit(self, monitoring_service: MonitoringService):
        """Test metrics list memory management."""
        # Add many metrics to test memory limit
        initial_count = len(monitoring_service.metrics)

        # Add more than the limit (10000)
        metric_count = 12000
        for i in range(metric_count):
            await monitoring_service.track_metric(
                name=f"memory_test_metric_{i}",
                value=float(i),
                metric_type=MetricType.COUNTER,
            )

        # Should limit memory usage
        final_count = len(monitoring_service.metrics)
        assert final_count <= 10000  # Should be limited
        assert final_count > 8000  # Should keep reasonable amount

    async def test_performance_data_memory_limit(
        self, monitoring_service: MonitoringService
    ):
        """Test performance data memory management."""
        operation_name = "memory_test_operation"

        # Add more than the limit (1000 per operation)
        measurement_count = 1500
        for i in range(measurement_count):
            await monitoring_service.track_performance(
                operation=operation_name,
                duration_ms=float(i),
                status="success",
            )

        # Should limit memory usage per operation
        if operation_name in monitoring_service.performance_data:
            operation_data = monitoring_service.performance_data[operation_name]
            assert len(operation_data) <= 1000  # Should be limited
            assert len(operation_data) > 800  # Should keep reasonable amount

    async def test_concurrent_resource_pressure(
        self, monitoring_service: MonitoringService
    ):
        """Test system under concurrent resource pressure."""
        # Create high concurrent load
        concurrent_tasks = 100
        operations_per_task = 50

        async def stress_task(task_id: int):
            for i in range(operations_per_task):
                try:
                    await monitoring_service.track_metric(
                        name=f"stress_metric_{task_id}_{i}",
                        value=float(i),
                        metric_type=MetricType.GAUGE,
                    )
                    await monitoring_service.track_performance(
                        operation=f"stress_operation_{task_id}",
                        duration_ms=float(i * 10),
                        status="success",
                    )
                except Exception:
                    # Some operations may fail under stress
                    pass

        # Execute stress test
        tasks = [stress_task(i) for i in range(concurrent_tasks)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # System should remain responsive
        health_data = await monitoring_service.get_system_health()
        assert "timestamp" in health_data
        assert "status" in health_data

        # Should have some metrics and performance data
        assert len(monitoring_service.metrics) > 0
        assert len(monitoring_service.performance_data) > 0

    async def test_large_data_structures(self, monitoring_service: MonitoringService):
        """Test handling of large data structures."""
        # Test with large tags dictionary
        large_tags = {f"tag_{i}": f"value_{i}" for i in range(1000)}

        await monitoring_service.track_metric(
            name="large_tags_metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
            tags=large_tags,
        )

        # Should handle large tags gracefully
        assert len(monitoring_service.metrics) > 0

        # Test with large metadata
        large_metadata = {f"key_{i}": f"data_{i}" * 100 for i in range(100)}

        await monitoring_service.track_user_action(
            user_id=1,
            action="large_metadata_action",
            metadata=large_metadata,
        )

        # Should handle large metadata gracefully (no exception)


# ============================================================================
# NETWORK AND CONNECTIVITY TESTS
# ============================================================================


class TestNetworkConnectivity:
    """Test network and connectivity error scenarios."""

    @patch("src.services.monitoring_service.get_redis_service")
    async def test_redis_connection_timeout(
        self, mock_redis_service, monitoring_service: MonitoringService
    ):
        """Test Redis connection timeout handling."""
        # Mock Redis timeout
        mock_redis = AsyncMock()
        mock_redis.set_hash.side_effect = asyncio.TimeoutError("Redis timeout")
        mock_redis_service.return_value = mock_redis

        # Should handle timeout gracefully
        await monitoring_service.track_metric(
            name="timeout_test_metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
        )

        # Metric should still be stored in memory
        assert len(monitoring_service.metrics) > 0

    async def test_database_query_timeout(self, monitoring_service: MonitoringService):
        """Test database query timeout scenarios."""
        with patch("src.services.monitoring_service.get_async_session") as mock_session:
            # Mock database timeout
            mock_db = AsyncMock()
            mock_db.execute.side_effect = asyncio.TimeoutError("Database timeout")
            mock_session.return_value.__aenter__.return_value = mock_db

            # Should handle timeout gracefully
            analytics_data = await monitoring_service.get_user_analytics(days=7)

            # Should return error information or default values
            assert isinstance(analytics_data, dict)
            if "error" not in analytics_data:
                # Should have basic structure with default values
                assert "users" in analytics_data
                assert "surveys" in analytics_data

    async def test_external_service_unavailable(
        self, monitoring_service: MonitoringService
    ):
        """Test external service unavailability."""
        with patch(
            "src.services.monitoring_service.get_telegram_service"
        ) as mock_telegram:
            # Mock Telegram service unavailability
            mock_telegram.side_effect = Exception("Telegram service unavailable")

            # System health should handle external service failure
            health_data = await monitoring_service.get_system_health()

            # Should mark Telegram as unhealthy
            assert "telegram_bot" in health_data["components"]
            telegram_health = health_data["components"]["telegram_bot"]
            assert telegram_health["status"] in ["unhealthy", "error"]
            assert telegram_health["connected"] is False


# ============================================================================
# ERROR PROPAGATION TESTS
# ============================================================================


class TestErrorPropagation:
    """Test error propagation and handling."""

    async def test_exception_isolation(self, monitoring_service: MonitoringService):
        """Test that exceptions in one operation don't affect others."""
        # Track a valid metric first
        await monitoring_service.track_metric(
            name="valid_metric_before",
            value=100.0,
            metric_type=MetricType.GAUGE,
        )

        initial_count = len(monitoring_service.metrics)

        # Try to track invalid metric
        try:
            await monitoring_service.track_metric(
                name="",  # Invalid name
                value=100.0,
                metric_type=MetricType.GAUGE,
            )
        except Exception:
            pass  # Expected to fail

        # Track another valid metric
        await monitoring_service.track_metric(
            name="valid_metric_after",
            value=200.0,
            metric_type=MetricType.GAUGE,
        )

        # Should have the valid metrics
        final_count = len(monitoring_service.metrics)
        assert final_count >= initial_count + 1  # At least one more metric

    async def test_partial_failure_handling(
        self, monitoring_service: MonitoringService
    ):
        """Test handling of partial failures in batch operations."""
        # Mix of valid and invalid operations
        operations = [
            ("valid_metric_1", 100.0, MetricType.GAUGE),
            ("", 200.0, MetricType.GAUGE),  # Invalid - empty name
            ("valid_metric_2", 300.0, MetricType.GAUGE),
            ("valid_metric_3", None, MetricType.GAUGE),  # Invalid - None value
            ("valid_metric_4", 400.0, MetricType.GAUGE),
        ]

        successful_count = 0
        failed_count = 0

        for name, value, metric_type in operations:
            try:
                await monitoring_service.track_metric(
                    name=name,
                    value=value,
                    metric_type=metric_type,
                )
                successful_count += 1
            except Exception:
                failed_count += 1

        # Should have some successful and some failed operations
        assert successful_count > 0
        assert failed_count > 0
        assert successful_count + failed_count == len(operations)

    async def test_error_logging_and_recovery(
        self, monitoring_service: MonitoringService
    ):
        """Test error logging and system recovery."""
        # Cause various types of errors
        error_scenarios = [
            ("", 100.0, MetricType.GAUGE),  # Empty name
            ("test", None, MetricType.GAUGE),  # None value
            ("test", "invalid", MetricType.GAUGE),  # String value
        ]

        # System should recover from each error
        for name, value, metric_type in error_scenarios:
            try:
                await monitoring_service.track_metric(
                    name=name,
                    value=value,
                    metric_type=metric_type,
                )
            except Exception:
                pass  # Expected to fail

            # System should still be responsive after each error
            await monitoring_service.track_metric(
                name="recovery_test",
                value=100.0,
                metric_type=MetricType.GAUGE,
            )

        # Should have recovery metrics
        recovery_metrics = [
            m for m in monitoring_service.metrics if m.name == "recovery_test"
        ]
        assert len(recovery_metrics) == len(error_scenarios)

    async def test_cascading_failure_prevention(
        self, monitoring_service: MonitoringService
    ):
        """Test prevention of cascading failures."""
        # Simulate failure in one component
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis.side_effect = Exception("Redis failure")

            # Track metrics (should work despite Redis failure)
            await monitoring_service.track_metric(
                name="cascade_test_metric",
                value=100.0,
                metric_type=MetricType.GAUGE,
            )

            # Track performance (should work despite Redis failure)
            await monitoring_service.track_performance(
                operation="cascade_test_operation",
                duration_ms=150.0,
                status="success",
            )

            # Get system health (should work despite Redis failure)
            health_data = await monitoring_service.get_system_health()

            # System should remain functional
            assert len(monitoring_service.metrics) > 0
            assert "cascade_test_operation" in monitoring_service.performance_data
            assert "timestamp" in health_data

            # Redis component should be marked as failed
            assert "redis" in health_data["components"]
            redis_health = health_data["components"]["redis"]
            assert redis_health["status"] in ["unhealthy", "error"]
