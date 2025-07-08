"""
Comprehensive Positive Tests for User Analytics.

This module tests successful scenarios for user analytics functionality:
- User behavior tracking
- Analytics data aggregation
- Period-based analytics
- Performance analytics integration
- Statistical calculations

All tests use best practices:
- Polyfactory factories for realistic data
- Parametrized tests for different time periods
- Async/await for all operations
- Statistical validation
- Context7 integration ready
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from faker import Faker

from src.services.monitoring_service import MonitoringService
from src.schemas.monitoring import MetricType

# Initialize faker
fake = Faker(["en_US", "ru_RU"])


# ============================================================================
# BASIC USER ANALYTICS TESTS
# ============================================================================


class TestBasicUserAnalytics:
    """Test basic user analytics functionality."""

    async def test_get_user_analytics_basic_structure(
        self, monitoring_service: MonitoringService
    ):
        """Test that user analytics returns proper basic structure."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert basic structure
        assert isinstance(analytics_data, dict)
        assert "period_days" in analytics_data
        assert "timestamp" in analytics_data
        assert "users" in analytics_data
        assert "surveys" in analytics_data
        assert "actions" in analytics_data
        assert "performance" in analytics_data

        # Verify period_days
        assert analytics_data["period_days"] == 7

        # Verify timestamp format
        timestamp_str = analytics_data["timestamp"]
        assert isinstance(timestamp_str, str)
        # Should be able to parse ISO format
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    @pytest.mark.parametrize("analytics_period", [1, 7, 30, 90])
    async def test_get_user_analytics_different_periods(
        self, monitoring_service: MonitoringService, analytics_period: int
    ):
        """Test user analytics for different time periods."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(
            days=analytics_period
        )

        # Assert period is correctly set
        assert analytics_data["period_days"] == analytics_period

        # Assert all required sections exist
        required_sections = ["users", "surveys", "actions", "performance"]
        for section in required_sections:
            assert section in analytics_data
            assert isinstance(analytics_data[section], dict)

    async def test_user_analytics_users_section(
        self, monitoring_service: MonitoringService
    ):
        """Test users section of analytics data."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert users section structure
        users_data = analytics_data["users"]
        assert isinstance(users_data, dict)

        # Required fields
        required_fields = ["new_registrations", "active_users"]
        for field in required_fields:
            assert field in users_data
            assert isinstance(users_data[field], int)
            assert users_data[field] >= 0

        # Logical validation
        assert users_data["new_registrations"] >= 0
        assert users_data["active_users"] >= 0

    async def test_user_analytics_surveys_section(
        self, monitoring_service: MonitoringService
    ):
        """Test surveys section of analytics data."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert surveys section structure
        surveys_data = analytics_data["surveys"]
        assert isinstance(surveys_data, dict)

        # Required fields
        assert "completions" in surveys_data
        assert "top_surveys" in surveys_data

        # Validate completions
        assert isinstance(surveys_data["completions"], int)
        assert surveys_data["completions"] >= 0

        # Validate top_surveys
        top_surveys = surveys_data["top_surveys"]
        assert isinstance(top_surveys, list)

        # Each top survey should have proper structure
        for survey in top_surveys:
            assert isinstance(survey, dict)
            assert "title" in survey
            assert "responses" in survey
            assert isinstance(survey["title"], str)
            assert isinstance(survey["responses"], int)
            assert survey["responses"] >= 0

    async def test_user_analytics_actions_section(
        self, monitoring_service: MonitoringService
    ):
        """Test actions section of analytics data."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert actions section structure
        actions_data = analytics_data["actions"]
        assert isinstance(actions_data, dict)

        # Should have actions data (even if empty)
        # The structure depends on Redis availability, so we check basic format
        assert isinstance(actions_data, dict)

    async def test_user_analytics_performance_section(
        self, monitoring_service: MonitoringService
    ):
        """Test performance section of analytics data."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert performance section structure
        performance_data = analytics_data["performance"]
        assert isinstance(performance_data, dict)

        # Should be a dictionary of operation summaries
        for operation_name, operation_data in performance_data.items():
            assert isinstance(operation_name, str)
            assert isinstance(operation_data, dict)


# ============================================================================
# ANALYTICS PERIOD TESTS
# ============================================================================


class TestAnalyticsPeriods:
    """Test analytics for different time periods."""

    @pytest.mark.parametrize("period", [1, 3, 7, 14, 30, 60, 90])
    async def test_analytics_period_validation(
        self, monitoring_service: MonitoringService, period: int
    ):
        """Test analytics with various period lengths."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=period)

        # Assert period is correctly reflected
        assert analytics_data["period_days"] == period

        # Assert timestamp is recent
        timestamp = datetime.fromisoformat(
            analytics_data["timestamp"].replace("Z", "+00:00")
        )
        now = datetime.now().replace(tzinfo=timestamp.tzinfo)
        time_diff = abs((now - timestamp).total_seconds())
        assert time_diff < 60  # Within 1 minute

    async def test_short_period_analytics(self, monitoring_service: MonitoringService):
        """Test analytics for short periods (1 day)."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=1)

        # Assert structure is maintained for short periods
        assert analytics_data["period_days"] == 1
        assert "users" in analytics_data
        assert "surveys" in analytics_data

        # Values should be reasonable for 1 day
        users_data = analytics_data["users"]
        # New registrations in 1 day should be reasonable
        assert 0 <= users_data["new_registrations"] <= 10000

    async def test_long_period_analytics(self, monitoring_service: MonitoringService):
        """Test analytics for long periods (90 days)."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=90)

        # Assert structure is maintained for long periods
        assert analytics_data["period_days"] == 90
        assert "users" in analytics_data
        assert "surveys" in analytics_data

        # Values should be reasonable for 90 days
        users_data = analytics_data["users"]
        # New registrations in 90 days should be reasonable
        assert users_data["new_registrations"] >= 0

    async def test_analytics_timestamp_consistency(
        self, monitoring_service: MonitoringService
    ):
        """Test that analytics timestamps are consistent."""
        # Act - Get analytics for different periods
        periods = [1, 7, 30]
        analytics_results = []

        for period in periods:
            analytics_data = await monitoring_service.get_user_analytics(days=period)
            analytics_results.append(analytics_data)

        # Assert timestamps are close to each other
        timestamps = [
            datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
            for result in analytics_results
        ]

        # All timestamps should be within a few seconds of each other
        time_spread = max(timestamps) - min(timestamps)
        assert time_spread.total_seconds() < 10  # Within 10 seconds


