"""
Позитивные тесты для push уведомлений.

Этот модуль содержит все успешные сценарии работы с push уведомлениями:
- VAPID ключи
- Подписки на push уведомления
- Отправка push уведомлений
- Аналитика push уведомлений
- Управление подписками
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory


class TestVapidKeys:
    """Позитивные тесты для VAPID ключей."""

    async def test_get_vapid_public_key_success(self, api_client: AsyncClient):
        """Тест получения публичного VAPID ключа."""
        # Act
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_vapid_public_key.return_value = (
                "BExample_valid_vapid_public_key_string_that_is_base64_encoded"
            )

            response = await api_client.get(api_client.url_for("get_vapid_public_key"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "public_key" in data
        assert (
            data["public_key"]
            == "BExample_valid_vapid_public_key_string_that_is_base64_encoded"
        )
        assert data["public_key"].startswith("B")  # VAPID ключи начинаются с "B"

    async def test_get_vapid_key_metadata(self, api_client: AsyncClient):
        """Тест получения метаданных VAPID ключа."""
        # Act
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_vapid_metadata.return_value = {
                "public_key": "BExample_public_key",
                "algorithm": "ES256",
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2025-01-01T00:00:00Z",
            }

            response = await api_client.get(api_client.url_for("get_vapid_metadata"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "public_key" in data
        assert "algorithm" in data
        assert "created_at" in data
        assert "expires_at" in data
        assert data["algorithm"] == "ES256"


class TestPushSubscriptions:
    """Позитивные тесты для push подписок."""

    async def test_subscribe_to_push_notifications_success(
        self, api_client: AsyncClient, verified_user, async_session
    ):
        """Тест успешной подписки на push уведомления."""
        # Arrange
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/example_endpoint_id",
                "keys": {
                    "p256dh": "example_p256dh_key_base64_encoded",
                    "auth": "example_auth_key_base64_encoded",
                },
            },
            "categories": ["surveys", "reminders", "announcements"],
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription = MagicMock()
            mock_subscription.id = 123
            mock_subscription_repo.create_subscription = AsyncMock(
                return_value=mock_subscription
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("subscribe_push_notifications"),
                json=subscription_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "Подписка успешно создана" in data["message"]
        assert data["subscription_id"] == "123"

    async def test_subscribe_with_device_info(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подписки с информацией об устройстве."""
        # Arrange
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/mobile_endpoint",
                "keys": {"p256dh": "mobile_p256dh_key", "auth": "mobile_auth_key"},
            },
            "device_info": {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
                "platform": "iOS",
                "device_type": "mobile",
                "app_version": "1.2.3",
            },
            "categories": ["surveys", "reminders"],
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription = MagicMock()
            mock_subscription.id = 456
            mock_subscription_repo.create_subscription = AsyncMock(
                return_value=mock_subscription
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("subscribe_push_notifications"),
                json=subscription_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["subscription_id"] == "456"

    async def test_get_user_subscriptions_success(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения подписок пользователя."""
        # Arrange
        mock_subscriptions = [
            {
                "id": 1,
                "endpoint": "https://fcm.googleapis.com/fcm/send/endpoint1",
                "created_at": "2024-01-15T10:00:00Z",
                "is_active": True,
                "categories": ["surveys", "reminders"],
                "device_info": {"platform": "desktop", "device_type": "desktop"},
            },
            {
                "id": 2,
                "endpoint": "https://fcm.googleapis.com/fcm/send/endpoint2",
                "created_at": "2024-01-14T15:30:00Z",
                "is_active": True,
                "categories": ["surveys", "announcements"],
                "device_info": {"platform": "iOS", "device_type": "mobile"},
            },
        ]

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.get_user_subscriptions = AsyncMock(
                return_value=mock_subscriptions
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.get(
                api_client.url_for("get_user_push_subscriptions")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["categories"] == ["surveys", "reminders"]
        assert data[1]["device_info"]["platform"] == "iOS"

    async def test_update_subscription_categories(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест обновления категорий подписки."""
        # Arrange
        subscription_id = 123
        categories_data = {
            "categories": ["surveys", "reminders", "announcements", "achievements"]
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.update_categories = AsyncMock(return_value=True)
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.put(
                api_client.url_for(
                    "update_subscription_categories", subscription_id=subscription_id
                ),
                json=categories_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "Категории обновлены" in data["message"]

    async def test_unsubscribe_from_push_notifications(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отписки от push уведомлений."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.delete_user_subscriptions = AsyncMock(
                return_value=2
            )  # удалено 2 подписки
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("unsubscribe_push_notifications")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "Подписка успешно удалена" in data["message"]

    async def test_deactivate_subscription(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест деактивации конкретной подписки."""
        # Arrange
        subscription_id = 456

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.deactivate_subscription = AsyncMock(
                return_value=True
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for(
                    "deactivate_push_subscription", subscription_id=subscription_id
                )
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "деактивирована" in data["message"]


class TestPushNotificationSending:
    """Позитивные тесты отправки push уведомлений."""

    async def test_send_test_push_notification(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки тестового push уведомления."""
        # Arrange
        test_data = {
            "title": "Test Push Notification",
            "body": "This is a test push notification to verify your subscription is working",
            "data": {"test": True, "timestamp": "2024-01-15T12:00:00Z"},
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_to_user = AsyncMock(
                return_value={"success": True, "sent_count": 2, "failed_count": 0}
            )

            response = await api_client.post(
                api_client.url_for("send_test_push_notification"), json=test_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["sent_count"] == 2
        assert data["failed_count"] == 0

    async def test_send_push_notification_to_user(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест отправки push уведомления конкретному пользователю."""
        # Arrange
        notification_data = {
            "user_id": 789,
            "title": "Survey Available",
            "body": "A new survey is available for you to complete",
            "data": {
                "survey_id": "survey_123",
                "category": "surveys",
                "action_url": "/surveys/survey_123",
            },
            "categories": ["surveys"],
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_to_user = AsyncMock(
                return_value={"success": True, "sent_count": 1, "failed_count": 0}
            )

            response = await api_client.post(
                api_client.url_for("send_push_notification_to_user"),
                json=notification_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["sent_count"] == 1

    async def test_send_push_notification_to_all_users(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест отправки push уведомления всем пользователям."""
        # Arrange
        broadcast_data = {
            "title": "Platform Update",
            "body": "The platform has been updated with new features and improvements",
            "data": {
                "update_version": "2.1.0",
                "features": ["new_dashboard", "improved_analytics"],
                "action_url": "/updates/2.1.0",
            },
            "categories": ["announcements"],
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_to_all = AsyncMock(
                return_value={"success": True, "sent_count": 1500, "failed_count": 25}
            )

            response = await api_client.post(
                api_client.url_for("broadcast_push_notification"), json=broadcast_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["sent_count"] == 1500
        assert data["failed_count"] == 25

    async def test_send_push_notification_with_image(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест отправки push уведомления с изображением."""
        # Arrange
        notification_data = {
            "title": "Achievement Unlocked!",
            "body": "Congratulations! You've completed 50 surveys",
            "image": "https://app.com/images/achievements/survey_master_50.png",
            "icon": "https://app.com/images/icons/achievement.png",
            "data": {
                "achievement_id": "survey_master_50",
                "points": 1000,
                "badge": "🏆",
            },
            "categories": ["achievements"],
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_rich_notification = AsyncMock(
                return_value={"success": True, "sent_count": 1, "failed_count": 0}
            )

            response = await api_client.post(
                api_client.url_for("send_rich_push_notification"),
                json=notification_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["sent_count"] == 1

    async def test_send_scheduled_push_notification(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест планирования push уведомления."""
        # Arrange
        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
        notification_data = {
            "title": "Reminder: Complete Weekly Survey",
            "body": "Don't forget to complete your weekly survey before it expires",
            "scheduled_for": future_time,
            "data": {
                "survey_id": "weekly_survey_456",
                "expires_at": "2024-01-20T23:59:59Z",
            },
            "categories": ["reminders"],
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.schedule_notification = AsyncMock(
                return_value={
                    "success": True,
                    "notification_id": "scheduled_789",
                    "scheduled_for": future_time,
                }
            )

            response = await api_client.post(
                api_client.url_for("schedule_push_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["notification_id"] == "scheduled_789"
        assert data["scheduled_for"] == future_time


class TestPushNotificationAnalytics:
    """Позитивные тесты аналитики push уведомлений."""

    async def test_record_notification_analytics(self, api_client: AsyncClient):
        """Тест записи аналитики уведомлений."""
        # Arrange
        analytics_data = {
            "notification_id": "notif_123",
            "event": "delivered",
            "timestamp": "2024-01-15T14:30:00Z",
            "device_info": {"platform": "iOS", "app_version": "1.2.3"},
        }

        # Act
        response = await api_client.post(
            api_client.url_for("record_push_analytics"), json=analytics_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "Аналитика записана" in data["message"]

    async def test_record_notification_click(self, api_client: AsyncClient):
        """Тест записи клика по уведомлению."""
        # Arrange
        click_data = {
            "notification_id": "notif_456",
            "event": "clicked",
            "timestamp": "2024-01-15T14:35:00Z",
            "action": "open_survey",
            "survey_id": "survey_789",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("record_push_click"), json=click_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "Клик записан" in data["message"]

    async def test_get_push_notification_stats(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики push уведомлений."""
        # Arrange
        mock_stats = {
            "total_sent": 5000,
            "total_delivered": 4850,
            "total_clicked": 1200,
            "delivery_rate": 97.0,
            "click_rate": 24.7,
            "by_platform": {
                "iOS": {"sent": 2500, "delivered": 2450, "clicked": 650},
                "Android": {"sent": 2000, "delivered": 1950, "clicked": 480},
                "Web": {"sent": 500, "delivered": 450, "clicked": 70},
            },
            "by_category": {
                "surveys": {"sent": 3000, "clicked": 800},
                "reminders": {"sent": 1500, "clicked": 300},
                "announcements": {"sent": 500, "clicked": 100},
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_analytics_stats = AsyncMock(return_value=mock_stats)

            response = await api_client.get(
                api_client.url_for("get_push_notification_stats"),
                params={"period": "30d"},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_sent"] == 5000
        assert data["delivery_rate"] == 97.0
        assert data["click_rate"] == 24.7
        assert "by_platform" in data
        assert "by_category" in data
        assert data["by_platform"]["iOS"]["sent"] == 2500

    async def test_get_notification_performance_metrics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения метрик производительности уведомлений."""
        # Arrange
        mock_metrics = {
            "avg_delivery_time_ms": 850,
            "success_rate": 98.5,
            "error_rate": 1.5,
            "peak_sending_hour": 14,
            "best_performing_category": "surveys",
            "device_preferences": {
                "iOS": {"open_rate": 25.2},
                "Android": {"open_rate": 23.8},
                "Web": {"open_rate": 18.5},
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_performance_metrics = AsyncMock(return_value=mock_metrics)

            response = await api_client.get(
                api_client.url_for("get_push_performance_metrics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["avg_delivery_time_ms"] == 850
        assert data["success_rate"] == 98.5
        assert data["best_performing_category"] == "surveys"
        assert data["device_preferences"]["iOS"]["open_rate"] == 25.2

    async def test_get_user_notification_history(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения истории push уведомлений пользователя."""
        # Arrange
        mock_history = [
            {
                "id": "push_1",
                "title": "Survey Available",
                "body": "New survey available",
                "sent_at": "2024-01-15T10:00:00Z",
                "delivered_at": "2024-01-15T10:00:02Z",
                "clicked_at": "2024-01-15T10:05:30Z",
                "category": "surveys",
            },
            {
                "id": "push_2",
                "title": "Reminder",
                "body": "Survey reminder",
                "sent_at": "2024-01-14T15:00:00Z",
                "delivered_at": "2024-01-14T15:00:01Z",
                "clicked_at": None,
                "category": "reminders",
            },
        ]

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_user_notification_history = AsyncMock(
                return_value=mock_history
            )

            response = await api_client.get(
                api_client.url_for("get_user_push_history"), params={"limit": 10}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert data[0]["title"] == "Survey Available"
        assert data[0]["clicked_at"] is not None
        assert data[1]["clicked_at"] is None


class TestPushNotificationMaintenance:
    """Позитивные тесты обслуживания push уведомлений."""

    async def test_cleanup_expired_subscriptions(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест очистки истекших подписок."""
        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.cleanup_expired = AsyncMock(
                return_value={"removed_count": 45}
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("cleanup_expired_push_subscriptions")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["removed_count"] == 45
        assert "expired subscriptions removed" in data["message"]

    async def test_validate_push_subscriptions(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест валидации push подписок."""
        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.validate_subscriptions = AsyncMock(
                return_value={
                    "valid_count": 980,
                    "invalid_count": 20,
                    "total_checked": 1000,
                }
            )

            response = await api_client.post(
                api_client.url_for("validate_push_subscriptions")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["valid_count"] == 980
        assert data["invalid_count"] == 20
        assert data["total_checked"] == 1000

    async def test_refresh_vapid_keys(self, api_client: AsyncClient, admin_user):
        """Тест обновления VAPID ключей."""
        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.refresh_vapid_keys = AsyncMock(
                return_value={
                    "success": True,
                    "new_public_key": "BNew_vapid_public_key",
                    "updated_at": "2024-01-15T16:00:00Z",
                }
            )

            response = await api_client.post(api_client.url_for("refresh_vapid_keys"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["new_public_key"] == "BNew_vapid_public_key"
        assert "VAPID keys refreshed" in data["message"]
