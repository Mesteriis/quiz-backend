"""
Тесты для Telegram API роутера Quiz App.

Этот модуль содержит тесты для всех Telegram bot endpoints,
включая управление webhook, отправку уведомлений и статус бота.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest_asyncio


class TestTelegramWebhook:
    """Тесты для управления webhook."""


    async def test_get_webhook_info_success(self, api_client, mock_telegram_service):
        """Тест успешного получения информации о webhook."""
        # Настраиваем mock для webhook info
        mock_webhook_info = MagicMock()
        mock_webhook_info.url = "https://example.com/webhook"
        mock_webhook_info.has_custom_certificate = False
        mock_webhook_info.pending_update_count = 0
        mock_webhook_info.last_error_date = None
        mock_webhook_info.last_error_message = None
        mock_webhook_info.max_connections = 40
        mock_webhook_info.allowed_updates = ["message", "callback_query"]
        mock_webhook_info.ip_address = "127.0.0.1"

        mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info

        response = await api_client.get("/api/telegram/webhook/info")

        assert response.status_code == 200
        data = response.json()

        assert data["url"] == "https://example.com/webhook"
        assert data["has_custom_certificate"] is False
        assert data["pending_update_count"] == 0
        assert data["max_connections"] == 40
        assert data["allowed_updates"] == ["message", "callback_query"]
        assert data["ip_address"] == "127.0.0.1"

        mock_telegram_service.bot.get_webhook_info.assert_called_once()


    async def test_get_webhook_info_bot_not_initialized(
        self, api_client, mock_telegram_service
    ):
        """Тест получения информации когда бот не инициализирован."""
        mock_telegram_service.bot = None

        response = await api_client.get("/api/telegram/webhook/info")

        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"].lower()


    async def test_get_webhook_info_service_error(
        self, api_client, mock_telegram_service
    ):
        """Тест обработки ошибки сервиса."""
        mock_telegram_service.bot.get_webhook_info.side_effect = Exception(
            "Service error"
        )

        response = await api_client.get("/api/telegram/webhook/info")

        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()


    async def test_set_webhook_success(self, api_client, mock_telegram_service):
        """Тест успешной установки webhook."""
        mock_telegram_service.bot.set_webhook.return_value = True

        webhook_data = {"url": "https://example.com/webhook/telegram"}

        response = await api_client.post("/api/telegram/webhook/set", json=webhook_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "successfully" in data["message"].lower()

        mock_telegram_service.bot.set_webhook.assert_called_once_with(
            url="https://example.com/webhook/telegram",
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=True,
        )


    async def test_set_webhook_no_url(self, api_client, mock_telegram_service):
        """Тест установки webhook без URL."""
        webhook_data = {}

        response = await api_client.post("/api/telegram/webhook/set", json=webhook_data)

        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()


    async def test_set_webhook_failure(self, api_client, mock_telegram_service):
        """Тест неуспешной установки webhook."""
        mock_telegram_service.bot.set_webhook.return_value = False

        webhook_data = {"url": "https://example.com/webhook/telegram"}

        response = await api_client.post("/api/telegram/webhook/set", json=webhook_data)

        assert response.status_code == 500
        assert "failed to set" in response.json()["detail"].lower()


    async def test_delete_webhook_success(self, api_client, mock_telegram_service):
        """Тест успешного удаления webhook."""
        mock_telegram_service.bot.delete_webhook.return_value = True

        response = await api_client.post("/api/telegram/webhook/delete")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "deleted" in data["message"].lower()

        mock_telegram_service.bot.delete_webhook.assert_called_once_with(
            drop_pending_updates=True
        )


    async def test_delete_webhook_failure(self, api_client, mock_telegram_service):
        """Тест неуспешного удаления webhook."""
        mock_telegram_service.bot.delete_webhook.return_value = False

        response = await api_client.post("/api/telegram/webhook/delete")

        assert response.status_code == 500
        assert "failed to delete" in response.json()["detail"].lower()


class TestTelegramWebhookHandler:
    """Тесты для обработки webhook обновлений."""


    async def test_webhook_handler_success(
        self, api_client, mock_telegram_service, test_settings
    ):
        """Тест успешной обработки webhook обновления."""
        # Настраиваем mock для диспетчера
        mock_telegram_service.dp = MagicMock()
        mock_telegram_service.dp.feed_update = AsyncMock()

        # Данные обновления от Telegram
        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "is_bot": False, "first_name": "Test User"},
                "text": "/start",
            },
        }

        response = await api_client.post(
            f"/api/telegram/webhook/{test_settings.telegram_bot_token}",
            json=update_data,
        )

        assert response.status_code == 200

        # Проверяем что диспетчер был вызван
        mock_telegram_service.dp.feed_update.assert_called_once()
        args = mock_telegram_service.dp.feed_update.call_args[0]
        assert args[0] == mock_telegram_service.bot  # bot instance
        # args[1] - это Update object


    async def test_webhook_handler_invalid_token(
        self, api_client, mock_telegram_service
    ):
        """Тест обработки с неверным токеном."""
        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "is_bot": False, "first_name": "Test User"},
                "text": "/start",
            },
        }

        response = await api_client.post(
            "/api/telegram/webhook/invalid-token", json=update_data
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


    async def test_webhook_handler_bot_not_initialized(
        self, api_client, mock_telegram_service, test_settings
    ):
        """Тест обработки когда бот не инициализирован."""
        mock_telegram_service.bot = None

        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "is_bot": False, "first_name": "Test User"},
                "text": "/start",
            },
        }

        response = await api_client.post(
            f"/api/telegram/webhook/{test_settings.telegram_bot_token}",
            json=update_data,
        )

        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"].lower()


    async def test_webhook_handler_dispatcher_error(
        self, api_client, mock_telegram_service, test_settings
    ):
        """Тест обработки ошибки диспетчера."""
        mock_telegram_service.dp = MagicMock()
        mock_telegram_service.dp.feed_update = AsyncMock(
            side_effect=Exception("Dispatcher error")
        )

        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "is_bot": False, "first_name": "Test User"},
                "text": "/start",
            },
        }

        response = await api_client.post(
            f"/api/telegram/webhook/{test_settings.telegram_bot_token}",
            json=update_data,
        )

        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()


class TestTelegramStatus:
    """Тесты для получения статуса бота."""


    async def test_get_bot_status_success(self, api_client, mock_telegram_service):
        """Тест успешного получения статуса бота."""
        # Настраиваем mock для bot info
        mock_bot_info = MagicMock()
        mock_bot_info.id = 123456789
        mock_bot_info.username = "quiz_bot"
        mock_bot_info.first_name = "Quiz Bot"
        mock_bot_info.is_bot = True
        mock_bot_info.can_join_groups = True
        mock_bot_info.can_read_all_group_messages = False
        mock_bot_info.supports_inline_queries = True

        mock_telegram_service.bot.get_me.return_value = mock_bot_info

        # Настраиваем mock для webhook info
        mock_webhook_info = MagicMock()
        mock_webhook_info.url = "https://example.com/webhook"
        mock_webhook_info.pending_update_count = 0
        mock_webhook_info.last_error_date = None
        mock_webhook_info.last_error_message = None

        mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info

        response = await api_client.get("/api/telegram/status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "active"
        assert "running" in data["message"].lower()

        # Проверяем bot info
        bot_info = data["bot_info"]
        assert bot_info["id"] == 123456789
        assert bot_info["username"] == "quiz_bot"
        assert bot_info["first_name"] == "Quiz Bot"
        assert bot_info["is_bot"] is True
        assert bot_info["can_join_groups"] is True
        assert bot_info["supports_inline_queries"] is True

        # Проверяем webhook info
        webhook_info = data["webhook_info"]
        assert webhook_info["url"] == "https://example.com/webhook"
        assert webhook_info["pending_update_count"] == 0


    async def test_get_bot_status_not_initialized(
        self, api_client, mock_telegram_service
    ):
        """Тест получения статуса когда бот не инициализирован."""
        mock_telegram_service.bot = None

        response = await api_client.get("/api/telegram/status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "not_initialized"
        assert "not initialized" in data["message"].lower()
        assert data["bot_info"] is None
        assert data["webhook_info"] is None


    async def test_get_bot_status_service_error(
        self, api_client, mock_telegram_service
    ):
        """Тест обработки ошибки получения статуса."""
        mock_telegram_service.bot.get_me.side_effect = Exception("Service error")

        response = await api_client.get("/api/telegram/status")

        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()


class TestTelegramNotifications:
    """Тесты для отправки уведомлений через Telegram."""


    async def test_send_notification_success(self, api_client, mock_telegram_service):
        """Тест успешной отправки уведомления."""
        mock_telegram_service.send_notification = AsyncMock(return_value=True)

        notification_data = {
            "user_id": 123456789,
            "message": "Test notification",
            "parse_mode": "HTML",
        }

        response = await api_client.post(
            "/api/telegram/send-notification", json=notification_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "sent" in data["message"].lower()

        mock_telegram_service.send_notification.assert_called_once_with(
            user_id=123456789, message="Test notification", parse_mode="HTML"
        )


    async def test_send_notification_missing_data(
        self, api_client, mock_telegram_service
    ):
        """Тест отправки уведомления с неполными данными."""
        notification_data = {
            "message": "Test notification"
            # Нет user_id
        }

        response = await api_client.post(
            "/api/telegram/send-notification", json=notification_data
        )

        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()


    async def test_send_notification_failure(self, api_client, mock_telegram_service):
        """Тест неуспешной отправки уведомления."""
        mock_telegram_service.send_notification = AsyncMock(return_value=False)

        notification_data = {"user_id": 123456789, "message": "Test notification"}

        response = await api_client.post(
            "/api/telegram/send-notification", json=notification_data
        )

        assert response.status_code == 500
        assert "failed to send" in response.json()["detail"].lower()


    async def test_send_admin_notification_success(
        self, api_client, mock_telegram_service, admin_headers
    ):
        """Тест успешной отправки уведомления администраторам."""
        mock_telegram_service.send_admin_notification = AsyncMock(return_value=True)

        notification_data = {"message": "Admin notification", "alert_type": "critical"}

        response = await api_client.auth_post(
            "/api/telegram/send-admin-notification",
            headers=admin_headers,
            json=notification_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "sent" in data["message"].lower()

        mock_telegram_service.send_admin_notification.assert_called_once_with(
            message="Admin notification", alert_type="critical"
        )


    async def test_send_admin_notification_requires_admin(
        self, api_client, auth_headers, regular_user
    ):
        """Тест что отправка админ уведомлений требует админ права."""
        headers = await auth_headers(regular_user)

        notification_data = {"message": "Admin notification"}

        response = await api_client.auth_post(
            "/api/telegram/send-admin-notification",
            headers=headers,
            json=notification_data,
        )

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()


    async def test_send_admin_notification_requires_auth(self, api_client):
        """Тест что отправка админ уведомлений требует авторизацию."""
        notification_data = {"message": "Admin notification"}

        response = await api_client.post(
            "/api/telegram/send-admin-notification", json=notification_data
        )

        assert response.status_code == 401


class TestTelegramSecurity:
    """Тесты для безопасности Telegram интеграции."""


    async def test_get_security_stats(self, api_client):
        """Тест получения статистики безопасности."""
        response = await api_client.get("/api/telegram/security/stats")

        assert response.status_code == 200
        data = response.json()

        # Проверяем что возвращается информация о безопасности
        assert "middleware_status" in data
        assert "rate_limiting" in data
        assert "ip_whitelisting" in data
        assert "request_validation" in data
        assert "security_headers" in data
        assert "webhook_logging" in data

        # Проверяем что статусы являются строками
        assert isinstance(data["middleware_status"], str)
        assert isinstance(data["rate_limiting"], str)
        assert isinstance(data["ip_whitelisting"], str)


    async def test_health_check(self, api_client):
        """Тест проверки здоровья Telegram сервиса."""
        response = await api_client.get("/api/telegram/health")

        assert response.status_code == 200
        data = response.json()

        # Проверяем базовую структуру ответа
        assert "status" in data
        assert "timestamp" in data
        assert "telegram_service" in data

        # Статус должен быть positive
        assert data["status"] in ["ok", "healthy", "operational"]
        assert data["telegram_service"] in ["available", "operational", "active"]


class TestTelegramIntegration:
    """Интеграционные тесты для Telegram функций."""


    async def test_complete_webhook_management_flow(
        self, api_client, mock_telegram_service
    ):
        """Тест полного цикла управления webhook."""
        # Настраиваем mocks
        mock_telegram_service.bot.set_webhook.return_value = True
        mock_telegram_service.bot.delete_webhook.return_value = True

        mock_webhook_info = MagicMock()
        mock_webhook_info.url = ""
        mock_webhook_info.pending_update_count = 0
        mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info

        # 1. Проверяем начальный статус
        response = await api_client.get("/api/telegram/webhook/info")
        assert response.status_code == 200
        assert response.json()["url"] == ""

        # 2. Устанавливаем webhook
        webhook_data = {"url": "https://example.com/webhook"}
        response = await api_client.post("/api/telegram/webhook/set", json=webhook_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # 3. Проверяем что webhook установлен
        mock_webhook_info.url = "https://example.com/webhook"
        response = await api_client.get("/api/telegram/webhook/info")
        assert response.status_code == 200
        assert response.json()["url"] == "https://example.com/webhook"

        # 4. Удаляем webhook
        response = await api_client.post("/api/telegram/webhook/delete")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # 5. Проверяем что webhook удален
        mock_webhook_info.url = ""
        response = await api_client.get("/api/telegram/webhook/info")
        assert response.status_code == 200
        assert response.json()["url"] == ""


    async def test_bot_status_and_notifications_flow(
        self, api_client, mock_telegram_service, admin_headers
    ):
        """Тест полного цикла статуса бота и уведомлений."""
        # Настраиваем mocks для статуса бота
        mock_bot_info = MagicMock()
        mock_bot_info.id = 123456789
        mock_bot_info.username = "quiz_bot"
        mock_bot_info.first_name = "Quiz Bot"
        mock_bot_info.is_bot = True
        mock_bot_info.can_join_groups = True
        mock_bot_info.can_read_all_group_messages = False
        mock_bot_info.supports_inline_queries = True

        mock_telegram_service.bot.get_me.return_value = mock_bot_info

        mock_webhook_info = MagicMock()
        mock_webhook_info.url = "https://example.com/webhook"
        mock_webhook_info.pending_update_count = 0
        mock_webhook_info.last_error_date = None
        mock_webhook_info.last_error_message = None

        mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info

        # Настраиваем mocks для уведомлений
        mock_telegram_service.send_notification = AsyncMock(return_value=True)
        mock_telegram_service.send_admin_notification = AsyncMock(return_value=True)

        # 1. Проверяем статус бота
        response = await api_client.get("/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["bot_info"]["username"] == "quiz_bot"

        # 2. Отправляем обычное уведомление
        notification_data = {"user_id": 123456789, "message": "Test notification"}
        response = await api_client.post(
            "/api/telegram/send-notification", json=notification_data
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # 3. Отправляем админ уведомление
        admin_notification_data = {
            "message": "Admin notification",
            "alert_type": "info",
        }
        response = await api_client.auth_post(
            "/api/telegram/send-admin-notification",
            headers=admin_headers,
            json=admin_notification_data,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # 4. Проверяем статистику безопасности
        response = await api_client.get("/api/telegram/security/stats")
        assert response.status_code == 200
        data = response.json()
        assert "middleware_status" in data
        assert "rate_limiting" in data

        # 5. Проверяем health check
        response = await api_client.get("/api/telegram/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "healthy", "operational"]

        # Проверяем что все сервисы были вызваны
        mock_telegram_service.send_notification.assert_called_once()
        mock_telegram_service.send_admin_notification.assert_called_once()
