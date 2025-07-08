"""
Позитивные тесты админских функций для респондентов.

Этот модуль содержит успешные сценарии админ операций:
- Поиск и фильтрация респондентов
- Статистика и аналитика
- Массовые операции с респондентами
- Мониторинг и управление данными
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


class TestRespondentSearch:
    """Позитивные тесты поиска респондентов."""

    async def test_search_respondents_basic(self, api_client: AsyncClient, admin_user):
        """Тест базового поиска респондентов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        search_params = {"query": "john", "page": 1, "per_page": 20}

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.search_respondents = AsyncMock(
                return_value={
                    "respondents": [
                        {
                            "id": 1,
                            "anonymous_name": "John Doe",
                            "anonymous_email": "john@example.com",
                            "is_anonymous": True,
                            "user_id": None,
                            "created_at": "2024-01-15T10:00:00Z",
                            "last_activity": "2024-01-20T16:30:00Z",
                            "surveys_participated": 5,
                            "total_responses": 25,
                            "completion_rate": 0.85,
                            "status": "active",
                        },
                        {
                            "id": 2,
                            "anonymous_name": "John Smith",
                            "anonymous_email": "johnsmith@example.com",
                            "is_anonymous": True,
                            "user_id": None,
                            "created_at": "2024-01-18T14:20:00Z",
                            "last_activity": "2024-01-20T15:45:00Z",
                            "surveys_participated": 2,
                            "total_responses": 8,
                            "completion_rate": 0.75,
                            "status": "active",
                        },
                    ],
                    "pagination": {
                        "page": 1,
                        "per_page": 20,
                        "total": 2,
                        "total_pages": 1,
                    },
                    "search_info": {
                        "query": "john",
                        "matches_found": 2,
                        "search_time": 0.05,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("search_respondents"), params=search_params
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        respondents = data["respondents"]
        assert len(respondents) == 2

        # Check first respondent
        assert respondents[0]["id"] == 1
        assert respondents[0]["anonymous_name"] == "John Doe"
        assert respondents[0]["surveys_participated"] == 5
        assert respondents[0]["completion_rate"] == 0.85

        # Check pagination
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["total"] == 2

        # Check search info
        search_info = data["search_info"]
        assert search_info["query"] == "john"
        assert search_info["matches_found"] == 2

    async def test_search_respondents_with_filters(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска респондентов с фильтрами."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        search_params = {
            "is_anonymous": "true",
            "min_surveys": 3,
            "max_surveys": 10,
            "min_completion_rate": 0.7,
            "created_after": "2024-01-01",
            "created_before": "2024-01-31",
            "status": "active",
            "has_location": "true",
            "source": "web",
            "sort_by": "surveys_participated",
            "sort_order": "desc",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.search_respondents = AsyncMock(
                return_value={
                    "respondents": [
                        {
                            "id": 10,
                            "anonymous_name": "Active User 1",
                            "anonymous_email": "active1@example.com",
                            "is_anonymous": True,
                            "user_id": None,
                            "created_at": "2024-01-10T09:00:00Z",
                            "last_activity": "2024-01-20T16:00:00Z",
                            "surveys_participated": 8,
                            "total_responses": 45,
                            "completion_rate": 0.90,
                            "status": "active",
                            "location": {"city": "New York", "country": "USA"},
                            "source": "web",
                        },
                        {
                            "id": 11,
                            "anonymous_name": "Active User 2",
                            "anonymous_email": "active2@example.com",
                            "is_anonymous": True,
                            "user_id": None,
                            "created_at": "2024-01-12T11:30:00Z",
                            "last_activity": "2024-01-20T14:20:00Z",
                            "surveys_participated": 5,
                            "total_responses": 22,
                            "completion_rate": 0.82,
                            "status": "active",
                            "location": {"city": "Los Angeles", "country": "USA"},
                            "source": "web",
                        },
                    ],
                    "pagination": {
                        "page": 1,
                        "per_page": 20,
                        "total": 2,
                        "total_pages": 1,
                    },
                    "filters_applied": {
                        "is_anonymous": True,
                        "min_surveys": 3,
                        "max_surveys": 10,
                        "min_completion_rate": 0.7,
                        "date_range": "2024-01-01 to 2024-01-31",
                        "status": "active",
                        "has_location": True,
                        "source": "web",
                    },
                    "sorting": {
                        "sort_by": "surveys_participated",
                        "sort_order": "desc",
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("search_respondents"), params=search_params
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        respondents = data["respondents"]
        assert len(respondents) == 2

        # Check sorting (descending by surveys_participated)
        assert respondents[0]["surveys_participated"] == 8
        assert respondents[1]["surveys_participated"] == 5

        # Check filters applied
        filters_applied = data["filters_applied"]
        assert filters_applied["is_anonymous"] is True
        assert filters_applied["min_surveys"] == 3
        assert filters_applied["min_completion_rate"] == 0.7
        assert filters_applied["has_location"] is True

        # Check sorting
        sorting = data["sorting"]
        assert sorting["sort_by"] == "surveys_participated"
        assert sorting["sort_order"] == "desc"

    async def test_search_respondents_by_location(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска респондентов по геолокации."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        search_params = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "radius": 10,  # 10 km
            "unit": "km",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.search_respondents = AsyncMock(
                return_value={
                    "respondents": [
                        {
                            "id": 15,
                            "anonymous_name": "NYC User 1",
                            "is_anonymous": True,
                            "location": {
                                "latitude": 40.7589,
                                "longitude": -73.9851,
                                "city": "New York",
                                "state": "NY",
                                "country": "USA",
                                "distance_km": 3.2,
                            },
                            "surveys_participated": 4,
                            "total_responses": 18,
                        },
                        {
                            "id": 16,
                            "anonymous_name": "NYC User 2",
                            "is_anonymous": True,
                            "location": {
                                "latitude": 40.6892,
                                "longitude": -74.0445,
                                "city": "New York",
                                "state": "NY",
                                "country": "USA",
                                "distance_km": 5.8,
                            },
                            "surveys_participated": 6,
                            "total_responses": 28,
                        },
                    ],
                    "location_search": {
                        "center": {"latitude": 40.7128, "longitude": -74.0060},
                        "radius": 10,
                        "unit": "km",
                        "matches_found": 2,
                    },
                    "pagination": {
                        "page": 1,
                        "per_page": 20,
                        "total": 2,
                        "total_pages": 1,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("search_respondents"), params=search_params
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        respondents = data["respondents"]
        assert len(respondents) == 2

        # Check location data
        for respondent in respondents:
            assert "location" in respondent
            assert "distance_km" in respondent["location"]
            assert respondent["location"]["distance_km"] <= 10
            assert respondent["location"]["city"] == "New York"

        # Check location search info
        location_search = data["location_search"]
        assert location_search["center"]["latitude"] == 40.7128
        assert location_search["center"]["longitude"] == -74.0060
        assert location_search["radius"] == 10
        assert location_search["matches_found"] == 2


class TestRespondentStatistics:
    """Позитивные тесты статистики респондентов."""

    async def test_get_respondent_statistics_overview(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения общей статистики респондентов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_respondent_statistics = AsyncMock(
                return_value={
                    "overview": {
                        "total_respondents": 1247,
                        "anonymous_respondents": 823,
                        "authenticated_respondents": 424,
                        "active_respondents": 1156,
                        "inactive_respondents": 91,
                    },
                    "growth": {
                        "new_this_month": 87,
                        "new_this_week": 23,
                        "new_today": 5,
                        "growth_rate_monthly": 0.075,
                        "growth_rate_weekly": 0.020,
                    },
                    "engagement": {
                        "average_surveys_per_respondent": 4.2,
                        "average_responses_per_respondent": 18.6,
                        "average_completion_rate": 0.78,
                        "highly_engaged_respondents": 234,
                        "low_engagement_respondents": 156,
                    },
                    "demographics": {
                        "by_source": {
                            "web": 678,
                            "mobile": 345,
                            "telegram": 156,
                            "api": 68,
                        },
                        "by_location": {
                            "USA": 456,
                            "Canada": 123,
                            "UK": 89,
                            "Germany": 67,
                            "other": 512,
                        },
                    },
                    "activity": {
                        "active_last_24h": 234,
                        "active_last_7d": 567,
                        "active_last_30d": 890,
                        "average_session_duration": 8.5,
                        "total_sessions": 15678,
                    },
                    "data_quality": {
                        "complete_profiles": 892,
                        "incomplete_profiles": 355,
                        "verified_emails": 567,
                        "location_enabled": 445,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_respondent_statistics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check overview
        overview = data["overview"]
        assert overview["total_respondents"] == 1247
        assert overview["anonymous_respondents"] == 823
        assert overview["authenticated_respondents"] == 424
        assert overview["active_respondents"] == 1156

        # Check growth
        growth = data["growth"]
        assert growth["new_this_month"] == 87
        assert growth["growth_rate_monthly"] == 0.075

        # Check engagement
        engagement = data["engagement"]
        assert engagement["average_surveys_per_respondent"] == 4.2
        assert engagement["average_completion_rate"] == 0.78
        assert engagement["highly_engaged_respondents"] == 234

        # Check demographics
        demographics = data["demographics"]
        assert demographics["by_source"]["web"] == 678
        assert demographics["by_location"]["USA"] == 456

        # Check activity
        activity = data["activity"]
        assert activity["active_last_24h"] == 234
        assert activity["average_session_duration"] == 8.5

        # Check data quality
        data_quality = data["data_quality"]
        assert data_quality["complete_profiles"] == 892
        assert data_quality["verified_emails"] == 567

    async def test_get_respondent_engagement_analytics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения аналитики вовлеченности респондентов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_engagement_analytics = AsyncMock(
                return_value={
                    "engagement_segments": {
                        "highly_engaged": {
                            "count": 234,
                            "percentage": 18.8,
                            "criteria": "5+ surveys, 80%+ completion rate",
                            "average_surveys": 8.2,
                            "average_completion_rate": 0.92,
                        },
                        "moderately_engaged": {
                            "count": 567,
                            "percentage": 45.5,
                            "criteria": "2-4 surveys, 60-80% completion rate",
                            "average_surveys": 3.1,
                            "average_completion_rate": 0.71,
                        },
                        "low_engaged": {
                            "count": 446,
                            "percentage": 35.7,
                            "criteria": "1-2 surveys, <60% completion rate",
                            "average_surveys": 1.3,
                            "average_completion_rate": 0.45,
                        },
                    },
                    "retention_analysis": {
                        "1_day_retention": 0.78,
                        "7_day_retention": 0.56,
                        "30_day_retention": 0.34,
                        "90_day_retention": 0.22,
                        "cohort_analysis": [
                            {
                                "cohort": "2024-01",
                                "initial_size": 156,
                                "day_1": 0.82,
                                "day_7": 0.61,
                                "day_30": 0.38,
                                "day_90": 0.24,
                            },
                            {
                                "cohort": "2024-02",
                                "initial_size": 123,
                                "day_1": 0.75,
                                "day_7": 0.52,
                                "day_30": 0.31,
                                "day_90": 0.19,
                            },
                        ],
                    },
                    "survey_completion_trends": {
                        "daily_completion_rates": [
                            {"date": "2024-01-20", "completion_rate": 0.79},
                            {"date": "2024-01-19", "completion_rate": 0.82},
                            {"date": "2024-01-18", "completion_rate": 0.76},
                        ],
                        "completion_by_survey_length": {
                            "short": {"avg_questions": 3, "completion_rate": 0.94},
                            "medium": {"avg_questions": 8, "completion_rate": 0.78},
                            "long": {"avg_questions": 15, "completion_rate": 0.56},
                        },
                    },
                    "response_time_analysis": {
                        "average_response_time": 4.2,
                        "median_response_time": 3.1,
                        "response_time_distribution": {
                            "0-2_seconds": 0.23,
                            "2-5_seconds": 0.45,
                            "5-10_seconds": 0.22,
                            "10+_seconds": 0.10,
                        },
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_engagement_analytics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check engagement segments
        engagement_segments = data["engagement_segments"]
        assert engagement_segments["highly_engaged"]["count"] == 234
        assert engagement_segments["highly_engaged"]["percentage"] == 18.8
        assert engagement_segments["moderately_engaged"]["count"] == 567
        assert engagement_segments["low_engaged"]["count"] == 446

        # Check retention analysis
        retention_analysis = data["retention_analysis"]
        assert retention_analysis["1_day_retention"] == 0.78
        assert retention_analysis["30_day_retention"] == 0.34
        assert len(retention_analysis["cohort_analysis"]) == 2

        # Check survey completion trends
        survey_completion_trends = data["survey_completion_trends"]
        assert len(survey_completion_trends["daily_completion_rates"]) == 3
        completion_by_length = survey_completion_trends["completion_by_survey_length"]
        assert completion_by_length["short"]["completion_rate"] == 0.94
        assert completion_by_length["long"]["completion_rate"] == 0.56

        # Check response time analysis
        response_time_analysis = data["response_time_analysis"]
        assert response_time_analysis["average_response_time"] == 4.2
        assert response_time_analysis["median_response_time"] == 3.1
        distribution = response_time_analysis["response_time_distribution"]
        assert distribution["0-2_seconds"] == 0.23
        assert distribution["2-5_seconds"] == 0.45


class TestRespondentBulkOperations:
    """Позитивные тесты массовых операций с респондентами."""

    async def test_bulk_update_respondents(self, api_client: AsyncClient, admin_user):
        """Тест массового обновления респондентов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        bulk_data = {
            "respondent_ids": [1, 2, 3, 4, 5],
            "updates": {
                "status": "active",
                "notification_preferences": {
                    "email_notifications": True,
                    "survey_reminders": True,
                },
                "tags": ["bulk_updated", "admin_action"],
            },
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.bulk_update_respondents = AsyncMock(
                return_value={
                    "success": True,
                    "updated_count": 5,
                    "failed_count": 0,
                    "results": [
                        {
                            "respondent_id": 1,
                            "status": "updated",
                            "updated_fields": [
                                "status",
                                "notification_preferences",
                                "tags",
                            ],
                        },
                        {
                            "respondent_id": 2,
                            "status": "updated",
                            "updated_fields": [
                                "status",
                                "notification_preferences",
                                "tags",
                            ],
                        },
                        {
                            "respondent_id": 3,
                            "status": "updated",
                            "updated_fields": [
                                "status",
                                "notification_preferences",
                                "tags",
                            ],
                        },
                        {
                            "respondent_id": 4,
                            "status": "updated",
                            "updated_fields": [
                                "status",
                                "notification_preferences",
                                "tags",
                            ],
                        },
                        {
                            "respondent_id": 5,
                            "status": "updated",
                            "updated_fields": [
                                "status",
                                "notification_preferences",
                                "tags",
                            ],
                        },
                    ],
                    "execution_summary": {
                        "total_requested": 5,
                        "successfully_updated": 5,
                        "failed_updates": 0,
                        "execution_time": 1.23,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("bulk_update_respondents"), json=bulk_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["updated_count"] == 5
        assert data["failed_count"] == 0

        results = data["results"]
        assert len(results) == 5
        for result in results:
            assert result["status"] == "updated"
            assert len(result["updated_fields"]) == 3

        execution_summary = data["execution_summary"]
        assert execution_summary["total_requested"] == 5
        assert execution_summary["successfully_updated"] == 5
        assert execution_summary["failed_updates"] == 0

    async def test_bulk_export_respondents(self, api_client: AsyncClient, admin_user):
        """Тест массового экспорта респондентов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        export_data = {
            "filters": {
                "created_after": "2024-01-01",
                "created_before": "2024-01-31",
                "is_anonymous": True,
                "min_surveys": 1,
            },
            "format": "csv",
            "include_fields": [
                "id",
                "anonymous_name",
                "anonymous_email",
                "created_at",
                "surveys_participated",
            ],
            "include_responses": False,
            "anonymize_data": True,
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.bulk_export_respondents = AsyncMock(
                return_value={
                    "export_id": "bulk_export_20240120_001",
                    "status": "completed",
                    "created_at": "2024-01-20T16:30:00Z",
                    "completed_at": "2024-01-20T16:32:45Z",
                    "format": "csv",
                    "respondents_exported": 156,
                    "file_size": "2.8MB",
                    "download_url": "https://secure.example.com/exports/bulk_export_20240120_001.csv",
                    "expires_at": "2024-01-27T16:30:00Z",
                    "filters_applied": {
                        "date_range": "2024-01-01 to 2024-01-31",
                        "is_anonymous": True,
                        "min_surveys": 1,
                    },
                    "fields_included": [
                        "id",
                        "anonymous_name",
                        "anonymous_email",
                        "created_at",
                        "surveys_participated",
                    ],
                    "anonymization": {
                        "enabled": True,
                        "fields_anonymized": ["anonymous_name", "anonymous_email"],
                        "method": "hash_with_salt",
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("bulk_export_respondents"), json=export_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["export_id"] == "bulk_export_20240120_001"
        assert data["status"] == "completed"
        assert data["respondents_exported"] == 156
        assert data["format"] == "csv"
        assert data["file_size"] == "2.8MB"
        assert "download_url" in data
        assert "expires_at" in data

        filters_applied = data["filters_applied"]
        assert filters_applied["is_anonymous"] is True
        assert filters_applied["min_surveys"] == 1

        anonymization = data["anonymization"]
        assert anonymization["enabled"] is True
        assert len(anonymization["fields_anonymized"]) == 2
        assert anonymization["method"] == "hash_with_salt"

    async def test_bulk_delete_respondents(self, api_client: AsyncClient, admin_user):
        """Тест массового удаления респондентов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        deletion_data = {
            "respondent_ids": [101, 102, 103],
            "reason": "gdpr_request",
            "confirmation_code": "BULK_DELETE_CONFIRM_123",
            "delete_associated_data": True,
            "anonymize_responses": True,
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.bulk_delete_respondents = AsyncMock(
                return_value={
                    "success": True,
                    "deletion_id": "bulk_deletion_20240120_001",
                    "deleted_count": 3,
                    "failed_count": 0,
                    "results": [
                        {
                            "respondent_id": 101,
                            "status": "deleted",
                            "data_deleted": {
                                "profile": True,
                                "responses": True,
                                "consents": True,
                                "activity_logs": True,
                            },
                            "responses_anonymized": 12,
                        },
                        {
                            "respondent_id": 102,
                            "status": "deleted",
                            "data_deleted": {
                                "profile": True,
                                "responses": True,
                                "consents": True,
                                "activity_logs": True,
                            },
                            "responses_anonymized": 8,
                        },
                        {
                            "respondent_id": 103,
                            "status": "deleted",
                            "data_deleted": {
                                "profile": True,
                                "responses": True,
                                "consents": True,
                                "activity_logs": True,
                            },
                            "responses_anonymized": 15,
                        },
                    ],
                    "summary": {
                        "total_respondents_deleted": 3,
                        "total_responses_anonymized": 35,
                        "total_consents_revoked": 9,
                        "total_activity_logs_purged": 28,
                    },
                    "completed_at": "2024-01-20T16:35:00Z",
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("bulk_delete_respondents"), json=deletion_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["deleted_count"] == 3
        assert data["failed_count"] == 0

        results = data["results"]
        assert len(results) == 3
        for result in results:
            assert result["status"] == "deleted"
            assert result["data_deleted"]["profile"] is True
            assert result["data_deleted"]["responses"] is True
            assert result["responses_anonymized"] > 0

        summary = data["summary"]
        assert summary["total_respondents_deleted"] == 3
        assert summary["total_responses_anonymized"] == 35
        assert summary["total_consents_revoked"] == 9
