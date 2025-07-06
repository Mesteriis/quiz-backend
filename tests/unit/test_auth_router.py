"""
Тесты для Authentication Router.

Этот модуль содержит тесты для всех endpoints аутентификации,
включая регистрацию, вход, Telegram аутентификацию и управление профилем.
"""

from pathlib import Path

# Локальные импорты
import sys

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))

from services.jwt_service import jwt_service


class TestUserRegistration:
    """Тесты регистрации пользователей."""

    @pytest.mark.asyncio
    async def test_successful_registration(self, api_client, db_session):
        """Тест успешной регистрации пользователя."""
        # Arrange
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "language": "en",
            "timezone": "UTC",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

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
        assert user["username"] == "newuser"
        assert user["email"] == "newuser@example.com"
        assert user["first_name"] == "New"
        assert user["last_name"] == "User"
        assert user["is_active"] is True
        assert user["is_admin"] is False

        # Проверяем JWT токены
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert len(data["access_token"]) > 10
        assert len(data["refresh_token"]) > 10

    @pytest.mark.asyncio
    async def test_registration_duplicate_username(
        self, api_client, db_session, regular_user
    ):
        """Тест ошибки при дублировании username."""
        # Arrange
        user_data = {
            "username": regular_user.username,  # Используем существующий username
            "email": "different@example.com",
            "first_name": "Different",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_duplicate_email(
        self, api_client, db_session, regular_user
    ):
        """Тест ошибки при дублировании email."""
        # Arrange
        user_data = {
            "username": "differentuser",
            "email": regular_user.email,  # Используем существующий email
            "first_name": "Different",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_invalid_data(self, api_client, db_session):
        """Тест ошибки при невалидных данных."""
        # Arrange
        invalid_data = {
            "username": "",  # Пустой username
            "email": "invalid-email",  # Невалидный email
            "first_name": "",
            "last_name": "",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=invalid_data)

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_registration_telegram_user(self, api_client, db_session):
        """Тест регистрации пользователя через Telegram."""
        # Arrange
        user_data = {
            "telegram_id": 123456789,
            "telegram_username": "tguser",
            "telegram_first_name": "Telegram",
            "telegram_last_name": "User",
            "first_name": "Telegram",
            "last_name": "User",
            "language": "ru",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_id"] == 123456789
        assert user["telegram_username"] == "tguser"
        assert user["telegram_first_name"] == "Telegram"
        assert user["telegram_last_name"] == "User"


class TestUserLogin:
    """Тесты входа пользователей."""

    @pytest.mark.asyncio
    async def test_login_by_username(self, api_client, db_session, regular_user):
        """Тест входа по username."""
        # Arrange
        login_data = {"identifier": regular_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data

        user = data["user"]
        assert user["username"] == regular_user.username
        assert user["id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_login_by_email(self, api_client, db_session, regular_user):
        """Тест входа по email."""
        # Arrange
        login_data = {"identifier": regular_user.email}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["email"] == regular_user.email
        assert user["id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_login_by_telegram_id(self, api_client, db_session, regular_user):
        """Тест входа по Telegram ID."""
        # Arrange
        login_data = {"telegram_id": regular_user.telegram_id}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_id"] == regular_user.telegram_id
        assert user["id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, api_client, db_session):
        """Тест ошибки при неверных credentials."""
        # Arrange
        login_data = {"identifier": "nonexistent_user"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, api_client, db_session):
        """Тест ошибки при отсутствии credentials."""
        # Arrange
        login_data = {}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "must be provided" in data["detail"].lower()


class TestTelegramAuthentication:
    """Тесты Telegram аутентификации."""

    @pytest.mark.asyncio
    async def test_telegram_auth_new_user(self, api_client, db_session):
        """Тест создания нового пользователя через Telegram."""
        # Arrange
        telegram_data = {
            "telegram_id": 999888777,
            "telegram_username": "newtguser",
            "telegram_first_name": "New",
            "telegram_last_name": "TgUser",
            "telegram_photo_url": "https://t.me/photo.jpg",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=telegram_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "user" in data
        assert "access_token" in data

        user = data["user"]
        assert user["telegram_id"] == 999888777
        assert user["telegram_username"] == "newtguser"
        assert user["telegram_first_name"] == "New"
        assert user["telegram_last_name"] == "TgUser"
        assert user["telegram_photo_url"] == "https://t.me/photo.jpg"

    @pytest.mark.asyncio
    async def test_telegram_auth_existing_user(
        self, api_client, db_session, regular_user
    ):
        """Тест обновления существующего пользователя через Telegram."""
        # Arrange
        telegram_data = {
            "telegram_id": regular_user.telegram_id,
            "telegram_username": "updatedusername",
            "telegram_first_name": "Updated",
            "telegram_last_name": "Name",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=telegram_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["id"] == regular_user.id
        assert user["telegram_username"] == "updatedusername"
        assert user["telegram_first_name"] == "Updated"
        assert user["telegram_last_name"] == "Name"

    @pytest.mark.asyncio
    async def test_telegram_auth_invalid_data(self, api_client, db_session):
        """Тест ошибки при невалидных Telegram данных."""
        # Arrange
        invalid_data = {
            "telegram_id": "invalid_id",  # Должно быть числом
            "telegram_username": "",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=invalid_data)

        # Assert
        assert response.status_code == 422  # Validation error


class TestUserProfile:
    """Тесты управления профилем пользователя."""

    @pytest.mark.asyncio
    async def test_get_current_user_profile(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест получения профиля текущего пользователя."""
        # Arrange
        headers = await auth_headers(regular_user)

        # Act
        response = await api_client.auth_get("/api/auth/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == regular_user.id
        assert data["username"] == regular_user.username
        assert data["email"] == regular_user.email
        assert data["first_name"] == regular_user.first_name
        assert data["last_name"] == regular_user.last_name
        assert data["is_active"] == regular_user.is_active
        assert data["is_admin"] == regular_user.is_admin

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, api_client, db_session):
        """Тест ошибки получения профиля без авторизации."""
        # Act
        response = await api_client.get("/api/auth/me")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест обновления профиля пользователя."""
        # Arrange
        headers = await auth_headers(regular_user)
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "Updated bio",
            "language": "ru",
        }

        # Act
        response = await api_client.auth_put(
            "/api/auth/profile", headers=headers, json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["bio"] == "Updated bio"
        assert data["language"] == "ru"

    @pytest.mark.asyncio
    async def test_update_profile_unauthorized(self, api_client, db_session):
        """Тест ошибки обновления профиля без авторизации."""
        # Arrange
        update_data = {"first_name": "Should Fail"}

        # Act
        response = await api_client.put("/api/auth/profile", json=update_data)

        # Assert
        assert response.status_code == 401


class TestUsersList:
    """Тесты получения списка пользователей."""

    @pytest.mark.asyncio
    async def test_get_users_list_admin(
        self, api_client, db_session, admin_user, auth_headers
    ):
        """Тест получения списка пользователей админом."""
        # Arrange
        headers = await auth_headers(admin_user)

        # Act
        response = await api_client.auth_get("/api/auth/users", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1  # Как минимум админ должен быть в списке

        # Проверяем структуру пользователя в списке
        user = data[0]
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "is_active" in user
        assert "is_admin" in user
        assert "created_at" in user

    @pytest.mark.asyncio
    async def test_get_users_list_regular_user(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест ошибки получения списка пользователей обычным пользователем."""
        # Arrange
        headers = await auth_headers(regular_user)

        # Act
        response = await api_client.auth_get("/api/auth/users", headers=headers)

        # Assert
        assert response.status_code == 403  # Forbidden

    @pytest.mark.asyncio
    async def test_get_users_list_unauthorized(self, api_client, db_session):
        """Тест ошибки получения списка пользователей без авторизации."""
        # Act
        response = await api_client.get("/api/auth/users")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_users_list_pagination(
        self, api_client, db_session, admin_user, auth_headers, create_test_data
    ):
        """Тест пагинации списка пользователей."""
        # Arrange
        headers = await auth_headers(admin_user)

        # Создаем несколько тестовых пользователей
        await create_test_data["users"](db_session, count=5)

        # Act
        response = await api_client.auth_get(
            "/api/auth/users?skip=0&limit=2", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 2  # Проверяем limit


class TestUserProfileById:
    """Тесты получения профиля пользователя по ID."""

    @pytest.mark.asyncio
    async def test_get_user_profile_by_id(self, api_client, db_session, regular_user):
        """Тест получения публичного профиля пользователя по ID."""
        # Act
        response = await api_client.get(f"/api/auth/users/{regular_user.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем публичные поля профиля
        assert data["id"] == regular_user.id
        assert data["display_name"] == regular_user.get_display_name()
        assert data["first_name"] == regular_user.first_name
        assert data["last_name"] == regular_user.last_name
        assert data["is_verified"] == regular_user.is_verified
        assert data["created_at"] is not None
        assert "responses_count" in data

        # Проверяем, что приватные поля не возвращаются
        assert "email" not in data or data["email"] is None

    @pytest.mark.asyncio
    async def test_get_user_profile_nonexistent(self, api_client, db_session):
        """Тест ошибки получения профиля несуществующего пользователя."""
        # Act
        response = await api_client.get("/api/auth/users/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestJWTTokens:
    """Тесты работы с JWT токенами."""

    @pytest.mark.asyncio
    async def test_token_validation(self, api_client, db_session, regular_user):
        """Тест валидации JWT токена."""
        # Arrange
        token = jwt_service.create_access_token(
            user_id=regular_user.id,
            username=regular_user.username,
            is_admin=regular_user.is_admin,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await api_client.auth_get("/api/auth/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_invalid_token(self, api_client, db_session):
        """Тест ошибки при невалидном токене."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = await api_client.auth_get("/api/auth/me", headers=headers)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token(self, api_client, db_session):
        """Тест ошибки при отсутствии токена."""
        # Act
        response = await api_client.get("/api/auth/me")

        # Assert
        assert response.status_code == 401


class TestAuthenticationIntegration:
    """Интеграционные тесты аутентификации."""

    @pytest.mark.asyncio
    async def test_full_auth_flow(self, api_client, db_session):
        """Тест полного потока аутентификации: регистрация -> вход -> профиль."""
        # 1. Регистрация
        register_data = {
            "username": "testflow",
            "email": "testflow@example.com",
            "first_name": "Test",
            "last_name": "Flow",
        }

        register_response = await api_client.post(
            "/api/auth/register", json=register_data
        )
        assert register_response.status_code == 200
        register_data = register_response.json()

        user_id = register_data["user"]["id"]
        access_token = register_data["access_token"]

        # 2. Проверка профиля с токеном из регистрации
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await api_client.auth_get("/api/auth/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["id"] == user_id

        # 3. Повторный вход
        login_data = {"identifier": "testflow"}
        login_response = await api_client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        login_data = login_response.json()

        new_access_token = login_data["access_token"]

        # 4. Проверка профиля с новым токеном
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        final_profile_response = await api_client.auth_get(
            "/api/auth/me", headers=new_headers
        )
        assert final_profile_response.status_code == 200
        final_profile_data = final_profile_response.json()
        assert final_profile_data["id"] == user_id

    @pytest.mark.asyncio
    async def test_telegram_to_regular_auth_flow(self, api_client, db_session):
        """Тест потока: Telegram аутентификация -> обычный вход."""
        # 1. Telegram аутентификация
        telegram_data = {
            "telegram_id": 555444333,
            "telegram_username": "testuser_tg",
            "telegram_first_name": "Test",
            "telegram_last_name": "TgUser",
        }

        tg_response = await api_client.post("/api/auth/telegram", json=telegram_data)
        assert tg_response.status_code == 200
        tg_data = tg_response.json()

        user_id = tg_data["user"]["id"]

        # 2. Попытка входа по Telegram ID
        login_data = {"telegram_id": 555444333}
        login_response = await api_client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        login_data = login_response.json()

        assert login_data["user"]["id"] == user_id
