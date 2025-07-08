"""
Authentication API router for the Quiz App.

This module contains FastAPI endpoints for user authentication,
registration, and profile management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.user import User
from schemas.user import (
    UserCreate,
    UserLogin,
    TelegramAuth,
    UserProfile,
    UserResponse,
    UserUpdate,
    RefreshTokenRequest,
)
from repositories.dependencies import get_user_repository
from repositories.user import UserRepository
from schemas.admin import SuccessResponse
from services.jwt_service import jwt_service

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials
        user_repo: User repository

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    try:
        # Verify token to get user ID
        payload = jwt_service.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from repository
        user = await user_repo.get(int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Optional[User]:
    """
    Dependency to get current user if token is provided (optional authentication).

    Args:
        authorization: Authorization header
        user_repo: User repository

    Returns:
        User or None: Current user if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]

    try:
        # Verify token to get user ID
        payload = jwt_service.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id")

        if not user_id:
            return None

        # Get user from repository
        user = await user_repo.get(int(user_id))
        return user

    except Exception:
        return None


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user is an admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user


@router.post("/register", response_model=dict)
async def register_user(
    user_data: UserCreate, user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Register a new user.

    Creates a new user account and returns JWT tokens.
    Supports both regular and Telegram users.
    """
    try:
        # Check if user already exists
        if user_data.telegram_id:
            existing_user = await user_repo.get_by_telegram_id(user_data.telegram_id)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this Telegram ID already exists",
                )

        if user_data.username:
            existing_user = await user_repo.get_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this username already exists",
                )

        if user_data.email:
            existing_user = await user_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )

        # Create user
        user = await user_repo.create(obj_in=user_data)

        # Generate tokens
        tokens = _generate_user_tokens(user)

        return {
            "message": "User created successfully",
            "user": UserResponse.model_validate(user).model_dump(),
            **tokens,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {e!s}",
        )


@router.post("/login", response_model=dict)
async def login_user(
    login_data: UserLogin,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Authenticate user and return JWT tokens.

    Supports authentication by:
    - Username/email + no password (for simplicity)
    - Telegram ID
    """
    try:
        if not login_data.identifier and not login_data.telegram_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either identifier or telegram_id must be provided",
            )

        user = None

        # Authenticate by Telegram ID
        if login_data.telegram_id:
            user = await user_repo.get_by_telegram_id(login_data.telegram_id)
        # Authenticate by username/email
        elif login_data.identifier:
            user = await user_repo.get_by_identifier(login_data.identifier)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or user not found",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active",
            )

        # Generate tokens
        tokens = _generate_user_tokens(user)

        return {
            "message": "Login successful",
            "user": UserResponse.model_validate(user).model_dump(),
            **tokens,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {e!s}",
        )


@router.post("/telegram", response_model=dict)
async def telegram_auth(
    telegram_data: TelegramAuth,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Authenticate or register user via Telegram.

    Creates a new user if doesn't exist, or authenticates existing user.
    """
    try:
        # Check if user already exists
        existing_user = await user_repo.get_by_telegram_id(telegram_data.telegram_id)

        if existing_user:
            # User exists, update their Telegram data and authenticate
            update_data = UserUpdate(
                telegram_username=telegram_data.telegram_username,
                telegram_first_name=telegram_data.telegram_first_name,
                telegram_last_name=telegram_data.telegram_last_name,
                first_name=telegram_data.telegram_first_name
                or existing_user.first_name,
                last_name=telegram_data.telegram_last_name or existing_user.last_name,
            )

            updated_user = await user_repo.update(
                db_obj=existing_user, obj_in=update_data
            )
            tokens = _generate_user_tokens(updated_user)

            return {
                "message": "Telegram authentication successful",
                "user": UserResponse.model_validate(updated_user).model_dump(),
                **tokens,
            }
        else:
            # User doesn't exist, create new
            user_data = UserCreate(
                username=telegram_data.telegram_username
                or f"user_{telegram_data.telegram_id}",
                email=None,
                telegram_id=telegram_data.telegram_id,
                telegram_username=telegram_data.telegram_username,
                telegram_first_name=telegram_data.telegram_first_name,
                telegram_last_name=telegram_data.telegram_last_name,
                telegram_photo_url=telegram_data.telegram_photo_url,
                first_name=telegram_data.telegram_first_name,
                last_name=telegram_data.telegram_last_name,
                display_name=telegram_data.telegram_first_name
                or telegram_data.telegram_username
                or f"User {telegram_data.telegram_id}",
            )

            user = await user_repo.create(obj_in=user_data)

            # Generate tokens
            tokens = _generate_user_tokens(user)

            return {
                "message": "Telegram user created and authenticated",
                "user": UserResponse.model_validate(user).model_dump(),
                **tokens,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telegram authentication failed: {e!s}",
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Refresh JWT access token using refresh token.

    Validates refresh token and returns new access token.
    """
    try:
        # Verify refresh token to get user ID
        payload = jwt_service.verify_token(request.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Get user from repository
        user = await user_repo.get(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Generate new access token
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            is_admin=user.is_admin,
        )

        return {
            "message": "Token refreshed successfully",
            "access_token": access_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {e!s}",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.

    Returns detailed profile information for the authenticated user.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Update current user's profile information.

    Allows users to update their own profile data.
    """
    try:
        # Update user using repository
        updated_user = await user_repo.update(db_obj=current_user, obj_in=user_data)

        return UserResponse.model_validate(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {e!s}",
        )


@router.get("/users", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Get all users (admin only).

    Returns paginated list of all users in the system.
    """
    try:
        # Get users using repository
        users = await user_repo.get_multi(skip=skip, limit=limit)

        return [UserResponse.model_validate(user) for user in users]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {e!s}",
        )


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get user profile by ID.

    Returns public profile information for any user.
    """
    try:
        # Get user using repository
        user = await user_repo.get(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Create profile response
        profile = UserProfile(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            first_name=user.first_name,
            last_name=user.last_name,
            bio=user.bio,
            telegram_username=user.telegram_username,
            telegram_photo_url=user.telegram_photo_url,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {e!s}",
        )


@router.post("/verify-token", response_model=dict)
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify JWT token validity.

    Returns token validity status and user information.
    """
    return {
        "message": "Token is valid",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin,
            "is_verified": current_user.is_verified,
        },
        "token_valid": True,
    }


@router.delete("/logout", response_model=SuccessResponse)
async def logout_user(current_user: User = Depends(get_current_user)):
    """
    Logout user (invalidate token).

    Note: In a stateless JWT system, logout is handled client-side
    by removing the token. This endpoint confirms logout intent.
    """
    return SuccessResponse(
        success=True,
        message=f"User {current_user.username} logged out successfully",
    )


def _generate_user_tokens(user: User) -> dict[str, str]:
    """
    Generate JWT tokens for user.

    Args:
        user: User instance

    Returns:
        Dictionary with access and refresh tokens
    """
    access_token = jwt_service.create_access_token(
        user_id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        is_admin=user.is_admin,
    )
    refresh_token = jwt_service.create_refresh_token(
        user_id=user.id, telegram_id=user.telegram_id
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
