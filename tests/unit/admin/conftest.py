"""
Фикстуры для тестов домена Admin.

Этот модуль содержит фикстуры для тестирования административных функций:
- Пользователи с разными ролями (admin, regular, inactive)
- Опросы и данные для аналитики
- Системные настройки и конфигурация
- Моки сервисов и внешних API
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from tests.factories import UserFactory, SurveyFactory, QuestionFactory, ResponseFactory


@pytest.fixture
def admin_user():
    """Фикстура администратора."""
    return UserFactory(
        username="admin",
        email="admin@quizapp.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_admin=True,
        created_at=datetime.now() - timedelta(days=30),
    )


@pytest.fixture
def regular_user():
    """Фикстура обычного пользователя."""
    return UserFactory(
        username="regular_user",
        email="user@example.com",
        first_name="Regular",
        last_name="User",
        is_active=True,
        is_admin=False,
        created_at=datetime.now() - timedelta(days=7),
    )


@pytest.fixture
def inactive_user():
    """Фикстура неактивного пользователя."""
    return UserFactory(
        username="inactive_user",
        email="inactive@example.com",
        first_name="Inactive",
        last_name="User",
        is_active=False,
        is_admin=False,
        created_at=datetime.now() - timedelta(days=90),
    )


@pytest.fixture
def premium_user():
    """Фикстура премиум пользователя."""
    return UserFactory(
        username="premium_user",
        email="premium@example.com",
        first_name="Premium",
        last_name="User",
        is_active=True,
        is_admin=False,
        is_premium=True,
        created_at=datetime.now() - timedelta(days=14),
    )


@pytest.fixture
def sample_surveys():
    """Фикстура с набором опросов для тестирования."""
    return [
        SurveyFactory(
            title="Customer Satisfaction Survey",
            description="Annual customer satisfaction survey",
            is_public=True,
            is_active=True,
            created_at=datetime.now() - timedelta(days=30),
        ),
        SurveyFactory(
            title="Product Feedback Survey",
            description="Feedback on new product features",
            is_public=False,
            is_active=True,
            created_at=datetime.now() - timedelta(days=15),
        ),
        SurveyFactory(
            title="Draft Survey",
            description="Survey in draft state",
            is_public=False,
            is_active=False,
            created_at=datetime.now() - timedelta(days=5),
        ),
    ]


@pytest.fixture
def sample_dashboard_data():
    """Фикстура с данными дашборда."""
    return {
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
            "response_rate": 0.78,
            "avg_completion_time": 4.2,
        },
        "recent_surveys": [
            {
                "id": 1,
                "title": "Recent Survey 1",
                "is_active": True,
                "is_public": True,
                "responses_count": 45,
                "created_at": "2024-01-20T10:00:00Z",
            },
            {
                "id": 2,
                "title": "Recent Survey 2",
                "is_active": True,
                "is_public": False,
                "responses_count": 23,
                "created_at": "2024-01-19T15:30:00Z",
            },
        ],
        "recent_users": [
            {
                "id": 101,
                "username": "new_user_1",
                "email": "new1@example.com",
                "is_active": True,
                "created_at": "2024-01-20T14:30:00Z",
            },
            {
                "id": 102,
                "username": "new_user_2",
                "email": "new2@example.com",
                "is_active": True,
                "created_at": "2024-01-20T12:15:00Z",
            },
        ],
        "activity_overview": {
            "surveys_created_today": 2,
            "surveys_created_this_week": 8,
            "responses_today": 89,
            "responses_this_week": 456,
            "users_registered_today": 5,
            "users_registered_this_week": 23,
        },
    }


@pytest.fixture
def sample_system_health():
    """Фикстура с данными о здоровье системы."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-20T16:30:00Z",
        "uptime": "15d 8h 42m",
        "services": {
            "database": {"status": "healthy", "response_time": 0.015},
            "redis": {"status": "healthy", "response_time": 0.002},
            "email": {"status": "healthy", "response_time": 0.156},
            "telegram": {"status": "healthy", "response_time": 0.089},
        },
        "resources": {
            "cpu_usage": 15.2,
            "memory_usage": 68.4,
            "disk_usage": 42.1,
            "network_io": 125.6,
        },
        "performance": {
            "avg_response_time": 0.145,
            "requests_per_second": 45.2,
            "error_rate": 0.002,
            "cache_hit_rate": 0.85,
        },
    }