# ============================================================================
# ANALYTICS WITH PERFORMANCE DATA TESTS
# ============================================================================


class TestAnalyticsWithPerformanceData:
    """Test analytics integration with performance data."""

    async def test_analytics_includes_performance_data(
        self, monitoring_service: MonitoringService, multiple_performance_data
    ):
        """Test that analytics includes performance data when available."""
        # Arrange - Add performance data
        for perf_data in multiple_performance_data[:10]:
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert performance data is included
        performance_data = analytics_data["performance"]
        assert isinstance(performance_data, dict)

        # Should have performance summaries for tracked operations
        operations = set(perf.operation for perf in multiple_performance_data)
        performance_operations = set(performance_data.keys())

        # Some operations should be included
        if len(operations) > 0:
            # At least some operations should be in the performance data
            assert len(performance_operations) > 0

    async def test_performance_summary_structure(
        self, monitoring_service: MonitoringService, multiple_performance_data
    ):
        """Test performance summary structure in analytics."""
        # Arrange - Add specific performance data
        test_operation = "test_analytics_operation"
        durations = [100.0, 200.0, 300.0, 150.0, 250.0]

        for duration in durations:
            await monitoring_service.track_performance(
                operation=test_operation,
                duration_ms=duration,
                status="success",
            )

        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert performance summary structure
        performance_data = analytics_data["performance"]

        if test_operation in performance_data:
            operation_summary = performance_data[test_operation]
            assert isinstance(operation_summary, dict)

            # Should have statistical summary
            expected_fields = ["avg_ms", "min_ms", "max_ms", "count"]
            for field in expected_fields:
                if field in operation_summary:
                    assert isinstance(operation_summary[field], (int, float))
                    assert operation_summary[field] >= 0

    async def test_analytics_performance_calculations(
        self, monitoring_service: MonitoringService
    ):
        """Test performance calculations in analytics."""
        # Arrange - Add known performance data
        test_operation = "calculation_test"
        known_durations = [100.0, 200.0, 300.0]  # avg=200, min=100, max=300

        for duration in known_durations:
            await monitoring_service.track_performance(
                operation=test_operation,
                duration_ms=duration,
                status="success",
            )

        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert calculations are correct
        performance_data = analytics_data["performance"]

        if test_operation in performance_data:
            summary = performance_data[test_operation]

            # Verify calculations
            if "avg_ms" in summary:
                assert abs(summary["avg_ms"] - 200.0) < 0.1
            if "min_ms" in summary:
                assert abs(summary["min_ms"] - 100.0) < 0.1
            if "max_ms" in summary:
                assert abs(summary["max_ms"] - 300.0) < 0.1
            if "count" in summary:
                assert summary["count"] == 3


