"""
Direct Auth Router Tests - No fixture dependencies.

Tests auth endpoints directly without relying on the problematic fixture configuration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import FastAPI

from tests.factories.users.model_factories import UserModelFactory
from tests.factories.users.pydantic_factories import UserCreateDataFactory

# Import the app directly
from src.main import app


@pytest.mark.asyncio
async def test_auth_registration_direct():
    """Test auth registration directly with minimal fixture dependency."""
    # Use hardcoded user data instead of factories to avoid fixture issues
    user_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "language": "en",
        "timezone": "UTC",
    }

    created_user = UserModelFactory.build(
        id=1,
        username=user_data["username"],
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
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

        # Create client directly
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Act
            response = await client.post("/auth/register", json=user_data)

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
            assert user["username"] == user_data["username"]
            assert user["email"] == user_data["email"]
            assert user["first_name"] == user_data["first_name"]
            assert user["last_name"] == user_data["last_name"]


@pytest.mark.asyncio
async def test_auth_login_direct():
    """Test auth login directly with minimal fixture dependency."""
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

        # Create client directly
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Act
            response = await client.post("/auth/login", json=login_data)

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_auth_duplicate_username_direct():
    """Test auth registration with duplicate username directly."""
    user_data = {
        "username": "duplicate_user",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
    }

    existing_user = UserModelFactory.build(username=user_data["username"])

    with patch("src.routers.auth.get_user_repository") as mock_user_repo:
        # Mock existing username
        mock_user_repo.return_value.get_by_username.return_value = existing_user
        mock_user_repo.return_value.get_by_email.return_value = None

        # Create client directly
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Act
            response = await client.post("/auth/register", json=user_data)

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_auth_invalid_credentials_direct():
    """Test auth login with invalid credentials directly."""
    login_data = {"identifier": "nonexistent_user"}

    with patch("src.routers.auth.get_user_repository") as mock_user_repo:
        # Mock user not found
        mock_user_repo.return_value.get_by_username.return_value = None
        mock_user_repo.return_value.get_by_email.return_value = None

        # Create client directly
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Act
            response = await client.post("/auth/login", json=login_data)

            # Assert
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Invalid credentials" in data["detail"]


@pytest.mark.asyncio
async def test_auth_get_profile_direct():
    """Test getting current user profile directly."""
    user = UserModelFactory.build(id=1, username="testuser")

    with patch("src.routers.auth.get_current_user") as mock_get_user:
        # Mock authenticated user
        mock_get_user.return_value = user

        # Create client directly
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Act
            response = await client.get(
                "/auth/me", headers={"Authorization": "Bearer valid_token_123"}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 1
            assert data["username"] == "testuser"