@pytest.fixture
def sample_user_analytics():
    """Фикстура с аналитикой пользователей."""
    return {
        "total_users": 450,
        "active_users": 367,
        "admin_users": 5,
        "new_users_today": 12,
        "new_users_this_week": 45,
        "engagement_stats": {
            "high_engagement": 89,
            "medium_engagement": 156,
            "low_engagement": 122,
            "inactive": 83,
        },
        "user_distribution": {
            "by_age": {"18-25": 89, "26-35": 156, "36-45": 123, "46+": 82},
            "by_location": {"US": 189, "Europe": 134, "Asia": 78, "Other": 49},
        },
    }


@pytest.fixture
def sample_survey_analytics():
    """Фикстура с аналитикой опросов."""
    return {
        "survey_id": 1,
        "survey_title": "Customer Satisfaction Survey",
        "response_analytics": {
            "total_responses": 234,
            "completed_responses": 186,
            "partial_responses": 48,
            "completion_rate": 0.795,
            "average_completion_time": 4.2,
            "bounce_rate": 0.15,
        },
        "engagement_metrics": {
            "unique_visitors": 312,
            "return_visitors": 67,
            "conversion_rate": 0.596,
            "average_time_on_page": 6.8,
            "social_shares": 23,
        },
        "question_performance": [
            {
                "question_id": 1,
                "question_type": "rating",
                "response_count": 186,
                "completion_rate": 1.0,
                "average_response_time": 2.1,
                "satisfaction_score": 4.2,
            },
            {
                "question_id": 2,
                "question_type": "text",
                "response_count": 156,
                "completion_rate": 0.839,
                "average_response_time": 8.5,
                "skip_rate": 0.161,
            },
        ],
    }


@pytest.fixture
def sample_system_settings():
    """Фикстура с системными настройками."""
    return {
        "general": {
            "site_name": "Quiz App",
            "site_description": "Advanced Survey Platform",
            "contact_email": "admin@quizapp.com",
            "maintenance_mode": False,
            "registration_enabled": True,
        },
        "security": {
            "password_min_length": 8,
            "login_attempts_limit": 5,
            "session_timeout": 3600,
            "two_factor_enabled": True,
            "rate_limiting_enabled": True,
        },
        "features": {
            "telegram_integration": True,
            "email_notifications": True,
            "real_time_updates": True,
            "analytics_enabled": True,
            "file_uploads": True,
        },
        "limits": {
            "max_surveys_per_user": 50,
            "max_questions_per_survey": 100,
            "max_responses_per_survey": 10000,
            "max_file_size": 10485760,
        },
    }


@pytest.fixture
def mock_admin_service():
    """Мок сервиса администратора."""
    mock_service = MagicMock()
    mock_service.get_dashboard_data = AsyncMock()
    mock_service.get_quick_stats = AsyncMock()
    mock_service.get_performance_metrics = AsyncMock()
    mock_service.get_user_engagement_analytics = AsyncMock()
    mock_service.get_survey_performance_analytics = AsyncMock()
    mock_service.get_real_time_updates = AsyncMock()
    mock_service.export_dashboard_data = AsyncMock()
    return mock_service


@pytest.fixture
def mock_survey_service():
    """Мок сервиса опросов."""
    mock_service = MagicMock()
    mock_service.get_all_surveys = AsyncMock()
    mock_service.get_filtered_surveys = AsyncMock()
    mock_service.create_survey = AsyncMock()
    mock_service.update_survey = AsyncMock()
    mock_service.delete_survey = AsyncMock()
    mock_service.bulk_update_surveys = AsyncMock()
    mock_service.bulk_delete_surveys = AsyncMock()
    mock_service.bulk_export_surveys = AsyncMock()
    mock_service.get_survey_detailed_analytics = AsyncMock()
    mock_service.get_survey_comparison_analytics = AsyncMock()
    mock_service.get_survey_predictive_analytics = AsyncMock()
    return mock_service


@pytest.fixture
def mock_user_service():
    """Мок сервиса пользователей."""
    mock_service = MagicMock()
    mock_service.get_all_users = AsyncMock()
    mock_service.get_user_analytics = AsyncMock()
    mock_service.update_user_role = AsyncMock()
    mock_service.bulk_update_users = AsyncMock()
    mock_service.get_user_activity_log = AsyncMock()
    mock_service.reset_user_password = AsyncMock()
    return mock_service


