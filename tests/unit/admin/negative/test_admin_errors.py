"""
Негативные тесты для Admin API.

Этот модуль содержит тесты для ошибочных сценариев админ интерфейса:
- Ошибки авторизации и доступа
- Ошибки валидации данных
- Ошибки сервисов и ресурсов
- Ошибки безопасности
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch


class TestAdminAuthorizationErrors:
    """Негативные тесты ошибок авторизации."""

    async def test_dashboard_requires_authentication(self, api_client: AsyncClient):
        """Тест что дашборд требует аутентификации."""
        # Act
        response = await api_client.get(api_client.url_for("get_admin_dashboard"))

        # Assert
        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()

    async def test_dashboard_requires_admin_role(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что дашборд требует админ роль."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(api_client.url_for("get_admin_dashboard"))

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_survey_management_requires_admin(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что управление опросами требует админ права."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(api_client.url_for("get_all_admin_surveys"))

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_user_management_requires_admin(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что управление пользователями требует админ права."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(api_client.url_for("get_all_admin_users"))

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_system_settings_requires_admin(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что системные настройки требуют админ права."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(api_client.url_for("get_system_settings"))

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_expired_token_access(self, api_client: AsyncClient, admin_user):
        """Тест доступа с истекшим токеном."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Simulate expired token
        with patch("src.routers.admin.verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token expired")

            # Act
            response = await api_client.get(api_client.url_for("get_admin_dashboard"))

            # Assert
            assert response.status_code == 401
            assert "token" in response.json()["detail"].lower()


class TestAdminValidationErrors:
    """Негативные тесты ошибок валидации."""

    async def test_create_survey_invalid_data(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест создания опроса с невалидными данными."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.post(
            api_client.url_for("create_admin_survey"),
            json={"title": ""},  # Пустое название
        )

        # Assert
        assert response.status_code == 422
        assert "validation" in response.json()["detail"][0]["type"]

    async def test_update_survey_invalid_id(self, api_client: AsyncClient, admin_user):
        """Тест обновления опроса с невалидным ID."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.put(
            api_client.url_for("update_admin_survey", survey_id="invalid"),
            json={"title": "Updated Title"},
        )

        # Assert
        assert response.status_code == 422
        assert "validation" in response.json()["detail"][0]["type"]

    async def test_bulk_operation_empty_ids(self, api_client: AsyncClient, admin_user):
        """Тест массовой операции с пустым списком ID."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.post(
            api_client.url_for("bulk_update_admin_surveys"),
            json={"survey_ids": [], "updates": {"is_active": True}},
        )

        # Assert
        assert response.status_code == 422
        assert "validation" in response.json()["detail"][0]["type"]

    async def test_update_user_role_invalid_permissions(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест обновления роли с невалидными правами."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.patch(
            api_client.url_for("update_user_role", user_id=1),
            json={"permissions": ["invalid_permission"]},
        )

        # Assert
        assert response.status_code == 422
        assert "validation" in response.json()["detail"][0]["type"]

    async def test_system_settings_invalid_config(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест обновления системных настроек с невалидной конфигурацией."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.patch(
            api_client.url_for("update_system_settings"),
            json={"security": {"password_min_length": -1}},  # Невалидная длина
        )

        # Assert
        assert response.status_code == 422
        assert "validation" in response.json()["detail"][0]["type"]


class TestAdminResourceErrors:
    """Негативные тесты ошибок ресурсов."""

    async def test_survey_not_found(self, api_client: AsyncClient, admin_user):
        """Тест получения несуществующего опроса."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_survey_by_id = AsyncMock(return_value=None)
            mock_service.return_value = mock_survey_service

            response = await api_client.get(
                api_client.url_for("get_admin_survey", survey_id=99999)
            )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_user_not_found(self, api_client: AsyncClient, admin_user):
        """Тест получения несуществующего пользователя."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.get_user_by_id = AsyncMock(return_value=None)
            mock_service.return_value = mock_user_service

            response = await api_client.get(
                api_client.url_for("get_admin_user", user_id=99999)
            )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_non_existent_survey(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест удаления несуществующего опроса."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.delete_survey = AsyncMock(
                side_effect=Exception("Survey not found")
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.delete(
                api_client.url_for("delete_admin_survey", survey_id=99999)
            )

        # Assert
        assert response.status_code == 404

    async def test_update_non_existent_user(self, api_client: AsyncClient, admin_user):
        """Тест обновления несуществующего пользователя."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.update_user_role = AsyncMock(
                side_effect=Exception("User not found")
            )
            mock_service.return_value = mock_user_service

            response = await api_client.patch(
                api_client.url_for("update_user_role", user_id=99999),
                json={"is_admin": True},
            )

        # Assert
        assert response.status_code == 404


class TestAdminServiceErrors:
    """Негативные тесты ошибок сервисов."""

    async def test_dashboard_service_error(self, api_client: AsyncClient, admin_user):
        """Тест ошибки сервиса дашборда."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.get_dashboard_data = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.get(api_client.url_for("get_admin_dashboard"))

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()

    async def test_survey_service_timeout(self, api_client: AsyncClient, admin_user):
        """Тест таймаута сервиса опросов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_all_surveys = AsyncMock(
                side_effect=TimeoutError("Service timeout")
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.get(api_client.url_for("get_all_admin_surveys"))

        # Assert
        assert response.status_code == 504
        assert "timeout" in response.json()["detail"].lower()

    async def test_user_service_unavailable(self, api_client: AsyncClient, admin_user):
        """Тест недоступности сервиса пользователей."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_user_service") as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.get_user_analytics = AsyncMock(
                side_effect=ConnectionError("Service unavailable")
            )
            mock_service.return_value = mock_user_service

            response = await api_client.get(api_client.url_for("get_user_analytics"))

        # Assert
        assert response.status_code == 503
        assert "service unavailable" in response.json()["detail"].lower()

    async def test_system_service_error(self, api_client: AsyncClient, admin_user):
        """Тест ошибки системного сервиса."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_system_service") as mock_service:
            mock_system_service = MagicMock()
            mock_system_service.get_system_health = AsyncMock(
                side_effect=Exception("System monitoring failed")
            )
            mock_service.return_value = mock_system_service

            response = await api_client.get(api_client.url_for("get_system_health"))

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()

    async def test_backup_service_error(self, api_client: AsyncClient, admin_user):
        """Тест ошибки сервиса резервного копирования."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_backup_service") as mock_service:
            mock_backup_service = MagicMock()
            mock_backup_service.create_backup = AsyncMock(
                side_effect=Exception("Backup failed")
            )
            mock_service.return_value = mock_backup_service

            response = await api_client.post(
                api_client.url_for("create_system_backup"),
                json={"include_data": ["surveys"]},
            )

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()


