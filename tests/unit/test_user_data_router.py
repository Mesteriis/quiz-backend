"""
Тесты для User Data Router.

Этот модуль содержит тесты для всех endpoints user_data router,
включая сбор данных пользователей, fingerprinting и геолокацию.
"""

from pathlib import Path

# Локальные импорты
import sys

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))


class TestCreateUserData:
    """Тесты создания данных пользователей."""

    @pytest.mark.asyncio
    async def test_create_user_data_success(self, api_client, db_session):
        """Тест успешного создания данных пользователя."""
        # Arrange
        user_data = {
            "session_id": "test_session_123",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "fingerprint": "unique_fingerprint_hash",
            "geolocation": {"latitude": 55.7558, "longitude": 37.6173},
            "device_info": {
                "platform": "desktop",
                "screen_width": 1920,
                "screen_height": 1080,
            },
            "telegram_user_id": 123456789,
            "telegram_username": "testuser",
            "telegram_first_name": "Test",
            "telegram_last_name": "User",
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_session_123"
        assert data["user_agent"] == user_data["user_agent"]
        assert data["fingerprint"] == user_data["fingerprint"]
        assert data["geolocation"] == user_data["geolocation"]
        assert data["telegram_user_id"] == user_data["telegram_user_id"]
        assert "id" in data
        assert "created_at" in data
        assert "ip_address" in data

    @pytest.mark.asyncio
    async def test_create_user_data_update_existing(self, api_client, db_session):
        """Тест обновления существующих данных пользователя."""
        # Arrange - создаем первоначальные данные
        initial_data = {
            "session_id": "existing_session",
            "user_agent": "Old User Agent",
            "fingerprint": "old_fingerprint",
            "telegram_user_id": 123456789,
        }

        # Создаем первую запись
        response1 = await api_client.post("/api/user-data/", json=initial_data)
        assert response1.status_code == 200

        # Обновляем данные
        updated_data = {
            "session_id": "existing_session",
            "user_agent": "New User Agent",
            "fingerprint": "new_fingerprint",
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "telegram_first_name": "Updated",
        }

        # Act
        response2 = await api_client.post("/api/user-data/", json=updated_data)

        # Assert
        assert response2.status_code == 200
        data = response2.json()
        assert data["session_id"] == "existing_session"
        assert data["user_agent"] == "New User Agent"
        assert data["fingerprint"] == "new_fingerprint"
        assert data["geolocation"] == updated_data["geolocation"]
        assert data["telegram_first_name"] == "Updated"
        assert data["telegram_user_id"] == 123456789  # Сохранено от первой записи

    @pytest.mark.asyncio
    async def test_create_user_data_minimal(self, api_client, db_session):
        """Тест создания данных с минимальными полями."""
        # Arrange
        minimal_data = {"session_id": "minimal_session"}

        # Act
        response = await api_client.post("/api/user-data/", json=minimal_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "minimal_session"
        assert "ip_address" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_user_data_invalid_data(self, api_client, db_session):
        """Тест создания данных с невалидными данными."""
        # Arrange
        invalid_data = {
            "session_id": "",  # Пустой session_id
            "geolocation": {"invalid": "data"},
        }

        # Act
        response = await api_client.post("/api/user-data/", json=invalid_data)

        # Assert
        assert response.status_code == 422  # Validation error


class TestGetUserData:
    """Тесты получения данных пользователей."""

    @pytest.mark.asyncio
    async def test_get_user_data_success(
        self, api_client, db_session, sample_user_data
    ):
        """Тест успешного получения данных пользователя."""
        # Act
        response = await api_client.get(f"/api/user-data/{sample_user_data.session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == sample_user_data.session_id
        assert data["id"] == sample_user_data.id
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_user_data_not_found(self, api_client, db_session):
        """Тест получения несуществующих данных пользователя."""
        # Act
        response = await api_client.get("/api/user-data/nonexistent_session")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "User data not found" in data["detail"]


class TestUpdateUserData:
    """Тесты обновления данных пользователей."""

    @pytest.mark.asyncio
    async def test_update_user_data_success(
        self, api_client, db_session, sample_user_data
    ):
        """Тест успешного обновления данных пользователя."""
        # Arrange
        update_data = {
            "user_agent": "Updated User Agent",
            "geolocation": {"latitude": 51.5074, "longitude": -0.1278},
            "telegram_first_name": "Updated Name",
        }

        # Act
        response = await api_client.put(
            f"/api/user-data/{sample_user_data.session_id}", json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_agent"] == "Updated User Agent"
        assert data["geolocation"] == update_data["geolocation"]
        assert data["telegram_first_name"] == "Updated Name"
        assert data["session_id"] == sample_user_data.session_id

    @pytest.mark.asyncio
    async def test_update_user_data_partial(
        self, api_client, db_session, sample_user_data
    ):
        """Тест частичного обновления данных пользователя."""
        # Arrange
        partial_update = {"telegram_last_name": "NewLastName"}

        # Act
        response = await api_client.put(
            f"/api/user-data/{sample_user_data.session_id}", json=partial_update
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_last_name"] == "NewLastName"
        assert data["session_id"] == sample_user_data.session_id

    @pytest.mark.asyncio
    async def test_update_user_data_not_found(self, api_client, db_session):
        """Тест обновления несуществующих данных пользователя."""
        # Arrange
        update_data = {"user_agent": "Updated User Agent"}

        # Act
        response = await api_client.put(
            "/api/user-data/nonexistent_session", json=update_data
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "User data not found" in data["detail"]


class TestCreateSessionData:
    """Тесты создания данных из сессионной информации."""

    @pytest.mark.asyncio
    async def test_create_session_data_success(self, api_client, db_session):
        """Тест успешного создания данных из сессии."""
        # Arrange
        session_data = {
            "session_id": "session_test_123",
            "referrer": "https://example.com",
            "fingerprint": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "language": "en-US",
                "platform": "Win32",
                "screen_width": 1920,
                "screen_height": 1080,
                "timezone": "America/New_York",
            },
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 10},
            "device_info": {
                "platform": "desktop",
                "browser": "Chrome",
                "version": "91.0.4472.124",
            },
            "telegram_data": {
                "user_id": 123456789,
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "language_code": "en",
                "photo_url": "https://t.me/i/userpic/320/testuser.jpg",
            },
        }

        # Act
        response = await api_client.post("/api/user-data/session", json=session_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session_test_123"
        assert data["referrer"] == "https://example.com"
        assert data["user_agent"] == session_data["fingerprint"]["user_agent"]
        assert data["telegram_user_id"] == 123456789
        assert data["telegram_username"] == "testuser"
        assert data["telegram_first_name"] == "Test"
        assert "fingerprint" in data
        assert "geolocation" in data
        assert "device_info" in data
        assert "browser_info" in data

    @pytest.mark.asyncio
    async def test_create_session_data_minimal(self, api_client, db_session):
        """Тест создания данных из минимальной сессии."""
        # Arrange
        minimal_session_data = {
            "session_id": "minimal_session_test",
            "fingerprint": {"user_agent": "Mozilla/5.0 (Minimal)"},
            "device_info": {"platform": "mobile"},
        }

        # Act
        response = await api_client.post(
            "/api/user-data/session", json=minimal_session_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "minimal_session_test"
        assert data["user_agent"] == "Mozilla/5.0 (Minimal)"

    @pytest.mark.asyncio
    async def test_create_session_data_update_existing(self, api_client, db_session):
        """Тест обновления существующих данных сессии."""
        # Arrange - создаем первоначальные данные
        initial_session_data = {
            "session_id": "update_session_test",
            "fingerprint": {"user_agent": "Old User Agent"},
            "device_info": {"platform": "desktop"},
        }

        # Создаем первую запись
        response1 = await api_client.post(
            "/api/user-data/session", json=initial_session_data
        )
        assert response1.status_code == 200

        # Обновляем данные
        updated_session_data = {
            "session_id": "update_session_test",
            "fingerprint": {"user_agent": "New User Agent"},
            "device_info": {"platform": "mobile"},
            "telegram_data": {"user_id": 987654321, "username": "newuser"},
        }

        # Act
        response2 = await api_client.post(
            "/api/user-data/session", json=updated_session_data
        )

        # Assert
        assert response2.status_code == 200
        data = response2.json()
        assert data["session_id"] == "update_session_test"
        assert data["user_agent"] == "New User Agent"
        assert data["telegram_user_id"] == 987654321
        assert data["telegram_username"] == "newuser"


class TestListUserData:
    """Тесты получения списка данных пользователей."""

    @pytest.mark.asyncio
    async def test_list_user_data_success(
        self, api_client, db_session, create_test_data
    ):
        """Тест успешного получения списка данных пользователей."""
        # Arrange - создаем тестовые данные
        test_data = []
        for i in range(5):
            data = {
                "session_id": f"test_session_{i}",
                "user_agent": f"Test User Agent {i}",
                "fingerprint": f"fingerprint_{i}",
            }
            response = await api_client.post("/api/user-data/", json=data)
            assert response.status_code == 200
            test_data.append(response.json())

        # Act
        response = await api_client.get("/api/user-data/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5
        assert all("session_id" in item for item in data)
        assert all("created_at" in item for item in data)

    @pytest.mark.asyncio
    async def test_list_user_data_pagination(self, api_client, db_session):
        """Тест пагинации списка данных пользователей."""
        # Arrange - создаем тестовые данные
        for i in range(10):
            data = {
                "session_id": f"pagination_test_{i}",
                "user_agent": f"Test User Agent {i}",
            }
            response = await api_client.post("/api/user-data/", json=data)
            assert response.status_code == 200

        # Act - получаем первую страницу
        response1 = await api_client.get("/api/user-data/?skip=0&limit=5")
        response2 = await api_client.get("/api/user-data/?skip=5&limit=5")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert len(data1) <= 5
        assert len(data2) <= 5

    @pytest.mark.asyncio
    async def test_list_user_data_empty(self, api_client, db_session):
        """Тест получения пустого списка данных пользователей."""
        # Act
        response = await api_client.get("/api/user-data/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestDeleteUserData:
    """Тесты удаления данных пользователей."""

    @pytest.mark.asyncio
    async def test_delete_user_data_success(
        self, api_client, db_session, sample_user_data
    ):
        """Тест успешного удаления данных пользователя."""
        # Act
        response = await api_client.delete(
            f"/api/user-data/{sample_user_data.session_id}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]

        # Проверяем, что данные действительно удалены
        get_response = await api_client.get(
            f"/api/user-data/{sample_user_data.session_id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_data_not_found(self, api_client, db_session):
        """Тест удаления несуществующих данных пользователя."""
        # Act
        response = await api_client.delete("/api/user-data/nonexistent_session")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "User data not found" in data["detail"]


class TestUserDataIntegration:
    """Интеграционные тесты для user_data router."""

    @pytest.mark.asyncio
    async def test_full_user_data_flow(self, api_client, db_session):
        """Тест полного потока работы с данными пользователя."""
        # Arrange
        session_id = "integration_test_session"

        # Act & Assert - создаем данные
        create_data = {
            "session_id": session_id,
            "user_agent": "Integration Test Agent",
            "fingerprint": "integration_fingerprint",
            "geolocation": {"latitude": 55.7558, "longitude": 37.6173},
            "telegram_user_id": 123456789,
        }

        create_response = await api_client.post("/api/user-data/", json=create_data)
        assert create_response.status_code == 200
        created_data = create_response.json()

        # Получаем данные
        get_response = await api_client.get(f"/api/user-data/{session_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["session_id"] == session_id
        assert get_data["user_agent"] == "Integration Test Agent"

        # Обновляем данные
        update_data = {
            "user_agent": "Updated Integration Agent",
            "telegram_first_name": "Integration",
        }

        update_response = await api_client.put(
            f"/api/user-data/{session_id}", json=update_data
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["user_agent"] == "Updated Integration Agent"
        assert updated_data["telegram_first_name"] == "Integration"

        # Проверяем в списке
        list_response = await api_client.get("/api/user-data/")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert any(item["session_id"] == session_id for item in list_data)

        # Удаляем данные
        delete_response = await api_client.delete(f"/api/user-data/{session_id}")
        assert delete_response.status_code == 200

        # Проверяем, что данные удалены
        final_get_response = await api_client.get(f"/api/user-data/{session_id}")
        assert final_get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_session_data_flow(self, api_client, db_session):
        """Тест потока создания данных из сессии."""
        # Arrange
        session_id = "session_integration_test"

        # Act & Assert - создаем данные из сессии
        session_data = {
            "session_id": session_id,
            "referrer": "https://integration-test.com",
            "fingerprint": {
                "user_agent": "Session Integration Agent",
                "language": "en-US",
                "platform": "Win32",
                "screen_width": 1920,
                "screen_height": 1080,
            },
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 10},
            "device_info": {"platform": "desktop", "browser": "Chrome"},
            "telegram_data": {
                "user_id": 987654321,
                "username": "sessionuser",
                "first_name": "Session",
                "last_name": "User",
            },
        }

        session_response = await api_client.post(
            "/api/user-data/session", json=session_data
        )
        assert session_response.status_code == 200
        session_result = session_response.json()

        # Проверяем, что данные корректно преобразованы
        assert session_result["session_id"] == session_id
        assert session_result["referrer"] == "https://integration-test.com"
        assert session_result["user_agent"] == "Session Integration Agent"
        assert session_result["telegram_user_id"] == 987654321
        assert session_result["telegram_username"] == "sessionuser"
        assert session_result["telegram_first_name"] == "Session"
        assert session_result["telegram_last_name"] == "User"

        # Проверяем, что данные можно получить через обычный GET
        get_response = await api_client.get(f"/api/user-data/{session_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["session_id"] == session_id
        assert get_data["user_agent"] == "Session Integration Agent"

    @pytest.mark.asyncio
    async def test_fingerprint_and_geolocation_handling(self, api_client, db_session):
        """Тест обработки fingerprint и geolocation данных."""
        # Arrange
        session_id = "fingerprint_test_session"

        # Act - создаем данные с комплексными fingerprint и geolocation
        complex_data = {
            "session_id": session_id,
            "fingerprint": {
                "user_agent": "Complex Fingerprint Agent",
                "language": "ru-RU",
                "platform": "MacIntel",
                "screen_width": 2560,
                "screen_height": 1440,
                "timezone": "Europe/Moscow",
                "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer"],
                "canvas_hash": "complex_canvas_hash_123",
            },
            "geolocation": {
                "latitude": 55.7558,
                "longitude": 37.6173,
                "accuracy": 5,
                "altitude": 156,
                "heading": 90,
                "speed": 0,
            },
            "device_info": {
                "platform": "desktop",
                "browser": "Chrome",
                "version": "91.0.4472.124",
                "mobile": False,
                "touch": False,
            },
        }

        session_response = await api_client.post(
            "/api/user-data/session", json=complex_data
        )

        # Assert
        assert session_response.status_code == 200
        data = session_response.json()
        assert data["session_id"] == session_id
        assert data["user_agent"] == "Complex Fingerprint Agent"
        assert "fingerprint" in data
        assert "geolocation" in data
        assert "device_info" in data
        assert "browser_info" in data

        # Проверяем, что данные корректно сохранены
        get_response = await api_client.get(f"/api/user-data/{session_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["geolocation"]["latitude"] == 55.7558
        assert get_data["geolocation"]["longitude"] == 37.6173
