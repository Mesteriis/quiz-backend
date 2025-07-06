"""
Тесты для Notifications API роутера Quiz App.

Этот модуль содержит тесты для всех уведомлений endpoints,
включая WebSocket соединения и управление уведомлениями.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from tests.factories.user_factory import UserFactory
import pytest_asyncio


class TestNotificationsSending:
    """Тесты для отправки уведомлений."""


    async def test_send_notification_success(
        self, api_client, auth_headers, db_session
    ):
        """Тест успешной отправки уведомления."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        notification_data = {
            "type": "system_message",
            "title": "Test Notification",
            "message": "This is a test notification",
            "user_id": user.id,
            "channels": ["websocket"],
            "data": {"extra_info": "test"},
        }

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_post(
                "/api/notifications/send", headers=headers, json=notification_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "notification_id" in data
            assert data["results"]["websocket"] is True

            # Проверяем что сервис был вызван
            mock_notification_service.send_notification.assert_called_once()


    async def test_send_notification_admin_only_type(
        self, api_client, auth_headers, db_session
    ):
        """Тест отправки уведомлений требующих админ права."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create(is_admin=False)

        headers = await auth_headers(user)

        notification_data = {
            "type": "admin_alert",
            "title": "Admin Alert",
            "message": "This requires admin access",
            "user_id": user.id,
        }

        response = await api_client.auth_post(
            "/api/notifications/send", headers=headers, json=notification_data
        )

        assert response.status_code == 403
        assert "admin access required" in response.json()["detail"].lower()


    async def test_send_notification_admin_access(
        self, api_client, admin_headers, db_session
    ):
        """Тест отправки админ уведомлений администратором."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        notification_data = {
            "type": "admin_alert",
            "title": "Admin Alert",
            "message": "This is an admin alert",
            "user_id": user.id,
        }

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"all": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_post(
                "/api/notifications/send", headers=admin_headers, json=notification_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


    async def test_send_notification_requires_auth(self, api_client):
        """Тест что отправка уведомлений требует авторизацию."""
        notification_data = {
            "type": "system_message",
            "title": "Test",
            "message": "Test message",
        }

        response = await api_client.post(
            "/api/notifications/send", json=notification_data
        )

        assert response.status_code == 401


    async def test_send_notification_service_error(
        self, api_client, auth_headers, db_session
    ):
        """Тест обработки ошибки сервиса уведомлений."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        notification_data = {
            "type": "system_message",
            "title": "Test",
            "message": "Test message",
        }

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_service.side_effect = Exception("Service error")

            response = await api_client.auth_post(
                "/api/notifications/send", headers=headers, json=notification_data
            )

            assert response.status_code == 500
            assert "failed to send" in response.json()["detail"].lower()


class TestNotificationHistory:
    """Тесты для получения истории уведомлений."""


    async def test_get_user_notifications_own_history(
        self, api_client, auth_headers, db_session
    ):
        """Тест получения собственной истории уведомлений."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        # Мокируем уведомления
        mock_notifications = [
            {
                "id": "1",
                "type": "system_message",
                "title": "Test 1",
                "message": "Message 1",
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "2",
                "type": "survey_completed",
                "title": "Test 2",
                "message": "Message 2",
                "created_at": "2024-01-02T00:00:00Z",
            },
        ]

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_obj = MagicMock()
            mock_notification_obj.to_dict.return_value = mock_notifications[0]
            mock_notification_service.get_user_notifications.return_value = [
                mock_notification_obj
            ]
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_get(
                f"/api/notifications/history/{user.id}", headers=headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "notifications" in data
            assert "total" in data
            assert len(data["notifications"]) >= 0
            assert data["total"] >= 0

            # Проверяем что сервис был вызван с правильными параметрами
            mock_notification_service.get_user_notifications.assert_called_once_with(
                user.id, 50
            )


    async def test_get_user_notifications_admin_access(
        self, api_client, admin_headers, db_session
    ):
        """Тест получения истории уведомлений администратором."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_user_notifications.return_value = []
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_get(
                f"/api/notifications/history/{user.id}", headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "notifications" in data


    async def test_get_user_notifications_forbidden_other_user(
        self, api_client, auth_headers, db_session
    ):
        """Тест что пользователь не может получить историю другого пользователя."""
        user_factory = UserFactory(db_session)
        user1 = await user_factory.create()
        user2 = await user_factory.create()

        headers = await auth_headers(user1)

        response = await api_client.auth_get(
            f"/api/notifications/history/{user2.id}", headers=headers
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()


    async def test_get_user_notifications_with_limit(
        self, api_client, auth_headers, db_session
    ):
        """Тест получения истории с лимитом."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_user_notifications.return_value = []
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_get(
                f"/api/notifications/history/{user.id}?limit=10", headers=headers
            )

            assert response.status_code == 200

            # Проверяем что лимит был передан
            mock_notification_service.get_user_notifications.assert_called_once_with(
                user.id, 10
            )


    async def test_get_user_notifications_requires_auth(self, api_client, db_session):
        """Тест что получение истории требует авторизацию."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        response = await api_client.get(f"/api/notifications/history/{user.id}")

        assert response.status_code == 401


class TestNotificationStats:
    """Тесты для получения статистики уведомлений."""


    async def test_get_notification_stats_success(self, api_client, admin_headers):
        """Тест успешного получения статистики уведомлений."""
        mock_stats = {
            "total_notifications": 150,
            "notifications_by_type": {
                "system_message": 50,
                "survey_completed": 30,
                "admin_alert": 20,
            },
            "notifications_by_channel": {"websocket": 80, "email": 40, "telegram": 30},
            "active_connections": 15,
            "notification_rate": 12.5,
        }

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.get_notification_stats.return_value = mock_stats
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_get(
                "/api/notifications/stats", headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total_notifications"] == 150
            assert "notifications_by_type" in data
            assert "notifications_by_channel" in data
            assert data["active_connections"] == 15


    async def test_get_notification_stats_requires_admin(
        self, api_client, auth_headers, regular_user
    ):
        """Тест что получение статистики требует админ права."""
        headers = await auth_headers(regular_user)

        response = await api_client.auth_get(
            "/api/notifications/stats", headers=headers
        )

        assert response.status_code == 403
        assert "admin access required" in response.json()["detail"].lower()


    async def test_get_notification_stats_requires_auth(self, api_client):
        """Тест что получение статистики требует авторизацию."""
        response = await api_client.get("/api/notifications/stats")

        assert response.status_code == 401


class TestNotificationBroadcast:
    """Тесты для трансляции уведомлений."""


    async def test_broadcast_notification_success(self, api_client, admin_headers):
        """Тест успешной трансляции уведомления."""
        notification_data = {
            "type": "system_message",
            "title": "System Maintenance",
            "message": "System will be down for maintenance",
            "channels": ["all"],
            "data": {"priority": "high"},
        }

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True, "email": True, "telegram": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_post(
                "/api/notifications/broadcast",
                headers=admin_headers,
                json=notification_data,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "notification_id" in data
            assert data["results"]["websocket"] is True
            assert data["results"]["email"] is True
            assert data["results"]["telegram"] is True


    async def test_broadcast_notification_requires_admin(
        self, api_client, auth_headers, regular_user
    ):
        """Тест что трансляция требует админ права."""
        headers = await auth_headers(regular_user)

        notification_data = {
            "type": "system_message",
            "title": "System Maintenance",
            "message": "System will be down for maintenance",
        }

        response = await api_client.auth_post(
            "/api/notifications/broadcast", headers=headers, json=notification_data
        )

        assert response.status_code == 403
        assert "admin access required" in response.json()["detail"].lower()


    async def test_broadcast_notification_requires_auth(self, api_client):
        """Тест что трансляция требует авторизацию."""
        notification_data = {
            "type": "system_message",
            "title": "System Maintenance",
            "message": "System will be down for maintenance",
        }

        response = await api_client.post(
            "/api/notifications/broadcast", json=notification_data
        )

        assert response.status_code == 401


class TestNotificationManagement:
    """Тесты для управления уведомлениями."""


    async def test_clear_user_notifications_own(
        self, api_client, auth_headers, db_session
    ):
        """Тест очистки собственных уведомлений."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.clear_user_notifications = AsyncMock(
                return_value=True
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_delete(
                f"/api/notifications/clear/{user.id}", headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "cleared" in data["message"].lower()


    async def test_clear_user_notifications_admin_access(
        self, api_client, admin_headers, db_session
    ):
        """Тест очистки уведомлений администратором."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.clear_user_notifications = AsyncMock(
                return_value=True
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_delete(
                f"/api/notifications/clear/{user.id}", headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


    async def test_clear_user_notifications_forbidden_other_user(
        self, api_client, auth_headers, db_session
    ):
        """Тест что пользователь не может очистить уведомления другого пользователя."""
        user_factory = UserFactory(db_session)
        user1 = await user_factory.create()
        user2 = await user_factory.create()

        headers = await auth_headers(user1)

        response = await api_client.auth_delete(
            f"/api/notifications/clear/{user2.id}", headers=headers
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()


    async def test_get_notification_channels(self, api_client):
        """Тест получения доступных каналов уведомлений."""
        response = await api_client.get("/api/notifications/channels")

        assert response.status_code == 200
        data = response.json()

        assert "channels" in data
        assert isinstance(data["channels"], list)

        # Проверяем что есть основные каналы
        channels = data["channels"]
        assert "websocket" in channels
        assert "email" in channels
        assert "telegram" in channels


    async def test_test_notification_success(
        self, api_client, auth_headers, db_session
    ):
        """Тест отправки тестового уведомления."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True}
            )
            mock_service.return_value = mock_notification_service

            response = await api_client.auth_post(
                "/api/notifications/test?channel=websocket", headers=headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "test" in data["message"].lower()


    async def test_test_notification_requires_auth(self, api_client):
        """Тест что тестовое уведомление требует авторизацию."""
        response = await api_client.post("/api/notifications/test")

        assert response.status_code == 401


class TestNotificationIntegration:
    """Интеграционные тесты для уведомлений."""


    async def test_complete_notification_flow(
        self, api_client, auth_headers, admin_headers, db_session
    ):
        """Тест полного цикла работы с уведомлениями."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"websocket": True}
            )
            mock_notification_service.get_user_notifications = MagicMock(
                return_value=[]
            )
            mock_notification_service.clear_user_notifications = AsyncMock(
                return_value=True
            )
            mock_service.return_value = mock_notification_service

            # 1. Отправляем уведомление
            notification_data = {
                "type": "system_message",
                "title": "Integration Test",
                "message": "This is integration test notification",
                "user_id": user.id,
            }

            response = await api_client.auth_post(
                "/api/notifications/send", headers=headers, json=notification_data
            )

            assert response.status_code == 200
            assert response.json()["success"] is True

            # 2. Получаем историю уведомлений
            response = await api_client.auth_get(
                f"/api/notifications/history/{user.id}", headers=headers
            )

            assert response.status_code == 200
            assert "notifications" in response.json()

            # 3. Отправляем тестовое уведомление
            response = await api_client.auth_post(
                "/api/notifications/test?channel=websocket", headers=headers
            )

            assert response.status_code == 200
            assert response.json()["success"] is True

            # 4. Очищаем уведомления
            response = await api_client.auth_delete(
                f"/api/notifications/clear/{user.id}", headers=headers
            )

            assert response.status_code == 200
            assert response.json()["success"] is True


    async def test_admin_notification_flow(self, api_client, admin_headers, db_session):
        """Тест полного цикла админских уведомлений."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        mock_stats = {
            "total_notifications": 100,
            "active_connections": 5,
            "notification_rate": 10.0,
        }

        with patch(
            "services.realtime_notifications.get_notification_service"
        ) as mock_service:
            mock_notification_service = MagicMock()
            mock_notification_service.send_notification = AsyncMock(
                return_value={"all": True}
            )
            mock_notification_service.get_notification_stats = MagicMock(
                return_value=mock_stats
            )
            mock_service.return_value = mock_notification_service

            # 1. Получаем статистику
            response = await api_client.auth_get(
                "/api/notifications/stats", headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_notifications"] == 100

            # 2. Отправляем админ уведомление
            notification_data = {
                "type": "admin_alert",
                "title": "Admin Alert",
                "message": "System alert message",
                "user_id": user.id,
            }

            response = await api_client.auth_post(
                "/api/notifications/send", headers=admin_headers, json=notification_data
            )

            assert response.status_code == 200
            assert response.json()["success"] is True

            # 3. Транслируем уведомление всем
            broadcast_data = {
                "type": "system_message",
                "title": "System Broadcast",
                "message": "System maintenance scheduled",
                "channels": ["all"],
            }

            response = await api_client.auth_post(
                "/api/notifications/broadcast",
                headers=admin_headers,
                json=broadcast_data,
            )

            assert response.status_code == 200
            assert response.json()["success"] is True

            # Проверяем что все сервисы были вызваны
            assert mock_notification_service.send_notification.call_count == 2
            mock_notification_service.get_notification_stats.assert_called_once()
