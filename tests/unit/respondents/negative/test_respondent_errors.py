"""
Негативные тесты для респондентов.

Этот модуль содержит тесты для ошибочных сценариев работы с респондентами:
- Ошибки авторизации и доступа
- Ошибки валидации данных
- Ошибки сервисов и ресурсов
- Ошибки GDPR операций
- Ошибки согласий
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch


class TestRespondentAuthorizationErrors:
    """Негативные тесты ошибок авторизации респондентов."""

    async def test_get_my_respondent_unauthorized(self, api_client: AsyncClient):
        """Тест получения профиля без авторизации."""
        # Act
        response = await api_client.get(api_client.url_for("get_my_respondent"))

        # Assert
        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()

    async def test_search_respondents_requires_admin(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что поиск респондентов требует админ права."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(api_client.url_for("search_respondents"))

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_get_respondent_statistics_forbidden(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что статистика требует админ права."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(api_client.url_for("get_respondent_statistics"))

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_bulk_operations_require_admin(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест что массовые операции требуют админ права."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.post(
            api_client.url_for("bulk_update_respondents"),
            json={"respondent_ids": [1, 2, 3], "updates": {"status": "active"}},
        )

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_expired_token_access(self, api_client: AsyncClient, regular_user):
        """Тест доступа с истекшим токеном."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.respondents.verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token expired")

            response = await api_client.get(api_client.url_for("get_my_respondent"))

        # Assert
        assert response.status_code == 401
        assert "token" in response.json()["detail"].lower()

    async def test_invalid_session_access(self, api_client: AsyncClient):
        """Тест доступа с невалидной сессией."""
        # Act
        response = await api_client.get(
            api_client.url_for("get_activity_summary", respondent_id=1)
        )

        # Assert
        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()


