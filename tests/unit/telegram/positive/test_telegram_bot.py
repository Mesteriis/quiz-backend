"""
Позитивные тесты для Telegram Bot API.

Этот модуль содержит все успешные сценарии работы с Telegram Bot:
- Управление webhook (получение/установка/удаление)
- Обработка webhook обновлений
- Статус и мониторинг бота
- Отправка уведомлений пользователям
- Административные функции бота
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from tests.factories import UserFactory


class TestTelegramWebhookManagement:
    """Позитивные тесты управления webhook."""

    async def test_get_webhook_info_complete(self, api_client: AsyncClient):
        """Тест получения полной информации о webhook."""
        # Arrange
        mock_webhook_info = MagicMock()
        mock_webhook_info.url = "https://example.com/webhook/telegram"
        mock_webhook_info.has_custom_certificate = False
        mock_webhook_info.pending_update_count = 5
        mock_webhook_info.last_error_date = None
        mock_webhook_info.last_error_message = None
        mock_webhook_info.max_connections = 40
        mock_webhook_info.allowed_updates = [
            "message",
            "callback_query",
            "inline_query",
        ]
        mock_webhook_info.ip_address = "127.0.0.1"
        mock_webhook_info.last_synchronization_error_date = None

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_webhook_info"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["url"] == "https://example.com/webhook/telegram"
        assert data["has_custom_certificate"] is False
        assert data["pending_update_count"] == 5
        assert data["max_connections"] == 40
        assert data["allowed_updates"] == ["message", "callback_query", "inline_query"]
        assert data["ip_address"] == "127.0.0.1"
        assert data["status"] == "active"

    async def test_get_webhook_info_with_errors(self, api_client: AsyncClient):
        """Тест получения информации о webhook с ошибками."""
        # Arrange
        mock_webhook_info = MagicMock()
        mock_webhook_info.url = "https://example.com/webhook/telegram"
        mock_webhook_info.has_custom_certificate = True
        mock_webhook_info.pending_update_count = 0
        mock_webhook_info.last_error_date = 1642680000  # Unix timestamp
        mock_webhook_info.last_error_message = "Connection timeout"
        mock_webhook_info.max_connections = 40
        mock_webhook_info.allowed_updates = ["message", "callback_query"]
        mock_webhook_info.ip_address = "192.168.1.1"
        mock_webhook_info.last_synchronization_error_date = 1642679000

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_webhook_info"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["url"] == "https://example.com/webhook/telegram"
        assert data["has_custom_certificate"] is True
        assert data["last_error_date"] == 1642680000
        assert data["last_error_message"] == "Connection timeout"
        assert data["last_synchronization_error_date"] == 1642679000
        assert data["status"] == "error"

    async def test_set_webhook_success_with_options(self, api_client: AsyncClient):
        """Тест успешной установки webhook с дополнительными опциями."""
        # Arrange
        webhook_data = {
            "url": "https://example.com/webhook/telegram",
            "certificate": None,
            "ip_address": "192.168.1.100",
            "max_connections": 50,
            "allowed_updates": [
                "message",
                "callback_query",
                "inline_query",
                "edited_message",
            ],
            "drop_pending_updates": True,
            "secret_token": "webhook_secret_token_123",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.set_webhook.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("set_webhook"), json=webhook_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "successfully set" in data["message"].lower()
        assert data["webhook_url"] == "https://example.com/webhook/telegram"
        assert data["configuration"]["max_connections"] == 50
        assert data["configuration"]["allowed_updates"] == [
            "message",
            "callback_query",
            "inline_query",
            "edited_message",
        ]

        # Проверяем вызов метода с правильными параметрами
        mock_telegram_service.bot.set_webhook.assert_called_once_with(
            url="https://example.com/webhook/telegram",
            certificate=None,
            ip_address="192.168.1.100",
            max_connections=50,
            allowed_updates=[
                "message",
                "callback_query",
                "inline_query",
                "edited_message",
            ],
            drop_pending_updates=True,
            secret_token="webhook_secret_token_123",
        )

    async def test_set_webhook_minimal_config(self, api_client: AsyncClient):
        """Тест установки webhook с минимальной конфигурацией."""
        # Arrange
        webhook_data = {"url": "https://example.com/webhook"}

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.set_webhook.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("set_webhook"), json=webhook_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["webhook_url"] == "https://example.com/webhook"

        # Проверяем что используются значения по умолчанию
        mock_telegram_service.bot.set_webhook.assert_called_once_with(
            url="https://example.com/webhook",
            certificate=None,
            ip_address=None,
            max_connections=40,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
            secret_token=None,
        )

    async def test_delete_webhook_success_with_cleanup(self, api_client: AsyncClient):
        """Тест успешного удаления webhook с очисткой."""
        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.delete_webhook.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("delete_webhook"),
                json={"drop_pending_updates": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "deleted" in data["message"].lower()
        assert data["dropped_updates"] is True

        mock_telegram_service.bot.delete_webhook.assert_called_once_with(
            drop_pending_updates=True
        )

    async def test_delete_webhook_preserve_updates(self, api_client: AsyncClient):
        """Тест удаления webhook с сохранением обновлений."""
        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.delete_webhook.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("delete_webhook"),
                json={"drop_pending_updates": False},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["dropped_updates"] is False

        mock_telegram_service.bot.delete_webhook.assert_called_once_with(
            drop_pending_updates=False
        )


class TestTelegramWebhookHandler:
    """Позитивные тесты обработки webhook обновлений."""

    async def test_handle_message_update(self, api_client: AsyncClient, test_settings):
        """Тест обработки текстового сообщения."""
        # Arrange
        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1642680000,
                "chat": {
                    "id": 123456789,
                    "type": "private",
                    "first_name": "Test",
                    "last_name": "User",
                },
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                },
                "text": "Hello, bot!",
            },
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock()
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=update_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["update_id"] == 123456
        assert data["update_type"] == "message"

        # Проверяем что диспетчер был вызван
        mock_telegram_service.dp.feed_update.assert_called_once()

    async def test_handle_callback_query_update(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест обработки callback query."""
        # Arrange
        update_data = {
            "update_id": 123457,
            "callback_query": {
                "id": "callback_123",
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "message": {
                    "message_id": 2,
                    "date": 1642680000,
                    "chat": {"id": 123456789, "type": "private"},
                    "text": "Choose an option:",
                },
                "data": "survey_123_start",
            },
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock()
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=update_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["update_id"] == 123457
        assert data["update_type"] == "callback_query"

    async def test_handle_inline_query_update(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест обработки inline query."""
        # Arrange
        update_data = {
            "update_id": 123458,
            "inline_query": {
                "id": "inline_123",
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "query": "search surveys",
                "offset": "",
            },
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock()
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=update_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["update_id"] == 123458
        assert data["update_type"] == "inline_query"

    async def test_handle_edited_message_update(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест обработки отредактированного сообщения."""
        # Arrange
        update_data = {
            "update_id": 123459,
            "edited_message": {
                "message_id": 1,
                "date": 1642680000,
                "edit_date": 1642680060,
                "chat": {"id": 123456789, "type": "private"},
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "text": "Hello, bot! (edited)",
            },
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock()
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=update_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["update_id"] == 123459
        assert data["update_type"] == "edited_message"

    async def test_handle_channel_post_update(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест обработки поста в канале."""
        # Arrange
        update_data = {
            "update_id": 123460,
            "channel_post": {
                "message_id": 10,
                "date": 1642680000,
                "chat": {
                    "id": -1001234567890,
                    "type": "channel",
                    "title": "Test Channel",
                    "username": "testchannel",
                },
                "author_signature": "Admin",
                "text": "New survey available!",
            },
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock()
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=update_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["update_id"] == 123460
        assert data["update_type"] == "channel_post"


class TestTelegramBotStatus:
    """Позитивные тесты статуса бота."""

    async def test_get_bot_status_healthy(self, api_client: AsyncClient):
        """Тест получения здорового статуса бота."""
        # Arrange
        mock_bot_info = MagicMock()
        mock_bot_info.id = 987654321
        mock_bot_info.username = "quiz_bot"
        mock_bot_info.first_name = "Quiz Bot"
        mock_bot_info.can_join_groups = True
        mock_bot_info.can_read_all_group_messages = False
        mock_bot_info.supports_inline_queries = True

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.get_me.return_value = mock_bot_info
            mock_telegram_service.get_bot_status = MagicMock(
                return_value={
                    "status": "online",
                    "uptime": "5d 12h 30m",
                    "last_update": "2024-01-20T10:00:00Z",
                    "webhook_status": "active",
                    "message_count": 1250,
                    "error_count": 0,
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_bot_status"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["bot_info"]["id"] == 987654321
        assert data["bot_info"]["username"] == "quiz_bot"
        assert data["bot_info"]["first_name"] == "Quiz Bot"
        assert data["bot_info"]["can_join_groups"] is True
        assert data["bot_info"]["supports_inline_queries"] is True

        assert data["status"]["status"] == "online"
        assert data["status"]["uptime"] == "5d 12h 30m"
        assert data["status"]["webhook_status"] == "active"
        assert data["status"]["message_count"] == 1250
        assert data["status"]["error_count"] == 0

    async def test_get_bot_status_with_metrics(self, api_client: AsyncClient):
        """Тест получения статуса бота с метриками."""
        # Arrange
        mock_bot_info = MagicMock()
        mock_bot_info.id = 987654321
        mock_bot_info.username = "quiz_bot"
        mock_bot_info.first_name = "Quiz Bot"

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.get_me.return_value = mock_bot_info
            mock_telegram_service.get_bot_status = MagicMock(
                return_value={
                    "status": "online",
                    "uptime": "5d 12h 30m",
                    "metrics": {
                        "messages_today": 350,
                        "unique_users_today": 85,
                        "surveys_created_today": 12,
                        "avg_response_time": 0.08,
                        "error_rate": 0.02,
                    },
                    "performance": {
                        "cpu_usage": 15.5,
                        "memory_usage": 45.2,
                        "active_connections": 25,
                    },
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(
                api_client.url_for("get_bot_status"), params={"include_metrics": True}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"]["status"] == "online"
        assert "metrics" in data["status"]
        assert "performance" in data["status"]

        metrics = data["status"]["metrics"]
        assert metrics["messages_today"] == 350
        assert metrics["unique_users_today"] == 85
        assert metrics["surveys_created_today"] == 12
        assert metrics["avg_response_time"] == 0.08

        performance = data["status"]["performance"]
        assert performance["cpu_usage"] == 15.5
        assert performance["memory_usage"] == 45.2
        assert performance["active_connections"] == 25

    async def test_get_bot_commands_list(self, api_client: AsyncClient):
        """Тест получения списка команд бота."""
        # Arrange
        mock_commands = [
            {"command": "start", "description": "Start using the bot"},
            {"command": "help", "description": "Get help information"},
            {"command": "create", "description": "Create a new survey"},
            {"command": "list", "description": "List your surveys"},
            {"command": "stats", "description": "View survey statistics"},
            {"command": "settings", "description": "Bot settings"},
        ]

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.get_my_commands.return_value = mock_commands
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_bot_commands"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "commands" in data
        assert len(data["commands"]) == 6
        assert data["commands"][0]["command"] == "start"
        assert data["commands"][0]["description"] == "Start using the bot"
        assert data["commands"][2]["command"] == "create"

    async def test_get_bot_health_check(self, api_client: AsyncClient):
        """Тест проверки здоровья бота."""
        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.health_check = AsyncMock(
                return_value={
                    "status": "healthy",
                    "timestamp": "2024-01-20T10:00:00Z",
                    "checks": {
                        "bot_api": True,
                        "webhook": True,
                        "database": True,
                        "redis": True,
                    },
                    "response_time": 0.05,
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("telegram_health_check"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "checks" in data
        assert all(data["checks"].values())  # Все проверки прошли
        assert data["response_time"] == 0.05


class TestTelegramNotifications:
    """Позитивные тесты отправки уведомлений."""

    async def test_send_notification_to_user(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки уведомления конкретному пользователю."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        notification_data = {
            "user_id": regular_user.id,
            "message": "Your survey has received new responses!",
            "type": "info",
            "action_url": "/surveys/123/results",
            "priority": "normal",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                return_value={
                    "success": True,
                    "message_id": 456,
                    "chat_id": 123456789,
                    "delivery_status": "delivered",
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message_id"] == 456
        assert data["chat_id"] == 123456789
        assert data["delivery_status"] == "delivered"

    async def test_send_notification_with_inline_keyboard(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки уведомления с inline клавиатурой."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        notification_data = {
            "user_id": regular_user.id,
            "message": "Survey completed! What would you like to do next?",
            "type": "success",
            "inline_keyboard": [
                [
                    {"text": "View Results", "callback_data": "view_results_123"},
                    {"text": "Share Survey", "callback_data": "share_survey_123"},
                ],
                [{"text": "Create New Survey", "callback_data": "create_new_survey"}],
            ],
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                return_value={
                    "success": True,
                    "message_id": 457,
                    "chat_id": 123456789,
                    "delivery_status": "delivered",
                    "has_inline_keyboard": True,
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["has_inline_keyboard"] is True

    async def test_send_admin_notification(self, api_client: AsyncClient, admin_user):
        """Тест отправки административного уведомления."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        admin_notification_data = {
            "message": "System alert: High load detected",
            "type": "warning",
            "priority": "high",
            "broadcast": True,
            "target_admins": True,
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_admin_notification = AsyncMock(
                return_value={
                    "success": True,
                    "sent_count": 3,
                    "failed_count": 0,
                    "admin_recipients": [111, 222, 333],
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_admin_notification"),
                json=admin_notification_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["sent_count"] == 3
        assert data["failed_count"] == 0
        assert len(data["admin_recipients"]) == 3

    async def test_send_broadcast_notification(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест отправки массового уведомления."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        broadcast_data = {
            "message": "🎉 New feature available: Advanced analytics for your surveys!",
            "type": "announcement",
            "target_audience": "all_users",
            "schedule_time": None,  # Отправить сразу
            "include_unsubscribed": False,
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_broadcast = AsyncMock(
                return_value={
                    "success": True,
                    "total_recipients": 1250,
                    "sent_count": 1205,
                    "failed_count": 45,
                    "broadcast_id": "broadcast_789",
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("send_broadcast_notification"), json=broadcast_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["total_recipients"] == 1250
        assert data["sent_count"] == 1205
        assert data["failed_count"] == 45
        assert data["broadcast_id"] == "broadcast_789"

    async def test_schedule_notification(self, api_client: AsyncClient, admin_user):
        """Тест планирования уведомления."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        scheduled_notification = {
            "message": "Weekly survey reminder",
            "type": "reminder",
            "schedule_time": "2024-01-27T10:00:00Z",
            "target_audience": "active_users",
            "recurrence": "weekly",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.schedule_notification = AsyncMock(
                return_value={
                    "success": True,
                    "scheduled_id": "scheduled_456",
                    "schedule_time": "2024-01-27T10:00:00Z",
                    "estimated_recipients": 950,
                    "status": "scheduled",
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("schedule_telegram_notification"),
                json=scheduled_notification,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["scheduled_id"] == "scheduled_456"
        assert data["schedule_time"] == "2024-01-27T10:00:00Z"
        assert data["estimated_recipients"] == 950
        assert data["status"] == "scheduled"


class TestTelegramBotConfiguration:
    """Позитивные тесты конфигурации бота."""

    async def test_set_bot_commands(self, api_client: AsyncClient, admin_user):
        """Тест установки команд бота."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        commands_data = {
            "commands": [
                {"command": "start", "description": "Start using the bot"},
                {"command": "help", "description": "Get help information"},
                {"command": "create", "description": "Create a new survey"},
                {"command": "list", "description": "List your surveys"},
                {"command": "stats", "description": "View survey statistics"},
                {"command": "settings", "description": "Bot settings"},
                {"command": "support", "description": "Contact support"},
            ],
            "scope": "default",
            "language_code": "en",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.set_my_commands.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("set_bot_commands"), json=commands_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["commands_count"] == 7
        assert "commands updated" in data["message"].lower()

    async def test_set_bot_description(self, api_client: AsyncClient, admin_user):
        """Тест установки описания бота."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        description_data = {
            "description": "🔍 Quiz Bot - Create and manage surveys easily with Telegram integration!",
            "short_description": "Survey creation and management bot",
            "language_code": "en",
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.set_my_description.return_value = True
            mock_telegram_service.bot.set_my_short_description.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("set_bot_description"), json=description_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "description updated" in data["message"].lower()

    async def test_get_bot_configuration(self, api_client: AsyncClient, admin_user):
        """Тест получения конфигурации бота."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.get_bot_configuration = MagicMock(
                return_value={
                    "bot_info": {
                        "username": "quiz_bot",
                        "first_name": "Quiz Bot",
                        "description": "Survey creation and management bot",
                        "short_description": "Quiz Bot",
                    },
                    "commands": [
                        {"command": "start", "description": "Start using the bot"},
                        {"command": "help", "description": "Get help information"},
                    ],
                    "webhook": {
                        "url": "https://example.com/webhook",
                        "max_connections": 40,
                        "allowed_updates": ["message", "callback_query"],
                    },
                    "features": {
                        "inline_queries": True,
                        "group_chat": True,
                        "channel_admin": False,
                    },
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_bot_configuration"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "bot_info" in data
        assert "commands" in data
        assert "webhook" in data
        assert "features" in data

        assert data["bot_info"]["username"] == "quiz_bot"
        assert len(data["commands"]) == 2
        assert data["webhook"]["max_connections"] == 40
        assert data["features"]["inline_queries"] is True
