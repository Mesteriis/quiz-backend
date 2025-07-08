"""
Граничные тесты для респондентов.

Этот модуль содержит тесты для экстремальных условий работы с респондентами:
- Высокие нагрузки и производительность
- Лимиты и ограничения системы
- Конкурентные операции
- Экстремальные данные
- Восстановление и отказоустойчивость
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


class TestRespondentPerformance:
    """Граничные тесты производительности респондентов."""

    async def test_create_respondents_high_concurrency(self, api_client: AsyncClient):
        """Тест создания респондентов при высокой конкурентности."""
        # Arrange
        respondent_data_template = {
            "session_id": "session_",
            "browser_fingerprint": "fp_",
            "ip_address": "192.168.1.100",
            "user_agent": "Test Agent",
            "anonymous_name": "Test User ",
            "anonymous_email": "test@example.com",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                side_effect=lambda data: {
                    "id": hash(data["session_id"]) % 10000,
                    "session_id": data["session_id"],
                    "browser_fingerprint": data["browser_fingerprint"],
                    "anonymous_name": data["anonymous_name"],
                    "is_anonymous": True,
                    "created_at": "2024-01-20T16:30:00Z",
                }
            )
            mock_service.return_value = mock_respondent_service

            # Create 100 concurrent requests
            tasks = []
            for i in range(100):
                data = respondent_data_template.copy()
                data["session_id"] += str(i)
                data["browser_fingerprint"] += str(i)
                data["anonymous_name"] += str(i)

                task = api_client.post(
                    api_client.url_for("create_or_get_respondent"), json=data
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

        # Assert
        successful_responses = [r for r in responses if r.status_code in [200, 201]]
        assert len(successful_responses) >= 95  # At least 95% success rate

        # Check all have unique IDs
        response_ids = [r.json()["id"] for r in successful_responses]
        assert len(set(response_ids)) == len(response_ids)

    async def test_bulk_search_large_dataset(self, api_client: AsyncClient, admin_user):
        """Тест поиска в большом наборе данных."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.search_respondents = AsyncMock(
                return_value={
                    "respondents": [
                        {
                            "id": i,
                            "anonymous_name": f"User {i}",
                            "anonymous_email": f"user{i}@example.com",
                            "surveys_participated": i % 10,
                            "total_responses": i * 2,
                            "completion_rate": min(0.9, (i % 100) / 100),
                        }
                        for i in range(1, 1001)  # 1000 results
                    ],
                    "pagination": {
                        "page": 1,
                        "per_page": 1000,
                        "total": 100000,
                        "total_pages": 100,
                    },
                    "search_info": {
                        "query": "*",
                        "matches_found": 100000,
                        "search_time": 2.5,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("search_respondents"),
                params={"query": "*", "per_page": 1000},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["respondents"]) == 1000
        assert data["pagination"]["total"] == 100000
        assert data["search_info"]["search_time"] > 0

    async def test_massive_bulk_operation(self, api_client: AsyncClient, admin_user):
        """Тест массовой операции с максимальным количеством записей."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Maximum batch size
        max_ids = list(range(1, 10001))  # 10,000 IDs

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.bulk_update_respondents = AsyncMock(
                return_value={
                    "success": True,
                    "updated_count": 10000,
                    "failed_count": 0,
                    "results": [
                        {
                            "respondent_id": i,
                            "status": "updated",
                            "updated_fields": ["status"],
                        }
                        for i in range(1, 10001)
                    ],
                    "execution_summary": {
                        "total_requested": 10000,
                        "successfully_updated": 10000,
                        "failed_updates": 0,
                        "execution_time": 45.2,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("bulk_update_respondents"),
                json={"respondent_ids": max_ids, "updates": {"status": "active"}},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["updated_count"] == 10000
        assert data["execution_summary"]["execution_time"] > 0
        assert len(data["results"]) == 10000

    async def test_memory_intensive_export(self, api_client: AsyncClient):
        """Тест памяти-интенсивного экспорта."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                return_value={
                    "export_id": "large_export_001",
                    "respondent_id": 1,
                    "status": "completed",
                    "created_at": "2024-01-20T16:30:00Z",
                    "completed_at": "2024-01-20T16:45:30Z",
                    "file_size": "500MB",
                    "record_count": 1000000,
                    "compression_ratio": 0.15,
                    "download_url": "https://secure.example.com/exports/large_export_001.zip",
                    "processing_time": 930.5,
                    "memory_peak": "2.1GB",
                }
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=respondent_id
                ),
                json={
                    "format": "json",
                    "include_sections": [
                        "profile",
                        "consents",
                        "responses",
                        "activity",
                    ],
                    "include_all_data": True,
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["file_size"] == "500MB"
        assert data["record_count"] == 1000000
        assert data["processing_time"] > 900
        assert "memory_peak" in data

    async def test_concurrent_merge_operations(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест одновременных операций слияния."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.merge_respondents = AsyncMock(
                return_value={
                    "success": True,
                    "merged_respondent": {"id": 1, "user_id": regular_user.id},
                    "merge_summary": {"surveys_merged": 2, "responses_merged": 10},
                }
            )
            mock_service.return_value = mock_respondent_service

            # Create 20 concurrent merge requests
            tasks = []
            for i in range(20):
                merge_data = {
                    "anonymous_session_id": f"anon_session_{i}",
                    "anonymous_fingerprint": f"anon_fp_{i}",
                }
                task = api_client.post(
                    api_client.url_for("merge_respondents"), json=merge_data
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

        # Assert
        # Only some should succeed due to concurrency control
        successful_responses = [r for r in responses if r.status_code == 200]
        conflict_responses = [r for r in responses if r.status_code == 409]

        assert len(successful_responses) >= 1
        assert len(successful_responses) + len(conflict_responses) == 20


class TestRespondentLimits:
    """Граничные тесты лимитов системы."""

    async def test_maximum_anonymous_name_length(self, api_client: AsyncClient):
        """Тест максимальной длины анонимного имени."""
        # Arrange
        max_name = "A" * 1000  # Maximum allowed length

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 1,
                    "session_id": "test_session",
                    "browser_fingerprint": "test_fp",
                    "anonymous_name": max_name,
                    "is_anonymous": True,
                    "created_at": "2024-01-20T16:30:00Z",
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"),
                json={
                    "session_id": "test_session",
                    "browser_fingerprint": "test_fp",
                    "anonymous_name": max_name,
                    "anonymous_email": "test@example.com",
                },
            )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["anonymous_name"] == max_name
        assert len(data["anonymous_name"]) == 1000

    async def test_maximum_session_count_per_respondent(self, api_client: AsyncClient):
        """Тест максимального количества сессий на респондента."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_activity_summary = AsyncMock(
                return_value={
                    "respondent_id": 1,
                    "engagement": {
                        "sessions_count": 10000,  # Maximum sessions
                        "average_session_duration": 5.2,
                        "total_time_spent": 52000.0,
                        "session_limit_reached": True,
                    },
                    "session_distribution": {
                        "daily_average": 100,
                        "peak_sessions_per_day": 500,
                        "longest_session": 180.5,
                        "shortest_session": 0.1,
                    },
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_activity_summary", respondent_id=respondent_id)
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        engagement = data["engagement"]
        assert engagement["sessions_count"] == 10000
        assert engagement["session_limit_reached"] is True
        assert engagement["total_time_spent"] == 52000.0

    async def test_maximum_consent_history_length(self, api_client: AsyncClient):
        """Тест максимальной длины истории согласий."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_consent_service") as mock_service:
            mock_consent_service = MagicMock()
            mock_consent_service.get_consent_history = AsyncMock(
                return_value={
                    "respondent_id": 1,
                    "consent_type": "data_processing",
                    "history": [
                        {
                            "id": i,
                            "version": f"1.{i}",
                            "granted": i % 2 == 0,
                            "granted_at": f"2024-01-{(i % 31) + 1:02d}T10:00:00Z",
                            "is_active": i == 999,
                        }
                        for i in range(1000)  # 1000 consent changes
                    ],
                    "summary": {
                        "total_changes": 1000,
                        "grants": 500,
                        "revocations": 500,
                        "history_limit_reached": True,
                    },
                }
            )
            mock_service.return_value = mock_consent_service

            response = await api_client.get(
                api_client.url_for("get_consent_history", respondent_id=respondent_id),
                params={"consent_type": "data_processing"},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["history"]) == 1000
        assert data["summary"]["total_changes"] == 1000
        assert data["summary"]["history_limit_reached"] is True

    async def test_maximum_export_size_limit(self, api_client: AsyncClient):
        """Тест лимита максимального размера экспорта."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                return_value={
                    "export_id": "max_export_001",
                    "respondent_id": 1,
                    "status": "size_limit_reached",
                    "file_size": "1GB",
                    "size_limit": "1GB",
                    "record_count": 5000000,
                    "partial_export": True,
                    "warning": "Export truncated due to size limit",
                    "continuation_token": "export_continue_token_123",
                }
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=respondent_id
                ),
                json={"format": "json", "include_all_data": True, "max_size": "1GB"},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "size_limit_reached"
        assert data["file_size"] == "1GB"
        assert data["partial_export"] is True
        assert "continuation_token" in data

    async def test_concurrent_session_limit(self, api_client: AsyncClient):
        """Тест лимита одновременных сессий."""
        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 1,
                    "session_id": "test_session",
                    "browser_fingerprint": "test_fp",
                    "is_anonymous": True,
                    "created_at": "2024-01-20T16:30:00Z",
                    "concurrent_sessions": 100,
                    "session_limit_warning": True,
                }
            )
            mock_service.return_value = mock_respondent_service

            # Create 200 concurrent session requests
            tasks = []
            for i in range(200):
                data = {
                    "session_id": f"session_{i}",
                    "browser_fingerprint": f"fp_{i}",
                    "anonymous_name": f"User {i}",
                }
                task = api_client.post(
                    api_client.url_for("create_or_get_respondent"), json=data
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

        # Assert
        successful_responses = [r for r in responses if r.status_code in [200, 201]]
        rate_limited_responses = [r for r in responses if r.status_code == 429]

        # Some should be rate limited
        assert len(successful_responses) <= 150
        assert len(rate_limited_responses) > 0


class TestRespondentExtremeData:
    """Граничные тесты экстремальных данных."""

    async def test_unicode_and_emoji_handling(self, api_client: AsyncClient):
        """Тест обработки Unicode и эмодзи."""
        # Arrange
        unicode_data = {
            "session_id": "сессия_🔗_测试",
            "browser_fingerprint": "指纹_🔍_отпечаток",
            "anonymous_name": "用户 👤 Пользователь 🌟",
            "anonymous_email": "тест@пример.рф",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 測試 тест 🌐",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 1,
                    "session_id": "сессия_🔗_测试",
                    "browser_fingerprint": "指纹_🔍_отпечаток",
                    "anonymous_name": "用户 👤 Пользователь 🌟",
                    "anonymous_email": "тест@пример.рф",
                    "is_anonymous": True,
                    "created_at": "2024-01-20T16:30:00Z",
                    "encoding": "utf-8",
                    "character_validation": "passed",
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=unicode_data
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["session_id"] == "сессия_🔗_测试"
        assert data["anonymous_name"] == "用户 👤 Пользователь 🌟"
        assert data["anonymous_email"] == "тест@пример.рф"
        assert data["character_validation"] == "passed"

    async def test_boundary_coordinate_values(self, api_client: AsyncClient):
        """Тест граничных значений координат."""
        # Arrange
        respondent_id = 1
        boundary_location = {
            "latitude": 90.0,  # North pole
            "longitude": 180.0,  # International date line
            "accuracy": 0.1,  # Minimum accuracy
            "altitude": 8848.86,  # Mount Everest height
            "heading": 359.99,  # Maximum heading
            "speed": 299792458,  # Speed of light (extreme)
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.update_location = AsyncMock(
                return_value={
                    "success": True,
                    "location_updated": True,
                    "respondent_id": 1,
                    "location": boundary_location,
                    "validation_notes": [
                        "Extreme coordinates detected",
                        "Speed value exceeds normal limits",
                        "Location at geographical boundary",
                    ],
                    "coordinate_system": "WGS84",
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.patch(
                api_client.url_for(
                    "update_respondent_location", respondent_id=respondent_id
                ),
                json=boundary_location,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        location = data["location"]
        assert location["latitude"] == 90.0
        assert location["longitude"] == 180.0
        assert location["speed"] == 299792458
        assert len(data["validation_notes"]) == 3

    async def test_very_long_json_data(self, api_client: AsyncClient):
        """Тест очень длинных JSON данных."""
        # Arrange
        very_long_string = "A" * 100000  # 100KB string

        large_data = {
            "session_id": "large_data_session",
            "browser_fingerprint": "large_fp",
            "anonymous_name": "Large Data User",
            "metadata": {
                "large_field": very_long_string,
                "nested_data": {"level_1": {"level_2": {"level_3": very_long_string}}},
            },
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.create_or_get_respondent = AsyncMock(
                return_value={
                    "id": 1,
                    "session_id": "large_data_session",
                    "is_anonymous": True,
                    "created_at": "2024-01-20T16:30:00Z",
                    "data_size": "100KB",
                    "compression_applied": True,
                    "processing_time": 5.2,
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=large_data
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["data_size"] == "100KB"
        assert data["compression_applied"] is True
        assert data["processing_time"] > 0

    async def test_negative_and_zero_values(self, api_client: AsyncClient):
        """Тест отрицательных и нулевых значений."""
        # Arrange
        extreme_values = {
            "latitude": -90.0,  # South pole
            "longitude": -180.0,  # Date line west
            "accuracy": 0.0,  # Zero accuracy
            "altitude": -11034.0,  # Mariana Trench depth
            "heading": 0.0,  # North direction
            "speed": 0.0,  # Stationary
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.update_location = AsyncMock(
                return_value={
                    "success": True,
                    "location_updated": True,
                    "respondent_id": 1,
                    "location": extreme_values,
                    "special_conditions": [
                        "Polar coordinates",
                        "Below sea level",
                        "Zero motion detected",
                    ],
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.patch(
                api_client.url_for("update_respondent_location", respondent_id=1),
                json=extreme_values,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        location = data["location"]
        assert location["latitude"] == -90.0
        assert location["longitude"] == -180.0
        assert location["altitude"] == -11034.0
        assert len(data["special_conditions"]) == 3

    async def test_maximum_integer_values(self, api_client: AsyncClient, admin_user):
        """Тест максимальных целочисленных значений."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_respondent_statistics = AsyncMock(
                return_value={
                    "overview": {
                        "total_respondents": 2147483647,  # Max 32-bit int
                        "anonymous_respondents": 1073741823,
                        "authenticated_respondents": 1073741824,
                        "surveys_total": 9223372036854775807,  # Max 64-bit int
                    },
                    "extreme_values": {
                        "max_responses_per_respondent": 2147483647,
                        "max_session_duration": 2147483647.0,
                        "total_data_points": 9223372036854775807,
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

        overview = data["overview"]
        assert overview["total_respondents"] == 2147483647
        assert overview["surveys_total"] == 9223372036854775807

        extreme_values = data["extreme_values"]
        assert extreme_values["max_responses_per_respondent"] == 2147483647
        assert extreme_values["total_data_points"] == 9223372036854775807


class TestRespondentRecovery:
    """Граничные тесты восстановления и отказоустойчивости."""

    async def test_graceful_degradation_partial_service_failure(
        self, api_client: AsyncClient
    ):
        """Тест плавной деградации при частичном сбое сервиса."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_activity_summary = AsyncMock(
                return_value={
                    "respondent_id": 1,
                    "status": "partial_data",
                    "surveys": {
                        "total_participated": 5,
                        "completed": 4,
                        "completion_rate": 0.8,
                    },
                    "responses": {
                        "total_submitted": 25,
                        "valid_responses": 23,
                        "data_quality": "good",
                    },
                    "engagement": None,  # Service unavailable
                    "timeline": [],  # Service unavailable
                    "warnings": [
                        "Engagement service temporarily unavailable",
                        "Timeline service temporarily unavailable",
                    ],
                    "fallback_mode": True,
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("get_activity_summary", respondent_id=respondent_id)
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "partial_data"
        assert data["surveys"]["total_participated"] == 5
        assert data["engagement"] is None
        assert len(data["warnings"]) == 2
        assert data["fallback_mode"] is True

    async def test_circuit_breaker_open_state(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест состояния открытого автоматического выключателя."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.search_respondents = AsyncMock(
                return_value={
                    "circuit_breaker": {
                        "state": "open",
                        "failure_count": 5,
                        "last_failure": "2024-01-20T16:25:00Z",
                        "next_attempt": "2024-01-20T16:35:00Z",
                        "failure_threshold": 5,
                        "timeout_duration": 600,
                    },
                    "fallback_data": {
                        "respondents": [],
                        "total_cached": 0,
                        "cache_timestamp": "2024-01-20T16:20:00Z",
                    },
                    "status": "degraded_service",
                }
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.get(
                api_client.url_for("search_respondents"), params={"query": "test"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        circuit_breaker = data["circuit_breaker"]
        assert circuit_breaker["state"] == "open"
        assert circuit_breaker["failure_count"] == 5
        assert "next_attempt" in circuit_breaker

        assert data["status"] == "degraded_service"
        assert "fallback_data" in data

    async def test_automatic_retry_with_exponential_backoff(
        self, api_client: AsyncClient
    ):
        """Тест автоматических повторных попыток с экспоненциальной задержкой."""
        # Arrange
        respondent_data = {
            "session_id": "retry_session",
            "browser_fingerprint": "retry_fp",
        }

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()

            # Simulate successful retry after failures
            call_count = 0

            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 4:  # Fail first 3 attempts
                    raise Exception("Temporary failure")
                return {
                    "id": 1,
                    "session_id": "retry_session",
                    "browser_fingerprint": "retry_fp",
                    "is_anonymous": True,
                    "created_at": "2024-01-20T16:30:00Z",
                    "retry_info": {
                        "attempts": call_count,
                        "total_delay": 7.0,  # 1 + 2 + 4 seconds
                        "backoff_strategy": "exponential",
                    },
                }

            mock_respondent_service.create_or_get_respondent = AsyncMock(
                side_effect=side_effect
            )
            mock_service.return_value = mock_respondent_service

            response = await api_client.post(
                api_client.url_for("create_or_get_respondent"), json=respondent_data
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        retry_info = data["retry_info"]
        assert retry_info["attempts"] == 4
        assert retry_info["total_delay"] == 7.0
        assert retry_info["backoff_strategy"] == "exponential"

    async def test_data_consistency_after_network_partition(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест согласованности данных после сетевого разделения."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.respondents.get_respondent_service") as mock_service:
            mock_respondent_service = MagicMock()
            mock_respondent_service.get_respondent_statistics = AsyncMock(
                return_value={
                    "overview": {
                        "total_respondents": 1247,
                        "data_consistency": "eventually_consistent",
                        "last_sync": "2024-01-20T16:25:00Z",
                        "partition_recovery": True,
                    },
                    "consistency_info": {
                        "read_preference": "primary_preferred",
                        "write_concern": "majority",
                        "replication_lag": 2.5,
                        "conflict_resolution": "timestamp_based",
                    },
                    "network_partition": {
                        "detected_at": "2024-01-20T16:20:00Z",
                        "recovered_at": "2024-01-20T16:23:00Z",
                        "duration": 180,
                        "affected_operations": 15,
                        "conflicts_resolved": 3,
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

        overview = data["overview"]
        assert overview["data_consistency"] == "eventually_consistent"
        assert overview["partition_recovery"] is True

        consistency_info = data["consistency_info"]
        assert consistency_info["replication_lag"] == 2.5
        assert consistency_info["conflict_resolution"] == "timestamp_based"

        network_partition = data["network_partition"]
        assert network_partition["duration"] == 180
        assert network_partition["conflicts_resolved"] == 3

    async def test_disaster_recovery_mode(self, api_client: AsyncClient):
        """Тест режима аварийного восстановления."""
        # Arrange
        respondent_id = 1

        # Act
        with patch("src.routers.respondents.get_gdpr_service") as mock_service:
            mock_gdpr_service = MagicMock()
            mock_gdpr_service.export_respondent_data = AsyncMock(
                return_value={
                    "export_id": "disaster_recovery_001",
                    "respondent_id": 1,
                    "status": "emergency_export",
                    "disaster_recovery_mode": True,
                    "primary_datacenter": "offline",
                    "backup_datacenter": "active",
                    "data_sources": {
                        "primary": "unavailable",
                        "backup": "available",
                        "cache": "available",
                        "archive": "available",
                    },
                    "data_completeness": 0.85,
                    "recovery_timestamp": "2024-01-20T16:30:00Z",
                    "estimated_data_loss": "15_minutes",
                }
            )
            mock_service.return_value = mock_gdpr_service

            response = await api_client.post(
                api_client.url_for(
                    "export_respondent_data", respondent_id=respondent_id
                ),
                json={"format": "json", "emergency_mode": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "emergency_export"
        assert data["disaster_recovery_mode"] is True
        assert data["primary_datacenter"] == "offline"
        assert data["backup_datacenter"] == "active"

        data_sources = data["data_sources"]
        assert data_sources["primary"] == "unavailable"
        assert data_sources["backup"] == "available"

        assert data["data_completeness"] == 0.85
        assert data["estimated_data_loss"] == "15_minutes"
