"""
Простые тесты для MonitoringService.

Покрывает основные функции мониторинга без сложных зависимостей.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.services.monitoring_service import (
    MonitoringService,
    MetricType,
    AlertLevel,
    Metric,
    Alert,
    get_monitoring_service,
)


class TestMonitoringServiceBasic:
    """Базовые тесты MonitoringService."""

    @pytest.fixture
    def monitoring_service(self):
        """Создание экземпляра сервиса мониторинга."""
        return MonitoringService()

    @pytest.mark.asyncio
    async def test_track_metric_success(self, monitoring_service):
        """Тест успешного отслеживания метрики."""
        # Arrange
        metric_name = "test_metric"
        metric_value = 100.0
        metric_type = MetricType.COUNTER
        tags = {"service": "test", "environment": "test"}

        # Mock get_redis_service to return None (no Redis)
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            # Act
            await monitoring_service.track_metric(
                name=metric_name, value=metric_value, metric_type=metric_type, tags=tags
            )

        # Assert
        assert len(monitoring_service.metrics) == 1
        metric = monitoring_service.metrics[0]
        assert metric.name == metric_name
        assert metric.value == metric_value
        assert metric.type == metric_type
        assert metric.tags == tags
        assert isinstance(metric.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_track_multiple_metrics(self, monitoring_service):
        """Тест отслеживания нескольких метрик."""
        # Arrange & Act
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            await monitoring_service.track_metric("metric1", 10.0, MetricType.COUNTER)
            await monitoring_service.track_metric("metric2", 20.0, MetricType.GAUGE)
            await monitoring_service.track_metric("metric3", 30.0, MetricType.TIMER)

        # Assert
        assert len(monitoring_service.metrics) == 3
        assert monitoring_service.metrics[0].name == "metric1"
        assert monitoring_service.metrics[1].name == "metric2"
        assert monitoring_service.metrics[2].name == "metric3"

    @pytest.mark.asyncio
    async def test_track_performance(self, monitoring_service):
        """Тест отслеживания производительности."""
        # Arrange
        operation = "database_query"
        duration_ms = 150.5
        status = "success"

        # Act
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            await monitoring_service.track_performance(operation, duration_ms, status)

        # Assert
        assert operation in monitoring_service.performance_data
        assert duration_ms in monitoring_service.performance_data[operation]
        assert len(monitoring_service.metrics) == 1  # Performance metric created
        metric = monitoring_service.metrics[0]
        assert metric.name == f"performance.{operation}.duration"
        assert metric.value == duration_ms

    @pytest.mark.asyncio
    async def test_track_user_action_without_redis(self, monitoring_service):
        """Тест отслеживания действия пользователя без Redis."""
        # Arrange
        user_id = 123
        action = "survey_completed"
        metadata = {"survey_id": 456}

        # Act & Assert - не должно упасть
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            await monitoring_service.track_user_action(user_id, action, metadata)

        # Метод должен завершиться без ошибок

    @pytest.mark.asyncio
    async def test_get_system_health(self, monitoring_service):
        """Тест получения системного здоровья."""
        # Mock all health check methods
        with (
            patch.object(monitoring_service, "_check_database_health") as mock_db,
            patch.object(monitoring_service, "_check_redis_health") as mock_redis,
            patch.object(
                monitoring_service, "_check_telegram_bot_health"
            ) as mock_telegram,
            patch.object(monitoring_service, "_get_memory_usage") as mock_memory,
            patch.object(monitoring_service, "_get_application_metrics") as mock_app,
        ):
            # Configure mocks
            mock_db.return_value = {"status": "healthy", "connected": True}
            mock_redis.return_value = {"status": "healthy", "connected": True}
            mock_telegram.return_value = {"status": "healthy", "connected": True}
            mock_memory.return_value = {"used": 50.0, "total": 100.0}
            mock_app.return_value = {"metrics_count": 0}

            # Act
            result = await monitoring_service.get_system_health()

            # Assert
            assert "status" in result
            assert "timestamp" in result
            assert "components" in result
            assert isinstance(result["timestamp"], datetime)

    @pytest.mark.asyncio
    async def test_create_custom_dashboard(self, monitoring_service):
        """Тест создания кастомного дашборда."""
        # Arrange
        name = "Test Dashboard"
        metrics = ["cpu_usage", "memory_usage"]

        # Act
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            result = await monitoring_service.create_custom_dashboard(name, metrics)

        # Assert
        assert result["name"] == name
        assert result["metrics"] == metrics
        assert "id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_get_real_time_metrics(self, monitoring_service):
        """Тест получения метрик в реальном времени."""
        # Arrange
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            await monitoring_service.track_metric(
                "test_metric", 100.0, MetricType.GAUGE
            )
            await monitoring_service.track_performance("test_op", 200.0)

        # Mock private methods
        with (
            patch.object(monitoring_service, "_get_performance_summary") as mock_perf,
            patch.object(monitoring_service, "_get_memory_usage") as mock_memory,
        ):
            mock_perf.return_value = {
                "operations": {"test_op": {"count": 1, "avg": 200.0}}
            }
            mock_memory.return_value = {"used": 75.0, "total": 100.0}

            # Act
            result = await monitoring_service.get_real_time_metrics()

            # Assert
            assert "timestamp" in result
            assert "metrics" in result
            assert "performance" in result
            assert "alerts" in result
            assert len(result["metrics"]) == 1

    def test_metric_dataclass(self):
        """Тест структуры данных Metric."""
        # Arrange
        metric = Metric(
            name="test_metric",
            value=100.0,
            type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"env": "test"},
        )

        # Act
        result = metric.to_dict()

        # Assert
        assert result["name"] == "test_metric"
        assert result["value"] == 100.0
        assert result["type"] == MetricType.COUNTER
        assert "timestamp" in result
        assert result["tags"] == {"env": "test"}

    def test_alert_dataclass(self):
        """Тест структуры данных Alert."""
        # Arrange
        alert = Alert(
            id="alert_123",
            name="Test Alert",
            level=AlertLevel.WARNING,
            message="Test alert message",
            timestamp=datetime.now(),
        )

        # Act & Assert
        assert alert.id == "alert_123"
        assert alert.name == "Test Alert"
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test alert message"
        assert alert.resolved is False
        assert isinstance(alert.timestamp, datetime)

    def test_get_monitoring_service_singleton(self):
        """Тест получения синглтона сервиса мониторинга."""
        # Act
        service1 = get_monitoring_service()
        service2 = get_monitoring_service()

        # Assert
        assert service1 is service2
        assert isinstance(service1, MonitoringService)

    def test_metric_types_enum(self):
        """Тест enum типов метрик."""
        # Act & Assert
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.TIMER == "timer"

    def test_alert_levels_enum(self):
        """Тест enum уровней алертов."""
        # Act & Assert
        assert AlertLevel.INFO == "info"
        assert AlertLevel.WARNING == "warning"
        assert AlertLevel.ERROR == "error"
        assert AlertLevel.CRITICAL == "critical"

    @pytest.mark.asyncio
    async def test_metrics_list_size_limit(self, monitoring_service):
        """Тест ограничения размера списка метрик."""
        # Arrange - создаем много метрик
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            # Act
            for i in range(10001):
                await monitoring_service.track_metric(
                    f"metric_{i}", float(i), MetricType.COUNTER
                )

        # Assert - список должен быть обрезан
        assert len(monitoring_service.metrics) == 8000

    @pytest.mark.asyncio
    async def test_performance_data_list_limit(self, monitoring_service):
        """Тест ограничения размера данных производительности."""
        # Arrange
        operation = "test_operation"

        # Act
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            for i in range(1001):
                await monitoring_service.track_performance(operation, float(i))

        # Assert - список должен быть обрезан
        assert len(monitoring_service.performance_data[operation]) == 800

    @pytest.mark.asyncio
    async def test_error_handling_in_track_metric(self, monitoring_service):
        """Тест обработки ошибок при отслеживании метрики."""
        # Arrange - мокаем get_redis_service чтобы бросало исключение
        with patch(
            "src.services.monitoring_service.get_redis_service",
            side_effect=Exception("Redis error"),
        ):
            # Act & Assert - метод не должен упасть
            await monitoring_service.track_metric(
                "test_metric", 100.0, MetricType.GAUGE
            )

            # Метрика все равно должна быть добавлена в локальный список
            assert len(monitoring_service.metrics) == 1

    @pytest.mark.asyncio
    async def test_error_handling_in_track_user_action(self, monitoring_service):
        """Тест обработки ошибок при отслеживании действий пользователя."""
        # Arrange
        with patch(
            "src.services.monitoring_service.get_redis_service",
            side_effect=Exception("Redis error"),
        ):
            # Act & Assert - метод не должен упасть
            await monitoring_service.track_user_action(123, "test_action")


class TestMonitoringServiceIntegration:
    """Интеграционные тесты."""

    @pytest.fixture
    def monitoring_service(self):
        """Создание экземпляра сервиса мониторинга."""
        return MonitoringService()

    @pytest.mark.asyncio
    async def test_full_monitoring_workflow(self, monitoring_service):
        """Тест полного workflow мониторинга."""
        # Arrange
        with patch(
            "src.services.monitoring_service.get_redis_service", return_value=None
        ):
            # Act
            # 1. Отслеживание метрики
            await monitoring_service.track_metric(
                "survey_completion_rate", 0.85, MetricType.GAUGE, {"period": "hourly"}
            )

            # 2. Отслеживание производительности
            await monitoring_service.track_performance(
                "survey_completion", 250.0, "success"
            )

            # 3. Отслеживание действия пользователя
            await monitoring_service.track_user_action(
                123, "survey_started", {"survey_id": 456}
            )

        # Assert
        assert len(monitoring_service.metrics) == 2  # metric + performance metric
        assert "survey_completion" in monitoring_service.performance_data
        assert len(monitoring_service.performance_data["survey_completion"]) == 1

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, monitoring_service):
        """Тест параллельных операций мониторинга."""
        # Arrange
        import asyncio

        async def track_metrics():
            with patch(
                "src.services.monitoring_service.get_redis_service", return_value=None
            ):
                for i in range(10):
                    await monitoring_service.track_metric(
                        f"concurrent_metric_{i}", float(i), MetricType.COUNTER
                    )

        async def track_performance():
            with patch(
                "src.services.monitoring_service.get_redis_service", return_value=None
            ):
                for i in range(10):
                    await monitoring_service.track_performance(
                        f"concurrent_op_{i}", float(i * 10)
                    )

        # Act
        await asyncio.gather(track_metrics(), track_performance())

        # Assert
        assert len(monitoring_service.metrics) >= 10  # At least 10 metrics tracked
        assert len(monitoring_service.performance_data) == 10  # 10 different operations
