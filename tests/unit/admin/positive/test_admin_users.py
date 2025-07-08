"""
Позитивные тесты для Admin User Management.

Управление пользователями через админ интерфейс:
- Получение списка пользователей с фильтрацией
- Управление ролями и правами доступа
- Массовые операции с пользователями
- Аналитика пользователей
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from tests.factories import UserFactory


class TestAdminUserManagement:
    """Позитивные тесты управления пользователями."""

    async def test_get_all_users_with_details(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения всех пользователей с подробной информацией."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.get_all_users = AsyncMock(
                return_value={
                    "users": [
                        {
                            "id": 1,
                            "username": "john_doe",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john@example.com",
                            "is_active": True,
                            "is_admin": False,
                            "created_at": "2024-01-15T10:00:00Z",
                            "last_login": "2024-01-20T14:30:00Z",
                            "surveys_participated": 5,
                            "responses_submitted": 23,
                            "profile_completion": 0.85,
                            "engagement_score": 0.72,
                        },
                        {
                            "id": 2,
                            "username": "admin_user",
                            "first_name": "Admin",
                            "last_name": "User",
                            "email": "admin@example.com",
                            "is_active": True,
                            "is_admin": True,
                            "created_at": "2024-01-01T00:00:00Z",
                            "last_login": "2024-01-20T16:00:00Z",
                            "surveys_created": 12,
                            "surveys_managed": 25,
                            "admin_actions": 156,
                        },
                    ],
                    "pagination": {
                        "total": 2,
                        "page": 1,
                        "per_page": 10,
                        "total_pages": 1,
                    },
                }
            )
            mock_service.return_value = mock_user_service

            response = await api_client.get(
                api_client.url_for("get_all_admin_users"),
                params={"include_stats": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        users = data["users"]
        assert len(users) == 2

        # Проверяем обычного пользователя
        user1 = users[0]
        assert user1["username"] == "john_doe"
        assert user1["is_admin"] is False
        assert user1["surveys_participated"] == 5
        assert user1["engagement_score"] == 0.72

        # Проверяем админа
        user2 = users[1]
        assert user2["username"] == "admin_user"
        assert user2["is_admin"] is True
        assert user2["surveys_created"] == 12
        assert user2["admin_actions"] == 156

    async def test_update_user_role(self, api_client: AsyncClient, admin_user):
        """Тест обновления роли пользователя."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.update_user_role = AsyncMock(
                return_value={
                    "id": 1,
                    "username": "john_doe",
                    "is_admin": True,
                    "role_updated_at": "2024-01-20T16:30:00Z",
                    "updated_by": "admin",
                    "permissions": [
                        "survey_create",
                        "survey_manage",
                        "user_view",
                        "analytics_view",
                    ],
                }
            )
            mock_service.return_value = mock_user_service

            response = await api_client.patch(
                api_client.url_for("update_user_role", user_id=1),
                json={
                    "is_admin": True,
                    "permissions": ["survey_create", "survey_manage"],
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == 1
        assert data["username"] == "john_doe"
        assert data["is_admin"] is True
        assert len(data["permissions"]) == 4
        assert "survey_create" in data["permissions"]

    async def test_bulk_user_operations(self, api_client: AsyncClient, admin_user):
        """Тест массовых операций с пользователями."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.bulk_update_users = AsyncMock(
                return_value={
                    "success": True,
                    "updated_count": 3,
                    "failed_count": 0,
                    "updated_users": [
                        {"id": 1, "username": "user1", "is_active": False},
                        {"id": 2, "username": "user2", "is_active": False},
                        {"id": 3, "username": "user3", "is_active": False},
                    ],
                }
            )
            mock_service.return_value = mock_user_service

            response = await api_client.post(
                api_client.url_for("bulk_update_users"),
                json={
                    "user_ids": [1, 2, 3],
                    "updates": {"is_active": False},
                    "reason": "Inactive users cleanup",
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["updated_count"] == 3
        assert data["failed_count"] == 0
        assert len(data["updated_users"]) == 3

    async def test_get_user_analytics(self, api_client: AsyncClient, admin_user):
        """Тест получения аналитики пользователей."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.get_user_analytics = AsyncMock(
                return_value={
                    "total_users": 450,
                    "active_users": 367,
                    "admin_users": 5,
                    "new_users_today": 12,
                    "new_users_this_week": 45,
                    "engagement_stats": {
                        "high_engagement": 89,
                        "medium_engagement": 156,
                        "low_engagement": 122,
                        "inactive": 83,
                    },
                    "user_distribution": {
                        "by_age": {"18-25": 89, "26-35": 156, "36-45": 123, "46+": 82},
                        "by_location": {
                            "US": 189,
                            "Europe": 134,
                            "Asia": 78,
                            "Other": 49,
                        },
                    },
                }
            )
            mock_service.return_value = mock_user_service

            response = await api_client.get(api_client.url_for("get_user_analytics"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_users"] == 450
        assert data["active_users"] == 367
        assert data["admin_users"] == 5

        engagement = data["engagement_stats"]
        assert engagement["high_engagement"] == 89
        assert engagement["inactive"] == 83

        distribution = data["user_distribution"]
        assert distribution["by_age"]["26-35"] == 156
        assert distribution["by_location"]["US"] == 189


class TestAdminUserSecurity:
    """Позитивные тесты безопасности пользователей."""

    async def test_get_user_activity_log(self, api_client: AsyncClient, admin_user):
        """Тест получения журнала активности пользователя."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.get_user_activity_log = AsyncMock(
                return_value={
                    "user_id": 1,
                    "username": "john_doe",
                    "activities": [
                        {
                            "id": 1,
                            "action": "login",
                            "timestamp": "2024-01-20T16:30:00Z",
                            "ip_address": "192.168.1.100",
                            "user_agent": "Mozilla/5.0...",
                            "location": "New York, US",
                            "success": True,
                        },
                        {
                            "id": 2,
                            "action": "survey_submitted",
                            "timestamp": "2024-01-20T16:25:00Z",
                            "survey_id": 5,
                            "survey_title": "Customer Feedback",
                            "completion_time": 4.2,
                            "success": True,
                        },
                    ],
                    "summary": {
                        "total_activities": 2,
                        "login_count": 1,
                        "survey_activities": 1,
                        "failed_attempts": 0,
                        "last_activity": "2024-01-20T16:30:00Z",
                    },
                }
            )
            mock_service.return_value = mock_user_service

            response = await api_client.get(
                api_client.url_for("get_user_activity_log", user_id=1)
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == 1
        assert data["username"] == "john_doe"
        assert len(data["activities"]) == 2

        login_activity = data["activities"][0]
        assert login_activity["action"] == "login"
        assert login_activity["success"] is True
        assert login_activity["location"] == "New York, US"

        survey_activity = data["activities"][1]
        assert survey_activity["action"] == "survey_submitted"
        assert survey_activity["completion_time"] == 4.2

        summary = data["summary"]
        assert summary["total_activities"] == 2
        assert summary["failed_attempts"] == 0

    async def test_reset_user_password(self, api_client: AsyncClient, admin_user):
        """Тест сброса пароля пользователя."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.reset_user_password = AsyncMock(
                return_value={
                    "success": True,
                    "user_id": 1,
                    "username": "john_doe",
                    "temporary_password": "temp_pass_123",
                    "password_reset_at": "2024-01-20T16:30:00Z",
                    "expires_at": "2024-01-21T16:30:00Z",
                    "email_sent": True,
                    "email_address": "john@example.com",
                }
            )
            mock_service.return_value = mock_user_service

            response = await api_client.post(
                api_client.url_for("reset_user_password", user_id=1),
                json={
                    "send_email": True,
                    "force_change": True,
                    "reason": "User requested password reset",
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["user_id"] == 1
        assert data["username"] == "john_doe"
        assert data["temporary_password"] == "temp_pass_123"
        assert data["email_sent"] is True
        assert data["email_address"] == "john@example.com"
