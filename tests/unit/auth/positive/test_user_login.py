"""
Positive тесты для входа пользователей.

Содержит тесты успешных сценариев входа по различным идентификаторам:
username, email, telegram_id, а также тесты JWT токенов.
"""

import pytest


class TestUserLoginPositive:
    """Positive тесты входа пользователей."""

    @pytest.mark.asyncio
    async def test_login_by_username(self, api_client, db_session, regular_user):
        """Тест успешного входа по username."""
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
        assert user["is_active"] is True

    @pytest.mark.asyncio
    async def test_login_by_email(self, api_client, db_session, regular_user):
        """Тест успешного входа по email."""
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
    async def test_login_by_telegram_id(self, api_client, db_session, telegram_user):
        """Тест успешного входа по Telegram ID."""
        # Arrange
        login_data = {"telegram_id": telegram_user.telegram_id}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["telegram_id"] == telegram_user.telegram_id
        assert user["id"] == telegram_user.id

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "login_identifier_type", ["username", "email"], indirect=True
    )
    async def test_login_by_different_identifiers(
        self, api_client, db_session, regular_user, login_identifier_type
    ):
        """Тест входа по различным типам идентификаторов."""
        # Arrange
        if login_identifier_type == "username":
            identifier = regular_user.username
        elif login_identifier_type == "email":
            identifier = regular_user.email
        else:
            pytest.skip(f"Unsupported identifier type: {login_identifier_type}")

        login_data = {"identifier": identifier}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_login_returns_valid_tokens(
        self, api_client, db_session, regular_user
    ):
        """Тест что вход возвращает валидные токены."""
        # Arrange
        login_data = {"identifier": regular_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Проверяем что access токен работает
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
    async def test_login_admin_user(self, api_client, db_session, admin_user):
        """Тест входа администратора."""
        # Arrange
        login_data = {"identifier": admin_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["id"] == admin_user.id
        assert user["is_admin"] is True
        assert user["is_active"] is True

    @pytest.mark.asyncio
    async def test_login_telegram_user(self, api_client, db_session, telegram_user):
        """Тест входа Telegram пользователя."""
        # Arrange
        login_data = {"identifier": telegram_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["id"] == telegram_user.id
        assert user["telegram_id"] == telegram_user.telegram_id
        assert user["telegram_username"] == telegram_user.telegram_username

    @pytest.mark.asyncio
    async def test_login_includes_user_profile(
        self, api_client, db_session, user_with_profile
    ):
        """Тест что вход включает данные профиля."""
        # Arrange
        user, profile = user_with_profile
        login_data = {"identifier": user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user_data = data["user"]
        assert user_data["id"] == user.id
        assert user_data["first_name"] == profile.first_name
        assert user_data["last_name"] == profile.last_name
        assert user_data["bio"] == profile.bio

    @pytest.mark.asyncio
    async def test_login_case_insensitive_email(
        self, api_client, db_session, regular_user
    ):
        """Тест что вход по email нечувствителен к регистру."""
        # Arrange
        login_data = {"identifier": regular_user.email.upper()}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_login_updates_last_login(self, api_client, db_session, regular_user):
        """Тест что вход обновляет время последнего входа."""
        # Arrange
        login_data = {"identifier": regular_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert "last_login" in user
        assert user["last_login"] is not None

    @pytest.mark.asyncio
    async def test_login_preserves_user_settings(
        self, api_client, db_session, regular_user
    ):
        """Тест что вход сохраняет пользовательские настройки."""
        # Arrange
        login_data = {"identifier": regular_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["language"] == regular_user.language
        assert user["timezone"] == regular_user.timezone

    @pytest.mark.asyncio
    async def test_login_with_fresh_token(self, api_client, db_session, regular_user):
        """Тест что новый токен имеет свежую дату истечения."""
        # Arrange
        login_data = {"identifier": regular_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        access_token = data["access_token"]

        # Проверяем что токен имеет правильную структуру
        from services.jwt_service import jwt_service

        decoded = jwt_service.decode_token(access_token)
        assert "user_id" in decoded
        assert "exp" in decoded
        assert decoded["user_id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_login_multiple_sessions(self, api_client, db_session, regular_user):
        """Тест что пользователь может иметь несколько активных сессий."""
        # Arrange
        login_data = {"identifier": regular_user.username}

        # Act - первый вход
        response1 = await api_client.post("/api/auth/login", json=login_data)
        assert response1.status_code == 200

        # Act - второй вход
        response2 = await api_client.post("/api/auth/login", json=login_data)
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


class TestJWTTokensPositive:
    """Positive тесты для JWT токенов."""

    @pytest.mark.asyncio
    async def test_access_token_validation(self, api_client, db_session, regular_user):
        """Тест валидации access токена."""
        # Arrange
        login_data = {"identifier": regular_user.username}
        response = await api_client.post("/api/auth/login", json=login_data)
        access_token = response.json()["access_token"]

        # Act
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert profile_response.status_code == 200
        data = profile_response.json()
        assert data["id"] == regular_user.id

    @pytest.mark.asyncio
    async def test_refresh_token_flow(self, api_client, db_session, regular_user):
        """Тест процесса обновления токена."""
        # Arrange
        login_data = {"identifier": regular_user.username}
        response = await api_client.post("/api/auth/login", json=login_data)
        refresh_token = response.json()["refresh_token"]

        # Act
        refresh_response = await api_client.post(
            "/api/auth/refresh", json={"refresh_token": refresh_token}
        )

        # Assert
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # Проверяем что новый access токен работает
        new_access_token = data["access_token"]
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = await api_client.get("/api/auth/profile", headers=headers)
        assert profile_response.status_code == 200

    @pytest.mark.asyncio
    async def test_token_contains_user_info(self, api_client, db_session, regular_user):
        """Тест что токен содержит информацию о пользователе."""
        # Arrange
        login_data = {"identifier": regular_user.username}
        response = await api_client.post("/api/auth/login", json=login_data)
        access_token = response.json()["access_token"]

        # Act
        from services.jwt_service import jwt_service

        decoded = jwt_service.decode_token(access_token)

        # Assert
        assert "user_id" in decoded
        assert "exp" in decoded
        assert decoded["user_id"] == regular_user.id
        assert decoded["exp"] > 0

    @pytest.mark.asyncio
    async def test_token_expiration_format(self, api_client, db_session, regular_user):
        """Тест формата времени истечения токена."""
        # Arrange
        login_data = {"identifier": regular_user.username}
        response = await api_client.post("/api/auth/login", json=login_data)
        access_token = response.json()["access_token"]

        # Act
        from services.jwt_service import jwt_service

        decoded = jwt_service.decode_token(access_token)

        # Assert
        import time

        current_time = int(time.time())
        token_exp = decoded["exp"]

        # Токен должен истечь в будущем
        assert token_exp > current_time
        # Но не слишком далеко (например, в разумных пределах)
        assert token_exp < current_time + 86400  # 24 часа
