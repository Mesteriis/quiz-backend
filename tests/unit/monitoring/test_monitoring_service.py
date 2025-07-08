"""
Comprehensive тесты для MonitoringService.

Покрывает все основные функции мониторинга:
- Отслеживание метрик
- Аналитика пользователей
- Мониторинг производительности
- Системное здоровье
- Дашборды и алерты
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from dataclasses import asdict

from src.services.monitoring_service import (
    MonitoringService,
    MetricType,
    AlertLevel,
    Metric,
    Alert,
    get_monitoring_service,
)
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


class TestMonitoringServiceMetrics:
    """Тесты отслеживания метрик."""

    @pytest.mark.asyncio
    async def test_track_metric_success(self, monitoring_service):
        """Тест успешного отслеживания метрики."""
        # Arrange
        metric_name = "test_metric"
        metric_value = 100.0
        metric_type = MetricType.COUNTER
        tags = {"service": "test", "environment": "test"}

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
    async def test_track_metric_with_redis_storage(self, monitoring_service):
        """Тест отслеживания метрики с сохранением в Redis."""
        # Arrange
        metric_data = MetricCreateFactory.build()

        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis.return_value = mock_redis_service

            # Act
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

            # Assert
            mock_redis_service.set_hash.assert_called_once()
            args = mock_redis_service.set_hash.call_args
            assert "metric:" in args[0][0]
            assert args[0][2] == 86400  # TTL

    @pytest.mark.asyncio
    async def test_track_metric_without_redis(self, monitoring_service):
        """Тест отслеживания метрики без Redis."""
        # Arrange
        metric_data = MetricCreateFactory.build()

        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis.return_value = None

            # Act
            await monitoring_service.track_metric(
                name=metric_data.name,
                value=metric_data.value,
                metric_type=metric_data.type,
                tags=metric_data.tags,
            )

            # Assert - не должно упасть даже без Redis
            assert len(monitoring_service.metrics) == 1

    @pytest.mark.asyncio
    async def test_track_metric_list_size_limit(self, monitoring_service):
        """Тест ограничения размера списка метрик."""
        # Arrange - создаем много метрик
        for i in range(10001):
            metric_data = MetricCreateFactory.build()
            await monitoring_service.track_metric(
                name=f"metric_{i}", value=float(i), metric_type=MetricType.COUNTER
            )

        # Assert - список должен быть обрезан
        assert len(monitoring_service.metrics) == 8000

    @pytest.mark.asyncio
    async def test_track_metric_error_handling(self, monitoring_service):
        """Тест обработки ошибок при отслеживании метрики."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")

            # Act & Assert - не должно упасть
            await monitoring_service.track_metric(
                name="test_metric", value=100.0, metric_type=MetricType.GAUGE
            )

    @pytest.mark.asyncio
    async def test_track_high_load_metric(self, monitoring_service):
        """Тест отслеживания высоконагруженной метрики."""
        # Arrange
        high_load_metric = HighLoadMetricFactory.build()

        # Act
        await monitoring_service.track_metric(
            name=high_load_metric.name,
            value=high_load_metric.value,
            metric_type=high_load_metric.type,
            tags=high_load_metric.tags,
        )

        # Assert
        assert len(monitoring_service.metrics) == 1
        metric = monitoring_service.metrics[0]
        assert metric.value >= 800.0  # High load value
        assert "severity" in metric.tags
        assert metric.tags["severity"] == "high"

    @pytest.mark.asyncio
    async def test_track_error_metric(self, monitoring_service):
        """Тест отслеживания метрики ошибок."""
        # Arrange
        error_metric = ErrorMetricFactory.build()

        # Act
        await monitoring_service.track_metric(
            name=error_metric.name,
            value=error_metric.value,
            metric_type=error_metric.type,
            tags=error_metric.tags,
        )

        # Assert
        metric = monitoring_service.metrics[0]
        assert "error_type" in metric.tags
        assert metric.type == MetricType.COUNTER


