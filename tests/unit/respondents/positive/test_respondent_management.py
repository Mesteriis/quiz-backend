"""
Позитивные тесты управления респондентами.

Этот модуль содержит успешные сценарии работы с респондентами:
- Создание и получение респондентов (анонимные и авторизованные)
- Слияние анонимных респондентов с авторизованными
- Обновление данных респондентов
- Получение профиля и активности
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory, RespondentFactory


class TestRespondentCreation:
    """Позитивные тесты создания респондентов."""

    async def test_create_anonymous_respondent(self, api_client: AsyncClient):
        """Тест создания нового анонимного респондента."""
        # Arrange
        respondent_data = {
            "session_id": "session_12345",
            "browser_fingerprint": "fp_abcdef123456",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "anonymous_name": "John Anonymous",
            "anonymous_email": "john.anon@example.com",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 1,
                    "session_id": "session_12345",
                    "browser_fingerprint": "fp_abcdef123456",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "anonymous_name": "John Anonymous",
                    "anonymous_email": "john.anon@example.com",
                    "is_anonymous": True,
                    "user_id": None,
                    "created_at": "2024-01-20T16:30:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "last_activity": "2024-01-20T16:30:00Z",
                    "surveys_participated": 0,
                    "total_responses": 0,
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["id"] == 1
        assert data["session_id"] == "session_12345"
        assert data["browser_fingerprint"] == "fp_abcdef123456"
        assert data["anonymous_name"] == "John Anonymous"
        assert data["anonymous_email"] == "john.anon@example.com"
        assert data["is_anonymous"] is True
        assert data["user_id"] is None
        assert data["surveys_participated"] == 0

    async def test_create_authenticated_respondent(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест создания респондента для авторизованного пользователя."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        respondent_data = {
            "session_id": "auth_session_67890",
            "browser_fingerprint": "auth_fp_xyz789",
            "ip_address": "10.0.0.50",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 2,
                    "session_id": "auth_session_67890",
                    "browser_fingerprint": "auth_fp_xyz789",
                    "ip_address": "10.0.0.50",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "user_id": regular_user.id,
                    "is_anonymous": False,
                    "anonymous_name": None,
                    "anonymous_email": None,
                    "created_at": "2024-01-20T16:30:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "last_activity": "2024-01-20T16:30:00Z",
                    "surveys_participated": 3,
                    "total_responses": 15,
                    "user_details": {
                        "username": regular_user.username,
                        "email": regular_user.email,
                        "first_name": regular_user.first_name,
                        "last_name": regular_user.last_name,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["id"] == 2
        assert data["user_id"] == regular_user.id
        assert data["is_anonymous"] is False
        assert data["anonymous_name"] is None
        assert data["anonymous_email"] is None
        assert data["surveys_participated"] == 3
        assert data["total_responses"] == 15
        assert data["user_details"]["username"] == regular_user.username

    async def test_get_existing_respondent_by_session(self, api_client: AsyncClient):
        """Тест получения существующего респондента по session_id."""
        # Arrange
        respondent_data = {
            "session_id": "existing_session_123",
            "browser_fingerprint": "different_fp",
            "ip_address": "192.168.1.200",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 5,
                    "session_id": "existing_session_123",
                    "browser_fingerprint": "different_fp",  # Updated
                    "ip_address": "192.168.1.200",  # Updated
                    "user_agent": "Original User Agent",
                    "anonymous_name": "Existing User",
                    "anonymous_email": "existing@example.com",
                    "is_anonymous": True,
                    "user_id": None,
                    "created_at": "2024-01-15T10:00:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "last_activity": "2024-01-20T16:30:00Z",
                    "surveys_participated": 2,
                    "total_responses": 8,
                    "was_updated": True,
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 200  # Existing respondent
        data = response.json()

        assert data["id"] == 5
        assert data["session_id"] == "existing_session_123"
        assert data["browser_fingerprint"] == "different_fp"  # Updated
        assert data["ip_address"] == "192.168.1.200"  # Updated
        assert data["was_updated"] is True
        assert data["surveys_participated"] == 2

    async def test_get_existing_respondent_by_fingerprint(
        self, api_client: AsyncClient
    ):
        """Тест получения существующего респондента по browser_fingerprint."""
        # Arrange
        respondent_data = {
            "session_id": "new_session_456",
            "browser_fingerprint": "existing_fp_abc123",
            "ip_address": "10.0.0.100",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 8,
                    "session_id": "new_session_456",  # Updated
                    "browser_fingerprint": "existing_fp_abc123",
                    "ip_address": "10.0.0.100",  # Updated
                    "user_agent": "Chrome/96.0.4664.110",
                    "anonymous_name": "Returning User",
                    "anonymous_email": "returning@example.com",
                    "is_anonymous": True,
                    "user_id": None,
                    "created_at": "2024-01-10T14:20:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "last_activity": "2024-01-20T16:30:00Z",
                    "surveys_participated": 5,
                    "total_responses": 25,
                    "was_updated": True,
                    "identified_by": "fingerprint",
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == 8
        assert data["session_id"] == "new_session_456"  # Updated
        assert data["browser_fingerprint"] == "existing_fp_abc123"
        assert data["identified_by"] == "fingerprint"
        assert data["surveys_participated"] == 5

    async def test_create_telegram_respondent(self, api_client: AsyncClient):
        """Тест создания респондента через Telegram."""
        # Arrange
        respondent_data = {
            "session_id": "tg_session_789",
            "browser_fingerprint": "telegram_client",
            "telegram_user_id": 123456789,
            "telegram_username": "john_doe_tg",
            "telegram_first_name": "John",
            "telegram_last_name": "Doe",
            "telegram_language_code": "en",
            "source": "telegram",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 10,
                    "session_id": "tg_session_789",
                    "browser_fingerprint": "telegram_client",
                    "telegram_user_id": 123456789,
                    "telegram_username": "john_doe_tg",
                    "telegram_first_name": "John",
                    "telegram_last_name": "Doe",
                    "telegram_language_code": "en",
                    "source": "telegram",
                    "is_anonymous": True,
                    "user_id": None,
                    "created_at": "2024-01-20T16:30:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "last_activity": "2024-01-20T16:30:00Z",
                    "platform": "telegram",
                    "surveys_participated": 0,
                    "total_responses": 0,
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["id"] == 10
        assert data["telegram_user_id"] == 123456789
        assert data["telegram_username"] == "john_doe_tg"
        assert data["telegram_first_name"] == "John"
        assert data["source"] == "telegram"
        assert data["platform"] == "telegram"


class TestRespondentRetrieval:
    """Позитивные тесты получения данных респондентов."""

    async def test_get_my_respondent_profile(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест получения профиля собственного респондента."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_my_respondent = AsyncMock(
                return_value={
                    "id": 15,
                    "user_id": regular_user.id,
                    "session_id": "user_session_abc",
                    "browser_fingerprint": "user_fp_123",
                    "is_anonymous": False,
                    "created_at": "2024-01-15T10:00:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "last_activity": "2024-01-20T16:30:00Z",
                    "surveys_participated": 8,
                    "total_responses": 45,
                    "completion_rate": 0.82,
                    "average_response_time": 4.5,
                    "preferred_language": "en",
                    "time_zone": "UTC",
                    "activity_summary": {
                        "last_7_days": {"surveys": 2, "responses": 8},
                        "last_30_days": {"surveys": 5, "responses": 22},
                        "total": {"surveys": 8, "responses": 45},
                    },
                    "user_details": {
                        "username": regular_user.username,
                        "email": regular_user.email,
                        "first_name": regular_user.first_name,
                        "last_name": regular_user.last_name,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(api_client.url_for("get_my_respondent"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == 15
        assert data["user_id"] == regular_user.id
        assert data["is_anonymous"] is False
        assert data["surveys_participated"] == 8
        assert data["completion_rate"] == 0.82
        assert data["average_response_time"] == 4.5

        activity = data["activity_summary"]
        assert activity["last_7_days"]["surveys"] == 2
        assert activity["total"]["responses"] == 45

        user_details = data["user_details"]
        assert user_details["username"] == regular_user.username

    async def test_get_respondent_activity_summary(self, api_client: AsyncClient):
        """Тест получения сводки активности респондента."""
        # Arrange
        respondent_id = 20

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_activity_summary = AsyncMock(
                return_value={
                    "respondent_id": 20,
                    "summary_period": "all_time",
                    "surveys": {
                        "total_participated": 12,
                        "completed": 10,
                        "partially_completed": 2,
                        "completion_rate": 0.83,
                    },
                    "responses": {
                        "total_submitted": 58,
                        "valid_responses": 55,
                        "invalid_responses": 3,
                        "average_response_time": 3.8,
                        "fastest_response": 1.2,
                        "slowest_response": 15.6,
                    },
                    "engagement": {
                        "sessions_count": 25,
                        "average_session_duration": 8.5,
                        "total_time_spent": 212.5,
                        "return_visits": 18,
                        "retention_rate": 0.72,
                    },
                    "timeline": [
                        {
                            "date": "2024-01-20",
                            "surveys_started": 1,
                            "surveys_completed": 1,
                            "responses_submitted": 5,
                            "time_spent": 6.2,
                        },
                        {
                            "date": "2024-01-19",
                            "surveys_started": 0,
                            "surveys_completed": 0,
                            "responses_submitted": 0,
                            "time_spent": 0,
                        },
                        {
                            "date": "2024-01-18",
                            "surveys_started": 2,
                            "surveys_completed": 1,
                            "responses_submitted": 8,
                            "time_spent": 12.4,
                        },
                    ],
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_activity_summary", respondent_id=respondent_id)
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["respondent_id"] == 20

        surveys = data["surveys"]
        assert surveys["total_participated"] == 12
        assert surveys["completion_rate"] == 0.83

        responses = data["responses"]
        assert responses["total_submitted"] == 58
        assert responses["average_response_time"] == 3.8

        engagement = data["engagement"]
        assert engagement["sessions_count"] == 25
        assert engagement["retention_rate"] == 0.72

        timeline = data["timeline"]
        assert len(timeline) == 3
        assert timeline[0]["date"] == "2024-01-20"
        assert timeline[0]["surveys_completed"] == 1


class TestRespondentMerging:
    """Позитивные тесты слияния респондентов."""

    async def test_merge_anonymous_with_authenticated(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест слияния анонимного респондента с авторизованным пользователем."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        merge_data = {
            "anonymous_session_id": "anon_session_merge123",
            "anonymous_fingerprint": "anon_fp_merge456",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.merge_respondents = AsyncMock(
                return_value={
                    "success": True,
                    "merged_respondent": {
                        "id": 25,
                        "user_id": regular_user.id,
                        "session_id": "auth_session_merged",
                        "browser_fingerprint": "anon_fp_merge456",
                        "is_anonymous": False,
                        "created_at": "2024-01-15T08:00:00Z",  # From anonymous
                        "updated_at": "2024-01-20T16:30:00Z",
                        "last_activity": "2024-01-20T16:30:00Z",
                    },
                    "merge_summary": {
                        "anonymous_respondent_id": 18,
                        "authenticated_respondent_id": 25,
                        "surveys_merged": 3,
                        "responses_merged": 12,
                        "consents_merged": 5,
                        "data_points_merged": 20,
                    },
                    "merged_activity": {
                        "total_surveys": 8,  # 5 auth + 3 anon
                        "total_responses": 35,  # 23 auth + 12 anon
                        "combined_completion_rate": 0.78,
                        "earliest_activity": "2024-01-15T08:00:00Z",
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("merge_respondents"), json=merge_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

        merged_respondent = data["merged_respondent"]
        assert merged_respondent["id"] == 25
        assert merged_respondent["user_id"] == regular_user.id
        assert merged_respondent["is_anonymous"] is False

        merge_summary = data["merge_summary"]
        assert merge_summary["surveys_merged"] == 3
        assert merge_summary["responses_merged"] == 12
        assert merge_summary["consents_merged"] == 5

        merged_activity = data["merged_activity"]
        assert merged_activity["total_surveys"] == 8
        assert merged_activity["total_responses"] == 35
        assert merged_activity["combined_completion_rate"] == 0.78

    async def test_merge_multiple_anonymous_sessions(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест слияния нескольких анонимных сессий."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        merge_data = {
            "anonymous_identifiers": [
                {"session_id": "anon1_session", "fingerprint": "anon1_fp"},
                {"session_id": "anon2_session", "fingerprint": "anon2_fp"},
                {"session_id": "anon3_session", "fingerprint": "anon3_fp"},
            ]
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.merge_multiple_respondents = AsyncMock(
                return_value={
                    "success": True,
                    "primary_respondent": {
                        "id": 30,
                        "user_id": regular_user.id,
                        "is_anonymous": False,
                    },
                    "merge_results": [
                        {
                            "anonymous_id": 19,
                            "session_id": "anon1_session",
                            "merged_successfully": True,
                            "surveys_merged": 2,
                            "responses_merged": 8,
                        },
                        {
                            "anonymous_id": 21,
                            "session_id": "anon2_session",
                            "merged_successfully": True,
                            "surveys_merged": 1,
                            "responses_merged": 4,
                        },
                        {
                            "anonymous_id": 23,
                            "session_id": "anon3_session",
                            "merged_successfully": True,
                            "surveys_merged": 3,
                            "responses_merged": 15,
                        },
                    ],
                    "total_merged": {
                        "anonymous_respondents": 3,
                        "surveys": 6,
                        "responses": 27,
                        "consents": 8,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("merge_multiple_respondents"), json=merge_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["primary_respondent"]["user_id"] == regular_user.id

        merge_results = data["merge_results"]
        assert len(merge_results) == 3
        assert all(result["merged_successfully"] for result in merge_results)

        total_merged = data["total_merged"]
        assert total_merged["anonymous_respondents"] == 3
        assert total_merged["surveys"] == 6
        assert total_merged["responses"] == 27


class TestRespondentUpdates:
    """Позитивные тесты обновления данных респондентов."""

    async def test_update_respondent_profile(self, api_client: AsyncClient):
        """Тест обновления профиля респондента."""
        # Arrange
        respondent_id = 35
        update_data = {
            "anonymous_name": "Updated Name",
            "anonymous_email": "updated@example.com",
            "preferred_language": "es",
            "time_zone": "Europe/Madrid",
            "notification_preferences": {
                "email_notifications": True,
                "push_notifications": False,
                "survey_reminders": True,
            },
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.update_respondent = AsyncMock(
                return_value={
                    "id": 35,
                    "anonymous_name": "Updated Name",
                    "anonymous_email": "updated@example.com",
                    "preferred_language": "es",
                    "time_zone": "Europe/Madrid",
                    "notification_preferences": {
                        "email_notifications": True,
                        "push_notifications": False,
                        "survey_reminders": True,
                    },
                    "updated_at": "2024-01-20T16:30:00Z",
                    "update_summary": {
                        "fields_updated": [
                            "anonymous_name",
                            "anonymous_email",
                            "preferred_language",
                            "time_zone",
                            "notification_preferences",
                        ],
                        "previous_values": {
                            "anonymous_name": "Old Name",
                            "preferred_language": "en",
                        },
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.patch(
                api_client.url_for("update_respondent", respondent_id=respondent_id),
                json=update_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == 35
        assert data["anonymous_name"] == "Updated Name"
        assert data["anonymous_email"] == "updated@example.com"
        assert data["preferred_language"] == "es"
        assert data["time_zone"] == "Europe/Madrid"

        preferences = data["notification_preferences"]
        assert preferences["email_notifications"] is True
        assert preferences["push_notifications"] is False

        update_summary = data["update_summary"]
        assert len(update_summary["fields_updated"]) == 5
        assert update_summary["previous_values"]["anonymous_name"] == "Old Name"

    async def test_update_respondent_location(self, api_client: AsyncClient):
        """Тест обновления геолокации респондента."""
        # Arrange
        respondent_id = 40
        location_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 10.5,
            "altitude": 15.2,
            "heading": 45.0,
            "speed": 0.0,
            "timestamp": "2024-01-20T16:30:00Z",
            "source": "gps",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.update_location = AsyncMock(
                return_value={
                    "success": True,
                    "location_updated": True,
                    "respondent_id": 40,
                    "location": {
                        "latitude": 40.7128,
                        "longitude": -74.0060,
                        "accuracy": 10.5,
                        "altitude": 15.2,
                        "heading": 45.0,
                        "speed": 0.0,
                        "timestamp": "2024-01-20T16:30:00Z",
                        "source": "gps",
                        "address": {
                            "city": "New York",
                            "state": "NY",
                            "country": "USA",
                            "postal_code": "10001",
                        },
                    },
                    "location_history_count": 15,
                    "privacy_note": "Location data is encrypted and anonymized",
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.patch(
                api_client.url_for(
                    "update_respondent_location", respondent_id=respondent_id
                ),
                json=location_data,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["location_updated"] is True
        assert data["respondent_id"] == 40

        location = data["location"]
        assert location["latitude"] == 40.7128
        assert location["longitude"] == -74.0060
        assert location["accuracy"] == 10.5
        assert location["source"] == "gps"

        address = location["address"]
        assert address["city"] == "New York"
        assert address["country"] == "USA"

        assert data["location_history_count"] == 15
        assert "privacy_note" in data
