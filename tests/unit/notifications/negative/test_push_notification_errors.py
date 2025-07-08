"""
Негативные тесты для ошибок push уведомлений.

Этот модуль содержит все негативные сценарии для push уведомлений:
- Ошибки подписки на push уведомления
- Ошибки VAPID ключей
- Ошибки отправки push уведомлений
- Ошибки валидации данных
- Ошибки внешних сервисов
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory


class TestPushSubscriptionErrors:
    """Негативные тесты ошибок подписки на push уведомления."""

    async def test_push_subscription_requires_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что подписка на push требует аутентификации."""
        # Arrange
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/example",
                "keys": {"p256dh": "example_key", "auth": "example_auth"},
            }
        }

        # Act
        response = await api_client.post(
            api_client.url_for("subscribe_push_notifications"), json=subscription_data
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert (
            "authentication" in data["detail"].lower()
            or "unauthorized" in data["detail"].lower()
        )

    async def test_push_subscription_incomplete_data(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подписки с неполными данными."""
        # Arrange
        incomplete_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/example",
                "keys": {
                    "p256dh": "example_p256dh_key"
                    # Отсутствует auth ключ
                },
            }
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("subscribe_push_notifications"), json=incomplete_data
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert (
            "incomplete" in data["detail"].lower()
            or "missing" in data["detail"].lower()
        )

    async def test_push_subscription_invalid_endpoint(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подписки с невалидным endpoint."""
        # Arrange
        invalid_data = {
            "subscription": {
                "endpoint": "invalid_endpoint_url",
                "keys": {"p256dh": "example_key", "auth": "example_auth"},
            }
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("subscribe_push_notifications"), json=invalid_data
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert (
            "invalid" in data["detail"].lower() or "endpoint" in data["detail"].lower()
        )

    async def test_push_subscription_invalid_keys(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подписки с невалидными ключами."""
        # Arrange
        invalid_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/example",
                "keys": {"p256dh": "invalid_key", "auth": "invalid_auth"},
            }
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.create_subscription = AsyncMock(
                side_effect=ValueError("Invalid subscription keys")
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("subscribe_push_notifications"), json=invalid_data
            )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "keys" in data["detail"].lower()

    async def test_push_subscription_duplicate_endpoint(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подписки с дублирующимся endpoint."""
        # Arrange
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/duplicate_endpoint",
                "keys": {"p256dh": "example_key", "auth": "example_auth"},
            }
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.create_subscription = AsyncMock(
                side_effect=Exception("Duplicate endpoint")
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("subscribe_push_notifications"),
                json=subscription_data,
            )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert (
            "duplicate" in data["detail"].lower()
            or "already exists" in data["detail"].lower()
        )

    async def test_push_subscription_invalid_categories(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подписки с невалидными категориями."""
        # Arrange
        invalid_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/example",
                "keys": {"p256dh": "example_key", "auth": "example_auth"},
            },
            "categories": ["invalid_category", "another_invalid"],
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("subscribe_push_notifications"), json=invalid_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "category" in str(data["detail"]).lower()

    async def test_push_subscription_malformed_json(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подписки с некорректным JSON."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("subscribe_push_notifications"),
            content="invalid json content",
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422

    async def test_push_subscription_service_error(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест ошибки сервиса подписки."""
        # Arrange
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/example",
                "keys": {"p256dh": "example_key", "auth": "example_auth"},
            }
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.create_subscription = AsyncMock(
                side_effect=Exception("Service error")
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("subscribe_push_notifications"),
                json=subscription_data,
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "service" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_get_user_subscriptions_no_subscriptions(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения подписок когда их нет."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.get_user_subscriptions = AsyncMock(return_value=[])
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.get(
                api_client.url_for("get_user_push_subscriptions")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    async def test_unsubscribe_no_subscriptions(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отписки когда нет подписок."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.delete_user_subscriptions = AsyncMock(return_value=0)
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("unsubscribe_push_notifications")
            )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert (
            "no subscriptions" in data["detail"].lower()
            or "not found" in data["detail"].lower()
        )


class TestVapidKeyErrors:
    """Негативные тесты ошибок VAPID ключей."""

    async def test_vapid_key_service_error(self, api_client: AsyncClient):
        """Тест ошибки сервиса VAPID ключей."""
        # Act
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_vapid_public_key.side_effect = Exception("VAPID key error")

            response = await api_client.get(api_client.url_for("get_vapid_public_key"))

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "vapid" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_vapid_key_not_configured(self, api_client: AsyncClient):
        """Тест отсутствия конфигурации VAPID ключей."""
        # Act
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_vapid_public_key.side_effect = Exception(
                "VAPID keys not configured"
            )

            response = await api_client.get(api_client.url_for("get_vapid_public_key"))

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert (
            "configured" in data["detail"].lower() or "vapid" in data["detail"].lower()
        )

    async def test_vapid_key_expired(self, api_client: AsyncClient):
        """Тест истекших VAPID ключей."""
        # Act
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_vapid_public_key.side_effect = Exception(
                "VAPID keys expired"
            )

            response = await api_client.get(api_client.url_for("get_vapid_public_key"))

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "expired" in data["detail"].lower() or "vapid" in data["detail"].lower()

    async def test_vapid_key_invalid_format(self, api_client: AsyncClient):
        """Тест невалидного формата VAPID ключей."""
        # Act
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_vapid_public_key.return_value = "invalid_key_format"

            response = await api_client.get(api_client.url_for("get_vapid_public_key"))

        # Assert - Возможно, это все еще успешный ответ, но с неправильным форматом
        assert response.status_code == 200
        data = response.json()
        # Проверяем что ключ не начинается с "B" как должно быть для VAPID
        assert not data["public_key"].startswith("B")

    async def test_refresh_vapid_keys_requires_admin(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что обновление VAPID ключей требует админ права."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(api_client.url_for("refresh_vapid_keys"))

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "forbidden" in data["detail"].lower()
        )

    async def test_refresh_vapid_keys_service_error(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест ошибки сервиса при обновлении VAPID ключей."""
        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.refresh_vapid_keys = AsyncMock(
                side_effect=Exception("Failed to refresh VAPID keys")
            )

            response = await api_client.post(api_client.url_for("refresh_vapid_keys"))

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "refresh" in data["detail"].lower() or "vapid" in data["detail"].lower()


class TestPushNotificationSendingErrors:
    """Негативные тесты ошибок отправки push уведомлений."""

    async def test_send_push_notification_requires_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что отправка push уведомления требует аутентификации."""
        # Arrange
        notification_data = {"title": "Test Push", "body": "Test message"}

        # Act
        response = await api_client.post(
            api_client.url_for("send_test_push_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 401

    async def test_send_push_notification_no_subscriptions(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки push уведомления без подписок."""
        # Arrange
        notification_data = {"title": "Test Push", "body": "Test message"}

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_to_user = AsyncMock(
                return_value={"success": False, "error": "No subscriptions found"}
            )

            response = await api_client.post(
                api_client.url_for("send_test_push_notification"),
                json=notification_data,
            )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert (
            "no subscriptions" in data["detail"].lower()
            or "not found" in data["detail"].lower()
        )

    async def test_send_push_notification_invalid_data(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки push уведомления с невалидными данными."""
        # Arrange
        invalid_data = {
            "title": "",  # Пустой заголовок
            "body": "A" * 5000,  # Слишком длинное тело
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_test_push_notification"), json=invalid_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "title" in str(data["detail"]).lower()
            or "body" in str(data["detail"]).lower()
        )

    async def test_send_push_notification_service_error(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест ошибки сервиса при отправке push уведомления."""
        # Arrange
        notification_data = {"title": "Test Push", "body": "Test message"}

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_to_user = AsyncMock(
                side_effect=Exception("Push service error")
            )

            response = await api_client.post(
                api_client.url_for("send_test_push_notification"),
                json=notification_data,
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "service" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_send_push_notification_delivery_failure(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест неудачной доставки push уведомления."""
        # Arrange
        notification_data = {"title": "Test Push", "body": "Test message"}

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_to_user = AsyncMock(
                return_value={"success": False, "sent_count": 0, "failed_count": 2}
            )

            response = await api_client.post(
                api_client.url_for("send_test_push_notification"),
                json=notification_data,
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert (
            "delivery" in data["detail"].lower() or "failed" in data["detail"].lower()
        )

    async def test_broadcast_push_notification_requires_admin(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что broadcast push уведомления требует админ права."""
        # Arrange
        broadcast_data = {"title": "Platform Update", "body": "New features available"}

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("broadcast_push_notification"), json=broadcast_data
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "forbidden" in data["detail"].lower()
        )

    async def test_send_push_notification_invalid_image_url(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки push уведомления с невалидным URL изображения."""
        # Arrange
        notification_data = {
            "title": "Test Push",
            "body": "Test message",
            "image": "invalid_image_url",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_rich_push_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "image" in str(data["detail"]).lower()
            or "url" in str(data["detail"]).lower()
        )

    async def test_send_push_notification_too_large_payload(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки push уведомления с слишком большим payload."""
        # Arrange
        notification_data = {
            "title": "Test Push",
            "body": "Test message",
            "data": {
                "large_field": "A" * 10000  # Очень большие данные
            },
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_test_push_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 413 or response.status_code == 422
        data = response.json()
        assert "size" in data["detail"].lower() or "too large" in data["detail"].lower()

    async def test_send_push_notification_invalid_schedule_time(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест планирования push уведомления на прошедшее время."""
        # Arrange
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
        notification_data = {
            "title": "Scheduled Push",
            "body": "This should fail",
            "scheduled_for": past_time,
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.post(
            api_client.url_for("schedule_push_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "schedule" in str(data["detail"]).lower()
            or "past" in str(data["detail"]).lower()
        )

    async def test_send_push_notification_rate_limit_exceeded(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест превышения лимита отправки push уведомлений."""
        # Arrange
        notification_data = {"title": "Test Push", "body": "Test message"}

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.send_to_user = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )

            response = await api_client.post(
                api_client.url_for("send_test_push_notification"),
                json=notification_data,
            )

        # Assert
        assert response.status_code == 429 or response.status_code == 500
        data = response.json()
        assert (
            "rate limit" in data["detail"].lower() or "limit" in data["detail"].lower()
        )


class TestPushNotificationAnalyticsErrors:
    """Негативные тесты ошибок аналитики push уведомлений."""

    async def test_record_push_analytics_invalid_data(self, api_client: AsyncClient):
        """Тест записи аналитики с невалидными данными."""
        # Arrange
        invalid_data = {
            "notification_id": "",  # Пустой ID
            "event": "invalid_event",  # Невалидное событие
            "timestamp": "invalid_timestamp",  # Невалидная дата
        }

        # Act
        response = await api_client.post(
            api_client.url_for("record_push_analytics"), json=invalid_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "notification_id" in str(data["detail"]).lower()
            or "event" in str(data["detail"]).lower()
        )

    async def test_record_push_analytics_service_error(self, api_client: AsyncClient):
        """Тест ошибки сервиса при записи аналитики."""
        # Arrange
        analytics_data = {
            "notification_id": "notif_123",
            "event": "delivered",
            "timestamp": "2024-01-15T14:30:00Z",
        }

        # Act
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.record_analytics = AsyncMock(
                side_effect=Exception("Analytics service error")
            )

            response = await api_client.post(
                api_client.url_for("record_push_analytics"), json=analytics_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "service" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_get_push_notification_stats_requires_admin(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что получение статистики push уведомлений требует админ права."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_push_notification_stats")
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "forbidden" in data["detail"].lower()
        )

    async def test_get_push_notification_stats_service_error(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест ошибки сервиса при получении статистики."""
        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_analytics_stats = AsyncMock(
                side_effect=Exception("Stats service error")
            )

            response = await api_client.get(
                api_client.url_for("get_push_notification_stats")
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "service" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_get_push_notification_stats_invalid_period(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики с невалидным периодом."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("get_push_notification_stats"),
            params={"period": "invalid_period"},
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "period" in str(data["detail"]).lower()

    async def test_get_user_push_history_no_history(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения истории push уведомлений когда её нет."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.get_user_notification_history = AsyncMock(return_value=[])

            response = await api_client.get(api_client.url_for("get_user_push_history"))

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestPushNotificationMaintenanceErrors:
    """Негативные тесты ошибок обслуживания push уведомлений."""

    async def test_cleanup_expired_subscriptions_requires_admin(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что очистка истекших подписок требует админ права."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("cleanup_expired_push_subscriptions")
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "forbidden" in data["detail"].lower()
        )

    async def test_cleanup_expired_subscriptions_service_error(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест ошибки сервиса при очистке истекших подписок."""
        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.routers.push_notifications.get_push_subscription_repository"
        ) as mock_repo:
            mock_subscription_repo = MagicMock()
            mock_subscription_repo.cleanup_expired = AsyncMock(
                side_effect=Exception("Cleanup service error")
            )
            mock_repo.return_value = mock_subscription_repo

            response = await api_client.post(
                api_client.url_for("cleanup_expired_push_subscriptions")
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "service" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_validate_push_subscriptions_requires_admin(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что валидация подписок требует админ права."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("validate_push_subscriptions")
        )

        # Assert
        assert response.status_code == 403

    async def test_validate_push_subscriptions_service_error(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест ошибки сервиса при валидации подписок."""
        # Act
        api_client.force_authenticate(user=admin_user)
        with patch("src.routers.push_notifications.push_service") as mock_service:
            mock_service.validate_subscriptions = AsyncMock(
                side_effect=Exception("Validation service error")
            )

            response = await api_client.post(
                api_client.url_for("validate_push_subscriptions")
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "service" in data["detail"].lower() or "error" in data["detail"].lower()