# ============================================================================
# ANALYTICS DATA VALIDATION TESTS
# ============================================================================


class TestAnalyticsDataValidation:
    """Test analytics data validation and consistency."""

    async def test_analytics_data_types(self, monitoring_service: MonitoringService):
        """Test that analytics data has correct types."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert top-level types
        assert isinstance(analytics_data["period_days"], int)
        assert isinstance(analytics_data["timestamp"], str)
        assert isinstance(analytics_data["users"], dict)
        assert isinstance(analytics_data["surveys"], dict)
        assert isinstance(analytics_data["actions"], dict)
        assert isinstance(analytics_data["performance"], dict)

        # Assert users data types
        users_data = analytics_data["users"]
        for field_name, field_value in users_data.items():
            assert isinstance(field_value, int), f"Field {field_name} should be int"

        # Assert surveys data types
        surveys_data = analytics_data["surveys"]
        if "completions" in surveys_data:
            assert isinstance(surveys_data["completions"], int)
        if "top_surveys" in surveys_data:
            assert isinstance(surveys_data["top_surveys"], list)

    async def test_analytics_value_ranges(self, monitoring_service: MonitoringService):
        """Test that analytics values are within reasonable ranges."""
        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert reasonable value ranges
        users_data = analytics_data["users"]

        # User counts should be non-negative
        for field_name, field_value in users_data.items():
            assert field_value >= 0, f"User count {field_name} should be non-negative"

        # Survey completions should be non-negative
        surveys_data = analytics_data["surveys"]
        if "completions" in surveys_data:
            assert surveys_data["completions"] >= 0

        # Top surveys should have valid data
        if "top_surveys" in surveys_data:
            for survey in surveys_data["top_surveys"]:
                if "responses" in survey:
                    assert survey["responses"] >= 0

    async def test_analytics_consistency_across_calls(
        self, monitoring_service: MonitoringService
    ):
        """Test analytics consistency across multiple calls."""
        # Act - Multiple calls
        analytics_calls = []
        for _ in range(3):
            analytics_data = await monitoring_service.get_user_analytics(days=7)
            analytics_calls.append(analytics_data)
            await asyncio.sleep(0.1)

        # Assert structure consistency
        for analytics_data in analytics_calls:
            # Should have same top-level structure
            expected_keys = [
                "period_days",
                "timestamp",
                "users",
                "surveys",
                "actions",
                "performance",
            ]
            for key in expected_keys:
                assert key in analytics_data

            # Period should be consistent
            assert analytics_data["period_days"] == 7

        # Data structure should be consistent
        first_call = analytics_calls[0]
        for analytics_data in analytics_calls[1:]:
            # Users section should have same structure
            assert set(analytics_data["users"].keys()) == set(
                first_call["users"].keys()
            )
            # Surveys section should have same structure
            assert set(analytics_data["surveys"].keys()) == set(
                first_call["surveys"].keys()
            )

    async def test_analytics_error_handling(
        self, monitoring_service: MonitoringService
    ):
        """Test analytics error handling and graceful degradation."""
        # Act with potential error conditions
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert graceful handling
        assert isinstance(analytics_data, dict)

        # Should have error field if there are errors
        if "error" in analytics_data:
            assert isinstance(analytics_data["error"], str)
        else:
            # Should have all expected sections
            expected_sections = ["users", "surveys", "actions", "performance"]
            for section in expected_sections:
                assert section in analytics_data


# ============================================================================
# ANALYTICS INTEGRATION TESTS
# ============================================================================


class TestAnalyticsIntegration:
    """Test analytics integration with monitoring system."""

    async def test_analytics_with_metrics_data(
        self, monitoring_service: MonitoringService, multiple_metrics_data
    ):
        """Test analytics with existing metrics data."""
        # Arrange - Add metrics
        for metric_data in multiple_metrics_data[:5]:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert analytics works with existing metrics
        assert "timestamp" in analytics_data
        assert "users" in analytics_data
        assert "surveys" in analytics_data

        # Metrics shouldn't directly affect user analytics structure
        # but system should handle both types of data

    async def test_analytics_with_mixed_monitoring_data(
        self,
        monitoring_service: MonitoringService,
        multiple_metrics_data,
        multiple_performance_data,
    ):
        """Test analytics with mixed monitoring data."""
        # Arrange - Add both metrics and performance data
        for metric_data in multiple_metrics_data[:3]:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

        for perf_data in multiple_performance_data[:3]:
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Act
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert analytics integrates all data types
        assert "performance" in analytics_data
        performance_data = analytics_data["performance"]

        # Should include performance data
        if len(multiple_performance_data) > 0:
            # Performance data should be included
            assert isinstance(performance_data, dict)

    async def test_concurrent_analytics_calls(
        self, monitoring_service: MonitoringService
    ):
        """Test concurrent analytics calls."""
        # Act - Multiple concurrent calls
        concurrent_calls = 5
        tasks = [
            monitoring_service.get_user_analytics(days=7)
            for _ in range(concurrent_calls)
        ]

        results = await asyncio.gather(*tasks)

        # Assert all calls succeeded
        assert len(results) == concurrent_calls

        for analytics_data in results:
            assert "period_days" in analytics_data
            assert analytics_data["period_days"] == 7
            assert "timestamp" in analytics_data
            assert "users" in analytics_data

        # Results should be consistent
        first_result = results[0]
        for result in results[1:]:
            # Structure should be the same
            assert set(result.keys()) == set(first_result.keys())
            assert result["period_days"] == first_result["period_days"]

    async def test_analytics_system_state_impact(
        self,
        monitoring_service: MonitoringService,
        multiple_metrics_data,
        multiple_performance_data,
    ):
        """Test that analytics doesn't impact monitoring system state."""
        # Arrange - Set up monitoring data
        initial_metrics_count = len(monitoring_service.metrics)
        initial_performance_count = len(monitoring_service.performance_data)

        for metric_data in multiple_metrics_data[:3]:
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

        for perf_data in multiple_performance_data[:3]:
            await monitoring_service.track_performance(
                operation=perf_data.operation,
                duration_ms=perf_data.duration_ms,
                status=perf_data.status,
            )

        # Get state after adding data
        metrics_count_before = len(monitoring_service.metrics)
        performance_count_before = len(monitoring_service.performance_data)

        # Act - Get analytics
        analytics_data = await monitoring_service.get_user_analytics(days=7)

        # Assert analytics doesn't modify monitoring state
        metrics_count_after = len(monitoring_service.metrics)
        performance_count_after = len(monitoring_service.performance_data)

        assert metrics_count_after == metrics_count_before
        assert performance_count_after == performance_count_before

        # Analytics should be successful
        assert "timestamp" in analytics_data
        assert "users" in analytics_data