@pytest.fixture
def mock_system_service():
    """Мок системного сервиса."""
    mock_service = MagicMock()
    mock_service.get_system_health = AsyncMock()
    mock_service.get_system_logs = AsyncMock()
    mock_service.get_system_settings = AsyncMock()
    mock_service.update_system_settings = AsyncMock()
    return mock_service


@pytest.fixture
def mock_backup_service():
    """Мок сервиса резервного копирования."""
    mock_service = MagicMock()
    mock_service.create_backup = AsyncMock()
    mock_service.restore_backup = AsyncMock()
    mock_service.list_backups = AsyncMock()
    mock_service.delete_backup = AsyncMock()
    return mock_service


@pytest.fixture
def bulk_operation_data():
    """Фикстура для массовых операций."""
    return {
        "success_response": {
            "success": True,
            "updated_count": 3,
            "failed_count": 0,
            "operation_summary": {
                "total_requested": 3,
                "successfully_processed": 3,
                "failed_operations": 0,
                "execution_time": 0.45,
            },
        },
        "partial_success_response": {
            "success": True,
            "updated_count": 2,
            "failed_count": 1,
            "updated_items": [
                {"id": 1, "status": "updated"},
                {"id": 2, "status": "updated"},
            ],
            "failed_items": [{"id": 3, "error": "Item not found"}],
        },
    }


@pytest.fixture
def error_responses():
    """Фикстура с ошибочными ответами для негативных тестов."""
    return {
        "unauthorized": {"status_code": 401, "detail": "Authentication required"},
        "forbidden": {"status_code": 403, "detail": "Admin privileges required"},
        "not_found": {"status_code": 404, "detail": "Resource not found"},
        "validation_error": {"status_code": 422, "detail": "Validation failed"},
        "server_error": {"status_code": 500, "detail": "Internal server error"},
    }


@pytest.fixture
def edge_case_data():
    """Фикстура с данными для граничных случаев."""
    return {
        "large_dataset": {
            "surveys_count": 10000,
            "users_count": 100000,
            "responses_count": 1000000,
        },
        "unicode_data": {
            "survey_title": "调查问卷 📊 Опрос 🔍",
            "user_name": "用户名 👤 Пользователь",
            "emoji_content": "😀🎉🚀💯🌟⭐",
        },
        "long_strings": {
            "very_long_title": "A" * 1000,
            "very_long_description": "B" * 5000,
            "very_long_email": "c" * 100 + "@example.com",
        },
        "boundary_values": {
            "max_int": 2147483647,
            "min_int": -2147483648,
            "zero": 0,
            "negative": -1,
            "float_precision": 0.123456789,
        },
    }


@pytest.fixture
def performance_metrics():
    """Фикстура с метриками производительности."""
    return {
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
    }


@pytest.fixture
def sample_export_data():
    """Фикстура с данными экспорта."""
    return {
        "export_id": "export_admin_20240120_163000",
        "format": "csv",
        "file_url": "https://example.com/exports/admin_data_20240120_163000.csv",
        "file_size": "5.2MB",
        "created_at": "2024-01-20T16:30:00Z",
        "expires_at": "2024-01-27T16:30:00Z",
        "includes": [
            "dashboard_statistics",
            "user_analytics",
            "survey_performance",
            "system_metrics",
        ],
        "row_count": 25000,
        "columns": [
            "timestamp",
            "metric_name",
            "metric_value",
            "category",
            "subcategory",
            "additional_data",
        ],
    }


@pytest.fixture
def integration_test_data():
    """Фикстура для интеграционных тестов."""
    return {
        "workflow_steps": [
            {"step": "login", "expected_status": 200},
            {"step": "dashboard", "expected_status": 200},
            {"step": "users", "expected_status": 200},
            {"step": "surveys", "expected_status": 200},
            {"step": "system", "expected_status": 200},
            {"step": "logout", "expected_status": 200},
        ],
        "cross_service_data": {
            "users_from_user_service": 450,
            "users_from_dashboard": 450,
            "surveys_from_survey_service": 25,
            "surveys_from_dashboard": 25,
        },
    }
