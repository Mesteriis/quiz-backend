"""
Simple Auth Router Tests - Using working pattern from responses.

Tests critical auth endpoints with proper async fixture usage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.factories.users.model_factories import UserModelFactory
from tests.factories.users.pydantic_factories import UserCreateDataFactory


class TestAuthRouterSimple:
    """Simple auth router tests using working pattern."""

    @pytest.mark.asyncio
    async def test_registration_success(self, api_client, async_session):
        """Test successful user registration."""
        # Arrange
        user_data = UserCreateDataFactory.build()
        created_user = UserModelFactory.build(
            id=1,
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=True,
            is_admin=False,
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

    @pytest.mark.asyncio
    async def test_login_success(self, api_client, async_session):
        """Test successful user login."""
        # Arrange
        user = UserModelFactory.build(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True,
        )

        login_data = {"identifier": "testuser"}

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
            response = await api_client.post("/auth/login", json=login_data)

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_registration_duplicate_username(self, api_client, async_session):
        """Test registration with duplicate username."""
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
    async def test_login_invalid_credentials(self, api_client, async_session):
        """Test login with invalid credentials."""
        # Arrange
        login_data = {"identifier": "nonexistent_user"}

        with patch("src.routers.auth.get_user_repository") as mock_user_repo:
            # Mock user not found
            mock_user_repo.return_value.get_by_username.return_value = None
            mock_user_repo.return_value.get_by_email.return_value = None

            # Act
            response = await api_client.post("/auth/login", json=login_data)

            # Assert
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_profile(self, api_client, async_session):
        """Test getting current user profile."""
        # Arrange
        user = UserModelFactory.build(id=1, username="testuser")

        with patch("src.routers.auth.get_current_user") as mock_get_user:
            # Mock authenticated user
            mock_get_user.return_value = user

            # Act
            response = await api_client.get(
                "/auth/me", headers={"Authorization": "Bearer valid_token_123"}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 1
            assert data["username"] == "testuser"
