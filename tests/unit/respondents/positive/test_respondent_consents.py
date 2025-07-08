"""
Позитивные тесты управления согласиями респондентов.

Этот модуль содержит успешные сценарии работы с согласиями:
- Выдача и отзыв согласий на обработку данных
- GDPR операции (экспорт, удаление данных)
- Управление различными типами согласий
- Журналирование согласий
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


class TestConsentManagement:
    """Позитивные тесты управления согласиями."""

    async def test_grant_data_processing_consent(self, api_client: AsyncClient):
        """Тест выдачи согласия на обработку данных."""
        # Arrange
        respondent_id = 10
        consent_data = {
            "consent_type": "data_processing",
            "purpose": "survey_participation",
            "granted": True,
            "source": "web_form",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "consent_text": "I agree to the processing of my personal data for survey participation",
            "version": "1.2",
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.grant_consent = AsyncMock(
                return_value={
                    "id": 101,
                    "respondent_id": 10,
                    "consent_type": "data_processing",
                    "purpose": "survey_participation",
                    "granted": True,
                    "granted_at": "2024-01-20T16:30:00Z",
                    "source": "web_form",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "consent_text": "I agree to the processing of my personal data for survey participation",
                    "version": "1.2",
                    "legal_basis": "consent",
                    "expires_at": "2025-01-20T16:30:00Z",
                    "is_active": True,
                    "checksum": "abc123def456",
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("grant_consent", respondent_id=respondent_id),
                json=consent_data,
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["id"] == 101
        assert data["respondent_id"] == 10
        assert data["consent_type"] == "data_processing"
        assert data["purpose"] == "survey_participation"
        assert data["granted"] is True
        assert data["legal_basis"] == "consent"
        assert data["is_active"] is True
        assert data["version"] == "1.2"
        assert "checksum" in data
        assert "expires_at" in data

    async def test_grant_location_consent(self, api_client: AsyncClient):
        """Тест выдачи согласия на обработку геолокации."""
        # Arrange
        respondent_id = 15
        consent_data = {
            "consent_type": "location_tracking",
            "purpose": "location_based_surveys",
            "granted": True,
            "source": "mobile_app",
            "precision_level": "city",
            "duration_days": 90,
            "additional_permissions": ["background_location", "precise_location"],
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.grant_consent = AsyncMock(
                return_value={
                    "id": 102,
                    "respondent_id": 15,
                    "consent_type": "location_tracking",
                    "purpose": "location_based_surveys",
                    "granted": True,
                    "granted_at": "2024-01-20T16:30:00Z",
                    "source": "mobile_app",
                    "precision_level": "city",
                    "duration_days": 90,
                    "expires_at": "2024-04-20T16:30:00Z",
                    "additional_permissions": [
                        "background_location",
                        "precise_location",
                    ],
                    "legal_basis": "consent",
                    "is_active": True,
                    "privacy_settings": {
                        "data_retention_days": 90,
                        "anonymization_enabled": True,
                        "sharing_permitted": False,
                    },
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("grant_consent", respondent_id=respondent_id),
                json=consent_data,
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["id"] == 102
        assert data["consent_type"] == "location_tracking"
        assert data["purpose"] == "location_based_surveys"
        assert data["precision_level"] == "city"
        assert data["duration_days"] == 90
        assert len(data["additional_permissions"]) == 2

        privacy_settings = data["privacy_settings"]
        assert privacy_settings["data_retention_days"] == 90
        assert privacy_settings["anonymization_enabled"] is True
        assert privacy_settings["sharing_permitted"] is False

    async def test_grant_marketing_consent(self, api_client: AsyncClient):
        """Тест выдачи согласия на маркетинг."""
        # Arrange
        respondent_id = 20
        consent_data = {
            "consent_type": "marketing_communications",
            "purpose": "survey_invitations",
            "granted": True,
            "source": "registration_form",
            "channels": ["email", "sms", "push_notifications"],
            "frequency": "weekly",
            "categories": ["product_surveys", "customer_feedback", "market_research"],
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.grant_consent = AsyncMock(
                return_value={
                    "id": 103,
                    "respondent_id": 20,
                    "consent_type": "marketing_communications",
                    "purpose": "survey_invitations",
                    "granted": True,
                    "granted_at": "2024-01-20T16:30:00Z",
                    "source": "registration_form",
                    "channels": ["email", "sms", "push_notifications"],
                    "frequency": "weekly",
                    "categories": [
                        "product_surveys",
                        "customer_feedback",
                        "market_research",
                    ],
                    "legal_basis": "consent",
                    "is_active": True,
                    "preferences": {
                        "preferred_time": "18:00",
                        "timezone": "UTC",
                        "language": "en",
                    },
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("grant_consent", respondent_id=respondent_id),
                json=consent_data,
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["id"] == 103
        assert data["consent_type"] == "marketing_communications"
        assert data["frequency"] == "weekly"
        assert len(data["channels"]) == 3
        assert len(data["categories"]) == 3
        assert data["preferences"]["preferred_time"] == "18:00"

    async def test_update_existing_consent(self, api_client: AsyncClient):
        """Тест обновления существующего согласия."""
        # Arrange
        respondent_id = 25
        consent_data = {
            "consent_type": "data_processing",
            "purpose": "survey_participation",
            "granted": True,
            "source": "web_form",
            "consent_text": "Updated consent text with new terms",
            "version": "2.0",
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.grant_consent = AsyncMock(
                return_value={
                    "id": 104,
                    "respondent_id": 25,
                    "consent_type": "data_processing",
                    "purpose": "survey_participation",
                    "granted": True,
                    "granted_at": "2024-01-20T16:30:00Z",
                    "source": "web_form",
                    "consent_text": "Updated consent text with new terms",
                    "version": "2.0",
                    "legal_basis": "consent",
                    "is_active": True,
                    "previous_consent_id": 98,
                    "update_reason": "terms_update",
                    "audit_trail": [
                        {
                            "version": "1.0",
                            "granted_at": "2024-01-15T10:00:00Z",
                            "revoked_at": "2024-01-20T16:30:00Z",
                            "reason": "terms_update",
                        }
                    ],
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("grant_consent", respondent_id=respondent_id),
                json=consent_data,
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["version"] == "2.0"
        assert data["consent_text"] == "Updated consent text with new terms"
        assert data["previous_consent_id"] == 98
        assert data["update_reason"] == "terms_update"
        assert len(data["audit_trail"]) == 1
        assert data["audit_trail"][0]["version"] == "1.0"


class TestConsentRevocation:
    """Позитивные тесты отзыва согласий."""

    async def test_revoke_data_processing_consent(self, api_client: AsyncClient):
        """Тест отзыва согласия на обработку данных."""
        # Arrange
        respondent_id = 30
        consent_id = 105
        revocation_data = {
            "reason": "user_request",
            "details": "User requested data processing to be stopped",
            "source": "web_form",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.revoke_consent = AsyncMock(
                return_value={
                    "success": True,
                    "consent_id": 105,
                    "respondent_id": 30,
                    "consent_type": "data_processing",
                    "revoked_at": "2024-01-20T16:30:00Z",
                    "reason": "user_request",
                    "details": "User requested data processing to be stopped",
                    "source": "web_form",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "is_active": False,
                    "data_actions": {
                        "data_processing_stopped": True,
                        "future_surveys_blocked": True,
                        "anonymization_scheduled": True,
                        "deletion_scheduled": False,
                    },
                    "effective_date": "2024-01-20T16:30:00Z",
                    "confirmation_sent": True,
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for(
                    "revoke_consent", respondent_id=respondent_id, consent_id=consent_id
                ),
                json=revocation_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["consent_id"] == 105
        assert data["respondent_id"] == 30
        assert data["is_active"] is False
        assert data["reason"] == "user_request"

        data_actions = data["data_actions"]
        assert data_actions["data_processing_stopped"] is True
        assert data_actions["future_surveys_blocked"] is True
        assert data_actions["anonymization_scheduled"] is True
        assert data_actions["deletion_scheduled"] is False

        assert data["confirmation_sent"] is True

    async def test_revoke_location_consent(self, api_client: AsyncClient):
        """Тест отзыва согласия на геолокацию."""
        # Arrange
        respondent_id = 35
        consent_id = 106
        revocation_data = {
            "reason": "privacy_concerns",
            "details": "No longer comfortable sharing location data",
            "source": "mobile_app",
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.revoke_consent = AsyncMock(
                return_value={
                    "success": True,
                    "consent_id": 106,
                    "respondent_id": 35,
                    "consent_type": "location_tracking",
                    "revoked_at": "2024-01-20T16:30:00Z",
                    "reason": "privacy_concerns",
                    "details": "No longer comfortable sharing location data",
                    "source": "mobile_app",
                    "is_active": False,
                    "location_actions": {
                        "location_tracking_stopped": True,
                        "historical_data_anonymized": True,
                        "future_collection_blocked": True,
                        "precise_location_deleted": True,
                    },
                    "data_retention": {
                        "anonymized_data_kept": True,
                        "retention_period": "90_days",
                        "deletion_schedule": "2024-04-20T16:30:00Z",
                    },
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for(
                    "revoke_consent", respondent_id=respondent_id, consent_id=consent_id
                ),
                json=revocation_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["consent_type"] == "location_tracking"
        assert data["reason"] == "privacy_concerns"

        location_actions = data["location_actions"]
        assert location_actions["location_tracking_stopped"] is True
        assert location_actions["historical_data_anonymized"] is True
        assert location_actions["precise_location_deleted"] is True

        data_retention = data["data_retention"]
        assert data_retention["anonymized_data_kept"] is True
        assert data_retention["retention_period"] == "90_days"

    async def test_revoke_all_consents(self, api_client: AsyncClient):
        """Тест отзыва всех согласий респондента."""
        # Arrange
        respondent_id = 40
        revocation_data = {
            "reason": "account_closure",
            "details": "User closing account and revoking all consents",
            "source": "web_form",
            "confirmation_code": "REVOKE_ALL_12345",
        }

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.revoke_all_consents = AsyncMock(
                return_value={
                    "success": True,
                    "respondent_id": 40,
                    "revoked_at": "2024-01-20T16:30:00Z",
                    "reason": "account_closure",
                    "details": "User closing account and revoking all consents",
                    "source": "web_form",
                    "confirmation_code": "REVOKE_ALL_12345",
                    "revoked_consents": [
                        {
                            "consent_id": 107,
                            "consent_type": "data_processing",
                            "purpose": "survey_participation",
                            "revoked_at": "2024-01-20T16:30:00Z",
                        },
                        {
                            "consent_id": 108,
                            "consent_type": "location_tracking",
                            "purpose": "location_based_surveys",
                            "revoked_at": "2024-01-20T16:30:00Z",
                        },
                        {
                            "consent_id": 109,
                            "consent_type": "marketing_communications",
                            "purpose": "survey_invitations",
                            "revoked_at": "2024-01-20T16:30:00Z",
                        },
                    ],
                    "total_revoked": 3,
                    "data_actions": {
                        "all_processing_stopped": True,
                        "anonymization_scheduled": True,
                        "deletion_scheduled": True,
                        "marketing_stopped": True,
                    },
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.post(
                api_client.url_for("revoke_all_consents", respondent_id=respondent_id),
                json=revocation_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["respondent_id"] == 40
        assert data["total_revoked"] == 3
        assert data["confirmation_code"] == "REVOKE_ALL_12345"

        revoked_consents = data["revoked_consents"]
        assert len(revoked_consents) == 3
        consent_types = [consent["consent_type"] for consent in revoked_consents]
        assert "data_processing" in consent_types
        assert "location_tracking" in consent_types
        assert "marketing_communications" in consent_types

        data_actions = data["data_actions"]
        assert data_actions["all_processing_stopped"] is True
        assert data_actions["anonymization_scheduled"] is True
        assert data_actions["deletion_scheduled"] is True


class TestConsentRetrieval:
    """Позитивные тесты получения согласий."""

    async def test_get_all_respondent_consents(self, api_client: AsyncClient):
        """Тест получения всех согласий респондента."""
        # Arrange
        respondent_id = 45

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.get_respondent_consents = AsyncMock(
                return_value={
                    "respondent_id": 45,
                    "consents": [
                        {
                            "id": 110,
                            "consent_type": "data_processing",
                            "purpose": "survey_participation",
                            "granted": True,
                            "granted_at": "2024-01-15T10:00:00Z",
                            "version": "1.0",
                            "is_active": True,
                            "expires_at": "2025-01-15T10:00:00Z",
                            "legal_basis": "consent",
                        },
                        {
                            "id": 111,
                            "consent_type": "location_tracking",
                            "purpose": "location_based_surveys",
                            "granted": True,
                            "granted_at": "2024-01-16T14:30:00Z",
                            "version": "1.0",
                            "is_active": True,
                            "expires_at": "2024-04-16T14:30:00Z",
                            "legal_basis": "consent",
                            "precision_level": "city",
                        },
                        {
                            "id": 112,
                            "consent_type": "marketing_communications",
                            "purpose": "survey_invitations",
                            "granted": False,
                            "granted_at": "2024-01-10T09:00:00Z",
                            "revoked_at": "2024-01-18T16:45:00Z",
                            "version": "1.0",
                            "is_active": False,
                            "legal_basis": "consent",
                        },
                    ],
                    "summary": {
                        "total_consents": 3,
                        "active_consents": 2,
                        "revoked_consents": 1,
                        "expiring_soon": 1,
                    },
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.get(
                api_client.url_for(
                    "get_respondent_consents", respondent_id=respondent_id
                )
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["respondent_id"] == 45

        consents = data["consents"]
        assert len(consents) == 3

        # Check active consents
        active_consents = [c for c in consents if c["is_active"]]
        assert len(active_consents) == 2

        # Check consent types
        consent_types = [c["consent_type"] for c in consents]
        assert "data_processing" in consent_types
        assert "location_tracking" in consent_types
        assert "marketing_communications" in consent_types

        summary = data["summary"]
        assert summary["total_consents"] == 3
        assert summary["active_consents"] == 2
        assert summary["revoked_consents"] == 1
        assert summary["expiring_soon"] == 1

    async def test_get_consent_history(self, api_client: AsyncClient):
        """Тест получения истории согласий."""
        # Arrange
        respondent_id = 50
        consent_type = "data_processing"

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.get_consent_history = AsyncMock(
                return_value={
                    "respondent_id": 50,
                    "consent_type": "data_processing",
                    "history": [
                        {
                            "id": 113,
                            "version": "1.0",
                            "granted": True,
                            "granted_at": "2024-01-10T08:00:00Z",
                            "revoked_at": "2024-01-15T12:00:00Z",
                            "reason": "terms_update",
                            "is_active": False,
                        },
                        {
                            "id": 114,
                            "version": "1.5",
                            "granted": True,
                            "granted_at": "2024-01-15T12:00:00Z",
                            "revoked_at": "2024-01-18T10:00:00Z",
                            "reason": "user_request",
                            "is_active": False,
                        },
                        {
                            "id": 115,
                            "version": "2.0",
                            "granted": True,
                            "granted_at": "2024-01-20T09:00:00Z",
                            "revoked_at": None,
                            "reason": None,
                            "is_active": True,
                        },
                    ],
                    "timeline": [
                        {
                            "date": "2024-01-10T08:00:00Z",
                            "action": "granted",
                            "version": "1.0",
                        },
                        {
                            "date": "2024-01-15T12:00:00Z",
                            "action": "revoked",
                            "reason": "terms_update",
                        },
                        {
                            "date": "2024-01-15T12:00:00Z",
                            "action": "granted",
                            "version": "1.5",
                        },
                        {
                            "date": "2024-01-18T10:00:00Z",
                            "action": "revoked",
                            "reason": "user_request",
                        },
                        {
                            "date": "2024-01-20T09:00:00Z",
                            "action": "granted",
                            "version": "2.0",
                        },
                    ],
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.get(
                api_client.url_for("get_consent_history", respondent_id=respondent_id),
                params={"consent_type": consent_type},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["respondent_id"] == 50
        assert data["consent_type"] == "data_processing"

        history = data["history"]
        assert len(history) == 3

        # Check current active consent
        active_consent = [h for h in history if h["is_active"]]
        assert len(active_consent) == 1
        assert active_consent[0]["version"] == "2.0"

        timeline = data["timeline"]
        assert len(timeline) == 5
        assert timeline[0]["action"] == "granted"
        assert timeline[-1]["action"] == "granted"
        assert timeline[-1]["version"] == "2.0"


class TestGDPROperations:
    """Позитивные тесты GDPR операций."""

    async def test_export_respondent_data(self, api_client: AsyncClient):
        """Тест экспорта данных респондента (право на портативность)."""
        # Arrange
        respondent_id = 55
        export_data = {
            "format": "json",
            "include_sections": ["profile", "consents", "responses", "activity"],
            "encryption": True,
            "delivery_method": "download",
        }

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                return_value={
                    "export_id": "export_55_20240120",
                    "respondent_id": 55,
                    "format": "json",
                    "status": "completed",
                    "created_at": "2024-01-20T16:30:00Z",
                    "completed_at": "2024-01-20T16:32:15Z",
                    "file_size": "2.5MB",
                    "encryption_enabled": True,
                    "download_url": "https://secure.example.com/exports/export_55_20240120.zip",
                    "expires_at": "2024-01-27T16:30:00Z",
                    "included_sections": {
                        "profile": {
                            "records": 1,
                            "fields": ["name", "email", "preferences"],
                        },
                        "consents": {
                            "records": 3,
                            "fields": ["consent_type", "granted_at", "status"],
                        },
                        "responses": {
                            "records": 45,
                            "fields": ["survey_id", "response_data", "submitted_at"],
                        },
                        "activity": {
                            "records": 28,
                            "fields": ["action", "timestamp", "ip_address"],
                        },
                    },
                    "legal_note": "Data exported in compliance with GDPR Article 20",
                }
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=respondent_id
                ),
                json=export_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["export_id"] == "export_55_20240120"
        assert data["respondent_id"] == 55
        assert data["status"] == "completed"
        assert data["file_size"] == "2.5MB"
        assert data["encryption_enabled"] is True
        assert "download_url" in data
        assert "expires_at" in data

        included_sections = data["included_sections"]
        assert included_sections["profile"]["records"] == 1
        assert included_sections["consents"]["records"] == 3
        assert included_sections["responses"]["records"] == 45
        assert included_sections["activity"]["records"] == 28

        assert "legal_note" in data

    async def test_delete_respondent_data(self, api_client: AsyncClient):
        """Тест удаления данных респондента (право на забвение)."""
        # Arrange
        respondent_id = 60
        deletion_data = {
            "reason": "user_request",
            "confirmation_code": "DELETE_60_CONFIRM",
            "delete_sections": ["profile", "responses", "activity"],
            "keep_anonymized": False,
            "immediate_deletion": True,
        }

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.delete_respondent_data = AsyncMock(
                return_value={
                    "deletion_id": "deletion_60_20240120",
                    "respondent_id": 60,
                    "status": "completed",
                    "initiated_at": "2024-01-20T16:30:00Z",
                    "completed_at": "2024-01-20T16:35:45Z",
                    "reason": "user_request",
                    "confirmation_code": "DELETE_60_CONFIRM",
                    "deleted_sections": {
                        "profile": {
                            "records_deleted": 1,
                            "fields_deleted": ["name", "email", "phone", "address"],
                        },
                        "responses": {"records_deleted": 45, "surveys_affected": 8},
                        "activity": {"records_deleted": 28, "logs_purged": True},
                    },
                    "kept_sections": {
                        "consents": {"records_kept": 3, "reason": "legal_requirement"}
                    },
                    "anonymization": {
                        "anonymized_data_kept": False,
                        "statistical_data_kept": True,
                    },
                    "legal_note": "Data deleted in compliance with GDPR Article 17",
                    "certificate_url": "https://secure.example.com/certificates/deletion_60_20240120.pdf",
                }
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "delete_respondent_data", respondent_id=respondent_id
                ),
                json=deletion_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["deletion_id"] == "deletion_60_20240120"
        assert data["respondent_id"] == 60
        assert data["status"] == "completed"
        assert data["reason"] == "user_request"
        assert data["confirmation_code"] == "DELETE_60_CONFIRM"

        deleted_sections = data["deleted_sections"]
        assert deleted_sections["profile"]["records_deleted"] == 1
        assert deleted_sections["responses"]["records_deleted"] == 45
        assert deleted_sections["activity"]["records_deleted"] == 28

        kept_sections = data["kept_sections"]
        assert kept_sections["consents"]["records_kept"] == 3
        assert kept_sections["consents"]["reason"] == "legal_requirement"

        anonymization = data["anonymization"]
        assert anonymization["anonymized_data_kept"] is False
        assert anonymization["statistical_data_kept"] is True

        assert "legal_note" in data
        assert "certificate_url" in data
