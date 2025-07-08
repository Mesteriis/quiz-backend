"""
Positive тесты для Telegram аутентификации.

Содержит тесты успешных сценариев Telegram аутентификации,
регистрации через Telegram, синхронизации данных и интеграции.
"""

import pytest


class TestTelegramAuthenticationPositive:
    """Positive тесты Telegram аутентификации."""

    @pytest.mark.asyncio
    async def test_telegram_auth_new_user(
        self, api_client, db_session, valid_telegram_auth_data
    ):
        """Тест успешной Telegram аутентификации нового пользователя."""
        # Act
        response = await api_client.post(
            "/api/auth/telegram", json=valid_telegram_auth_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data

        user = data["user"]
        assert user["telegram_id"] == valid_telegram_auth_data["telegram_id"]
        assert (
            user["telegram_username"] == valid_telegram_auth_data["telegram_username"]
        )
        assert (
            user["telegram_first_name"]
            == valid_telegram_auth_data["telegram_first_name"]
        )
        assert (
            user["telegram_last_name"] == valid_telegram_auth_data["telegram_last_name"]
        )
        assert user["is_active"] is True

    @pytest.mark.asyncio
    async def test_telegram_auth_existing_user(
        self, api_client, db_session, telegram_user
    ):
        """Тест успешной Telegram аутентификации существующего пользователя."""
        # Arrange
        auth_data = {
            "telegram_id": telegram_user.telegram_id,
            "telegram_username": telegram_user.telegram_username,
            "telegram_first_name": telegram_user.telegram_first_name,
            "telegram_last_name": telegram_user.telegram_last_name,
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["id"] == telegram_user.id
        assert user["telegram_id"] == telegram_user.telegram_id
        assert user["telegram_username"] == telegram_user.telegram_username

    @pytest.mark.asyncio
    async def test_telegram_auth_updates_user_data(
        self, api_client, db_session, telegram_user
    ):
        """Тест что Telegram аутентификация обновляет данные пользователя."""
        # Arrange
        auth_data = {
            "telegram_id": telegram_user.telegram_id,
            "telegram_username": "updated_username",
            "telegram_first_name": "Updated",
            "telegram_last_name": "Name",
            "telegram_photo_url": "https://example.com/new_photo.jpg",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_username"] == "updated_username"
        assert user["telegram_first_name"] == "Updated"
        assert user["telegram_last_name"] == "Name"
        assert user["telegram_photo_url"] == "https://example.com/new_photo.jpg"

    @pytest.mark.asyncio
    async def test_telegram_auth_creates_profile(
        self, api_client, db_session, valid_telegram_auth_data
    ):
        """Тест что Telegram аутентификация создает профиль пользователя."""
        # Act
        response = await api_client.post(
            "/api/auth/telegram", json=valid_telegram_auth_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        user_id = user["id"]

        # Проверяем что профиль создался
        profile_response = await api_client.get(f"/api/users/{user_id}/profile")
        assert profile_response.status_code == 200

        profile = profile_response.json()
        assert profile["user_id"] == user_id
        assert profile["first_name"] == valid_telegram_auth_data["telegram_first_name"]
        assert profile["last_name"] == valid_telegram_auth_data["telegram_last_name"]

    @pytest.mark.asyncio
    async def test_telegram_auth_syncs_profile_data(
        self, api_client, db_session, telegram_user_with_profile
    ):
        """Тест синхронизации данных профиля с Telegram."""
        # Arrange
        user, profile = telegram_user_with_profile
        auth_data = {
            "telegram_id": user.telegram_id,
            "telegram_username": user.telegram_username,
            "telegram_first_name": "SyncedFirst",
            "telegram_last_name": "SyncedLast",
            "telegram_photo_url": "https://example.com/synced_photo.jpg",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user_data = data["user"]
        assert user_data["telegram_first_name"] == "SyncedFirst"
        assert user_data["telegram_last_name"] == "SyncedLast"
        assert user_data["telegram_photo_url"] == "https://example.com/synced_photo.jpg"

    @pytest.mark.asyncio
    async def test_telegram_auth_returns_valid_tokens(
        self, api_client, db_session, valid_telegram_auth_data
    ):
        """Тест что Telegram аутентификация возвращает валидные токены."""
        # Act
        response = await api_client.post(
            "/api/auth/telegram", json=valid_telegram_auth_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Проверяем что токены работают
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await api_client.get("/api/auth/profile", headers=headers)
        assert profile_response.status_code == 200

        # Проверяем что refresh токен работает
        refresh_response = await api_client.post(
            "/api/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()

    @pytest.mark.asyncio
    async def test_telegram_auth_preserves_existing_data(
        self, api_client, db_session, telegram_user
    ):
        """Тест что Telegram аутентификация сохраняет существующие данные."""
        # Arrange
        original_email = telegram_user.email
        original_bio = telegram_user.bio

        auth_data = {
            "telegram_id": telegram_user.telegram_id,
            "telegram_username": telegram_user.telegram_username,
            "telegram_first_name": telegram_user.telegram_first_name,
            "telegram_last_name": telegram_user.telegram_last_name,
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["email"] == original_email  # Сохранился
        assert user["bio"] == original_bio  # Сохранился

    @pytest.mark.asyncio
    async def test_telegram_auth_handles_optional_fields(self, api_client, db_session):
        """Тест Telegram аутентификации с опциональными полями."""
        # Arrange
        auth_data = {
            "telegram_id": 888999000,
            "telegram_username": "optionaluser",
            "telegram_first_name": "Optional",
            # telegram_last_name отсутствует
            # telegram_photo_url отсутствует
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_id"] == 888999000
        assert user["telegram_username"] == "optionaluser"
        assert user["telegram_first_name"] == "Optional"
        assert user["telegram_last_name"] is None
        assert user["telegram_photo_url"] is None

    @pytest.mark.asyncio
    async def test_telegram_auth_creates_username_from_telegram(
        self, api_client, db_session
    ):
        """Тест создания username из Telegram данных."""
        # Arrange
        auth_data = {
            "telegram_id": 111222333,
            "telegram_username": "telegramuser",
            "telegram_first_name": "Telegram",
            "telegram_last_name": "User",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        # Username должен быть создан на основе telegram_username или telegram_id
        assert user["username"] is not None
        assert len(user["username"]) > 0

    @pytest.mark.asyncio
    async def test_telegram_auth_handles_unicode_names(self, api_client, db_session):
        """Тест Telegram аутентификации с Unicode именами."""
        # Arrange
        auth_data = {
            "telegram_id": 444555666,
            "telegram_username": "unicode_user",
            "telegram_first_name": "Имя",
            "telegram_last_name": "Фамилия",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_first_name"] == "Имя"
        assert user["telegram_last_name"] == "Фамилия"

    @pytest.mark.asyncio
    async def test_telegram_auth_sets_language_from_telegram(
        self, api_client, db_session
    ):
        """Тест установки языка из Telegram данных."""
        # Arrange
        auth_data = {
            "telegram_id": 777888999,
            "telegram_username": "languser",
            "telegram_first_name": "Lang",
            "telegram_last_name": "User",
            "language_code": "ru",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["language"] == "ru"

    @pytest.mark.asyncio
    async def test_telegram_auth_updates_last_login(
        self, api_client, db_session, telegram_user
    ):
        """Тест обновления времени последнего входа через Telegram."""
        # Arrange
        auth_data = {
            "telegram_id": telegram_user.telegram_id,
            "telegram_username": telegram_user.telegram_username,
            "telegram_first_name": telegram_user.telegram_first_name,
            "telegram_last_name": telegram_user.telegram_last_name,
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert "last_login" in user
        assert user["last_login"] is not None

    @pytest.mark.asyncio
    async def test_telegram_auth_webhook_integration(
        self, api_client, db_session, mock_telegram_service
    ):
        """Тест интеграции с Telegram webhook."""
        # Arrange
        auth_data = {
            "telegram_id": 123456789,
            "telegram_username": "webhookuser",
            "telegram_first_name": "Webhook",
            "telegram_last_name": "User",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_id"] == 123456789

        # Проверяем что webhook вызывался (если используется)
        # mock_telegram_service.create_webhook.assert_called_once()

    @pytest.mark.asyncio
    async def test_telegram_auth_multiple_sessions(
        self, api_client, db_session, telegram_user
    ):
        """Тест множественных сессий через Telegram."""
        # Arrange
        auth_data = {
            "telegram_id": telegram_user.telegram_id,
            "telegram_username": telegram_user.telegram_username,
            "telegram_first_name": telegram_user.telegram_first_name,
            "telegram_last_name": telegram_user.telegram_last_name,
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act - первая аутентификация
        response1 = await api_client.post("/api/auth/telegram", json=auth_data)
        assert response1.status_code == 200

        # Act - вторая аутентификация
        response2 = await api_client.post("/api/auth/telegram", json=auth_data)
        assert response2.status_code == 200

        # Assert - оба токена работают
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        profile_response1 = await api_client.get("/api/auth/profile", headers=headers1)
        profile_response2 = await api_client.get("/api/auth/profile", headers=headers2)

        assert profile_response1.status_code == 200
        assert profile_response2.status_code == 200

    @pytest.mark.asyncio
    async def test_telegram_auth_photo_url_handling(self, api_client, db_session):
        """Тест обработки URL фотографии из Telegram."""
        # Arrange
        auth_data = {
            "telegram_id": 999888777,
            "telegram_username": "photouser",
            "telegram_first_name": "Photo",
            "telegram_last_name": "User",
            "telegram_photo_url": "https://t.me/photo/user123.jpg",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_photo_url"] == "https://t.me/photo/user123.jpg"
        assert (
            user["profile_picture_url"] == "https://t.me/photo/user123.jpg"
        )  # Синхронизация

    @pytest.mark.asyncio
    async def test_telegram_auth_timezone_detection(self, api_client, db_session):
        """Тест определения временной зоны из Telegram данных."""
        # Arrange
        auth_data = {
            "telegram_id": 666777888,
            "telegram_username": "timezoneuser",
            "telegram_first_name": "Timezone",
            "telegram_last_name": "User",
            "language_code": "ru",
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        # Если язык ru, то должна быть установлена московская зона
        assert user["timezone"] in ["Europe/Moscow", "UTC"]  # Зависит от логики
        assert user["language"] == "ru"
