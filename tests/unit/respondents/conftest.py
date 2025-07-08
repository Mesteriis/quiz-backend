"""
Фикстуры для тестов домена respondents.

Этот модуль содержит фикстуры для тестирования функциональности респондентов:
- Различные типы респондентов
- Согласия и GDPR данные
- Моки сервисов респондентов
- Тестовые данные для поиска и аналитики
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4


@pytest.fixture
def anonymous_respondent():
    """Фикстура анонимного респондента."""
    return {
        "id": 1,
        "session_id": "anon_session_123",
        "browser_fingerprint": "anon_fp_456",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "anonymous_name": "Anonymous User",
        "anonymous_email": "anon@example.com",
        "is_anonymous": True,
        "user_id": None,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-20T16:30:00Z",
        "last_activity": "2024-01-20T16:30:00Z",
        "surveys_participated": 3,
        "total_responses": 12,
        "completion_rate": 0.75,
        "status": "active",
        "preferred_language": "en",
        "time_zone": "UTC",
        "source": "web",
    }


@pytest.fixture
def authenticated_respondent(regular_user):
    """Фикстура авторизованного респондента."""
    return {
        "id": 2,
        "session_id": "auth_session_789",
        "browser_fingerprint": "auth_fp_abc",
        "ip_address": "10.0.0.50",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "user_id": regular_user.id,
        "is_anonymous": False,
        "anonymous_name": None,
        "anonymous_email": None,
        "created_at": "2024-01-10T08:00:00Z",
        "updated_at": "2024-01-20T16:30:00Z",
        "last_activity": "2024-01-20T16:30:00Z",
        "surveys_participated": 8,
        "total_responses": 45,
        "completion_rate": 0.85,
        "status": "active",
        "preferred_language": "en",
        "time_zone": "America/New_York",
        "source": "web",
        "user_details": {
            "username": regular_user.username,
            "email": regular_user.email,
            "first_name": regular_user.first_name,
            "last_name": regular_user.last_name,
        },
    }


@pytest.fixture
def telegram_respondent():
    """Фикстура Telegram респондента."""
    return {
        "id": 3,
        "session_id": "tg_session_456",
        "browser_fingerprint": "telegram_client",
        "telegram_user_id": 123456789,
        "telegram_username": "john_doe_tg",
        "telegram_first_name": "John",
        "telegram_last_name": "Doe",
        "telegram_language_code": "en",
        "is_anonymous": True,
        "user_id": None,
        "created_at": "2024-01-18T14:00:00Z",
        "updated_at": "2024-01-20T16:30:00Z",
        "last_activity": "2024-01-20T16:30:00Z",
        "surveys_participated": 2,
        "total_responses": 8,
        "completion_rate": 0.80,
        "status": "active",
        "preferred_language": "en",
        "time_zone": "UTC",
        "source": "telegram",
        "platform": "telegram",
    }


@pytest.fixture
def location_enabled_respondent():
    """Фикстура респондента с включенной геолокацией."""
    return {
        "id": 4,
        "session_id": "location_session_789",
        "browser_fingerprint": "location_fp_def",
        "ip_address": "192.168.1.150",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "anonymous_name": "Location User",
        "anonymous_email": "location@example.com",
        "is_anonymous": True,
        "user_id": None,
        "created_at": "2024-01-12T09:00:00Z",
        "updated_at": "2024-01-20T16:30:00Z",
        "last_activity": "2024-01-20T16:30:00Z",
        "surveys_participated": 5,
        "total_responses": 22,
        "completion_rate": 0.88,
        "status": "active",
        "preferred_language": "en",
        "time_zone": "America/New_York",
        "source": "mobile",
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 10.5,
            "altitude": 15.2,
            "timestamp": "2024-01-20T16:30:00Z",
            "source": "gps",
            "address": {
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "postal_code": "10001",
            },
        },
    }


@pytest.fixture
def inactive_respondent():
    """Фикстура неактивного респондента."""
    return {
        "id": 5,
        "session_id": "inactive_session_999",
        "browser_fingerprint": "inactive_fp_xyz",
        "ip_address": "172.16.0.10",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "anonymous_name": "Inactive User",
        "anonymous_email": "inactive@example.com",
        "is_anonymous": True,
        "user_id": None,
        "created_at": "2024-01-05T10:00:00Z",
        "updated_at": "2024-01-08T12:00:00Z",
        "last_activity": "2024-01-08T12:00:00Z",
        "surveys_participated": 1,
        "total_responses": 2,
        "completion_rate": 0.25,
        "status": "inactive",
        "preferred_language": "en",
        "time_zone": "UTC",
        "source": "web",
    }


@pytest.fixture
def premium_respondent():
    """Фикстура премиум респондента."""
    return {
        "id": 6,
        "session_id": "premium_session_888",
        "browser_fingerprint": "premium_fp_vip",
        "ip_address": "203.0.113.10",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "anonymous_name": "Premium User",
        "anonymous_email": "premium@example.com",
        "is_anonymous": True,
        "user_id": None,
        "created_at": "2024-01-01T08:00:00Z",
        "updated_at": "2024-01-20T16:30:00Z",
        "last_activity": "2024-01-20T16:30:00Z",
        "surveys_participated": 15,
        "total_responses": 89,
        "completion_rate": 0.95,
        "status": "active",
        "preferred_language": "en",
        "time_zone": "Europe/London",
        "source": "web",
        "tier": "premium",
        "subscription": {
            "plan": "premium",
            "started_at": "2024-01-01T08:00:00Z",
            "expires_at": "2024-12-31T23:59:59Z",
        },
    }


@pytest.fixture
def sample_consents():
    """Фикстура образцов согласий."""
    return [
        {
            "id": 101,
            "respondent_id": 1,
            "consent_type": "data_processing",
            "purpose": "survey_participation",
            "granted": True,
            "granted_at": "2024-01-15T10:00:00Z",
            "revoked_at": None,
            "source": "web_form",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "consent_text": "I agree to the processing of my personal data",
            "version": "1.0",
            "legal_basis": "consent",
            "is_active": True,
            "expires_at": "2025-01-15T10:00:00Z",
        },
        {
            "id": 102,
            "respondent_id": 1,
            "consent_type": "location_tracking",
            "purpose": "location_based_surveys",
            "granted": True,
            "granted_at": "2024-01-15T10:05:00Z",
            "revoked_at": None,
            "source": "mobile_app",
            "ip_address": "192.168.1.100",
            "user_agent": "Mobile App v1.0",
            "consent_text": "I agree to share my location data",
            "version": "1.0",
            "legal_basis": "consent",
            "is_active": True,
            "expires_at": "2024-04-15T10:05:00Z",
            "precision_level": "city",
        },
        {
            "id": 103,
            "respondent_id": 1,
            "consent_type": "marketing_communications",
            "purpose": "survey_invitations",
            "granted": False,
            "granted_at": "2024-01-15T10:10:00Z",
            "revoked_at": "2024-01-18T15:00:00Z",
            "source": "web_form",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "consent_text": "I agree to receive marketing communications",
            "version": "1.0",
            "legal_basis": "consent",
            "is_active": False,
            "expires_at": None,
        },
    ]


@pytest.fixture
def sample_dashboard_data():
    """Фикстура данных дашборда респондентов."""
    return {
        "overview": {
            "total_respondents": 1247,
            "anonymous_respondents": 823,
            "authenticated_respondents": 424,
            "active_respondents": 1156,
            "inactive_respondents": 91,
        },
        "growth": {
            "new_this_month": 87,
            "new_this_week": 23,
            "new_today": 5,
            "growth_rate_monthly": 0.075,
            "growth_rate_weekly": 0.020,
        },
        "engagement": {
            "average_surveys_per_respondent": 4.2,
            "average_responses_per_respondent": 18.6,
            "average_completion_rate": 0.78,
            "highly_engaged_respondents": 234,
            "low_engagement_respondents": 156,
        },
        "demographics": {
            "by_source": {"web": 678, "mobile": 345, "telegram": 156, "api": 68},
            "by_location": {
                "USA": 456,
                "Canada": 123,
                "UK": 89,
                "Germany": 67,
                "other": 512,
            },
        },
    }


@pytest.fixture
def sample_activity_summary():
    """Фикстура сводки активности респондента."""
    return {
        "respondent_id": 1,
        "summary_period": "all_time",
        "surveys": {
            "total_participated": 12,
            "completed": 10,
            "partially_completed": 2,
            "completion_rate": 0.83,
        },
        "responses": {
            "total_submitted": 58,
            "valid_responses": 55,
            "invalid_responses": 3,
            "average_response_time": 3.8,
            "fastest_response": 1.2,
            "slowest_response": 15.6,
        },
        "engagement": {
            "sessions_count": 25,
            "average_session_duration": 8.5,
            "total_time_spent": 212.5,
            "return_visits": 18,
            "retention_rate": 0.72,
        },
        "timeline": [
            {
                "date": "2024-01-20",
                "surveys_started": 1,
                "surveys_completed": 1,
                "responses_submitted": 5,
                "time_spent": 6.2,
            },
            {
                "date": "2024-01-19",
                "surveys_started": 0,
                "surveys_completed": 0,
                "responses_submitted": 0,
                "time_spent": 0,
            },
            {
                "date": "2024-01-18",
                "surveys_started": 2,
                "surveys_completed": 1,
                "responses_submitted": 8,
                "time_spent": 12.4,
            },
        ],
    }


@pytest.fixture
def sample_search_results():
    """Фикстура результатов поиска респондентов."""
    return {
        "respondents": [
            {
                "id": 1,
                "anonymous_name": "John Doe",
                "anonymous_email": "john@example.com",
                "is_anonymous": True,
                "user_id": None,
                "created_at": "2024-01-15T10:00:00Z",
                "last_activity": "2024-01-20T16:30:00Z",
                "surveys_participated": 5,
                "total_responses": 25,
                "completion_rate": 0.85,
                "status": "active",
            },
            {
                "id": 2,
                "anonymous_name": "Jane Smith",
                "anonymous_email": "jane@example.com",
                "is_anonymous": True,
                "user_id": None,
                "created_at": "2024-01-18T14:20:00Z",
                "last_activity": "2024-01-20T15:45:00Z",
                "surveys_participated": 3,
                "total_responses": 12,
                "completion_rate": 0.75,
                "status": "active",
            },
        ],
        "pagination": {"page": 1, "per_page": 20, "total": 2, "total_pages": 1},
        "search_info": {"query": "john jane", "matches_found": 2, "search_time": 0.05},
    }


@pytest.fixture
def sample_export_data():
    """Фикстура данных экспорта респондентов."""
    return {
        "export_id": "export_20240120_001",
        "respondent_id": 1,
        "format": "json",
        "status": "completed",
        "created_at": "2024-01-20T16:30:00Z",
        "completed_at": "2024-01-20T16:32:15Z",
        "file_size": "2.5MB",
        "encryption_enabled": True,
        "download_url": "https://secure.example.com/exports/export_20240120_001.zip",
        "expires_at": "2024-01-27T16:30:00Z",
        "included_sections": {
            "profile": {"records": 1, "fields": ["name", "email", "preferences"]},
            "consents": {
                "records": 3,
                "fields": ["consent_type", "granted_at", "status"],
            },
            "responses": {
                "records": 45,
                "fields": ["survey_id", "response_data", "submitted_at"],
            },
            "activity": {
                "records": 28,
                "fields": ["action", "timestamp", "ip_address"],
            },
        },
    }


@pytest.fixture
def sample_merge_data():
    """Фикстура данных слияния респондентов."""
    return {
        "success": True,
        "merged_respondent": {
            "id": 25,
            "user_id": 1,
            "session_id": "auth_session_merged",
            "browser_fingerprint": "merged_fp_456",
            "is_anonymous": False,
            "created_at": "2024-01-15T08:00:00Z",
            "updated_at": "2024-01-20T16:30:00Z",
            "last_activity": "2024-01-20T16:30:00Z",
        },
        "merge_summary": {
            "anonymous_respondent_id": 18,
            "authenticated_respondent_id": 25,
            "surveys_merged": 3,
            "responses_merged": 12,
            "consents_merged": 5,
            "data_points_merged": 20,
        },
        "merged_activity": {
            "total_surveys": 8,
            "total_responses": 35,
            "combined_completion_rate": 0.78,
            "earliest_activity": "2024-01-15T08:00:00Z",
        },
    }


@pytest.fixture
def sample_bulk_operation_data():
    """Фикстура данных массовых операций."""
    return {
        "success": True,
        "updated_count": 5,
        "failed_count": 0,
        "results": [
            {
                "respondent_id": 1,
                "status": "updated",
                "updated_fields": ["status", "notification_preferences", "tags"],
            },
            {
                "respondent_id": 2,
                "status": "updated",
                "updated_fields": ["status", "notification_preferences", "tags"],
            },
        ],
        "execution_summary": {
            "total_requested": 5,
            "successfully_updated": 5,
            "failed_updates": 0,
            "execution_time": 1.23,
        },
    }


@pytest.fixture
def sample_gdpr_data():
    """Фикстура GDPR данных."""
    return {
        "deletion_id": "deletion_20240120_001",
        "respondent_id": 1,
        "status": "completed",
        "initiated_at": "2024-01-20T16:30:00Z",
        "completed_at": "2024-01-20T16:35:45Z",
        "reason": "user_request",
        "confirmation_code": "DELETE_CONFIRM_123",
        "deleted_sections": {
            "profile": {
                "records_deleted": 1,
                "fields_deleted": ["name", "email", "phone", "address"],
            },
            "responses": {"records_deleted": 45, "surveys_affected": 8},
            "activity": {"records_deleted": 28, "logs_purged": True},
        },
        "legal_note": "Data deleted in compliance with GDPR Article 17",
    }


@pytest.fixture
def mock_respondent_service():
    """Мок сервиса респондентов."""
    service = MagicMock()

    # Базовые CRUD операции
    service.create_or_get_respondent = AsyncMock()
    service.get_respondent_by_id = AsyncMock()
    service.get_my_respondent = AsyncMock()
    service.update_respondent = AsyncMock()
    service.delete_respondent = AsyncMock()

    # Операции слияния
    service.merge_respondents = AsyncMock()
    service.merge_multiple_respondents = AsyncMock()

    # Поиск и статистика
    service.search_respondents = AsyncMock()
    service.get_respondent_statistics = AsyncMock()
    service.get_engagement_analytics = AsyncMock()
    service.get_activity_summary = AsyncMock()

    # Геолокация
    service.update_location = AsyncMock()
    service.get_location_history = AsyncMock()

    # Массовые операции
    service.bulk_update_respondents = AsyncMock()
    service.bulk_export_respondents = AsyncMock()
    service.bulk_delete_respondents = AsyncMock()

    return service


@pytest.fixture
def mock_consent_service():
    """Мок сервиса согласий."""
    service = MagicMock()

    # Управление согласиями
    service.grant_consent = AsyncMock()
    service.revoke_consent = AsyncMock()
    service.revoke_all_consents = AsyncMock()
    service.update_consent = AsyncMock()

    # Получение согласий
    service.get_respondent_consents = AsyncMock()
    service.get_consent_by_id = AsyncMock()
    service.get_consent_history = AsyncMock()

    # Валидация и аналитика
    service.validate_consent = AsyncMock()
    service.get_consent_statistics = AsyncMock()

    return service


@pytest.fixture
def mock_gdpr_service():
    """Мок GDPR сервиса."""
    service = MagicMock()

    # Экспорт данных
    service.export_respondent_data = AsyncMock()
    service.get_export_status = AsyncMock()
    service.download_export = AsyncMock()

    # Удаление данных
    service.delete_respondent_data = AsyncMock()
    service.anonymize_respondent_data = AsyncMock()
    service.get_deletion_status = AsyncMock()

    # Права субъектов данных
    service.get_data_subject_rights = AsyncMock()
    service.process_data_subject_request = AsyncMock()

    return service


@pytest.fixture
def mock_notification_service():
    """Мок сервиса уведомлений."""
    service = MagicMock()

    # Отправка уведомлений
    service.send_consent_notification = AsyncMock()
    service.send_data_export_notification = AsyncMock()
    service.send_data_deletion_notification = AsyncMock()
    service.send_merge_notification = AsyncMock()

    # Управление предпочтениями
    service.update_notification_preferences = AsyncMock()
    service.get_notification_preferences = AsyncMock()

    return service


@pytest.fixture
def mock_analytics_service():
    """Мок сервиса аналитики."""
    service = MagicMock()

    # Аналитика респондентов
    service.track_respondent_activity = AsyncMock()
    service.calculate_engagement_metrics = AsyncMock()
    service.generate_activity_report = AsyncMock()

    # Когортный анализ
    service.perform_cohort_analysis = AsyncMock()
    service.calculate_retention_rates = AsyncMock()

    # Сегментация
    service.segment_respondents = AsyncMock()
    service.get_segment_statistics = AsyncMock()

    return service


@pytest.fixture
def error_responses():
    """Фикстура ошибочных ответов."""
    return {
        "not_found": {"detail": "Respondent not found", "status_code": 404},
        "validation_error": {
            "detail": [
                {
                    "loc": ["body", "anonymous_name"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ],
            "status_code": 422,
        },
        "permission_denied": {"detail": "Permission denied", "status_code": 403},
        "rate_limit_exceeded": {"detail": "Rate limit exceeded", "status_code": 429},
        "service_unavailable": {
            "detail": "Service temporarily unavailable",
            "status_code": 503,
        },
    }


@pytest.fixture
def edge_case_data():
    """Фикстура данных для граничных случаев."""
    return {
        "empty_respondent": {
            "id": None,
            "session_id": "",
            "browser_fingerprint": "",
            "anonymous_name": "",
            "anonymous_email": "",
            "surveys_participated": 0,
            "total_responses": 0,
        },
        "max_length_data": {
            "anonymous_name": "A" * 1000,
            "anonymous_email": "very.long.email.address@extremely.long.domain.name.example.com",
            "session_id": "x" * 255,
            "browser_fingerprint": "f" * 500,
        },
        "unicode_data": {
            "anonymous_name": "测试用户 👤",
            "anonymous_email": "тест@пример.com",
            "session_id": "сессия_🔗_测试",
            "browser_fingerprint": "指纹_🔍_отпечаток",
        },
        "boundary_numbers": {
            "surveys_participated": 2147483647,
            "total_responses": 2147483647,
            "completion_rate": 1.0,
            "latitude": 90.0,
            "longitude": 180.0,
        },
    }


@pytest.fixture
def performance_test_data():
    """Фикстура данных для тестов производительности."""
    return {
        "large_respondent_list": [
            {
                "id": i,
                "anonymous_name": f"User {i}",
                "anonymous_email": f"user{i}@example.com",
                "surveys_participated": i % 10,
                "total_responses": i * 3,
            }
            for i in range(1, 10001)  # 10,000 respondents
        ],
        "bulk_operation_ids": list(range(1, 1001)),  # 1,000 IDs
        "concurrent_requests": 100,
        "large_export_size": "500MB",
        "timeout_duration": 30.0,
    }
