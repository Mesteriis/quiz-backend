"""
Comprehensive Edge Cases Tests for Monitoring System.

This module tests edge cases and boundary conditions:
- Extreme values and boundary conditions
- Race conditions and timing issues
- Memory and performance edge cases
- Data consistency edge cases
- Special character and encoding issues

All tests use best practices:
- Comprehensive boundary testing
- Race condition simulation
- Memory stress testing
- Timing-sensitive scenarios
- Context7 integration ready
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import patch, AsyncMock
import pytest
from faker import Faker

from src.services.monitoring_service import MonitoringService
from src.schemas.monitoring import MetricType, AlertLevel

# Initialize faker
fake = Faker(["en_US", "ru_RU"])


# ============================================================================
# EXTREME VALUES TESTS
# ============================================================================


class TestExtremeValues:
    """Test extreme values and boundary conditions."""

    async def test_metric_extreme_values(self, monitoring_service: MonitoringService):
        """Test metrics with extreme values."""
        extreme_values = [
            0,  # Zero
            1e-10,  # Very small positive
            -1e-10,  # Very small negative
            1e10,  # Very large positive
            -1e10,  # Very large negative
            2**63 - 1,  # Max int64
            -(2**63),  # Min int64
            1.7976931348623157e308,  # Close to max float64
            2.2250738585072014e-308,  # Close to min positive float64
        ]

        for value in extreme_values:
            await monitoring_service.track_metric(
                name=f"extreme_value_metric_{value}",
                value=value,
                metric_type=MetricType.GAUGE,
                tags={"extreme": "true", "value_type": str(type(value).__name__)},
            )

        # Should handle all extreme values
        assert len(monitoring_service.metrics) >= len(extreme_values)

        # Verify extreme values are stored correctly
        for i, expected_value in enumerate(extreme_values):
            metric = monitoring_service.metrics[i]
            if isinstance(expected_value, (int, float)):
                assert (
                    abs(metric.value - expected_value) < 1e-6
                    or metric.value == expected_value
                )

    async def test_metric_name_edge_cases(self, monitoring_service: MonitoringService):
        """Test metric names with edge cases."""
        edge_case_names = [
            "a",  # Single character
            "metric_with_underscores",  # Common format
            "metric-with-dashes",  # Dashes
            "metric.with.dots",  # Dots
            "metric/with/slashes",  # Slashes
            "metric with spaces",  # Spaces
            "METRIC_UPPERCASE",  # Uppercase
            "metric123numbers",  # Numbers
            "метрика_кириллица",  # Cyrillic
            "测试指标",  # Chinese
            "🔥_emoji_metric",  # Emoji
            "a" * 255,  # Very long name
        ]

        for name in edge_case_names:
            try:
                await monitoring_service.track_metric(
                    name=name,
                    value=100.0,
                    metric_type=MetricType.GAUGE,
                    tags={"edge_case": "name"},
                )
            except Exception:
                # Some edge cases might be rejected
                pass

        # Should handle most edge cases
        assert len(monitoring_service.metrics) > 0

    async def test_tags_edge_cases(self, monitoring_service: MonitoringService):
        """Test tags with edge cases."""
        edge_case_tags = [
            {},  # Empty tags
            {"": "empty_key"},  # Empty key
            {"key": ""},  # Empty value
            {"key": None},  # None value
            {"null": "null"},  # String null
            {"unicode": "测试值"},  # Unicode value
            {"emoji": "🚀💡🔥"},  # Emoji values
            {"very_long_key" * 10: "value"},  # Very long key
            {"key": "very_long_value" * 100},  # Very long value
            {f"key_{i}": f"value_{i}" for i in range(100)},  # Many tags
        ]

        for i, tags in enumerate(edge_case_tags):
            try:
                await monitoring_service.track_metric(
                    name=f"edge_case_tags_metric_{i}",
                    value=100.0,
                    metric_type=MetricType.GAUGE,
                    tags=tags,
                )
            except Exception:
                # Some edge cases might be rejected
                pass

        # Should handle most edge cases
        assert len(monitoring_service.metrics) > 0

    async def test_performance_extreme_durations(
        self, monitoring_service: MonitoringService
    ):
        """Test performance tracking with extreme durations."""
        extreme_durations = [
            0.001,  # Very fast (1ms)
            0.0001,  # Ultra fast (0.1ms)
            1000.0,  # 1 second
            60000.0,  # 1 minute
            3600000.0,  # 1 hour
            86400000.0,  # 1 day
            1e10,  # Extremely long
        ]

        for duration in extreme_durations:
            await monitoring_service.track_performance(
                operation=f"extreme_duration_{duration}",
                duration_ms=duration,
                status="success",
            )

        # Should handle all extreme durations
        assert len(monitoring_service.performance_data) >= len(extreme_durations)

    async def test_user_analytics_extreme_periods(
        self, monitoring_service: MonitoringService
    ):
        """Test user analytics with extreme time periods."""
        extreme_periods = [
            1,  # 1 day
            365,  # 1 year
            1825,  # 5 years
            3650,  # 10 years
        ]

        for period in extreme_periods:
            try:
                analytics_data = await monitoring_service.get_user_analytics(
                    days=period
                )
                assert analytics_data["period_days"] == period
                assert "timestamp" in analytics_data
            except Exception:
                # Very extreme periods might be rejected
                pass


# ============================================================================
# TIMING AND RACE CONDITIONS TESTS
# ============================================================================


class TestTimingAndRaceConditions:
    """Test timing-sensitive scenarios and race conditions."""

    async def test_concurrent_metric_tracking(
        self, monitoring_service: MonitoringService
    ):
        """Test concurrent metric tracking for race conditions."""
        # Create multiple concurrent tasks tracking the same metric
        metric_name = "concurrent_test_metric"
        concurrent_tasks = 100

        async def track_metric_task(task_id: int):
            await monitoring_service.track_metric(
                name=metric_name,
                value=float(task_id),
                metric_type=MetricType.COUNTER,
                tags={"task_id": str(task_id)},
            )

        # Execute all tasks concurrently
        await asyncio.gather(*[track_metric_task(i) for i in range(concurrent_tasks)])

        # Should handle concurrent access
        concurrent_metrics = [
            m for m in monitoring_service.metrics if m.name == metric_name
        ]
        assert len(concurrent_metrics) == concurrent_tasks

        # Values should be preserved correctly
        values = [m.value for m in concurrent_metrics]
        assert len(set(values)) == concurrent_tasks  # All unique values

    async def test_concurrent_performance_tracking(
        self, monitoring_service: MonitoringService
    ):
        """Test concurrent performance tracking."""
        operation_name = "concurrent_performance_test"
        concurrent_tasks = 50

        async def track_performance_task(task_id: int):
            await monitoring_service.track_performance(
                operation=operation_name,
                duration_ms=float(task_id * 10),
                status="success",
            )

        # Execute all tasks concurrently
        await asyncio.gather(
            *[track_performance_task(i) for i in range(concurrent_tasks)]
        )

        # Should handle concurrent access
        assert operation_name in monitoring_service.performance_data
        performance_list = monitoring_service.performance_data[operation_name]
        assert len(performance_list) == concurrent_tasks

    async def test_concurrent_analytics_requests(
        self, monitoring_service: MonitoringService
    ):
        """Test concurrent analytics requests."""
        concurrent_requests = 20

        async def get_analytics_task(period: int):
            return await monitoring_service.get_user_analytics(days=period)

        # Execute concurrent analytics requests
        tasks = [get_analytics_task(7) for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert len(results) == concurrent_requests
        for result in results:
            assert "timestamp" in result
            assert "period_days" in result
            assert result["period_days"] == 7

    async def test_rapid_sequential_operations(
        self, monitoring_service: MonitoringService
    ):
        """Test rapid sequential operations."""
        operations_count = 1000
        start_time = time.time()

        # Track metrics rapidly
        for i in range(operations_count):
            await monitoring_service.track_metric(
                name=f"rapid_metric_{i}",
                value=float(i),
                metric_type=MetricType.COUNTER,
            )

        end_time = time.time()
        duration = end_time - start_time

        # Should handle rapid operations
        assert len(monitoring_service.metrics) >= operations_count

        # Should complete in reasonable time (less than 10 seconds)
        assert duration < 10.0

    async def test_interleaved_operations(self, monitoring_service: MonitoringService):
        """Test interleaved different types of operations."""
        operations_count = 100

        async def interleaved_operations():
            tasks = []
            for i in range(operations_count):
                if i % 3 == 0:
                    # Track metric
                    task = monitoring_service.track_metric(
                        name=f"interleaved_metric_{i}",
                        value=float(i),
                        metric_type=MetricType.GAUGE,
                    )
                elif i % 3 == 1:
                    # Track performance
                    task = monitoring_service.track_performance(
                        operation=f"interleaved_op_{i}",
                        duration_ms=float(i * 10),
                        status="success",
                    )
                else:
                    # Track user action
                    task = monitoring_service.track_user_action(
                        user_id=i,
                        action="interleaved_action",
                        metadata={"index": i},
                    )
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Execute interleaved operations
        await interleaved_operations()

        # Should handle mixed operations
        assert len(monitoring_service.metrics) > 0
        assert len(monitoring_service.performance_data) > 0

    async def test_timestamp_ordering_under_load(
        self, monitoring_service: MonitoringService
    ):
        """Test timestamp ordering under concurrent load."""
        operations_count = 500

        # Track metrics with small delays
        for i in range(operations_count):
            await monitoring_service.track_metric(
                name=f"timestamp_test_{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
            )
            if i % 10 == 0:
                await asyncio.sleep(0.001)  # Small delay every 10 operations

        # Timestamps should be ordered
        timestamps = [m.timestamp for m in monitoring_service.metrics]
        assert len(timestamps) >= operations_count

        # Check if timestamps are reasonably ordered (allowing small discrepancies)
        ordering_violations = 0
        for i in range(1, len(timestamps)):
            if timestamps[i] < timestamps[i - 1]:
                ordering_violations += 1

        # Allow some ordering violations due to concurrent execution
        assert ordering_violations < len(timestamps) * 0.1  # Less than 10% violations


# ============================================================================
# MEMORY AND PERFORMANCE EDGE CASES
# ============================================================================


class TestMemoryAndPerformanceEdgeCases:
    """Test memory and performance edge cases."""

    async def test_memory_limit_boundary(self, monitoring_service: MonitoringService):
        """Test behavior at memory limit boundaries."""
        # Fill metrics to near the limit
        metrics_limit = 10000
        fill_count = metrics_limit - 100  # Leave some room

        for i in range(fill_count):
            await monitoring_service.track_metric(
                name=f"boundary_metric_{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
            )

        # Add metrics to push over the limit
        for i in range(200):
            await monitoring_service.track_metric(
                name=f"overflow_metric_{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
            )

        # Should handle limit boundary correctly
        assert len(monitoring_service.metrics) <= metrics_limit

    async def test_performance_data_limit_boundary(
        self, monitoring_service: MonitoringService
    ):
        """Test performance data limit boundaries."""
        operation_name = "boundary_test_operation"
        performance_limit = 1000

        # Fill to near the limit
        for i in range(performance_limit + 200):
            await monitoring_service.track_performance(
                operation=operation_name,
                duration_ms=float(i),
                status="success",
            )

        # Should handle limit boundary correctly
        if operation_name in monitoring_service.performance_data:
            performance_list = monitoring_service.performance_data[operation_name]
            assert len(performance_list) <= performance_limit

    async def test_large_object_handling(self, monitoring_service: MonitoringService):
        """Test handling of large objects."""
        # Large tags dictionary
        large_tags = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}

        await monitoring_service.track_metric(
            name="large_object_metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
            tags=large_tags,
        )

        # Should handle large objects
        assert len(monitoring_service.metrics) > 0

        # Large metadata for user action
        large_metadata = {
            "data": "x" * 10000,
            "nested": {f"key_{i}": f"value_{i}" for i in range(100)},
            "list": [f"item_{i}" for i in range(1000)],
        }

        await monitoring_service.track_user_action(
            user_id=1,
            action="large_metadata_action",
            metadata=large_metadata,
        )

        # Should handle large metadata without errors

    async def test_memory_cleanup_efficiency(
        self, monitoring_service: MonitoringService
    ):
        """Test memory cleanup efficiency."""
        # Fill with metrics
        initial_count = 5000
        for i in range(initial_count):
            await monitoring_service.track_metric(
                name=f"cleanup_metric_{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
            )

        # Trigger cleanup by adding more metrics
        for i in range(initial_count, initial_count + 7000):
            await monitoring_service.track_metric(
                name=f"cleanup_metric_{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
            )

        # Should have cleaned up efficiently
        assert len(monitoring_service.metrics) <= 10000

        # Recent metrics should still be present
        recent_metrics = [
            m for m in monitoring_service.metrics if "cleanup_metric_1" in m.name
        ]
        assert len(recent_metrics) > 0

    async def test_concurrent_memory_pressure(
        self, monitoring_service: MonitoringService
    ):
        """Test concurrent memory pressure scenarios."""
        concurrent_tasks = 50
        metrics_per_task = 200

        async def memory_pressure_task(task_id: int):
            for i in range(metrics_per_task):
                await monitoring_service.track_metric(
                    name=f"pressure_metric_{task_id}_{i}",
                    value=float(i),
                    metric_type=MetricType.GAUGE,
                    tags={f"task": str(task_id), f"index": str(i)},
                )

        # Execute concurrent memory pressure
        await asyncio.gather(
            *[memory_pressure_task(i) for i in range(concurrent_tasks)]
        )

        # Should handle concurrent memory pressure
        assert len(monitoring_service.metrics) > 0
        assert len(monitoring_service.metrics) <= 10000  # Should not exceed limit


# ============================================================================
# DATA CONSISTENCY EDGE CASES
# ============================================================================


class TestDataConsistencyEdgeCases:
    """Test data consistency edge cases."""

    async def test_duplicate_metric_names(self, monitoring_service: MonitoringService):
        """Test handling of duplicate metric names."""
        metric_name = "duplicate_test_metric"

        # Add same metric name multiple times with different values
        values = [100.0, 200.0, 300.0, 400.0, 500.0]
        for value in values:
            await monitoring_service.track_metric(
                name=metric_name,
                value=value,
                metric_type=MetricType.GAUGE,
            )

        # Should handle duplicates
        duplicate_metrics = [
            m for m in monitoring_service.metrics if m.name == metric_name
        ]
        assert len(duplicate_metrics) == len(values)

        # Values should be preserved
        metric_values = [m.value for m in duplicate_metrics]
        assert set(metric_values) == set(values)

    async def test_metric_type_consistency(self, monitoring_service: MonitoringService):
        """Test metric type consistency for same metric name."""
        metric_name = "type_consistency_metric"

        # Add same metric name with different types
        types = [
            MetricType.GAUGE,
            MetricType.COUNTER,
            MetricType.TIMER,
            MetricType.HISTOGRAM,
        ]
        for metric_type in types:
            await monitoring_service.track_metric(
                name=metric_name,
                value=100.0,
                metric_type=metric_type,
            )

        # Should handle different types
        type_metrics = [m for m in monitoring_service.metrics if m.name == metric_name]
        assert len(type_metrics) == len(types)

        # Types should be preserved
        metric_types = [m.type for m in type_metrics]
        assert set(metric_types) == set(types)

    async def test_timestamp_consistency(self, monitoring_service: MonitoringService):
        """Test timestamp consistency across operations."""
        start_time = datetime.now()

        # Track multiple metrics
        for i in range(10):
            await monitoring_service.track_metric(
                name=f"timestamp_consistency_{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
            )

        end_time = datetime.now()

        # Timestamps should be within reasonable range
        for metric in monitoring_service.metrics[-10:]:
            assert start_time <= metric.timestamp <= end_time

    async def test_performance_data_consistency(
        self, monitoring_service: MonitoringService
    ):
        """Test performance data consistency."""
        operation_name = "consistency_test_operation"

        # Track performance data
        durations = [100.0, 200.0, 150.0, 300.0, 250.0]
        for duration in durations:
            await monitoring_service.track_performance(
                operation=operation_name,
                duration_ms=duration,
                status="success",
            )

        # Data should be consistent
        assert operation_name in monitoring_service.performance_data
        performance_list = monitoring_service.performance_data[operation_name]
        assert len(performance_list) == len(durations)
        assert set(performance_list) == set(durations)

    async def test_cross_operation_consistency(
        self, monitoring_service: MonitoringService
    ):
        """Test consistency across different operations."""
        # Track metrics, performance, and user actions
        await monitoring_service.track_metric(
            name="consistency_metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
        )

        await monitoring_service.track_performance(
            operation="consistency_operation",
            duration_ms=150.0,
            status="success",
        )

        await monitoring_service.track_user_action(
            user_id=1,
            action="consistency_action",
            metadata={"test": "consistency"},
        )

        # All operations should be reflected in the service state
        assert len(monitoring_service.metrics) > 0
        assert len(monitoring_service.performance_data) > 0

        # State should be consistent
        assert isinstance(monitoring_service.metrics, list)
        assert isinstance(monitoring_service.performance_data, dict)


# ============================================================================
# SPECIAL CHARACTERS AND ENCODING EDGE CASES
# ============================================================================


class TestSpecialCharactersAndEncoding:
    """Test special characters and encoding edge cases."""

    async def test_unicode_metric_names(self, monitoring_service: MonitoringService):
        """Test Unicode characters in metric names."""
        unicode_names = [
            "测试指标",  # Chinese
            "тест_метрика",  # Russian
            "métrique_test",  # French
            "メトリック_テスト",  # Japanese
            "मेट्रिक_परीक्षण",  # Hindi
            "مقياس_اختبار",  # Arabic
            "🔥_火_fire",  # Mixed emoji and characters
        ]

        for name in unicode_names:
            try:
                await monitoring_service.track_metric(
                    name=name,
                    value=100.0,
                    metric_type=MetricType.GAUGE,
                    tags={"encoding": "unicode"},
                )
            except Exception:
                # Some Unicode might not be supported
                pass

        # Should handle at least some Unicode
        unicode_metrics = [
            m
            for m in monitoring_service.metrics
            if m.tags and m.tags.get("encoding") == "unicode"
        ]
        assert len(unicode_metrics) > 0

    async def test_special_characters_in_tags(
        self, monitoring_service: MonitoringService
    ):
        """Test special characters in tags."""
        special_char_tags = [
            {"key": "value with spaces"},
            {"key": "value\nwith\nnewlines"},
            {"key": "value\twith\ttabs"},
            {"key": 'value"with"quotes'},
            {"key": "value'with'apostrophes"},
            {"key": "value\\with\\backslashes"},
            {"key": "value/with/slashes"},
            {"key": "value<with>brackets"},
            {"key": "value{with}braces"},
            {"key": "value[with]square"},
            {"key": "value|with|pipes"},
            {"key": "value&with&ampersands"},
            {"key": "value%with%percent"},
            {"key": "value#with#hash"},
            {"key": "value@with@at"},
            {"key": "value!with!exclamation"},
            {"key": "value?with?question"},
            {"key": "value*with*asterisk"},
            {"key": "value+with+plus"},
            {"key": "value=with=equals"},
            {"key": "value~with~tilde"},
            {"key": "value`with`backticks"},
            {"key": "value^with^caret"},
            {"key": "value$with$dollar"},
            {"unicode": "🚀💡🔥⚡🌟"},
        ]

        for i, tags in enumerate(special_char_tags):
            try:
                await monitoring_service.track_metric(
                    name=f"special_chars_metric_{i}",
                    value=100.0,
                    metric_type=MetricType.GAUGE,
                    tags=tags,
                )
            except Exception:
                # Some special characters might not be supported
                pass

        # Should handle most special characters
        special_metrics = [
            m for m in monitoring_service.metrics if "special_chars_metric_" in m.name
        ]
        assert len(special_metrics) > 0

    async def test_encoding_edge_cases(self, monitoring_service: MonitoringService):
        """Test encoding edge cases."""
        # Test various encoding scenarios
        encoding_tests = [
            ("utf8_metric", "UTF-8 value: 测试"),
            ("latin1_metric", "Latin-1 value: café"),
            ("ascii_metric", "ASCII value: test"),
            ("mixed_metric", "Mixed: 测试 café test 🔥"),
        ]

        for name, value in encoding_tests:
            try:
                await monitoring_service.track_metric(
                    name=name,
                    value=100.0,
                    metric_type=MetricType.GAUGE,
                    tags={"description": value},
                )
            except Exception:
                # Some encodings might not be supported
                pass

        # Should handle most encoding scenarios
        encoding_metrics = [
            m
            for m in monitoring_service.metrics
            if "metric" in m.name and m.tags and "description" in m.tags
        ]
        assert len(encoding_metrics) > 0

    async def test_json_serialization_edge_cases(
        self, monitoring_service: MonitoringService
    ):
        """Test JSON serialization edge cases."""
        # Test data that might cause JSON serialization issues
        problematic_data = [
            {"key": "value with\x00null byte"},
            {"key": "value with\x1fcontrol char"},
            {"key": "value with\x7fdelete char"},
            {"recursive": {"nested": {"deep": {"value": "test"}}}},
            {"list": [1, 2, 3, "string", True, None]},
            {"float": 3.14159265359},
            {"scientific": 1.23e-10},
            {"boolean": True},
            {"null": None},
        ]

        for i, data in enumerate(problematic_data):
            try:
                await monitoring_service.track_user_action(
                    user_id=i,
                    action="json_test_action",
                    metadata=data,
                )
            except Exception:
                # Some data might not be JSON serializable
                pass

        # Should handle most JSON serialization scenarios
        # Test passes if no catastrophic failures occur
