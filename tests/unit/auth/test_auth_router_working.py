"""
Comprehensive Auth Router Tests for Quiz App.

Tests all authentication endpoints with proper polyfactory usage
and async fixture management to avoid scope mismatch errors.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from tests.factories.users.model_factories import UserModelFactory
from tests.factories.users.pydantic_factories import (
    UserCreateDataFactory,
    UserLoginDataFactory,
    TelegramAuthDataFactory,
    UserUpdateDataFactory,
)


class TestAuthRouterRegistration:
    """Tests for user registration endpoints."""

    @pytest.mark.asyncio
    async def test_successful_registration(
        self, api_client: AsyncClient, async_session
    ):
        """Test successful user registration with valid data."""
        # Arrange
        user_data = UserCreateDataFactory.build()
        created_user = UserModelFactory.build(
            id=1,
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock repository methods
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = None
            mock_user_repo.return_value.create.return_value = created_user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Act
            response = await api_client.post(
                "/auth/register", json=user_data.model_dump()
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "message" in data
            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data

            # Check user data
            user = data["user"]
            assert user["username"] == user_data.username
            assert user["email"] == user_data.email
            assert user["first_name"] == user_data.first_name
            assert user["last_name"] == user_data.last_name

            # Check tokens
            assert data["access_token"] == "access_token_123"
            assert data["refresh_token"] == "refresh_token_123"

    @pytest.mark.asyncio
    async def test_registration_duplicate_username(
        self, api_client: AsyncClient, async_session
    ):
        """Test registration error with duplicate username."""
        # Arrange
        user_data = UserCreateDataFactory.build()
        existing_user = UserModelFactory.build(username=user_data.username)

        with patch("src.routers.auth.get_user_repository") as mock_user_repo:
            # Mock existing username
            mock_user_repo.return_value.get_by_username.return_value = existing_user
            mock_user_repo.return_value.get_by_email.return_value = None

            # Act
            response = await api_client.post(
                "/auth/register", json=user_data.model_dump()
            )

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_duplicate_email(
        self, api_client: AsyncClient, async_session
    ):
        """Test registration error with duplicate email."""
        # Arrange
        user_data = UserCreateDataFactory.build()
        existing_user = UserModelFactory.build(email=user_data.email)

        with patch("src.routers.auth.get_user_repository") as mock_user_repo:
            # Mock existing email
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = existing_user

            # Act
            response = await api_client.post(
                "/auth/register", json=user_data.model_dump()
            )

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_telegram_user(
        self, api_client: AsyncClient, async_session
    ):
        """Test registration of Telegram user."""
        # Arrange
        user_data = UserCreateDataFactory.build(
            telegram_id=123456789,
            telegram_username="tguser",
            telegram_first_name="Telegram",
            telegram_last_name="User",
        )
        created_user = UserModelFactory.build(
            id=1,
            telegram_id=user_data.telegram_id,
            telegram_username=user_data.telegram_username,
            telegram_first_name=user_data.telegram_first_name,
            telegram_last_name=user_data.telegram_last_name,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock repository methods
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = None
            mock_user_repo.return_value.get_by_telegram_id.return_value = None
            mock_user_repo.return_value.create.return_value = created_user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Act
            response = await api_client.post(
                "/auth/register", json=user_data.model_dump()
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            user = data["user"]
            assert user["telegram_id"] == 123456789
            assert user["telegram_username"] == "tguser"


class TestAuthRouterLogin:
    """Tests for user login endpoints."""

    @pytest.mark.asyncio
    async def test_login_by_username(self, api_client: AsyncClient, async_session):
        """Test login by username."""
        # Arrange
        login_data = UserLoginDataFactory.build()
        user = UserModelFactory.build(
            id=1,
            username=login_data.identifier,
            is_active=True,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock repository methods
            mock_user_repo.return_value.get_by_username.return_value = user
            mock_user_repo.return_value.update_last_login.return_value = user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Act
            response = await api_client.post(
                "/auth/login", json=login_data.model_dump()
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data

            assert data["user"]["username"] == login_data.identifier
            assert data["user"]["id"] == 1

    @pytest.mark.asyncio
    async def test_login_by_email(self, api_client: AsyncClient, async_session):
        """Test login by email."""
        # Arrange
        email = "test@example.com"
        login_data = UserLoginDataFactory.build(identifier=email)
        user = UserModelFactory.build(
            id=1,
            email=email,
            is_active=True,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock repository methods
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = user
            mock_user_repo.return_value.update_last_login.return_value = user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Act
            response = await api_client.post(
                "/auth/login", json=login_data.model_dump()
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert data["user"]["email"] == email
            assert data["user"]["id"] == 1

    @pytest.mark.asyncio
    async def test_login_by_telegram_id(self, api_client: AsyncClient, async_session):
        """Test login by Telegram ID."""
        # Arrange
        telegram_id = 123456789
        login_data = {"telegram_id": telegram_id}
        user = UserModelFactory.build(
            id=1,
            telegram_id=telegram_id,
            is_active=True,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock repository methods
            mock_user_repo.return_value.get_by_telegram_id.return_value = user
            mock_user_repo.return_value.update_last_login.return_value = user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Act
            response = await api_client.post("/auth/login", json=login_data)

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert data["user"]["telegram_id"] == telegram_id
            assert data["user"]["id"] == 1

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self, api_client: AsyncClient, async_session
    ):
        """Test login with invalid credentials."""
        # Arrange
        login_data = UserLoginDataFactory.build()

        with patch("src.routers.auth.get_user_repository") as mock_user_repo:
            # Mock user not found
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = None

            # Act
            response = await api_client.post(
                "/auth/login", json=login_data.model_dump()
            )

            # Assert
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, api_client: AsyncClient, async_session):
        """Test login with inactive user."""
        # Arrange
        login_data = UserLoginDataFactory.build()
        user = UserModelFactory.build(
            username=login_data.identifier,
            is_active=False,
        )

        with patch("src.routers.auth.get_user_repository") as mock_user_repo:
            # Mock inactive user
            mock_user_repo.return_value.get_by_username.return_value = user

            # Act
            response = await api_client.post(
                "/auth/login", json=login_data.model_dump()
            )

            # Assert
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "inactive" in data["detail"].lower()


class TestAuthRouterTelegram:
    """Tests for Telegram authentication endpoints."""

    @pytest.mark.asyncio
    async def test_telegram_auth_new_user(self, api_client: AsyncClient, async_session):
        """Test Telegram auth creating new user."""
        # Arrange
        telegram_data = TelegramAuthDataFactory.build()
        created_user = UserModelFactory.build(
            id=1,
            telegram_id=telegram_data.telegram_id,
            telegram_username=telegram_data.telegram_username,
            telegram_first_name=telegram_data.telegram_first_name,
            telegram_last_name=telegram_data.telegram_last_name,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock user not exists, then create
            mock_user_repo.return_value.get_by_telegram_id.return_value = None
            mock_user_repo.return_value.create.return_value = created_user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Act
            response = await api_client.post(
                "/auth/telegram", json=telegram_data.model_dump()
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert "user" in data
            assert data["user"]["telegram_id"] == telegram_data.telegram_id
            assert data["user"]["telegram_username"] == telegram_data.telegram_username

    @pytest.mark.asyncio
    async def test_telegram_auth_existing_user(
        self, api_client: AsyncClient, async_session
    ):
        """Test Telegram auth with existing user."""
        # Arrange
        telegram_data = TelegramAuthDataFactory.build()
        existing_user = UserModelFactory.build(
            id=1,
            telegram_id=telegram_data.telegram_id,
            is_active=True,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock existing user
            mock_user_repo.return_value.get_by_telegram_id.return_value = existing_user
            mock_user_repo.return_value.update.return_value = existing_user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Act
            response = await api_client.post(
                "/auth/telegram", json=telegram_data.model_dump()
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert data["user"]["id"] == 1
            assert data["user"]["telegram_id"] == telegram_data.telegram_id


class TestAuthRouterProfile:
    """Tests for user profile endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_user_profile(
        self, api_client: AsyncClient, async_session
    ):
        """Test getting current user profile."""
        # Arrange
        user = UserModelFactory.build(id=1, username="testuser")
        token = "Bearer valid_token_123"

        with (
            patch("src.routers.auth.get_current_user") as mock_get_user,
        ):
            # Mock authenticated user
            mock_get_user.return_value = user

            # Act
            response = await api_client.get(
                "/auth/me", headers={"Authorization": token}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 1
            assert data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(
        self, api_client: AsyncClient, async_session
    ):
        """Test getting profile without authorization."""
        # Act
        response = await api_client.get("/auth/me")

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_profile(self, api_client: AsyncClient, async_session):
        """Test updating user profile."""
        # Arrange
        user = UserModelFactory.build(id=1, username="testuser")
        update_data = UserUpdateDataFactory.build()
        updated_user = UserModelFactory.build(
            id=1,
            first_name=update_data.first_name,
            last_name=update_data.last_name,
            bio=update_data.bio,
        )

        with (
            patch("src.routers.auth.get_current_user") as mock_get_user,
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
        ):
            # Mock authenticated user and repository
            mock_get_user.return_value = user
            mock_user_repo.return_value.update.return_value = updated_user

            # Act
            response = await api_client.put(
                "/auth/profile",
                json=update_data.model_dump(),
                headers={"Authorization": "Bearer valid_token_123"},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert data["first_name"] == update_data.first_name
            assert data["last_name"] == update_data.last_name
            assert data["bio"] == update_data.bio


class TestAuthRouterAdmin:
    """Tests for admin-only auth endpoints."""

    @pytest.mark.asyncio
    async def test_get_users_list_admin(self, api_client: AsyncClient, async_session):
        """Test getting users list as admin."""
        # Arrange
        admin_user = UserModelFactory.build(id=1, is_admin=True)
        users_list = [
            UserModelFactory.build(id=1),
            UserModelFactory.build(id=2),
            UserModelFactory.build(id=3),
        ]

        with (
            patch("src.routers.auth.get_admin_user") as mock_get_admin,
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
        ):
            # Mock admin user and repository
            mock_get_admin.return_value = admin_user
            mock_user_repo.return_value.get_multi.return_value = users_list

            # Act
            response = await api_client.get(
                "/auth/users", headers={"Authorization": "Bearer admin_token_123"}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert len(data) == 3
            assert all("id" in user for user in data)

    @pytest.mark.asyncio
    async def test_get_users_list_regular_user(
        self, api_client: AsyncClient, async_session
    ):
        """Test getting users list as regular user (should fail)."""
        # Arrange
        regular_user = UserModelFactory.build(id=1, is_admin=False)

        with patch("src.routers.auth.get_current_user") as mock_get_user:
            # Mock regular user
            mock_get_user.return_value = regular_user

            # Act
            response = await api_client.get(
                "/auth/users", headers={"Authorization": "Bearer user_token_123"}
            )

            # Assert
            assert response.status_code == 403


class TestAuthRouterIntegration:
    """Integration tests for auth workflows."""

    @pytest.mark.asyncio
    async def test_full_auth_flow(self, api_client: AsyncClient, async_session):
        """Test complete registration -> login -> profile workflow."""
        # Arrange
        user_data = UserCreateDataFactory.build()
        created_user = UserModelFactory.build(
            id=1,
            username=user_data.username,
            email=user_data.email,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock registration
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = None
            mock_user_repo.return_value.create.return_value = created_user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Step 1: Register
            register_response = await api_client.post(
                "/auth/register", json=user_data.model_dump()
            )
            assert register_response.status_code == 200

            register_data = register_response.json()
            access_token = register_data["access_token"]

            # Step 2: Get profile with token
            with patch("src.routers.auth.get_current_user") as mock_get_user:
                mock_get_user.return_value = created_user

                profile_response = await api_client.get(
                    "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
                )

                assert profile_response.status_code == 200
                profile_data = profile_response.json()
                assert profile_data["username"] == user_data.username

    @pytest.mark.asyncio
    async def test_telegram_auth_flow(self, api_client: AsyncClient, async_session):
        """Test Telegram authentication workflow."""
        # Arrange
        telegram_data = TelegramAuthDataFactory.build()
        created_user = UserModelFactory.build(
            id=1,
            telegram_id=telegram_data.telegram_id,
            telegram_username=telegram_data.telegram_username,
        )

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
            patch("src.routers.auth.get_current_user") as mock_get_user,
        ):
            # Mock Telegram auth
            mock_user_repo.return_value.get_by_telegram_id.return_value = None
            mock_user_repo.return_value.create.return_value = created_user

            # Mock JWT service
            mock_jwt_service.create_access_token.return_value = "access_token_123"
            mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"

            # Step 1: Telegram auth
            auth_response = await api_client.post(
                "/auth/telegram", json=telegram_data.model_dump()
            )
            assert auth_response.status_code == 200

            auth_data = auth_response.json()
            access_token = auth_data["access_token"]

            # Step 2: Access protected endpoint
            mock_get_user.return_value = created_user

            profile_response = await api_client.get(
                "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
            )

            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            assert profile_data["telegram_id"] == telegram_data.telegram_id


class TestAuthRouterValidation:
    """Tests for auth router input validation."""

    @pytest.mark.asyncio
    async def test_registration_missing_required_fields(
        self, api_client: AsyncClient, async_session
    ):
        """Test registration with missing required fields."""
        # Arrange
        invalid_data = {}

        # Act
        response = await api_client.post("/auth/register", json=invalid_data)

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_missing_identifier(
        self, api_client: AsyncClient, async_session
    ):
        """Test login with missing identifier."""
        # Arrange
        invalid_data = {}

        # Act
        response = await api_client.post("/auth/login", json=invalid_data)

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_telegram_auth_invalid_data(
        self, api_client: AsyncClient, async_session
    ):
        """Test Telegram auth with invalid data."""
        # Arrange
        invalid_data = {"telegram_id": "not_a_number"}

        # Act
        response = await api_client.post("/auth/telegram", json=invalid_data)

        # Assert
        assert response.status_code == 422  # Validation error


class TestAuthRouterErrorHandling:
    """Tests for auth router error handling."""

    @pytest.mark.asyncio
    async def test_database_error_handling(
        self, api_client: AsyncClient, async_session
    ):
        """Test handling of database errors during registration."""
        # Arrange
        user_data = UserCreateDataFactory.build()

        with patch("src.routers.auth.get_user_repository") as mock_user_repo:
            # Mock database error
            mock_user_repo.return_value.get_by_username.side_effect = Exception(
                "Database error"
            )

            # Act
            response = await api_client.post(
                "/auth/register", json=user_data.model_dump()
            )

            # Assert
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_jwt_service_error_handling(
        self, api_client: AsyncClient, async_session
    ):
        """Test handling of JWT service errors."""
        # Arrange
        user_data = UserCreateDataFactory.build()
        created_user = UserModelFactory.build()

        with (
            patch("src.routers.auth.get_user_repository") as mock_user_repo,
            patch("src.services.jwt_service.jwt_service") as mock_jwt_service,
        ):
            # Mock successful user creation but JWT error
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = None
            mock_user_repo.return_value.create.return_value = created_user
            mock_jwt_service.create_access_token.side_effect = Exception("JWT error")

            # Act
            response = await api_client.post(
                "/auth/register", json=user_data.model_dump()
            )

            # Assert
            assert response.status_code == 500
