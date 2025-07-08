"""
Positive тесты для регистрации пользователей.

Содержит тесты успешных сценариев регистрации обычных пользователей,
админов, Telegram пользователей и интеграции с профилями.
"""

import pytest


class TestUserRegistrationPositive:
    """Positive тесты регистрации пользователей."""

    @pytest.mark.asyncio
    async def test_successful_registration(
        self, api_client, db_session, valid_registration_data
    ):
        """Тест успешной регистрации пользователя."""
        # Act
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "message" in data
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data

        # Проверяем данные пользователя
        user = data["user"]
        assert user["username"] == valid_registration_data["username"]
        assert user["email"] == valid_registration_data["email"]
        assert user["first_name"] == valid_registration_data["first_name"]
        assert user["last_name"] == valid_registration_data["last_name"]
        assert user["is_active"] is True
        assert user["is_admin"] is False

        # Проверяем JWT токены
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert len(data["access_token"]) > 10
        assert len(data["refresh_token"]) > 10

    @pytest.mark.asyncio
    async def test_registration_telegram_user(
        self, api_client, db_session, valid_telegram_auth_data
    ):
        """Тест успешной регистрации пользователя через Telegram."""
        # Arrange
        user_data = {
            "telegram_id": valid_telegram_auth_data["telegram_id"],
            "telegram_username": valid_telegram_auth_data["telegram_username"],
            "telegram_first_name": valid_telegram_auth_data["telegram_first_name"],
            "telegram_last_name": valid_telegram_auth_data["telegram_last_name"],
            "first_name": valid_telegram_auth_data["telegram_first_name"],
            "last_name": valid_telegram_auth_data["telegram_last_name"],
            "language": "ru",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

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

    @pytest.mark.asyncio
    async def test_registration_with_all_fields(self, api_client, db_session):
        """Тест регистрации с заполнением всех возможных полей."""
        # Arrange
        complete_user_data = {
            "username": "completeuser",
            "email": "complete@example.com",
            "first_name": "Complete",
            "last_name": "User",
            "bio": "Complete user bio",
            "location": "Test City",
            "language": "en",
            "timezone": "UTC",
            "telegram_id": 987654321,
            "telegram_username": "completeuser",
            "telegram_first_name": "Complete",
            "telegram_last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=complete_user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["username"] == complete_user_data["username"]
        assert user["email"] == complete_user_data["email"]
        assert user["bio"] == complete_user_data["bio"]
        assert user["location"] == complete_user_data["location"]
        assert user["language"] == complete_user_data["language"]
        assert user["timezone"] == complete_user_data["timezone"]
        assert user["telegram_id"] == complete_user_data["telegram_id"]

    @pytest.mark.asyncio
    async def test_registration_creates_profile(
        self, api_client, db_session, valid_registration_data
    ):
        """Тест что регистрация создает профиль пользователя."""
        # Act
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
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
        assert profile["first_name"] == valid_registration_data["first_name"]
        assert profile["last_name"] == valid_registration_data["last_name"]

    @pytest.mark.asyncio
    async def test_registration_returns_valid_tokens(
        self, api_client, db_session, valid_registration_data
    ):
        """Тест что регистрация возвращает валидные токены."""
        # Act
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
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
    @pytest.mark.parametrize(
        "localization_params",
        [
            {"language": "en", "timezone": "UTC"},
            {"language": "ru", "timezone": "Europe/Moscow"},
            {"language": "zh-CN", "timezone": "Asia/Shanghai"},
        ],
        indirect=True,
    )
    async def test_registration_with_localization(
        self, api_client, db_session, localization_params
    ):
        """Тест регистрации с различными настройками локализации."""
        # Arrange
        user_data = {
            "username": "localuser",
            "email": "local@example.com",
            "first_name": "Local",
            "last_name": "User",
            **localization_params,
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["language"] == localization_params["language"]
        assert user["timezone"] == localization_params["timezone"]

    @pytest.mark.asyncio
    async def test_registration_activates_user(
        self, api_client, db_session, valid_registration_data
    ):
        """Тест что регистрация активирует пользователя."""
        # Act
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["is_active"] is True
        assert user["is_verified"] is False  # По умолчанию не верифицирован
        assert user["is_admin"] is False  # По умолчанию не админ

    @pytest.mark.asyncio
    async def test_registration_sets_creation_timestamp(
        self, api_client, db_session, valid_registration_data
    ):
        """Тест что регистрация устанавливает временные метки."""
        # Act
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert "created_at" in user
        assert "updated_at" in user
        assert user["created_at"] is not None
        assert user["updated_at"] is not None

    @pytest.mark.asyncio
    async def test_registration_telegram_sync(self, api_client, db_session):
        """Тест синхронизации данных с Telegram при регистрации."""
        # Arrange
        telegram_user_data = {
            "telegram_id": 555666777,
            "telegram_username": "syncuser",
            "telegram_first_name": "Sync",
            "telegram_last_name": "User",
            "telegram_photo_url": "https://example.com/photo.jpg",
            "first_name": "Sync",
            "last_name": "User",
            "language": "ru",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=telegram_user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_id"] == telegram_user_data["telegram_id"]
        assert user["telegram_username"] == telegram_user_data["telegram_username"]
        assert user["telegram_first_name"] == telegram_user_data["telegram_first_name"]
        assert user["telegram_last_name"] == telegram_user_data["telegram_last_name"]
        assert user["telegram_photo_url"] == telegram_user_data["telegram_photo_url"]