class TestRespondentValidationErrors:
    """Негативные тесты ошибок валидации."""

    async def test_create_respondent_empty_required_fields(
        self, api_client: AsyncClient
    ):
        """Тест создания респондента с пустыми обязательными полями."""
        # Arrange
        invalid_data = {
            "session_id": "",
            "browser_fingerprint": "",
            "anonymous_name": "",
            "anonymous_email": "invalid_email",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("create_or_get_respondent"), json=invalid_data
        )

        # Assert
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("session_id" in str(error) for error in error_detail)
        assert any("browser_fingerprint" in str(error) for error in error_detail)

    async def test_create_respondent_invalid_email(self, api_client: AsyncClient):
        """Тест создания респондента с невалидным email."""
        # Arrange
        invalid_data = {
            "session_id": "test_session",
            "browser_fingerprint": "test_fp",
            "anonymous_name": "Test User",
            "anonymous_email": "not_an_email",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("create_or_get_respondent"), json=invalid_data
        )

        # Assert
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("email" in str(error).lower() for error in error_detail)

    async def test_update_location_invalid_coordinates(self, api_client: AsyncClient):
        """Тест обновления геолокации с невалидными координатами."""
        # Arrange
        respondent_id = 1
        invalid_location = {
            "latitude": 91.0,  # Невалидная широта
            "longitude": -181.0,  # Невалидная долгота
            "accuracy": -10.0,  # Невалидная точность
        }

        # Act
        response = await api_client.patch(
            api_client.url_for(
                "update_respondent_location", respondent_id=respondent_id
            ),
            json=invalid_location,
        )

        # Assert
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("latitude" in str(error).lower() for error in error_detail)
        assert any("longitude" in str(error).lower() for error in error_detail)

    async def test_grant_consent_invalid_type(self, api_client: AsyncClient):
        """Тест выдачи согласия с невалидным типом."""
        # Arrange
        respondent_id = 1
        invalid_consent = {
            "consent_type": "invalid_type",
            "purpose": "unknown_purpose",
            "granted": "not_boolean",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("grant_consent", respondent_id=respondent_id),
            json=invalid_consent,
        )

        # Assert
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("consent_type" in str(error).lower() for error in error_detail)
        assert any("granted" in str(error).lower() for error in error_detail)

    async def test_bulk_operation_empty_ids(self, api_client: AsyncClient, admin_user):
        """Тест массовой операции с пустым списком ID."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.post(
            api_client.url_for("bulk_update_respondents"),
            json={"respondent_ids": [], "updates": {"status": "active"}},
        )

        # Assert
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("respondent_ids" in str(error).lower() for error in error_detail)

    async def test_search_respondents_invalid_filters(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска с невалидными фильтрами."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.get(
            api_client.url_for("search_respondents"),
            params={
                "min_surveys": -1,
                "max_surveys": "not_a_number",
                "created_after": "invalid_date",
                "per_page": 0,
            },
        )

        # Assert
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("min_surveys" in str(error).lower() for error in error_detail)
        assert any("max_surveys" in str(error).lower() for error in error_detail)


class TestRespondentResourceErrors:
    """Негативные тесты ошибок ресурсов."""

    async def test_respondent_not_found(self, api_client: AsyncClient):
        """Тест получения несуществующего респондента."""
        # Arrange
        nonexistent_id = 99999

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_respondent_by_id = AsyncMock(return_value=None)
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_respondent", respondent_id=nonexistent_id)
            )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_activity_summary_not_found(self, api_client: AsyncClient):
        """Тест получения сводки активности несуществующего респондента."""
        # Arrange
        nonexistent_id = 99999

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_activity_summary = AsyncMock(
                side_effect=Exception("Respondent not found")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_activity_summary", respondent_id=nonexistent_id)
            )

        # Assert
        assert response.status_code == 404

    async def test_update_nonexistent_respondent(self, api_client: AsyncClient):
        """Тест обновления несуществующего респондента."""
        # Arrange
        nonexistent_id = 99999
        update_data = {"anonymous_name": "Updated Name"}

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.update_respondent = AsyncMock(
                side_effect=Exception("Respondent not found")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.patch(
                api_client.url_for("update_respondent", respondent_id=nonexistent_id),
                json=update_data,
            )

        # Assert
        assert response.status_code == 404

    async def test_delete_nonexistent_respondent(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест удаления несуществующего респондента."""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        nonexistent_id = 99999

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.delete_respondent = AsyncMock(
                side_effect=Exception("Respondent not found")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.delete(
                api_client.url_for("delete_respondent", respondent_id=nonexistent_id)
            )

        # Assert
        assert response.status_code == 404

    async def test_merge_nonexistent_anonymous_respondent(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест слияния с несуществующим анонимным респондентом."""
        # Arrange
        api_client.force_authenticate(user=regular_user)
        merge_data = {
            "anonymous_session_id": "nonexistent_session",
            "anonymous_fingerprint": "nonexistent_fp",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.merge_respondents = AsyncMock(
                side_effect=Exception("Anonymous respondent not found")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("merge_respondents"), json=merge_data
            )

        # Assert
        assert response.status_code == 404

    async def test_export_nonexistent_respondent_data(self, api_client: AsyncClient):
        """Тест экспорта данных несуществующего респондента."""
        # Arrange
        nonexistent_id = 99999

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                side_effect=Exception("Respondent not found")
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=nonexistent_id
                ),
                json={"format": "json"},
            )

        # Assert
        assert response.status_code == 404


class TestRespondentServiceErrors:
    """Негативные тесты ошибок сервисов."""

    async def test_respondent_service_unavailable(self, api_client: AsyncClient):
        """Тест недоступности сервиса респондентов."""
        # Arrange
        respondent_data = {
            "session_id": "test_session",
            "browser_fingerprint": "test_fp",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                side_effect=ConnectionError("Service unavailable")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 503
        assert "service unavailable" in response.json()["detail"].lower()

    async def test_database_connection_error(self, api_client: AsyncClient):
        """Тест ошибки подключения к базе данных."""
        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_respondent_statistics = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_respondent_statistics")
            )

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()

    async def test_consent_service_timeout(self, api_client: AsyncClient):
        """Тест таймаута сервиса согласий."""
        # Arrange
        respondent_id = 1
        consent_data = {
            "consent_type": "data_processing",
            "purpose": "survey_participation",
            "granted": True,
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.grant_consent = AsyncMock(
                side_effect=TimeoutError("Service timeout")
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("grant_consent", respondent_id=respondent_id),
                json=consent_data,
            )

        # Assert
        assert response.status_code == 504
        assert "timeout" in response.json()["detail"].lower()

    async def test_gdpr_service_error(self, api_client: AsyncClient):
        """Тест ошибки GDPR сервиса."""
        # Arrange
        respondent_id = 1
        export_data = {"format": "json"}

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                side_effect=Exception("GDPR service error")
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=respondent_id
                ),
                json=export_data,
            )

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()

    async def test_analytics_service_failure(self, api_client: AsyncClient, admin_user):
        """Тест сбоя сервиса аналитики."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_engagement_analytics = AsyncMock(
                side_effect=Exception("Analytics service failure")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_engagement_analytics")
            )

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()


class TestRespondentConsentErrors:
    """Негативные тесты ошибок согласий."""

    async def test_grant_consent_already_granted(self, api_client: AsyncClient):
        """Тест выдачи уже выданного согласия."""
        # Arrange
        respondent_id = 1
        consent_data = {
            "consent_type": "data_processing",
            "purpose": "survey_participation",
            "granted": True,
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.grant_consent = AsyncMock(
                side_effect=Exception("Consent already granted")
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("grant_consent", respondent_id=respondent_id),
                json=consent_data,
            )

        # Assert
        assert response.status_code == 409
        assert "already granted" in response.json()["detail"].lower()

    async def test_revoke_nonexistent_consent(self, api_client: AsyncClient):
        """Тест отзыва несуществующего согласия."""
        # Arrange
        respondent_id = 1
        consent_id = 99999

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.revoke_consent = AsyncMock(
                side_effect=Exception("Consent not found")
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for(
                    "revoke_consent", respondent_id=respondent_id, consent_id=consent_id
                ),
                json={"reason": "user_request"},
            )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_consent_expired(self, api_client: AsyncClient):
        """Тест работы с истекшим согласием."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.get_respondent_consents = AsyncMock(
                side_effect=Exception("Consent expired")
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.get(
                api_client.url_for(
                    "get_respondent_consents", respondent_id=respondent_id
                )
            )

        # Assert
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    async def test_consent_conflict(self, api_client: AsyncClient):
        """Тест конфликта согласий."""
        # Arrange
        respondent_id = 1
        consent_data = {
            "consent_type": "data_processing",
            "purpose": "survey_participation",
            "granted": True,
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.grant_consent = AsyncMock(
                side_effect=Exception("Consent conflict detected")
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("grant_consent", respondent_id=respondent_id),
                json=consent_data,
            )

        # Assert
        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()


class TestRespondentGDPRErrors:
    """Негативные тесты ошибок GDPR."""

    async def test_export_data_without_consent(self, api_client: AsyncClient):
        """Тест экспорта данных без согласия."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                side_effect=Exception("No consent for data export")
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=respondent_id
                ),
                json={"format": "json"},
            )

        # Assert
        assert response.status_code == 403
        assert "consent" in response.json()["detail"].lower()

    async def test_delete_data_without_confirmation(self, api_client: AsyncClient):
        """Тест удаления данных без подтверждения."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.delete_respondent_data = AsyncMock(
                side_effect=Exception("Confirmation required")
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "delete_respondent_data", respondent_id=respondent_id
                ),
                json={"reason": "user_request"},
            )

        # Assert
        assert response.status_code == 400
        assert "confirmation" in response.json()["detail"].lower()

    async def test_export_data_too_large(self, api_client: AsyncClient):
        """Тест экспорта слишком больших данных."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                side_effect=Exception("Export data too large")
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=respondent_id
                ),
                json={"format": "json", "include_all": True},
            )

        # Assert
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    async def test_data_retention_policy_violation(self, api_client: AsyncClient):
        """Тест нарушения политики хранения данных."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.delete_respondent_data = AsyncMock(
                side_effect=Exception("Data retention policy violation")
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "delete_respondent_data", respondent_id=respondent_id
                ),
                json={"reason": "user_request", "immediate_deletion": True},
            )

        # Assert
        assert response.status_code == 400
        assert "policy" in response.json()["detail"].lower()


class TestRespondentSecurityErrors:
    """Негативные тесты ошибок безопасности."""

    async def test_rate_limiting_exceeded(self, api_client: AsyncClient):
        """Тест превышения лимита запросов."""
        # Act
        with patch("src.routers.respondents.check_rate_limit") as mock_rate_limit:
            mock_rate_limit.side_effect = Exception("Rate limit exceeded")

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"),
                json={"session_id": "test", "browser_fingerprint": "test"},
            )

        # Assert
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()

    async def test_sql_injection_attempt(self, api_client: AsyncClient, admin_user):
        """Тест попытки SQL инъекции."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = await api_client.get(
            api_client.url_for("search_respondents"),
            params={"query": "'; DROP TABLE respondents; --"},
        )

        # Assert
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_xss_attempt(self, api_client: AsyncClient):
        """Тест попытки XSS атаки."""
        # Arrange
        malicious_data = {
            "session_id": "test_session",
            "browser_fingerprint": "test_fp",
            "anonymous_name": "<script>alert('xss')</script>",
        }

        # Act
        response = await api_client.post(
            api_client.url_for("create_or_get_respondent"), json=malicious_data
        )

        # Assert
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_insufficient_permissions(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест недостаточных прав доступа."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.delete(
            api_client.url_for("delete_respondent", respondent_id=1)
        )

        # Assert
        assert response.status_code == 403
        assert "insufficient" in response.json()["detail"].lower()

    async def test_unauthorized_data_access(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест неавторизованного доступа к данным."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        response = await api_client.get(
            api_client.url_for("get_respondent_consents", respondent_id=999)
        )

        # Assert
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()