class TestMonitoringServiceUserAnalytics:
    """Тесты аналитики пользователей."""

    @pytest.mark.asyncio
    async def test_track_user_action_success(self, monitoring_service):
        """Тест успешного отслеживания действия пользователя."""
        # Arrange
        user_id = 123
        action = "survey_completed"
        metadata = {"survey_id": 456, "completion_time": 180}

        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis_service.get_hash.return_value = {}
            mock_redis.return_value = mock_redis_service

            # Act
            await monitoring_service.track_user_action(
                user_id=user_id, action=action, metadata=metadata
            )

            # Assert
            mock_redis_service.increment_counter.assert_called()
            mock_redis_service.set_hash.assert_called()

    @pytest.mark.asyncio
    async def test_track_user_action_without_redis(self, monitoring_service):
        """Тест отслеживания действия пользователя без Redis."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis.return_value = None

            # Act & Assert - не должно упасть
            await monitoring_service.track_user_action(
                user_id=123, action="test_action"
            )

    @pytest.mark.asyncio
    async def test_track_user_action_increments_counters(self, monitoring_service):
        """Тест инкрементирования счетчиков пользователей."""
        # Arrange
        user_id = 123
        action = "survey_started"

        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis_service.get_hash.return_value = {"survey_started": "5"}
            mock_redis.return_value = mock_redis_service

            # Act
            await monitoring_service.track_user_action(user_id, action)

            # Assert
            calls = mock_redis_service.increment_counter.call_args_list
            assert len(calls) >= 2
            assert any(f"user_action:{action}" in str(call) for call in calls)
            assert any("user_action:total" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_track_user_action_updates_user_analytics(self, monitoring_service):
        """Тест обновления аналитики пользователя."""
        # Arrange
        user_id = 123
        action = "survey_completed"

        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis_service.get_hash.return_value = {"survey_completed": "2"}
            mock_redis.return_value = mock_redis_service

            # Act
            await monitoring_service.track_user_action(user_id, action)

            # Assert
            mock_redis_service.set_hash.assert_called()
            set_call = mock_redis_service.set_hash.call_args
            assert f"user_analytics:{user_id}" in set_call[0][0]
            assert set_call[0][2] == 604800  # TTL

    @pytest.mark.asyncio
    async def test_track_user_action_hourly_analytics(self, monitoring_service):
        """Тест обновления почасовой аналитики."""
        # Arrange
        user_id = 123
        action = "test_action"

        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis_service.get_hash.return_value = {}
            mock_redis.return_value = mock_redis_service

            # Act
            await monitoring_service.track_user_action(user_id, action)

            # Assert
            hourly_calls = [
                call
                for call in mock_redis_service.increment_counter.call_args_list
                if "analytics:hourly:" in str(call)
            ]
            assert len(hourly_calls) >= 1

    @pytest.mark.asyncio
    async def test_track_user_action_error_handling(self, monitoring_service):
        """Тест обработки ошибок при отслеживании действий."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis.side_effect = Exception("Redis error")

            # Act & Assert - не должно упасть
            await monitoring_service.track_user_action(123, "test_action")

    @pytest.mark.asyncio
    async def test_get_user_analytics_success(self, monitoring_service):
        """Тест получения аналитики пользователей."""
        # Arrange
        with patch("src.services.monitoring_service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.scalar.return_value = 100

            with patch(
                "src.services.monitoring_service.get_redis_service"
            ) as mock_redis:
                mock_redis_service = AsyncMock()
                mock_redis_service.get_counter.return_value = 50
                mock_redis.return_value = mock_redis_service

                # Act
                result = await monitoring_service.get_user_analytics(days=7)

                # Assert
                assert "period_days" in result
                assert result["period_days"] == 7
                assert "users" in result
                assert "surveys" in result
                assert "actions" in result

    @pytest.mark.asyncio
    async def test_get_user_analytics_without_redis(self, monitoring_service):
        """Тест получения аналитики без Redis."""
        # Arrange
        with patch("src.services.monitoring_service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.scalar.return_value = 100

            with patch(
                "src.services.monitoring_service.get_redis_service"
            ) as mock_redis:
                mock_redis.return_value = None

                # Act
                result = await monitoring_service.get_user_analytics(days=7)

                # Assert
                assert "period_days" in result
                assert result["actions"] == {}


class TestMonitoringServicePerformance:
    """Тесты мониторинга производительности."""

    @pytest.mark.asyncio
    async def test_track_performance_success(self, monitoring_service):
        """Тест успешного отслеживания производительности."""
        # Arrange
        operation = "database_query"
        duration_ms = 150.0
        status = "success"

        # Act
        await monitoring_service.track_performance(operation, duration_ms, status)

        # Assert
        assert operation in monitoring_service.performance_data
        assert duration_ms in monitoring_service.performance_data[operation]
        assert len(monitoring_service.metrics) == 1
        metric = monitoring_service.metrics[0]
        assert metric.name == f"performance.{operation}.duration"
        assert metric.value == duration_ms

    @pytest.mark.asyncio
    async def test_track_performance_list_size_limit(self, monitoring_service):
        """Тест ограничения размера списка производительности."""
        # Arrange
        operation = "test_operation"

        # Act - добавляем много измерений
        for i in range(1001):
            await monitoring_service.track_performance(operation, float(i))

        # Assert - список должен быть обрезан
        assert len(monitoring_service.performance_data[operation]) == 800

    @pytest.mark.asyncio
    async def test_track_performance_multiple_operations(self, monitoring_service):
        """Тест отслеживания нескольких операций."""
        # Arrange
        operations = ["db_query", "api_call", "file_processing"]

        # Act
        for op in operations:
            await monitoring_service.track_performance(op, 100.0)

        # Assert
        for op in operations:
            assert op in monitoring_service.performance_data
            assert len(monitoring_service.performance_data[op]) == 1

    @pytest.mark.asyncio
    async def test_track_performance_with_failure_status(self, monitoring_service):
        """Тест отслеживания производительности с ошибкой."""
        # Arrange
        operation = "failed_operation"
        duration_ms = 500.0
        status = "error"

        # Act
        await monitoring_service.track_performance(operation, duration_ms, status)

        # Assert
        metric = monitoring_service.metrics[0]
        assert metric.tags["status"] == "error"
        assert metric.value == duration_ms

    @pytest.mark.asyncio
    async def test_get_performance_summary(self, monitoring_service):
        """Тест получения сводки производительности."""
        # Arrange
        operation = "test_operation"
        durations = [100.0, 200.0, 300.0, 400.0, 500.0]
        for duration in durations:
            await monitoring_service.track_performance(operation, duration)

        # Act
        result = await monitoring_service._get_performance_summary()

        # Assert
        assert "operations" in result
        assert operation in result["operations"]
        op_data = result["operations"][operation]
        assert op_data["count"] == 5
        assert op_data["avg"] == 300.0
        assert op_data["min"] == 100.0
        assert op_data["max"] == 500.0

    @pytest.mark.asyncio
    async def test_get_avg_performance(self, monitoring_service):
        """Тест получения средней производительности."""
        # Arrange
        operations = ["op1", "op2", "op3"]
        for op in operations:
            await monitoring_service.track_performance(op, 100.0)
            await monitoring_service.track_performance(op, 200.0)

        # Act
        result = await monitoring_service._get_avg_performance()

        # Assert
        for op in operations:
            assert op in result
            assert result[op] == 150.0  # (100 + 200) / 2


class TestMonitoringServiceSystemHealth:
    """Тесты системного здоровья."""

    @pytest.mark.asyncio
    async def test_get_system_health_success(self, monitoring_service):
        """Тест успешного получения системного здоровья."""
        # Arrange
        with (
            patch.object(monitoring_service, "_check_database_health") as mock_db,
            patch.object(monitoring_service, "_check_redis_health") as mock_redis,
            patch.object(
                monitoring_service, "_check_telegram_bot_health"
            ) as mock_telegram,
        ):
            mock_db.return_value = {"status": "healthy", "connected": True}
            mock_redis.return_value = {"status": "healthy", "connected": True}
            mock_telegram.return_value = {"status": "healthy", "connected": True}

            # Act
            result = await monitoring_service.get_system_health()

            # Assert
            assert "status" in result
            assert "timestamp" in result
            assert "components" in result
            assert "database" in result["components"]
            assert "redis" in result["components"]
            assert "telegram_bot" in result["components"]

    @pytest.mark.asyncio
    async def test_get_system_health_with_failures(self, monitoring_service):
        """Тест получения системного здоровья с ошибками."""
        # Arrange
        with (
            patch.object(monitoring_service, "_check_database_health") as mock_db,
            patch.object(monitoring_service, "_check_redis_health") as mock_redis,
            patch.object(
                monitoring_service, "_check_telegram_bot_health"
            ) as mock_telegram,
        ):
            mock_db.return_value = {"status": "unhealthy", "connected": False}
            mock_redis.return_value = {"status": "healthy", "connected": True}
            mock_telegram.return_value = {"status": "error", "connected": False}

            # Act
            result = await monitoring_service.get_system_health()

            # Assert
            assert result["status"] == "unhealthy"
            assert result["components"]["database"]["status"] == "unhealthy"
            assert result["components"]["telegram_bot"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_check_database_health_success(self, monitoring_service):
        """Тест успешной проверки здоровья БД."""
        # Arrange
        with patch("src.services.monitoring_service.get_async_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.execute.return_value = MagicMock()

            # Act
            result = await monitoring_service._check_database_health()

            # Assert
            assert result["status"] == "healthy"
            assert result["connected"] is True
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_check_database_health_failure(self, monitoring_service):
        """Тест неудачной проверки здоровья БД."""
        # Arrange
        with patch("src.services.monitoring_service.get_async_session") as mock_session:
            mock_session.side_effect = Exception("Database connection failed")

            # Act
            result = await monitoring_service._check_database_health()

            # Assert
            assert result["status"] == "unhealthy"
            assert result["connected"] is False
            assert "error_message" in result

    @pytest.mark.asyncio
    async def test_check_redis_health_success(self, monitoring_service):
        """Тест успешной проверки здоровья Redis."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis_service.ping.return_value = True
            mock_redis.return_value = mock_redis_service

            # Act
            result = await monitoring_service._check_redis_health()

            # Assert
            assert result["status"] == "healthy"
            assert result["connected"] is True

    @pytest.mark.asyncio
    async def test_check_redis_health_unavailable(self, monitoring_service):
        """Тест проверки здоровья Redis при недоступности."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis.return_value = None

            # Act
            result = await monitoring_service._check_redis_health()

            # Assert
            assert result["status"] == "unavailable"
            assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_check_telegram_bot_health_success(self, monitoring_service):
        """Тест успешной проверки здоровья Telegram бота."""
        # Arrange
        with patch(
            "src.services.monitoring_service.get_telegram_service"
        ) as mock_telegram:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot = MagicMock()
            mock_telegram_service.bot.get_me = AsyncMock(return_value=MagicMock())
            mock_telegram.return_value = mock_telegram_service

            # Act
            result = await monitoring_service._check_telegram_bot_health()

            # Assert
            assert result["status"] == "healthy"
            assert result["connected"] is True

    @pytest.mark.asyncio
    async def test_check_telegram_bot_health_failure(self, monitoring_service):
        """Тест неудачной проверки здоровья Telegram бота."""
        # Arrange
        with patch(
            "src.services.monitoring_service.get_telegram_service"
        ) as mock_telegram:
            mock_telegram.side_effect = Exception("Telegram service unavailable")

            # Act
            result = await monitoring_service._check_telegram_bot_health()

            # Assert
            assert result["status"] == "error"
            assert result["connected"] is False


class TestMonitoringServiceAlerts:
    """Тесты системы алертов."""

    @pytest.mark.asyncio
    async def test_check_metric_alerts_threshold_exceeded(self, monitoring_service):
        """Тест проверки алертов при превышении порога."""
        # Arrange
        metric = Metric(
            name="response_time_ms",
            value=1500.0,  # Превышает порог 1000
            type=MetricType.TIMER,
            timestamp=datetime.now(),
        )

        # Act
        await monitoring_service._check_metric_alerts(metric)

        # Assert
        assert len(monitoring_service.alerts) == 1
        alert = monitoring_service.alerts[0]
        assert alert.level == AlertLevel.WARNING
        assert "response_time_ms" in alert.name

    @pytest.mark.asyncio
    async def test_check_metric_alerts_no_threshold_exceeded(self, monitoring_service):
        """Тест проверки алертов без превышения порога."""
        # Arrange
        metric = Metric(
            name="response_time_ms",
            value=500.0,  # Не превышает порог
            type=MetricType.TIMER,
            timestamp=datetime.now(),
        )

        # Act
        await monitoring_service._check_metric_alerts(metric)

        # Assert
        assert len(monitoring_service.alerts) == 0

    @pytest.mark.asyncio
    async def test_create_alert_success(self, monitoring_service):
        """Тест успешного создания алерта."""
        # Arrange
        alert_id = "test_alert_1"
        name = "Test Alert"
        level = AlertLevel.ERROR
        message = "Test alert message"

        # Act
        await monitoring_service._create_alert(alert_id, name, level, message)

        # Assert
        assert len(monitoring_service.alerts) == 1
        alert = monitoring_service.alerts[0]
        assert alert.id == alert_id
        assert alert.name == name
        assert alert.level == level
        assert alert.message == message
        assert alert.resolved is False

    @pytest.mark.asyncio
    async def test_create_alert_with_redis_storage(self, monitoring_service):
        """Тест создания алерта с сохранением в Redis."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis.return_value = mock_redis_service

            # Act
            await monitoring_service._create_alert(
                "test_alert", "Test", AlertLevel.INFO, "Test message"
            )

            # Assert
            mock_redis_service.set_hash.assert_called_once()


class TestMonitoringServiceDashboards:
    """Тесты дашбордов."""

    @pytest.mark.asyncio
    async def test_create_custom_dashboard_success(self, monitoring_service):
        """Тест успешного создания кастомного дашборда."""
        # Arrange
        name = "Test Dashboard"
        metrics = ["cpu_usage", "memory_usage", "response_time"]

        # Act
        result = await monitoring_service.create_custom_dashboard(name, metrics)

        # Assert
        assert result["name"] == name
        assert result["metrics"] == metrics
        assert "id" in result
        assert "created_at" in result
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_custom_dashboard_with_redis(self, monitoring_service):
        """Тест создания дашборда с сохранением в Redis."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis_service = AsyncMock()
            mock_redis.return_value = mock_redis_service

            # Act
            result = await monitoring_service.create_custom_dashboard(
                "Test Dashboard", ["test_metric"]
            )

            # Assert
            mock_redis_service.set_hash.assert_called_once()
            assert result["id"] is not None

    @pytest.mark.asyncio
    async def test_get_real_time_metrics_success(self, monitoring_service):
        """Тест получения метрик в реальном времени."""
        # Arrange
        # Добавляем тестовые метрики
        await monitoring_service.track_metric("test_metric", 100.0, MetricType.GAUGE)
        await monitoring_service.track_performance("test_op", 200.0)

        # Act
        result = await monitoring_service.get_real_time_metrics()

        # Assert
        assert "timestamp" in result
        assert "metrics" in result
        assert "performance" in result
        assert "alerts" in result
        assert len(result["metrics"]) == 1

    @pytest.mark.asyncio
    async def test_get_real_time_metrics_with_performance_data(
        self, monitoring_service
    ):
        """Тест получения метрик в реальном времени с данными производительности."""
        # Arrange
        for i in range(5):
            await monitoring_service.track_performance("db_query", float(i * 100))

        # Act
        result = await monitoring_service.get_real_time_metrics()

        # Assert
        assert "performance" in result
        assert "db_query" in result["performance"]
        assert result["performance"]["db_query"]["count"] == 5


class TestMonitoringServiceUtilities:
    """Тесты утилитарных функций."""

    @pytest.mark.asyncio
    async def test_get_memory_usage(self, monitoring_service):
        """Тест получения информации об использовании памяти."""
        # Act
        result = await monitoring_service._get_memory_usage()

        # Assert
        assert "total_mb" in result
        assert "available_mb" in result
        assert "percent" in result
        assert "process_mb" in result
        assert isinstance(result["percent"], float)

    @pytest.mark.asyncio
    async def test_get_application_metrics(self, monitoring_service):
        """Тест получения метрик приложения."""
        # Arrange
        await monitoring_service.track_metric("app_metric", 50.0, MetricType.GAUGE)

        # Act
        result = await monitoring_service._get_application_metrics()

        # Assert
        assert "total_metrics" in result
        assert "active_alerts" in result
        assert "performance_operations" in result
        assert result["total_metrics"] == 1

    def test_get_monitoring_service_singleton(self):
        """Тест получения синглтона сервиса мониторинга."""
        # Act
        service1 = get_monitoring_service()
        service2 = get_monitoring_service()

        # Assert
        assert service1 is service2
        assert isinstance(service1, MonitoringService)

    def test_metric_to_dict_conversion(self):
        """Тест конвертации метрики в словарь."""
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

    def test_alert_dataclass_creation(self):
        """Тест создания структуры Alert."""
        # Arrange
        alert_data = AlertCreateFactory.build()

        # Act
        alert = Alert(
            id=alert_data.name,
            name=alert_data.name,
            level=alert_data.level,
            message=alert_data.description,
            timestamp=datetime.now(),
        )

        # Assert
        assert alert.id == alert_data.name
        assert alert.name == alert_data.name
        assert alert.level == alert_data.level
        assert alert.resolved is False


class TestMonitoringServiceIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    async def test_full_monitoring_workflow(self, monitoring_service):
        """Тест полного рабочего процесса мониторинга."""
        # Arrange
        user_id = 123
        operation = "survey_completion"

        # Act - полный workflow
        # 1. Отслеживание действия пользователя
        await monitoring_service.track_user_action(
            user_id, "survey_started", {"survey_id": 456}
        )

        # 2. Отслеживание производительности
        await monitoring_service.track_performance(operation, 250.0, "success")

        # 3. Отслеживание метрики
        await monitoring_service.track_metric(
            "survey_completion_rate", 0.85, MetricType.GAUGE, {"period": "hourly"}
        )

        # 4. Получение системного здоровья
        with (
            patch.object(monitoring_service, "_check_database_health") as mock_db,
            patch.object(monitoring_service, "_check_redis_health") as mock_redis,
            patch.object(
                monitoring_service, "_check_telegram_bot_health"
            ) as mock_telegram,
        ):
            mock_db.return_value = {"status": "healthy", "connected": True}
            mock_redis.return_value = {"status": "healthy", "connected": True}
            mock_telegram.return_value = {"status": "healthy", "connected": True}

            health = await monitoring_service.get_system_health()

        # 5. Получение метрик в реальном времени
        metrics = await monitoring_service.get_real_time_metrics()

        # Assert
        assert len(monitoring_service.metrics) == 1
        assert operation in monitoring_service.performance_data
        assert health["status"] == "healthy"
        assert len(metrics["metrics"]) == 1

    @pytest.mark.asyncio
    async def test_monitoring_with_high_load(self, monitoring_service):
        """Тест мониторинга при высокой нагрузке."""
        # Arrange
        import asyncio

        # Act - создаем высокую нагрузку
        tasks = []
        for i in range(100):
            task = monitoring_service.track_metric(
                f"load_test_{i}", float(i), MetricType.COUNTER
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Assert
        assert len(monitoring_service.metrics) == 100

    @pytest.mark.asyncio
    async def test_monitoring_error_resilience(self, monitoring_service):
        """Тест устойчивости мониторинга к ошибкам."""
        # Arrange
        with patch("src.services.monitoring_service.get_redis_service") as mock_redis:
            mock_redis.side_effect = Exception("Redis down")

            # Act - все операции должны продолжать работать
            await monitoring_service.track_metric("test", 1.0, MetricType.GAUGE)
            await monitoring_service.track_user_action(123, "action")
            await monitoring_service.track_performance("op", 100.0)

            # Assert - операции не должны упасть
            assert len(monitoring_service.metrics) == 1
            assert "op" in monitoring_service.performance_data

    @pytest.mark.asyncio
    async def test_monitoring_dashboard_creation_workflow(self, monitoring_service):
        """Тест создания дашборда с метриками."""
        # Arrange
        dashboard_data = DashboardCreateFactory.build()

        # Act
        # 1. Создаем метрики
        for metric_name in dashboard_data.metrics:
            await monitoring_service.track_metric(metric_name, 100.0, MetricType.GAUGE)

        # 2. Создаем дашборд
        dashboard = await monitoring_service.create_custom_dashboard(
            dashboard_data.name, dashboard_data.metrics
        )

        # 3. Получаем метрики в реальном времени
        real_time_metrics = await monitoring_service.get_real_time_metrics()

        # Assert
        assert dashboard["name"] == dashboard_data.name
        assert len(real_time_metrics["metrics"]) == len(dashboard_data.metrics)