class TestAdminSecurityErrors:
    """Негативные тесты ошибок безопасности."""

    async def test_rate_limiting_exceeded(self, api_client: AsyncClient, admin_user):
        """Тест превышения лимита запросов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.check_rate_limit") as mock_rate_limit:
            mock_rate_limit.side_effect = Exception("Rate limit exceeded")

            response = await api_client.get(api_client.url_for("get_admin_dashboard"))

        # Assert
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()

    async def test_sql_injection_attempt(self, api_client: AsyncClient, admin_user):
        """Тест попытки SQL инъекции."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.get(
            api_client.url_for("get_all_admin_surveys"),
            params={"search": "'; DROP TABLE surveys; --"},
        )

        # Assert
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_xss_attempt(self, api_client: AsyncClient, admin_user):
        """Тест попытки XSS атаки."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.post(
            api_client.url_for("create_admin_survey"),
            json={"title": "<script>alert('xss')</script>"},
        )

        # Assert
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_path_traversal_attempt(self, api_client: AsyncClient, admin_user):
        """Тест попытки path traversal."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.get(
            api_client.url_for("get_system_logs"),
            params={"file_path": "../../../etc/passwd"},
        )

        # Assert
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_command_injection_attempt(self, api_client: AsyncClient, admin_user):
        """Тест попытки command injection."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.post(
            api_client.url_for("create_system_backup"),
            json={"backup_name": "backup; rm -rf /"},
        )

        # Assert
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_unauthorized_bulk_operation(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест неавторизованной массовой операции."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.post(
            api_client.url_for("bulk_delete_admin_surveys"),
            json={"survey_ids": [1, 2, 3]},
        )

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_insufficient_permissions(self, api_client: AsyncClient, admin_user):
        """Тест недостаточных прав доступа."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.check_permissions") as mock_permissions:
            mock_permissions.return_value = False

            response = await api_client.delete(
                api_client.url_for("delete_admin_survey", survey_id=1)
            )

        # Assert
        assert response.status_code == 403
        assert "insufficient" in response.json()["detail"].lower()


class TestAdminDataErrors:
    """Негативные тесты ошибок данных."""

    async def test_corrupted_data_error(self, api_client: AsyncClient, admin_user):
        """Тест ошибки поврежденных данных."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_survey_analytics = AsyncMock(
                side_effect=Exception("Corrupted data detected")
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.get(
                api_client.url_for("get_admin_survey_analytics", survey_id=1)
            )

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()

    async def test_data_integrity_violation(self, api_client: AsyncClient, admin_user):
        """Тест нарушения целостности данных."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.update_survey = AsyncMock(
                side_effect=Exception("Data integrity violation")
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.put(
                api_client.url_for("update_admin_survey", survey_id=1),
                json={"title": "Updated Title"},
            )

        # Assert
        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()

    async def test_export_data_too_large(self, api_client: AsyncClient, admin_user):
        """Тест экспорта слишком больших данных."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_admin_service") as mock_service:
            mock_admin_service = MagicMock()
            mock_admin_service.export_dashboard_data = AsyncMock(
                side_effect=Exception("Export data too large")
            )
            mock_service.return_value = mock_admin_service

            response = await api_client.post(
                api_client.url_for("export_dashboard_data"),
                json={"format": "csv", "include_all": True},
            )

        # Assert
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    async def test_concurrent_modification_error(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест ошибки конкурентного изменения."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_system_service") as mock_service:
            mock_system_service = MagicMock()
            mock_system_service.update_system_settings = AsyncMock(
                side_effect=Exception("Concurrent modification detected")
            )
            mock_service.return_value = mock_system_service

            response = await api_client.patch(
                api_client.url_for("update_system_settings"),
                json={"general": {"site_name": "New Name"}},
            )

        # Assert
        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()
