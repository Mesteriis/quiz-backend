"""
Позитивные тесты для Admin Dashboard.

Этот модуль содержит все успешные сценарии работы с административным дашбордом:
- Получение общей статистики системы
- Обзор недавних данных (опросы, пользователи, ответы)
- Мониторинг активности и производительности
- Аналитические метрики и отчеты
- Персонализированный админ интерфейс
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory, SurveyFactory, QuestionFactory, ResponseFactory


class TestAdminDashboardOverview:
    """Позитивные тесты общего обзора дашборда."""

    async def test_get_dashboard_complete_data(
        self, api_client: AsyncClient, admin_user, async_session
    ):
        """Тест получения полного дашборда с данными."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Создаем тестовые данные
        users = [UserFactory() for _ in range(5)]
        surveys = [SurveyFactory() for _ in range(3)]
        for user in users[:3]:
            async_session.add(user)
        for survey in surveys:
            async_session.add(survey)
        await async_session.commit()

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_dashboard_data = AsyncMock(
                return_value={
                    "statistics": {
                        "surveys_total": 25,
                        "surveys_active": 18,
                        "surveys_draft": 7,
                        "questions_total": 156,
                        "responses_total": 2340,
                        "users_total": 450,
                        "users_active_24h": 89,
                        "users_active_7d": 234,
                        "users_active_30d": 367,
                        "admin_users": 5,
                        "system_uptime": "15d 8h 42m",
                        "response_rate": 0.78,
                        "avg_completion_time": 4.2,
                    },
                    "recent_surveys": [
                        {
                            "id": 1,
                            "title": "Customer Satisfaction Q1 2024",
                            "description": "Quarterly satisfaction survey",
                            "is_active": True,
                            "is_public": True,
                            "questions_count": 12,
                            "responses_count": 234,
                            "created_at": "2024-01-20T10:00:00Z",
                            "created_by": "admin",
                            "completion_rate": 0.82,
                            "avg_rating": 4.1,
                        },
                        {
                            "id": 2,
                            "title": "Product Feedback Survey",
                            "description": "Feedback on our new product line",
                            "is_active": True,
                            "is_public": False,
                            "questions_count": 8,
                            "responses_count": 156,
                            "created_at": "2024-01-19T15:30:00Z",
                            "created_by": "product_admin",
                            "completion_rate": 0.75,
                            "avg_rating": 3.9,
                        },
                    ],
                    "recent_users": [
                        {
                            "id": 101,
                            "username": "new_user_1",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@example.com",
                            "is_active": True,
                            "is_admin": False,
                            "created_at": "2024-01-20T14:30:00Z",
                            "last_login": "2024-01-20T16:45:00Z",
                            "surveys_participated": 3,
                            "responses_submitted": 12,
                        },
                        {
                            "id": 102,
                            "username": "new_user_2",
                            "first_name": "Jane",
                            "last_name": "Smith",
                            "email": "jane.smith@example.com",
                            "is_active": True,
                            "is_admin": False,
                            "created_at": "2024-01-20T12:15:00Z",
                            "last_login": "2024-01-20T16:30:00Z",
                            "surveys_participated": 1,
                            "responses_submitted": 5,
                        },
                    ],
                    "activity_overview": {
                        "surveys_created_today": 2,
                        "surveys_created_this_week": 8,
                        "surveys_created_this_month": 25,
                        "responses_today": 89,
                        "responses_this_week": 456,
                        "responses_this_month": 2340,
                        "users_registered_today": 5,
                        "users_registered_this_week": 23,
                        "users_registered_this_month": 67,
                    },
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(api_client.url_for("get_admin_dashboard"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру
        assert "statistics" in data
        assert "recent_surveys" in data
        assert "recent_users" in data
        assert "activity_overview" in data

        # Проверяем статистику
        stats = data["statistics"]
        assert stats["surveys_total"] == 25
        assert stats["surveys_active"] == 18
        assert stats["users_total"] == 450
        assert stats["users_active_24h"] == 89
        assert stats["response_rate"] == 0.78
        assert stats["avg_completion_time"] == 4.2

        # Проверяем недавние опросы
        recent_surveys = data["recent_surveys"]
        assert len(recent_surveys) == 2
        survey = recent_surveys[0]
        assert survey["title"] == "Customer Satisfaction Q1 2024"
        assert survey["questions_count"] == 12
        assert survey["completion_rate"] == 0.82

        # Проверяем недавних пользователей
        recent_users = data["recent_users"]
        assert len(recent_users) == 2
        user = recent_users[0]
        assert user["username"] == "new_user_1"
        assert user["surveys_participated"] == 3

        # Проверяем обзор активности
        activity = data["activity_overview"]
        assert activity["surveys_created_today"] == 2
        assert activity["responses_today"] == 89
        assert activity["users_registered_today"] == 5

    async def test_get_dashboard_with_trends(self, api_client: AsyncClient, admin_user):
        """Тест получения дашборда с трендами и сравнениями."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_dashboard_data = AsyncMock(
                return_value={
                    "statistics": {
                        "surveys_total": 25,
                        "users_total": 450,
                        "responses_total": 2340,
                    },
                    "trends": {
                        "surveys": {
                            "current_period": 25,
                            "previous_period": 22,
                            "change_percentage": 13.6,
                            "trend": "up",
                        },
                        "users": {
                            "current_period": 450,
                            "previous_period": 420,
                            "change_percentage": 7.1,
                            "trend": "up",
                        },
                        "responses": {
                            "current_period": 2340,
                            "previous_period": 2180,
                            "change_percentage": 7.3,
                            "trend": "up",
                        },
                        "engagement": {
                            "current_period": 0.78,
                            "previous_period": 0.72,
                            "change_percentage": 8.3,
                            "trend": "up",
                        },
                    },
                    "charts_data": {
                        "surveys_over_time": [
                            {"date": "2024-01-14", "count": 20},
                            {"date": "2024-01-15", "count": 21},
                            {"date": "2024-01-16", "count": 22},
                            {"date": "2024-01-17", "count": 23},
                            {"date": "2024-01-18", "count": 24},
                            {"date": "2024-01-19", "count": 24},
                            {"date": "2024-01-20", "count": 25},
                        ],
                        "responses_over_time": [
                            {"date": "2024-01-14", "count": 2100},
                            {"date": "2024-01-15", "count": 2150},
                            {"date": "2024-01-16", "count": 2200},
                            {"date": "2024-01-17", "count": 2250},
                            {"date": "2024-01-18", "count": 2290},
                            {"date": "2024-01-19", "count": 2320},
                            {"date": "2024-01-20", "count": 2340},
                        ],
                    },
                    "recent_surveys": [],
                    "recent_users": [],
                    "activity_overview": {},
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(
                api_client.url_for("get_admin_dashboard"),
                params={"include_trends": True, "include_charts": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем тренды
        assert "trends" in data
        trends = data["trends"]
        assert trends["surveys"]["change_percentage"] == 13.6
        assert trends["surveys"]["trend"] == "up"
        assert trends["users"]["change_percentage"] == 7.1
        assert trends["responses"]["change_percentage"] == 7.3
        assert trends["engagement"]["change_percentage"] == 8.3

        # Проверяем данные графиков
        assert "charts_data" in data
        charts = data["charts_data"]
        assert len(charts["surveys_over_time"]) == 7
        assert len(charts["responses_over_time"]) == 7
        assert charts["surveys_over_time"][-1]["count"] == 25
        assert charts["responses_over_time"][-1]["count"] == 2340

    async def test_get_dashboard_quick_stats(self, api_client: AsyncClient, admin_user):
        """Тест получения быстрой статистики дашборда."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_quick_stats = AsyncMock(
                return_value={
                    "surveys": {"total": 25, "active": 18, "draft": 7, "archived": 0},
                    "users": {"total": 450, "active": 367, "admin": 5, "new_today": 5},
                    "responses": {
                        "total": 2340,
                        "today": 89,
                        "this_week": 456,
                        "avg_per_survey": 93.6,
                    },
                    "system": {
                        "uptime": "15d 8h 42m",
                        "cpu_usage": 15.2,
                        "memory_usage": 68.4,
                        "storage_usage": 42.1,
                        "status": "healthy",
                    },
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(api_client.url_for("get_admin_quick_stats"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем опросы
        surveys = data["surveys"]
        assert surveys["total"] == 25
        assert surveys["active"] == 18
        assert surveys["draft"] == 7

        # Проверяем пользователей
        users = data["users"]
        assert users["total"] == 450
        assert users["active"] == 367
        assert users["admin"] == 5
        assert users["new_today"] == 5

        # Проверяем ответы
        responses = data["responses"]
        assert responses["total"] == 2340
        assert responses["today"] == 89
        assert responses["avg_per_survey"] == 93.6

        # Проверяем систему
        system = data["system"]
        assert system["uptime"] == "15d 8h 42m"
        assert system["cpu_usage"] == 15.2
        assert system["status"] == "healthy"

    async def test_get_dashboard_customizable(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест настраиваемого дашборда с пользовательскими виджетами."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_customizable_dashboard = AsyncMock(
                return_value={
                    "layout": "grid_3x3",
                    "widgets": [
                        {
                            "id": "surveys_stats",
                            "type": "statistics",
                            "title": "Surveys Overview",
                            "position": {"row": 1, "col": 1},
                            "size": {"width": 2, "height": 1},
                            "data": {
                                "total": 25,
                                "active": 18,
                                "completion_rate": 0.78,
                            },
                            "settings": {"show_trends": True, "auto_refresh": 30},
                        },
                        {
                            "id": "recent_activity",
                            "type": "timeline",
                            "title": "Recent Activity",
                            "position": {"row": 1, "col": 3},
                            "size": {"width": 1, "height": 2},
                            "data": {
                                "events": [
                                    {
                                        "type": "survey_created",
                                        "title": "New survey created",
                                        "user": "admin",
                                        "timestamp": "2024-01-20T16:00:00Z",
                                    },
                                    {
                                        "type": "user_registered",
                                        "title": "New user registered",
                                        "user": "john.doe",
                                        "timestamp": "2024-01-20T15:30:00Z",
                                    },
                                ]
                            },
                        },
                        {
                            "id": "performance_chart",
                            "type": "chart",
                            "title": "System Performance",
                            "position": {"row": 2, "col": 1},
                            "size": {"width": 2, "height": 1},
                            "data": {
                                "chart_type": "line",
                                "metrics": ["cpu", "memory", "response_time"],
                                "time_range": "24h",
                            },
                        },
                    ],
                    "preferences": {
                        "theme": "dark",
                        "auto_refresh_interval": 30,
                        "notifications_enabled": True,
                    },
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(
                api_client.url_for("get_customizable_dashboard"),
                params={"layout": "grid_3x3"},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["layout"] == "grid_3x3"
        assert len(data["widgets"]) == 3

        # Проверяем виджет статистики
        stats_widget = data["widgets"][0]
        assert stats_widget["id"] == "surveys_stats"
        assert stats_widget["type"] == "statistics"
        assert stats_widget["data"]["total"] == 25
        assert stats_widget["settings"]["auto_refresh"] == 30

        # Проверяем виджет активности
        activity_widget = data["widgets"][1]
        assert activity_widget["id"] == "recent_activity"
        assert activity_widget["type"] == "timeline"
        assert len(activity_widget["data"]["events"]) == 2

        # Проверяем предпочтения
        preferences = data["preferences"]
        assert preferences["theme"] == "dark"
        assert preferences["auto_refresh_interval"] == 30
        assert preferences["notifications_enabled"] is True


class TestAdminDashboardAnalytics:
    """Позитивные тесты аналитики дашборда."""

    async def test_get_performance_metrics(self, api_client: AsyncClient, admin_user):
        """Тест получения метрик производительности."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_performance_metrics = AsyncMock(
                return_value={
                    "response_times": {
                        "api_avg": 0.15,
                        "api_p95": 0.45,
                        "api_p99": 0.89,
                        "database_avg": 0.08,
                        "database_p95": 0.25,
                    },
                    "throughput": {
                        "requests_per_second": 45.2,
                        "surveys_per_hour": 12.5,
                        "responses_per_minute": 8.9,
                    },
                    "error_rates": {
                        "api_errors": 0.02,
                        "database_errors": 0.001,
                        "timeout_rate": 0.005,
                    },
                    "resource_usage": {
                        "cpu_usage": 15.2,
                        "memory_usage": 68.4,
                        "disk_usage": 42.1,
                        "network_io": 125.6,
                        "active_connections": 23,
                    },
                    "cache_performance": {
                        "hit_rate": 0.85,
                        "miss_rate": 0.15,
                        "eviction_rate": 0.02,
                        "memory_usage": 256.5,
                    },
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(
                api_client.url_for("get_performance_metrics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем времена ответа
        response_times = data["response_times"]
        assert response_times["api_avg"] == 0.15
        assert response_times["api_p95"] == 0.45
        assert response_times["database_avg"] == 0.08

        # Проверяем пропускную способность
        throughput = data["throughput"]
        assert throughput["requests_per_second"] == 45.2
        assert throughput["surveys_per_hour"] == 12.5

        # Проверяем уровни ошибок
        error_rates = data["error_rates"]
        assert error_rates["api_errors"] == 0.02
        assert error_rates["database_errors"] == 0.001

        # Проверяем использование ресурсов
        resource_usage = data["resource_usage"]
        assert resource_usage["cpu_usage"] == 15.2
        assert resource_usage["memory_usage"] == 68.4

        # Проверяем производительность кэша
        cache_performance = data["cache_performance"]
        assert cache_performance["hit_rate"] == 0.85
        assert cache_performance["memory_usage"] == 256.5

    async def test_get_user_engagement_analytics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения аналитики вовлеченности пользователей."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_user_engagement_analytics = AsyncMock(
                return_value={
                    "engagement_overview": {
                        "daily_active_users": 89,
                        "weekly_active_users": 234,
                        "monthly_active_users": 367,
                        "retention_rate_7d": 0.72,
                        "retention_rate_30d": 0.58,
                        "avg_session_duration": 8.5,
                        "bounce_rate": 0.15,
                    },
                    "survey_participation": {
                        "participation_rate": 0.78,
                        "completion_rate": 0.85,
                        "avg_responses_per_user": 5.2,
                        "repeat_participation_rate": 0.42,
                        "avg_time_to_complete": 4.2,
                    },
                    "user_behavior": {
                        "most_active_hours": [14, 15, 16, 17, 18],
                        "most_active_days": ["Tuesday", "Wednesday", "Thursday"],
                        "preferred_survey_length": "medium",
                        "preferred_question_types": [
                            "multiple_choice",
                            "rating",
                            "text",
                        ],
                        "device_usage": {
                            "mobile": 0.65,
                            "desktop": 0.30,
                            "tablet": 0.05,
                        },
                    },
                    "geographic_distribution": {
                        "countries": {"US": 45, "GB": 25, "CA": 15, "AU": 10, "DE": 5},
                        "cities": [
                            {"name": "New York", "users": 25},
                            {"name": "London", "users": 18},
                            {"name": "Toronto", "users": 12},
                        ],
                    },
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(
                api_client.url_for("get_user_engagement_analytics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем обзор вовлеченности
        engagement = data["engagement_overview"]
        assert engagement["daily_active_users"] == 89
        assert engagement["retention_rate_7d"] == 0.72
        assert engagement["avg_session_duration"] == 8.5
        assert engagement["bounce_rate"] == 0.15

        # Проверяем участие в опросах
        participation = data["survey_participation"]
        assert participation["participation_rate"] == 0.78
        assert participation["completion_rate"] == 0.85
        assert participation["avg_responses_per_user"] == 5.2

        # Проверяем поведение пользователей
        behavior = data["user_behavior"]
        assert 14 in behavior["most_active_hours"]
        assert "Tuesday" in behavior["most_active_days"]
        assert behavior["device_usage"]["mobile"] == 0.65

        # Проверяем географическое распределение
        geographic = data["geographic_distribution"]
        assert geographic["countries"]["US"] == 45
        assert len(geographic["cities"]) == 3

    async def test_get_survey_performance_analytics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения аналитики производительности опросов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_survey_performance_analytics = AsyncMock(
                return_value={
                    "overall_performance": {
                        "total_surveys": 25,
                        "active_surveys": 18,
                        "avg_completion_rate": 0.78,
                        "avg_response_time": 4.2,
                        "total_responses": 2340,
                        "avg_responses_per_survey": 93.6,
                    },
                    "top_performing_surveys": [
                        {
                            "id": 1,
                            "title": "Customer Satisfaction Q1",
                            "completion_rate": 0.92,
                            "response_count": 234,
                            "avg_rating": 4.5,
                            "engagement_score": 0.88,
                        },
                        {
                            "id": 2,
                            "title": "Product Feedback",
                            "completion_rate": 0.87,
                            "response_count": 156,
                            "avg_rating": 4.2,
                            "engagement_score": 0.82,
                        },
                    ],
                    "performance_trends": {
                        "completion_rates": [
                            {"month": "Jan", "rate": 0.78},
                            {"month": "Feb", "rate": 0.81},
                            {"month": "Mar", "rate": 0.75},
                        ],
                        "response_volumes": [
                            {"month": "Jan", "count": 780},
                            {"month": "Feb", "count": 920},
                            {"month": "Mar", "count": 640},
                        ],
                    },
                    "question_type_performance": {
                        "multiple_choice": {"completion_rate": 0.92, "avg_time": 2.1},
                        "text": {"completion_rate": 0.68, "avg_time": 8.5},
                        "rating": {"completion_rate": 0.89, "avg_time": 3.2},
                        "yes_no": {"completion_rate": 0.95, "avg_time": 1.8},
                    },
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(
                api_client.url_for("get_survey_performance_analytics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем общую производительность
        overall = data["overall_performance"]
        assert overall["total_surveys"] == 25
        assert overall["avg_completion_rate"] == 0.78
        assert overall["avg_response_time"] == 4.2

        # Проверяем топ опросы
        top_surveys = data["top_performing_surveys"]
        assert len(top_surveys) == 2
        assert top_surveys[0]["completion_rate"] == 0.92
        assert top_surveys[0]["engagement_score"] == 0.88

        # Проверяем тренды
        trends = data["performance_trends"]
        assert len(trends["completion_rates"]) == 3
        assert len(trends["response_volumes"]) == 3

        # Проверяем производительность типов вопросов
        question_perf = data["question_type_performance"]
        assert question_perf["multiple_choice"]["completion_rate"] == 0.92
        assert question_perf["text"]["avg_time"] == 8.5

    async def test_get_real_time_dashboard_updates(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения обновлений дашборда в реальном времени."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_real_time_updates = AsyncMock(
                return_value={
                    "timestamp": "2024-01-20T16:30:00Z",
                    "live_stats": {
                        "active_users_now": 25,
                        "surveys_being_taken": 8,
                        "responses_last_hour": 45,
                        "new_registrations_today": 5,
                        "system_load": 0.15,
                    },
                    "recent_events": [
                        {
                            "id": "event_001",
                            "type": "survey_completed",
                            "timestamp": "2024-01-20T16:29:30Z",
                            "details": {
                                "survey_id": 1,
                                "survey_title": "Customer Satisfaction",
                                "user_id": 101,
                                "completion_time": 4.5,
                            },
                        },
                        {
                            "id": "event_002",
                            "type": "user_registered",
                            "timestamp": "2024-01-20T16:28:45Z",
                            "details": {
                                "user_id": 102,
                                "username": "new_user_123",
                                "registration_source": "direct",
                            },
                        },
                        {
                            "id": "event_003",
                            "type": "survey_created",
                            "timestamp": "2024-01-20T16:27:20Z",
                            "details": {
                                "survey_id": 26,
                                "survey_title": "New Product Survey",
                                "created_by": "admin",
                                "is_public": True,
                            },
                        },
                    ],
                    "alerts": [
                        {
                            "id": "alert_001",
                            "type": "info",
                            "message": "System performance is optimal",
                            "timestamp": "2024-01-20T16:30:00Z",
                        }
                    ],
                    "next_update_in": 30,
                }
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(
                api_client.url_for("get_real_time_dashboard_updates")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем живую статистику
        live_stats = data["live_stats"]
        assert live_stats["active_users_now"] == 25
        assert live_stats["surveys_being_taken"] == 8
        assert live_stats["responses_last_hour"] == 45
        assert live_stats["system_load"] == 0.15

        # Проверяем недавние события
        recent_events = data["recent_events"]
        assert len(recent_events) == 3
        assert recent_events[0]["type"] == "survey_completed"
        assert recent_events[1]["type"] == "user_registered"
        assert recent_events[2]["type"] == "survey_created"

        # Проверяем алерты
        alerts = data["alerts"]
        assert len(alerts) == 1
        assert alerts[0]["type"] == "info"
        assert alerts[0]["message"] == "System performance is optimal"

        assert data["next_update_in"] == 30

    async def test_export_dashboard_data(self, api_client: AsyncClient, admin_user):
        """Тест экспорта данных дашборда."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.export_dashboard_data = AsyncMock(
                return_value={
                    "export_id": "export_dashboard_20240120_163000",
                    "format": "csv",
                    "file_url": "https://example.com/exports/dashboard_20240120_163000.csv",
                    "size": "2.5MB",
                    "created_at": "2024-01-20T16:30:00Z",
                    "expires_at": "2024-01-27T16:30:00Z",
                    "includes": [
                        "survey_statistics",
                        "user_analytics",
                        "performance_metrics",
                        "engagement_data",
                    ],
                    "row_count": 15420,
                    "columns": [
                        "date",
                        "surveys_total",
                        "surveys_active",
                        "users_total",
                        "users_active",
                        "responses_total",
                        "completion_rate",
                        "avg_response_time",
                        "engagement_score",
                    ],
                }
            )
            mock_service.return_value = mock_admin_service

            export_request = {
                "format": "csv",
                "date_range": {"start": "2024-01-01", "end": "2024-01-20"},
                "include_data": [
                    "survey_statistics",
                    "user_analytics",
                    "performance_metrics",
                    "engagement_data",
                ],
                "aggregation": "daily",
            }

            response = await api_client.post(
                api_client.url_for("export_dashboard_data"), json=export_request
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["export_id"] == "export_dashboard_20240120_163000"
        assert data["format"] == "csv"
        assert data["size"] == "2.5MB"
        assert data["row_count"] == 15420

        includes = data["includes"]
        assert "survey_statistics" in includes
        assert "user_analytics" in includes
        assert "performance_metrics" in includes
        assert "engagement_data" in includes

        columns = data["columns"]
        assert "date" in columns
        assert "surveys_total" in columns
        assert "completion_rate" in columns
        assert "engagement_score" in columns
