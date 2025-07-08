"""
Позитивные тесты для realtime уведомлений.

Этот модуль содержит все успешные сценарии работы с WebSocket уведомлениями:
- Отправка различных типов уведомлений
- Получение истории уведомлений
- Статистика уведомлений
- Broadcast сообщения
- Управление уведомлениями
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory


class TestNotificationSending:
    """Позитивные тесты отправки уведомлений."""

    async def test_send_system_notification_success(
        self, api_client: AsyncClient, verified_user, async_session
    ):
        """Тест успешной отправки системного уведомления."""
        # Arrange
        notification_data = {
            "type": "system_message",
            "title": "System Update",
            "message": "The system has been updated successfully",
            "user_id": verified_user.id,
            "channels": ["websocket"],
            "data": {"update_version": "1.2.3"},
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True, "notification_id": "notif_123"}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "notification_id" in data
        assert data["results"]["websocket"] is True
        mock_notification_service.send_notification.assert_called_once()

    async def test_send_survey_notification_success(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки уведомления о завершении опроса."""
        # Arrange
        notification_data = {
            "type": "survey_completed",
            "title": "Survey Completed",
            "message": "Thank you for completing the customer satisfaction survey",
            "user_id": verified_user.id,
            "channels": ["websocket", "email"],
            "data": {
                "survey_id": "survey_456",
                "completion_time": "2024-01-15T14:30:00Z",
                "score": 85,
            },
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True, "email": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["results"]["websocket"] is True
        assert data["results"]["email"] is True

    async def test_send_reminder_notification_success(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки напоминания."""
        # Arrange
        notification_data = {
            "type": "reminder",
            "title": "Survey Reminder",
            "message": "Don't forget to complete your weekly survey",
            "user_id": verified_user.id,
            "channels": ["websocket", "push"],
            "data": {
                "reminder_type": "weekly_survey",
                "due_date": "2024-01-20T23:59:59Z",
                "survey_link": "https://app.com/surveys/weekly",
            },
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True, "push": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["results"]["websocket"] is True
        assert data["results"]["push"] is True

    async def test_send_achievement_notification_success(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки уведомления о достижении."""
        # Arrange
        notification_data = {
            "type": "achievement_unlocked",
            "title": "Achievement Unlocked!",
            "message": "Congratulations! You've completed 10 surveys this month",
            "user_id": verified_user.id,
            "channels": ["websocket", "push"],
            "data": {
                "achievement_id": "survey_master_10",
                "badge_icon": "🏆",
                "points_earned": 500,
                "next_milestone": 25,
            },
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True, "push": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["achievement_id"] == "survey_master_10"
        assert data["data"]["points_earned"] == 500

    async def test_send_multiple_channel_notification(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отправки уведомления через несколько каналов."""
        # Arrange
        notification_data = {
            "type": "multi_channel_test",
            "title": "Multi-Channel Test",
            "message": "Testing notification delivery across all channels",
            "user_id": verified_user.id,
            "channels": ["websocket", "email", "sms", "push"],
            "data": {"test_id": "multi_test_789"},
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={
                    "websocket": True,
                    "email": True,
                    "sms": False,  # SMS может быть недоступен
                    "push": True,
                }
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("send_notification"), json=notification_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["results"]["websocket"] is True
        assert data["results"]["email"] is True
        assert data["results"]["push"] is True
        # SMS может не сработать, но это не ошибка
        assert "sms" in data["results"]


class TestNotificationHistory:
    """Позитивные тесты получения истории уведомлений."""

    async def test_get_user_notifications_success(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения истории уведомлений пользователя."""
        # Arrange
        mock_notifications = [
            {
                "id": "notif_1",
                "type": "system_message",
                "title": "Welcome",
                "message": "Welcome to our platform!",
                "created_at": "2024-01-15T10:00:00Z",
                "read": False,
                "data": {"welcome_bonus": 100},
            },
            {
                "id": "notif_2",
                "type": "survey_completed",
                "title": "Survey Complete",
                "message": "Thank you for your feedback",
                "created_at": "2024-01-14T15:30:00Z",
                "read": True,
                "data": {"survey_id": "survey_123"},
            },
        ]

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notifications_obj = [MagicMock() for _ in mock_notifications]
            for i, notif_obj in enumerate(mock_notifications_obj):
                notif_obj.to_dict.return_value = mock_notifications[i]

            mock_notification_service.get_user_notifications.return_value = (
                mock_notifications_obj
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_user_notifications", user_id=verified_user.id)
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert data[0]["id"] == "notif_1"
        assert data[0]["read"] is False
        assert data[1]["id"] == "notif_2"
        assert data[1]["read"] is True

    async def test_get_user_notifications_with_pagination(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения уведомлений с пагинацией."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_user_notifications.return_value = []
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_user_notifications", user_id=verified_user.id),
                params={"limit": 10, "offset": 0},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_user_notifications_with_type_filter(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения уведомлений с фильтром по типу."""
        # Arrange
        survey_notifications = [
            {
                "id": "notif_survey_1",
                "type": "survey_completed",
                "title": "Survey 1 Complete",
                "message": "Survey completed successfully",
                "created_at": "2024-01-15T12:00:00Z",
            }
        ]

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notifications_obj = [MagicMock()]
            mock_notifications_obj[0].to_dict.return_value = survey_notifications[0]
            mock_notification_service.get_user_notifications.return_value = (
                mock_notifications_obj
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_user_notifications", user_id=verified_user.id),
                params={"type": "survey_completed"},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["type"] == "survey_completed"

    async def test_get_user_notifications_unread_only(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения только непрочитанных уведомлений."""
        # Arrange
        unread_notifications = [
            {
                "id": "notif_unread_1",
                "type": "reminder",
                "title": "Survey Reminder",
                "message": "Please complete your survey",
                "created_at": "2024-01-15T18:00:00Z",
                "read": False,
            }
        ]

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notifications_obj = [MagicMock()]
            mock_notifications_obj[0].to_dict.return_value = unread_notifications[0]
            mock_notification_service.get_user_notifications.return_value = (
                mock_notifications_obj
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for("get_user_notifications", user_id=verified_user.id),
                params={"unread_only": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["read"] is False

    async def test_mark_notification_as_read(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отметки уведомления как прочитанного."""
        # Arrange
        notification_id = "notif_123"

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.mark_as_read = AsyncMock(return_value=True)
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for(
                    "mark_notification_read", notification_id=notification_id
                )
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "marked as read" in data["message"]
        mock_notification_service.mark_as_read.assert_called_once_with(
            notification_id, verified_user.id
        )


class TestNotificationBroadcast:
    """Позитивные тесты broadcast уведомлений."""

    async def test_broadcast_announcement_success(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест broadcast объявления всем пользователям."""
        # Arrange
        broadcast_data = {
            "type": "announcement",
            "title": "Platform Maintenance",
            "message": "The platform will be under maintenance tomorrow from 2-4 AM UTC",
            "channels": ["websocket", "email"],
            "data": {
                "maintenance_start": "2024-01-16T02:00:00Z",
                "maintenance_end": "2024-01-16T04:00:00Z",
                "affected_services": ["surveys", "analytics"],
            },
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.broadcast_notification = AsyncMock(
                return_value={"sent_count": 1250, "failed_count": 5}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("broadcast_notification"), json=broadcast_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["sent_count"] == 1250
        assert data["failed_count"] == 5
        assert "broadcast sent" in data["message"]

    async def test_broadcast_targeted_announcement(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест broadcast с таргетингом по пользователям."""
        # Arrange
        broadcast_data = {
            "type": "targeted_announcement",
            "title": "Premium Feature Available",
            "message": "New premium features are now available for your account",
            "channels": ["websocket", "push"],
            "target_criteria": {"user_type": "premium", "active_in_days": 30},
            "data": {"feature_list": ["advanced_analytics", "custom_themes"]},
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.broadcast_notification = AsyncMock(
                return_value={"sent_count": 340, "failed_count": 2}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("broadcast_notification"), json=broadcast_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["sent_count"] == 340
        assert data["failed_count"] == 2

    async def test_schedule_broadcast_notification(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест планирования broadcast уведомления."""
        # Arrange
        future_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"
        broadcast_data = {
            "type": "scheduled_announcement",
            "title": "Weekly Survey Available",
            "message": "Your weekly survey is now available",
            "channels": ["websocket", "email", "push"],
            "scheduled_for": future_time,
            "data": {"survey_id": "weekly_survey_123"},
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.schedule_broadcast = AsyncMock(
                return_value={
                    "broadcast_id": "broadcast_456",
                    "scheduled_for": future_time,
                }
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("schedule_broadcast"), json=broadcast_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["broadcast_id"] == "broadcast_456"
        assert data["scheduled_for"] == future_time


class TestNotificationManagement:
    """Позитивные тесты управления уведомлениями."""

    async def test_clear_user_notifications_success(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест очистки уведомлений пользователя."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.clear_user_notifications = AsyncMock(
                return_value={"cleared_count": 15}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("clear_user_notifications", user_id=verified_user.id)
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["cleared_count"] == 15
        assert "notifications cleared" in data["message"]

    async def test_mark_all_notifications_read(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест отметки всех уведомлений как прочитанных."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.mark_all_as_read = AsyncMock(
                return_value={"marked_count": 8}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for(
                    "mark_all_notifications_read", user_id=verified_user.id
                )
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["marked_count"] == 8

    async def test_get_notification_channels(self, api_client: AsyncClient):
        """Тест получения доступных каналов уведомлений."""
        # Act
        response = await api_client.get(api_client.url_for("get_notification_channels"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "channels" in data
        assert isinstance(data["channels"], list)
        expected_channels = ["websocket", "email", "sms", "push"]
        for channel in expected_channels:
            assert channel in data["channels"]

    async def test_test_notification_delivery(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест проверки доставки уведомлений."""
        # Arrange
        test_data = {"channel": "websocket", "message": "Test notification delivery"}

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.test_delivery = AsyncMock(
                return_value={"success": True, "latency_ms": 45}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.post(
                api_client.url_for("test_notification"), json=test_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["latency_ms"] == 45
        assert "test notification sent" in data["message"]

    async def test_get_notification_preferences(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения настроек уведомлений пользователя."""
        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_user_preferences = AsyncMock(
                return_value={
                    "channels": {
                        "websocket": True,
                        "email": True,
                        "sms": False,
                        "push": True,
                    },
                    "types": {
                        "system_message": True,
                        "survey_completed": True,
                        "reminder": True,
                        "achievement_unlocked": True,
                    },
                }
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.get(
                api_client.url_for(
                    "get_notification_preferences", user_id=verified_user.id
                )
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "channels" in data
        assert "types" in data
        assert data["channels"]["websocket"] is True
        assert data["channels"]["sms"] is False
        assert data["types"]["system_message"] is True

    async def test_update_notification_preferences(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест обновления настроек уведомлений."""
        # Arrange
        preferences_data = {
            "channels": {"websocket": True, "email": False, "sms": False, "push": True},
            "types": {
                "system_message": True,
                "survey_completed": True,
                "reminder": False,
                "achievement_unlocked": True,
            },
        }

        # Act
        api_client.force_authenticate(user=verified_user)
        with patch(
            "src.services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.update_user_preferences = AsyncMock(
                return_value={"updated": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.put(
                api_client.url_for(
                    "update_notification_preferences", user_id=verified_user.id
                ),
                json=preferences_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "preferences updated" in data["message"]
