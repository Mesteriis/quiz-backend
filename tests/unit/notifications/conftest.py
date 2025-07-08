"""
Конфигурация и фикстуры для тестов домена notifications.

Этот модуль предоставляет фикстуры для:
- Пользователей с различными правами доступа
- Тестовых данных для уведомлений
- Моков для внешних сервисов
- Настроек для различных каналов доставки
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from tests.factories import UserFactory


@pytest.fixture
async def verified_user(async_session):
    """Фикстура для верифицированного пользователя."""
    user_factory = UserFactory(async_session)
    user = await user_factory.create(
        username="verified_user",
        email="verified@example.com",
        is_verified=True,
        is_active=True,
        is_admin=False,
        created_at=datetime.utcnow(),
    )
    return user


@pytest.fixture
async def admin_user(async_session):
    """Фикстура для администратора."""
    user_factory = UserFactory(async_session)
    admin = await user_factory.create(
        username="admin_user",
        email="admin@example.com",
        is_verified=True,
        is_active=True,
        is_admin=True,
        is_superuser=True,
        created_at=datetime.utcnow(),
    )
    return admin


@pytest.fixture
async def premium_user(async_session):
    """Фикстура для premium пользователя."""
    user_factory = UserFactory(async_session)
    user = await user_factory.create(
        username="premium_user",
        email="premium@example.com",
        is_verified=True,
        is_active=True,
        user_type="premium",
        subscription_active=True,
        created_at=datetime.utcnow(),
    )
    return user


@pytest.fixture
async def inactive_user(async_session):
    """Фикстура для неактивного пользователя."""
    user_factory = UserFactory(async_session)
    user = await user_factory.create(
        username="inactive_user",
        email="inactive@example.com",
        is_verified=True,
        is_active=False,
        last_login=datetime.utcnow() - timedelta(days=60),
        created_at=datetime.utcnow() - timedelta(days=90),
    )
    return user


@pytest.fixture
async def new_user(async_session):
    """Фикстура для нового пользователя."""
    user_factory = UserFactory(async_session)
    user = await user_factory.create(
        username="new_user",
        email="new@example.com",
        is_verified=True,
        is_active=True,
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    return user


# Фикстуры для тестовых данных уведомлений
@pytest.fixture
def system_notification_data() -> Dict[str, Any]:
    """Фикстура для данных системного уведомления."""
    return {
        "type": "system_message",
        "title": "System Update",
        "message": "The system has been updated with new features and improvements",
        "channels": ["websocket", "email"],
        "data": {
            "update_version": "1.2.3",
            "features": ["new_dashboard", "improved_performance"],
            "maintenance_scheduled": False,
        },
    }


@pytest.fixture
def survey_notification_data() -> Dict[str, Any]:
    """Фикстура для данных уведомления о опросе."""
    return {
        "type": "survey_completed",
        "title": "Survey Completed",
        "message": "Thank you for completing the customer satisfaction survey",
        "channels": ["websocket", "push"],
        "data": {
            "survey_id": "survey_123",
            "completion_time": "2024-01-15T14:30:00Z",
            "score": 85,
            "rewards_earned": 100,
        },
    }


@pytest.fixture
def reminder_notification_data() -> Dict[str, Any]:
    """Фикстура для данных напоминания."""
    return {
        "type": "reminder",
        "title": "Survey Reminder",
        "message": "Don't forget to complete your weekly survey",
        "channels": ["push", "email"],
        "data": {
            "reminder_type": "weekly_survey",
            "due_date": "2024-01-20T23:59:59Z",
            "survey_link": "https://app.com/surveys/weekly",
            "priority": "normal",
        },
    }


@pytest.fixture
def achievement_notification_data() -> Dict[str, Any]:
    """Фикстура для данных достижения."""
    return {
        "type": "achievement_unlocked",
        "title": "Achievement Unlocked!",
        "message": "Congratulations! You've completed 10 surveys this month",
        "channels": ["websocket", "push"],
        "data": {
            "achievement_id": "survey_master_10",
            "badge_icon": "🏆",
            "points_earned": 500,
            "next_milestone": 25,
            "rarity": "rare",
        },
    }


@pytest.fixture
def announcement_notification_data() -> Dict[str, Any]:
    """Фикстура для данных объявления."""
    return {
        "type": "announcement",
        "title": "Platform Maintenance",
        "message": "The platform will be under maintenance tomorrow from 2-4 AM UTC",
        "channels": ["websocket", "email", "push"],
        "data": {
            "maintenance_start": "2024-01-16T02:00:00Z",
            "maintenance_end": "2024-01-16T04:00:00Z",
            "affected_services": ["surveys", "analytics"],
            "severity": "medium",
        },
    }


# Фикстуры для push уведомлений
@pytest.fixture
def push_subscription_data() -> Dict[str, Any]:
    """Фикстура для данных push подписки."""
    return {
        "subscription": {
            "endpoint": "https://fcm.googleapis.com/fcm/send/example_endpoint_id",
            "keys": {
                "p256dh": "example_p256dh_key_base64_encoded",
                "auth": "example_auth_key_base64_encoded",
            },
        },
        "categories": ["surveys", "reminders", "announcements"],
        "device_info": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "platform": "web",
            "device_type": "desktop",
            "app_version": "1.2.3",
        },
    }


@pytest.fixture
def mobile_push_subscription_data() -> Dict[str, Any]:
    """Фикстура для данных мобильной push подписки."""
    return {
        "subscription": {
            "endpoint": "https://fcm.googleapis.com/fcm/send/mobile_endpoint_id",
            "keys": {
                "p256dh": "mobile_p256dh_key_base64_encoded",
                "auth": "mobile_auth_key_base64_encoded",
            },
        },
        "categories": ["surveys", "reminders", "achievements"],
        "device_info": {
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "platform": "iOS",
            "device_type": "mobile",
            "app_version": "1.2.3",
        },
    }


@pytest.fixture
def push_notification_data() -> Dict[str, Any]:
    """Фикстура для данных push уведомления."""
    return {
        "title": "New Survey Available",
        "body": "A new survey is available for you to complete",
        "image": "https://app.com/images/survey_notification.png",
        "icon": "https://app.com/images/icons/survey.png",
        "data": {
            "survey_id": "survey_456",
            "category": "surveys",
            "action_url": "/surveys/survey_456",
            "expires_at": "2024-01-25T23:59:59Z",
        },
    }


@pytest.fixture
def vapid_key_data() -> Dict[str, Any]:
    """Фикстура для данных VAPID ключа."""
    return {
        "public_key": "BExample_valid_vapid_public_key_string_that_is_base64_encoded",
        "algorithm": "ES256",
        "created_at": "2024-01-01T00:00:00Z",
        "expires_at": "2025-01-01T00:00:00Z",
    }


# Фикстуры для статистики и аналитики
@pytest.fixture
def notification_statistics_data() -> Dict[str, Any]:
    """Фикстура для данных статистики уведомлений."""
    return {
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
    }


@pytest.fixture
def user_notification_history() -> List[Dict[str, Any]]:
    """Фикстура для истории уведомлений пользователя."""
    return [
        {
            "id": "notif_1",
            "type": "system_message",
            "title": "Welcome to the Platform",
            "message": "Welcome! We're excited to have you on board",
            "created_at": "2024-01-15T10:00:00Z",
            "read": False,
            "channel": "websocket",
            "data": {"welcome_bonus": 100},
        },
        {
            "id": "notif_2",
            "type": "survey_completed",
            "title": "Survey Complete",
            "message": "Thank you for completing the survey",
            "created_at": "2024-01-14T15:30:00Z",
            "read": True,
            "channel": "push",
            "data": {"survey_id": "survey_123", "points": 50},
        },
        {
            "id": "notif_3",
            "type": "reminder",
            "title": "Survey Reminder",
            "message": "You have a pending survey to complete",
            "created_at": "2024-01-13T09:00:00Z",
            "read": False,
            "channel": "email",
            "data": {"survey_id": "survey_456", "due_date": "2024-01-20T23:59:59Z"},
        },
    ]


@pytest.fixture
def invalid_notification_data() -> Dict[str, Any]:
    """Фикстура для невалидных данных уведомления."""
    return {
        "type": "",  # Пустой тип
        "title": "A" * 300,  # Слишком длинный заголовок
        "message": "",  # Пустое сообщение
        "channels": ["invalid_channel"],  # Неверный канал
        "data": {
            "malicious_script": "<script>alert('xss')</script>",
            "sql_injection": "'; DROP TABLE users; --",
        },
    }


@pytest.fixture
def malformed_push_subscription_data() -> Dict[str, Any]:
    """Фикстура для некорректных данных push подписки."""
    return {
        "subscription": {
            "endpoint": "invalid_endpoint_url",
            "keys": {
                "p256dh": "invalid_key",
                # Отсутствует auth ключ
            },
        },
        "categories": ["invalid_category"],
        "device_info": {
            "user_agent": "",
            "platform": "unknown",
            "device_type": "invalid",
        },
    }


# Фикстуры для моков сервисов
@pytest.fixture
def mock_notification_service():
    """Фикстура для мока сервиса уведомлений."""
    with patch(
        "src.services.realtime_notifications.get_notification_service"
    ) as mock_service:
        mock_notification_service = MagicMock()

        # Настройка базовых методов
        mock_notification_service.send_notification = AsyncMock(
            return_value={"success": True, "notification_id": "test_notif_123"}
        )
        mock_notification_service.get_user_notifications = AsyncMock(return_value=[])
        mock_notification_service.get_statistics = AsyncMock(return_value={})
        mock_notification_service.broadcast_notification = AsyncMock(
            return_value={"sent_count": 100, "failed_count": 5}
        )
        mock_notification_service.clear_user_notifications = AsyncMock(
            return_value={"cleared_count": 10}
        )

        mock_service.return_value = mock_notification_service
        yield mock_notification_service


@pytest.fixture
def mock_push_service():
    """Фикстура для мока push сервиса."""
    with patch("src.routers.push_notifications.push_service") as mock_service:
        # Настройка базовых методов
        mock_service.get_vapid_public_key.return_value = (
            "BExample_valid_vapid_public_key"
        )
        mock_service.send_to_user = AsyncMock(
            return_value={"success": True, "sent_count": 1, "failed_count": 0}
        )
        mock_service.send_to_all = AsyncMock(
            return_value={"success": True, "sent_count": 1000, "failed_count": 25}
        )
        mock_service.get_analytics_stats = AsyncMock(return_value={})
        mock_service.validate_subscriptions = AsyncMock(
            return_value={"valid_count": 500, "invalid_count": 10}
        )

        yield mock_service


@pytest.fixture
def mock_push_subscription_repository():
    """Фикстура для мока репозитория push подписок."""
    with patch(
        "src.routers.push_notifications.get_push_subscription_repository"
    ) as mock_repo:
        mock_subscription_repo = MagicMock()

        # Настройка базовых методов
        mock_subscription = MagicMock()
        mock_subscription.id = 123
        mock_subscription_repo.create_subscription = AsyncMock(
            return_value=mock_subscription
        )
        mock_subscription_repo.get_user_subscriptions = AsyncMock(return_value=[])
        mock_subscription_repo.delete_user_subscriptions = AsyncMock(return_value=1)
        mock_subscription_repo.update_categories = AsyncMock(return_value=True)
        mock_subscription_repo.cleanup_expired = AsyncMock(
            return_value={"removed_count": 5}
        )

        mock_repo.return_value = mock_subscription_repo
        yield mock_subscription_repo


# Фикстуры для настроек каналов
@pytest.fixture
def websocket_channel_config() -> Dict[str, Any]:
    """Фикстура для настроек WebSocket канала."""
    return {
        "channel": "websocket",
        "enabled": True,
        "max_connections": 1000,
        "timeout": 30,
        "retry_attempts": 3,
        "supported_types": [
            "system_message",
            "survey_completed",
            "reminder",
            "achievement_unlocked",
        ],
    }


@pytest.fixture
def email_channel_config() -> Dict[str, Any]:
    """Фикстура для настроек email канала."""
    return {
        "channel": "email",
        "enabled": True,
        "smtp_server": "smtp.example.com",
        "rate_limit": 100,
        "template_engine": "jinja2",
        "supported_types": ["announcement", "reminder", "survey_completed"],
    }


@pytest.fixture
def push_channel_config() -> Dict[str, Any]:
    """Фикстура для настроек push канала."""
    return {
        "channel": "push",
        "enabled": True,
        "max_payload_size": 4096,
        "ttl": 86400,  # 24 часа
        "supported_platforms": ["iOS", "Android", "Web"],
        "supported_types": ["reminder", "achievement_unlocked", "announcement"],
    }


@pytest.fixture
def sms_channel_config() -> Dict[str, Any]:
    """Фикстура для настроек SMS канала."""
    return {
        "channel": "sms",
        "enabled": True,
        "provider": "twilio",
        "max_length": 160,
        "cost_per_message": 0.05,
        "supported_types": ["reminder", "urgent_announcement"],
    }


# Фикстуры для тестов производительности
@pytest.fixture
def performance_test_data() -> Dict[str, Any]:
    """Фикстура для данных тестов производительности."""
    return {
        "concurrent_users": 100,
        "notifications_per_user": 10,
        "target_response_time": 1.0,  # секунды
        "max_queue_size": 1000,
        "test_duration": 60,  # секунды
        "channels_to_test": ["websocket", "push", "email"],
    }


@pytest.fixture
def notification_categories() -> List[str]:
    """Фикстура для категорий уведомлений."""
    return [
        "surveys",
        "reminders",
        "announcements",
        "achievements",
        "system_messages",
        "security_alerts",
        "marketing",
        "support",
    ]


@pytest.fixture
def notification_types() -> List[str]:
    """Фикстура для типов уведомлений."""
    return [
        "system_message",
        "survey_completed",
        "survey_available",
        "reminder",
        "achievement_unlocked",
        "announcement",
        "security_alert",
        "marketing_campaign",
        "support_ticket_update",
    ]


@pytest.fixture
def supported_channels() -> List[str]:
    """Фикстура для поддерживаемых каналов."""
    return ["websocket", "email", "push", "sms"]


# Фикстуры для тестов безопасности
@pytest.fixture
def xss_test_data() -> List[str]:
    """Фикстура для тестов XSS."""
    return [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "<iframe src=javascript:alert('xss')></iframe>",
        "<%2Fscript%3E%3Cscript%3Ealert('xss')%3C%2Fscript%3E",
    ]


@pytest.fixture
def sql_injection_test_data() -> List[str]:
    """Фикстура для тестов SQL инъекций."""
    return [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "'; INSERT INTO users VALUES ('hacker', 'pass'); --",
        "' OR 1=1 --",
    ]


@pytest.fixture
def large_payload_test_data() -> Dict[str, Any]:
    """Фикстура для тестов с большими данными."""
    return {
        "type": "system_message",
        "title": "X" * 1000,  # Очень длинный заголовок
        "message": "Y" * 10000,  # Очень длинное сообщение
        "data": {
            "large_field": "Z" * 100000,  # Очень большое поле
            "nested": {
                "level1": {
                    "level2": {
                        "level3": ["item"]
                        * 10000  # Глубокая вложенность с большим массивом
                    }
                }
            },
        },
    }