class TestRespondentDataErrors:
    """Негативные тесты ошибок данных."""

    async def test_corrupted_respondent_data(self, api_client: AsyncClient):
        """Тест поврежденных данных респондента."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_respondent_by_id = AsyncMock(
                side_effect=Exception("Corrupted data detected")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_respondent", respondent_id=respondent_id)
            )

        # Assert
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()

    async def test_data_integrity_violation(self, api_client: AsyncClient):
        """Тест нарушения целостности данных."""
        # Arrange
        update_data = {"anonymous_name": "Updated Name"}

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.update_respondent = AsyncMock(
                side_effect=Exception("Data integrity violation")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.patch(
                api_client.url_for("update_respondent", respondent_id=1),
                json=update_data,
            )

        # Assert
        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()

    async def test_concurrent_modification_error(self, api_client: AsyncClient):
        """Тест ошибки конкурентного изменения."""
        # Arrange
        merge_data = {
            "anonymous_session_id": "test_session",
            "anonymous_fingerprint": "test_fp",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.merge_respondents = AsyncMock(
                side_effect=Exception("Concurrent modification detected")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("merge_respondents"), json=merge_data
            )

        # Assert
        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()

    async def test_storage_quota_exceeded(self, api_client: AsyncClient):
        """Тест превышения квоты хранения."""
        # Arrange
        respondent_data = {
            "session_id": "test_session",
            "browser_fingerprint": "test_fp",
            "anonymous_name": "A" * 10000,  # Very long name
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                side_effect=Exception("Storage quota exceeded")
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 413
        assert "quota" in response.json()["detail"].lower()
