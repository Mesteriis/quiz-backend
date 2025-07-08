"""
Негативные тесты для ошибок уведомлений.

Этот модуль содержит все негативные сценарии:
- Ошибки аутентификации и авторизации
- Ошибки валидации данных
- Ошибки сервисов и инфраструктуры
- Ошибки доступа к ресурсам
- Обработка исключений
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory


class TestAuthenticationErrors:
    """Негативные тесты ошибок аутентификации."""

    async def test_send_notification_requires_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что отправка уведомления требует аутентификации."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "This should fail without auth",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert (
            "authentication" in data["detail"].lower()
            or "unauthorized" in data["detail"].lower()
        )

    async def test_get_user_notifications_requires_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что получение уведомлений требует аутентификации."""
        # Act
        response = await api_client.get(
            api_client.url_for("get_user_notifications", user_id=123)
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert (
            "authentication" in data["detail"].lower()
            or "unauthorized" in data["detail"].lower()
        )

    async def test_broadcast_notification_requires_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что broadcast требует аутентификации."""
        # Arrange
        broadcast_data = {
            "type": "announcement",
            "title": "Test Broadcast",
            "message": "This should fail without auth",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("broadcast_notification"), json=broadcast_data
        )

        # Assert
        assert response.status_code == 401

    async def test_notification_stats_requires_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что статистика требует аутентификации."""
        # Act
        response = await api_client.get(
            api_client.url_for("get_notification_statistics")
        )

        # Assert
        assert response.status_code == 401

    async def test_invalid_token_authentication(self, api_client: AsyncClient):
        """Тест с невалидным токеном."""
        # Arrange
        invalid_headers = {"Authorization": "Bearer invalid_token_123"}
        notification_data = {
            "type": "system_message",
            "title": "Test",
            "message": "Test message",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("send_notification"),
            json=notification_data,
            headers=invalid_headers,
        )

        # Assert
        assert response.status_code == 401

    async def test_expired_token_authentication(self, api_client: AsyncClient):
        """Тест с истекшим токеном."""
        # Arrange
        expired_headers = {"Authorization": "Bearer expired_token_456"}
        notification_data = {
            "type": "system_message",
            "title": "Test",
            "message": "Test message",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("send_notification"),
            json=notification_data,
            headers=expired_headers,
        )

        # Assert
        assert response.status_code == 401


class TestAuthorizationErrors:
    """Негативные тесты ошибок авторизации."""

    async def test_admin_notification_requires_admin_access(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что админ уведомления требуют админ права."""
        # Arrange
        notification_data = {
            "type": "admin_alert",
            "title": "Admin Alert",
            "message": "This requires admin access",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "forbidden" in data["detail"].lower()
        )

    async def test_broadcast_notification_requires_admin_access(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что broadcast требует админ права."""
        # Arrange
        broadcast_data = {
            "type": "announcement",
            "title": "Platform Update",
            "message": "This requires admin access",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("broadcast_notification"), json=broadcast_data
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "forbidden" in data["detail"].lower()
        )

    async def test_notification_stats_requires_admin_access(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что статистика требует админ права."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_notification_statistics")
        )

        # Assert
        assert response.status_code == 403

    async def test_access_other_user_notifications_forbidden(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что доступ к чужим уведомлениям запрещен."""
        # Arrange
        other_user_id = 999

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_user_notifications", user_id=other_user_id)
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "access" in data["detail"].lower() or "forbidden" in data["detail"].lower()
        )

    async def test_clear_other_user_notifications_forbidden(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест что очистка чужих уведомлений запрещена."""
        # Arrange
        other_user_id = 999

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("clear_user_notifications", user_id=other_user_id)
        )

        # Assert
        assert response.status_code == 403

    async def test_inactive_user_access_denied(
        self, api_client: AsyncClient, inactive_user
    ):
        """Тест что неактивный пользователь не может отправлять уведомления."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=inactive_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "inactive" in data["detail"].lower()
            or "access denied" in data["detail"].lower()
        )


class TestValidationErrors:
    """Негативные тесты ошибок валидации."""

    async def test_empty_notification_type(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест с пустым типом уведомления."""
        # Arrange
        notification_data = {
            "type": "",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "type" in str(data["detail"]).lower()

    async def test_empty_notification_title(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест с пустым заголовком."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "title" in str(data["detail"]).lower()

    async def test_empty_notification_message(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест с пустым сообщением."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "message" in str(data["detail"]).lower()

    async def test_invalid_notification_type(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест с невалидным типом уведомления."""
        # Arrange
        notification_data = {
            "type": "invalid_type_123",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "type" in str(data["detail"]).lower()

    async def test_invalid_channels(self, api_client: AsyncClient, verified_user):
        """Тест с невалидными каналами."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "channels": ["invalid_channel", "another_invalid"],
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "channel" in str(data["detail"]).lower()

    async def test_too_long_notification_title(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест со слишком длинным заголовком."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "A" * 300,  # Слишком длинный заголовок
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "title" in str(data["detail"]).lower()
            or "length" in str(data["detail"]).lower()
        )

    async def test_too_long_notification_message(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест со слишком длинным сообщением."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "B" * 5000,  # Слишком длинное сообщение
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "message" in str(data["detail"]).lower()
            or "length" in str(data["detail"]).lower()
        )

    async def test_malformed_json_payload(self, api_client: AsyncClient, verified_user):
        """Тест с некорректным JSON."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"),
            content="invalid json content",
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422

    async def test_missing_required_fields(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест с отсутствующими обязательными полями."""
        # Arrange
        notification_data = {
            "title": "Test Notification"
            # Отсутствуют type и message
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "type" in str(data["detail"]).lower()
            or "message" in str(data["detail"]).lower()
        )

    async def test_invalid_user_id_format(self, api_client: AsyncClient, verified_user):
        """Тест с невалидным форматом user_id."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "user_id": "invalid_user_id",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "user_id" in str(data["detail"]).lower()


class TestServiceErrors:
    """Негативные тесты ошибок сервисов."""

    async def test_notification_service_unavailable(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест недоступности сервиса уведомлений."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_service.side_effect = Exception("Service unavailable")

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "service" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_notification_service_timeout(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест таймаута сервиса."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                side_effect=TimeoutError("Service timeout")
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "timeout" in data["detail"].lower() or "error" in data["detail"].lower()

    async def test_notification_service_connection_error(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест ошибки подключения к сервису."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                side_effect=ConnectionError("Connection failed")
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert (
            "connection" in data["detail"].lower() or "error" in data["detail"].lower()
        )

    async def test_notification_service_partial_failure(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест частичной ошибки сервиса."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "channels": ["websocket", "email", "push"],
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={
                    "success": False,
                    "results": {"websocket": True, "email": False, "push": False},
                    "errors": ["Email service down", "Push service timeout"],
                }
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "partial" in data["detail"].lower() or "failed" in data["detail"].lower()

    async def test_database_connection_error(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест ошибки подключения к базе данных."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500

    async def test_rate_limit_exceeded(self, api_client: AsyncClient, verified_user):
        """Тест превышения лимита запросов."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500 or response.status_code == 429


class TestResourceErrors:
    """Негативные тесты ошибок ресурсов."""

    async def test_notification_not_found(self, api_client: AsyncClient, verified_user):
        """Тест поиска несуществующего уведомления."""
        # Arrange
        notification_id = "non_existent_notification_123"

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_notification", notification_id=notification_id)
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_user_not_found(self, api_client: AsyncClient, admin_user):
        """Тест отправки уведомления несуществующему пользователю."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "user_id": 999999,  # Несуществующий пользователь
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert (
            "user" in data["detail"].lower() and "not found" in data["detail"].lower()
        )

    async def test_channel_not_available(self, api_client: AsyncClient, verified_user):
        """Тест с недоступным каналом."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "channels": ["sms"],  # Канал может быть недоступен
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                side_effect=Exception("SMS channel not available")
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert (
            "channel" in data["detail"].lower()
            or "not available" in data["detail"].lower()
        )

    async def test_storage_quota_exceeded(self, api_client: AsyncClient, verified_user):
        """Тест превышения квоты хранения."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                side_effect=Exception("Storage quota exceeded")
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "storage" in data["detail"].lower() or "quota" in data["detail"].lower()

    async def test_notification_history_not_found(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения истории несуществующего пользователя."""
        # Arrange
        non_existent_user_id = 999999

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_user_notifications", user_id=non_existent_user_id)
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert (
            "user" in data["detail"].lower() and "not found" in data["detail"].lower()
        )


class TestSecurityErrors:
    """Негативные тесты ошибок безопасности."""

    async def test_xss_in_notification_title(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест XSS в заголовке уведомления."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "<script>alert('xss')</script>",
            "message": "Test message",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "invalid" in data["detail"].lower() or "malicious" in data["detail"].lower()
        )

    async def test_sql_injection_in_notification_data(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест SQL инъекции в данных уведомления."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "data": {"malicious_field": "'; DROP TABLE users; --"},
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "invalid" in data["detail"].lower() or "malicious" in data["detail"].lower()
        )

    async def test_html_injection_in_message(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест HTML инъекции в сообщении."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "<iframe src='javascript:alert(1)'></iframe>",
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422

    async def test_suspicious_url_in_notification_data(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест подозрительных URL в данных."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "data": {"redirect_url": "javascript:alert('malicious')"},
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422

    async def test_excessive_payload_size(self, api_client: AsyncClient, verified_user):
        """Тест чрезмерного размера данных."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "Test message",
            "data": {
                "large_field": "A" * 1000000  # Очень большое поле
            },
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.post(
            api_client.url_for("send_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422 or response.status_code == 413
        data = response.json()
        assert "size" in data["detail"].lower() or "too large" in data["detail"].lower()
