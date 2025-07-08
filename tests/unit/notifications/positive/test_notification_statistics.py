"""
Позитивные тесты для статистики уведомлений.

Этот модуль содержит все успешные сценарии работы со статистикой:
- Общая статистика уведомлений
- Аналитика по каналам доставки
- Статистика по типам уведомлений
- Метрики производительности
- Отчеты по периодам
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory


class TestNotificationStatistics:
    """Позитивные тесты общей статистики уведомлений."""

    async def test_get_notification_stats_overview(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения общего обзора статистики уведомлений."""
        # Arrange
        mock_stats = {
            "total_notifications_sent": 50000,
            "total_notifications_delivered": 48500,
            "total_notifications_opened": 15000,
            "delivery_rate": 97.0,
            "open_rate": 30.9,
            "active_subscriptions": 2500,
            "channels": {
                "websocket": {"sent": 20000, "delivered": 19800, "success_rate": 99.0},
                "email": {"sent": 15000, "delivered": 14250, "success_rate": 95.0},
                "push": {"sent": 12000, "delivered": 11500, "success_rate": 95.8},
                "sms": {"sent": 3000, "delivered": 2950, "success_rate": 98.3},
            },
            "types": {
                "system_message": {"sent": 10000, "opened": 3000},
                "survey_completed": {"sent": 15000, "opened": 6000},
                "reminder": {"sent": 20000, "opened": 5000},
                "achievement_unlocked": {"sent": 5000, "opened": 1000},
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_statistics = AsyncMock(
                return_value=mock_stats
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_notification_statistics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_notifications_sent"] == 50000
        assert data["delivery_rate"] == 97.0
        assert data["open_rate"] == 30.9
        assert data["active_subscriptions"] == 2500

        # Проверяем статистику по каналам
        assert data["channels"]["websocket"]["success_rate"] == 99.0
        assert data["channels"]["email"]["sent"] == 15000
        assert data["channels"]["push"]["delivered"] == 11500

        # Проверяем статистику по типам
        assert data["types"]["survey_completed"]["sent"] == 15000
        assert data["types"]["reminder"]["opened"] == 5000

    async def test_get_notification_stats_with_date_range(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики за определенный период."""
        # Arrange
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()

        mock_stats = {
            "period": {"start": start_date, "end": end_date, "days": 30},
            "total_sent": 15000,
            "total_delivered": 14550,
            "daily_stats": [
                {"date": "2024-01-15", "sent": 500, "delivered": 485},
                {"date": "2024-01-14", "sent": 520, "delivered": 505},
                {"date": "2024-01-13", "sent": 480, "delivered": 470},
            ],
            "growth_rate": 5.2,
            "trends": {
                "best_day": "Monday",
                "best_hour": 14,
                "peak_period": "14:00-15:00",
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_period_statistics = AsyncMock(
                return_value=mock_stats
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_notification_statistics"),
                params={"start_date": start_date, "end_date": end_date},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["period"]["days"] == 30
        assert data["total_sent"] == 15000
        assert data["growth_rate"] == 5.2
        assert len(data["daily_stats"]) == 3
        assert data["trends"]["best_day"] == "Monday"
        assert data["trends"]["best_hour"] == 14

    async def test_get_notification_stats_by_user_segment(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики по сегментам пользователей."""
        # Arrange
        mock_stats = {
            "segments": {
                "new_users": {
                    "count": 500,
                    "notifications_sent": 2000,
                    "open_rate": 35.5,
                    "engagement_score": 7.8,
                },
                "active_users": {
                    "count": 1500,
                    "notifications_sent": 25000,
                    "open_rate": 28.2,
                    "engagement_score": 8.5,
                },
                "premium_users": {
                    "count": 300,
                    "notifications_sent": 8000,
                    "open_rate": 42.1,
                    "engagement_score": 9.2,
                },
                "inactive_users": {
                    "count": 200,
                    "notifications_sent": 1500,
                    "open_rate": 15.3,
                    "engagement_score": 4.1,
                },
            },
            "best_performing_segment": "premium_users",
            "segment_recommendations": {
                "new_users": "Increase onboarding notifications",
                "inactive_users": "Implement re-engagement campaign",
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_segment_statistics = AsyncMock(
                return_value=mock_stats
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_notification_stats_by_segment")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "segments" in data
        assert data["segments"]["premium_users"]["open_rate"] == 42.1
        assert data["segments"]["new_users"]["count"] == 500
        assert data["best_performing_segment"] == "premium_users"
        assert "segment_recommendations" in data

    async def test_get_real_time_notification_metrics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения метрик в реальном времени."""
        # Arrange
        mock_metrics = {
            "current_time": "2024-01-15T16:30:00Z",
            "last_24_hours": {
                "sent": 1200,
                "delivered": 1165,
                "opened": 350,
                "failed": 35,
            },
            "last_hour": {"sent": 85, "delivered": 82, "opened": 23, "failed": 3},
            "active_connections": {"websocket": 450, "total_online_users": 650},
            "queue_status": {
                "pending_notifications": 25,
                "processing_rate": "12/min",
                "avg_processing_time": "2.3s",
            },
            "system_health": {
                "service_status": "healthy",
                "error_rate": 0.8,
                "response_time": "145ms",
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_realtime_metrics = AsyncMock(
                return_value=mock_metrics
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_realtime_notification_metrics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["last_24_hours"]["sent"] == 1200
        assert data["last_hour"]["delivered"] == 82
        assert data["active_connections"]["websocket"] == 450
        assert data["queue_status"]["pending_notifications"] == 25
        assert data["system_health"]["service_status"] == "healthy"


class TestChannelAnalytics:
    """Позитивные тесты аналитики по каналам доставки."""

    async def test_get_channel_performance_stats(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики производительности каналов."""
        # Arrange
        mock_channel_stats = {
            "websocket": {
                "total_sent": 25000,
                "total_delivered": 24750,
                "avg_delivery_time": "50ms",
                "success_rate": 99.0,
                "peak_usage_hour": 14,
                "connected_users": 450,
                "message_types": {
                    "system_message": 8000,
                    "survey_completed": 10000,
                    "reminder": 5000,
                    "achievement_unlocked": 2000,
                },
            },
            "email": {
                "total_sent": 18000,
                "total_delivered": 17100,
                "avg_delivery_time": "2.5s",
                "success_rate": 95.0,
                "bounce_rate": 3.2,
                "open_rate": 22.5,
                "click_rate": 4.8,
                "unsubscribe_rate": 0.3,
            },
            "push": {
                "total_sent": 15000,
                "total_delivered": 14400,
                "avg_delivery_time": "800ms",
                "success_rate": 96.0,
                "click_rate": 8.5,
                "platforms": {
                    "iOS": {"sent": 8000, "delivered": 7800, "clicked": 720},
                    "Android": {"sent": 6000, "delivered": 5800, "clicked": 550},
                    "Web": {"sent": 1000, "delivered": 800, "clicked": 60},
                },
            },
            "sms": {
                "total_sent": 5000,
                "total_delivered": 4900,
                "avg_delivery_time": "1.2s",
                "success_rate": 98.0,
                "cost_per_message": 0.05,
                "total_cost": 250.0,
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_channel_analytics = AsyncMock(
                return_value=mock_channel_stats
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_channel_performance_stats")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # WebSocket статистика
        assert data["websocket"]["success_rate"] == 99.0
        assert data["websocket"]["connected_users"] == 450

        # Email статистика
        assert data["email"]["open_rate"] == 22.5
        assert data["email"]["bounce_rate"] == 3.2

        # Push статистика
        assert data["push"]["click_rate"] == 8.5
        assert data["push"]["platforms"]["iOS"]["sent"] == 8000

        # SMS статистика
        assert data["sms"]["cost_per_message"] == 0.05
        assert data["sms"]["total_cost"] == 250.0

    async def test_get_channel_comparison_report(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения сравнительного отчета по каналам."""
        # Arrange
        mock_comparison = {
            "comparison_period": "last_30_days",
            "metrics": {
                "delivery_rate": {
                    "websocket": 99.0,
                    "sms": 98.0,
                    "push": 96.0,
                    "email": 95.0,
                },
                "engagement_rate": {
                    "push": 8.5,
                    "email": 4.8,
                    "websocket": 25.0,
                    "sms": 2.1,
                },
                "cost_effectiveness": {
                    "websocket": {"cost_per_delivery": 0.001, "rank": 1},
                    "email": {"cost_per_delivery": 0.01, "rank": 2},
                    "push": {"cost_per_delivery": 0.02, "rank": 3},
                    "sms": {"cost_per_delivery": 0.05, "rank": 4},
                },
            },
            "recommendations": {
                "primary_channel": "websocket",
                "fallback_channels": ["push", "email"],
                "cost_optimization": "Increase websocket usage for cost savings",
                "engagement_optimization": "Use push for important notifications",
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_channel_comparison = AsyncMock(
                return_value=mock_comparison
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_channel_comparison_report")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["metrics"]["delivery_rate"]["websocket"] == 99.0
        assert data["metrics"]["engagement_rate"]["push"] == 8.5
        assert data["metrics"]["cost_effectiveness"]["websocket"]["rank"] == 1
        assert data["recommendations"]["primary_channel"] == "websocket"


class TestNotificationTypeAnalytics:
    """Позитивные тесты аналитики по типам уведомлений."""

    async def test_get_notification_type_performance(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения производительности по типам уведомлений."""
        # Arrange
        mock_type_stats = {
            "system_message": {
                "total_sent": 12000,
                "open_rate": 45.5,
                "avg_time_to_open": "2m 30s",
                "user_feedback_score": 7.8,
                "best_channels": ["websocket", "push"],
                "optimal_timing": "business_hours",
            },
            "survey_completed": {
                "total_sent": 18000,
                "open_rate": 38.2,
                "avg_time_to_open": "5m 15s",
                "user_feedback_score": 8.2,
                "best_channels": ["email", "push"],
                "optimal_timing": "evening",
            },
            "reminder": {
                "total_sent": 25000,
                "open_rate": 28.7,
                "avg_time_to_open": "15m 45s",
                "user_feedback_score": 6.5,
                "best_channels": ["push", "sms"],
                "optimal_timing": "1_hour_before",
            },
            "achievement_unlocked": {
                "total_sent": 8000,
                "open_rate": 65.3,
                "avg_time_to_open": "1m 20s",
                "user_feedback_score": 9.1,
                "best_channels": ["push", "websocket"],
                "optimal_timing": "immediate",
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_type_performance = AsyncMock(
                return_value=mock_type_stats
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_notification_type_performance")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["achievement_unlocked"]["open_rate"] == 65.3
        assert data["system_message"]["user_feedback_score"] == 7.8
        assert data["reminder"]["optimal_timing"] == "1_hour_before"
        assert "websocket" in data["achievement_unlocked"]["best_channels"]

    async def test_get_notification_content_analysis(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест анализа контента уведомлений."""
        # Arrange
        mock_content_analysis = {
            "title_analysis": {
                "avg_length": 45,
                "optimal_length": "30-50 characters",
                "top_performing_words": ["urgent", "completed", "new", "available"],
                "sentiment_scores": {
                    "positive": 65.2,
                    "neutral": 28.8,
                    "negative": 6.0,
                },
            },
            "message_analysis": {
                "avg_length": 120,
                "optimal_length": "80-150 characters",
                "readability_score": 8.5,
                "emoji_usage": {
                    "with_emoji": {"count": 15000, "open_rate": 35.2},
                    "without_emoji": {"count": 48000, "open_rate": 28.7},
                },
            },
            "personalization_impact": {
                "personalized": {"count": 20000, "open_rate": 42.1},
                "generic": {"count": 43000, "open_rate": 27.3},
            },
            "a_b_test_results": [
                {
                    "test_id": "title_urgency_test",
                    "variant_a": {"title": "Survey Available", "open_rate": 25.5},
                    "variant_b": {"title": "New Survey Ready!", "open_rate": 32.8},
                    "winner": "variant_b",
                    "confidence": 95.5,
                }
            ],
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_content_analysis = AsyncMock(
                return_value=mock_content_analysis
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_notification_content_analysis")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["title_analysis"]["optimal_length"] == "30-50 characters"
        assert "urgent" in data["title_analysis"]["top_performing_words"]
        assert data["emoji_usage"]["with_emoji"]["open_rate"] == 35.2
        assert data["personalization_impact"]["personalized"]["open_rate"] == 42.1
        assert data["a_b_test_results"][0]["winner"] == "variant_b"


class TestPerformanceMetrics:
    """Позитивные тесты метрик производительности уведомлений."""

    async def test_get_delivery_performance_metrics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения метрик производительности доставки."""
        # Arrange
        mock_performance_metrics = {
            "delivery_metrics": {
                "avg_delivery_time": "1.2s",
                "median_delivery_time": "0.8s",
                "p95_delivery_time": "3.5s",
                "p99_delivery_time": "8.2s",
                "timeout_rate": 0.5,
                "retry_rate": 2.1,
            },
            "throughput_metrics": {
                "notifications_per_second": 125,
                "peak_throughput": 500,
                "avg_queue_size": 45,
                "max_queue_size": 250,
                "processing_capacity": 1000,
            },
            "reliability_metrics": {
                "uptime_percentage": 99.95,
                "error_rate": 0.8,
                "duplicate_rate": 0.1,
                "data_loss_rate": 0.0,
            },
            "resource_usage": {
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "network_io": "250 MB/hour",
                "storage_usage": "15 GB",
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_performance_metrics = AsyncMock(
                return_value=mock_performance_metrics
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_delivery_performance_metrics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["delivery_metrics"]["avg_delivery_time"] == "1.2s"
        assert data["throughput_metrics"]["notifications_per_second"] == 125
        assert data["reliability_metrics"]["uptime_percentage"] == 99.95
        assert data["resource_usage"]["cpu_usage"] == 45.2

    async def test_get_user_engagement_trends(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения трендов взаимодействия пользователей."""
        # Arrange
        mock_engagement_trends = {
            "weekly_trends": [
                {"week": "2024-W01", "open_rate": 28.5, "click_rate": 5.2},
                {"week": "2024-W02", "open_rate": 30.1, "click_rate": 5.8},
                {"week": "2024-W03", "open_rate": 29.7, "click_rate": 6.1},
            ],
            "daily_patterns": {
                "monday": {"peak_hour": 10, "open_rate": 32.1},
                "tuesday": {"peak_hour": 14, "open_rate": 29.8},
                "wednesday": {"peak_hour": 11, "open_rate": 31.5},
                "thursday": {"peak_hour": 15, "open_rate": 28.9},
                "friday": {"peak_hour": 9, "open_rate": 33.2},
                "saturday": {"peak_hour": 16, "open_rate": 25.3},
                "sunday": {"peak_hour": 19, "open_rate": 27.1},
            },
            "seasonal_trends": {
                "spring": {
                    "avg_open_rate": 30.5,
                    "best_types": ["surveys", "reminders"],
                },
                "summer": {
                    "avg_open_rate": 27.8,
                    "best_types": ["achievements", "system"],
                },
                "autumn": {
                    "avg_open_rate": 32.1,
                    "best_types": ["surveys", "announcements"],
                },
                "winter": {
                    "avg_open_rate": 29.3,
                    "best_types": ["reminders", "system"],
                },
            },
            "cohort_analysis": {
                "new_users_week_1": {"open_rate": 45.2, "retention": 85.3},
                "new_users_week_4": {"open_rate": 32.8, "retention": 72.1},
                "new_users_week_12": {"open_rate": 28.5, "retention": 65.8},
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_engagement_trends = AsyncMock(
                return_value=mock_engagement_trends
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_user_engagement_trends")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["weekly_trends"]) == 3
        assert data["daily_patterns"]["friday"]["open_rate"] == 33.2
        assert data["seasonal_trends"]["autumn"]["avg_open_rate"] == 32.1
        assert data["cohort_analysis"]["new_users_week_1"]["retention"] == 85.3
