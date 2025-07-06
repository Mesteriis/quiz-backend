"""
Authentication API router for the Quiz App.

This module contains FastAPI endpoints for user authentication,
registration, and profile management.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models.user import User, UserCreate, UserUpdate, UserResponse, UserProfile
from services.user_service import user_service
from services.jwt_service import jwt_service
from schemas.admin import SuccessResponse


router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
        session: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token and get user
    user = await user_service.get_user_from_token(session, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    Dependency to get current user if token is provided (optional authentication).
    
    Args:
        authorization: Authorization header
        session: Database session
        
    Returns:
        User or None: Current user if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    
    try:
        user = await user_service.get_user_from_token(session, token)
        return user
    except Exception:
        return None


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


@router.post("/register", response_model=dict)
async def register_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user.
    
    Creates a new user account and returns JWT tokens.
    Supports both regular and Telegram users.
    """
    try:
        # Create user
        user = await user_service.create_user(session, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username, email, or Telegram ID already exists"
            )
        
        # Generate tokens
        tokens = user_service.generate_user_tokens(user)
        
        return {
            "message": "User created successfully",
            "user": user.to_dict(),
            **tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=dict)
async def login_user(
    identifier: Optional[str] = None,
    telegram_id: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user and return JWT tokens.
    
    Supports authentication by:
    - Username/email + no password (for simplicity)
    - Telegram ID
    """
    try:
        if not identifier and not telegram_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either identifier or telegram_id must be provided"
            )
        
        # Authenticate user
        user = await user_service.authenticate_user(session, identifier, telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or user not found"
            )
        
        # Generate tokens
        tokens = user_service.generate_user_tokens(user)
        
        return {
            "message": "Login successful",
            "user": user.to_dict(),
            **tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/telegram", response_model=dict)
async def telegram_auth(
    telegram_id: int,
    telegram_username: Optional[str] = None,
    telegram_first_name: Optional[str] = None,
    telegram_last_name: Optional[str] = None,
    telegram_photo_url: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate or create user via Telegram.
    
    Creates new user if doesn't exist, or updates existing user data.
    Returns JWT tokens for authentication.
    """
    try:
        # Create or update Telegram user
        user = await user_service.create_or_update_telegram_user(
            session=session,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            telegram_first_name=telegram_first_name,
            telegram_last_name=telegram_last_name,
            telegram_photo_url=telegram_photo_url
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create or update Telegram user"
            )
        
        # Generate tokens
        tokens = user_service.generate_user_tokens(user)
        
        return {
            "message": "Telegram authentication successful",
            "user": user.to_dict(),
            **tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telegram authentication failed: {str(e)}"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_token: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New access and refresh tokens
    """
    try:
        # Verify refresh token
        token_data = jwt_service.verify_token(refresh_token)
        if not token_data or token_data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = token_data.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user
        user = await user_service.get_user_by_id(session, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        tokens = user_service.generate_user_tokens(user)
        
        return {
            "message": "Token refreshed successfully",
            **tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile information.
    
    Returns:
        Current user's profile data
    """
    return UserResponse(**current_user.to_dict())


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update current user profile information.
    
    Args:
        user_data: Updated user data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Updated user profile
    """
    try:
        updated_user = await user_service.update_user(session, current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
        
        return UserResponse(**updated_user.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.get("/users", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get list of users (admin only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        admin_user: Current admin user
        session: Database session
        
    Returns:
        List of users
    """
    try:
        users = await user_service.get_users(session, skip, limit)
        return [UserResponse(**user.to_dict()) for user in users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get user profile by ID.
    
    Public endpoint that returns limited profile information.
    Admins can see full profile information.
    """
    try:
        user = await user_service.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return profile data
        profile_data = {
            "id": user.id,
            "display_name": user.get_display_name(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "bio": user.bio,
            "telegram_username": user.telegram_username,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "responses_count": len(user.responses) if user.responses else 0
        }
        
        return UserProfile(**profile_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.post("/verify-token", response_model=dict)
async def verify_token(
    token: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Verify JWT token validity.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Token validation result
    """
    try:
        user = await user_service.get_user_from_token(session, token)
        
        if user:
            return {
                "valid": True,
                "user": user.to_dict(),
                "expires_at": jwt_service.get_token_expiration(token).isoformat() if jwt_service.get_token_expiration(token) else None
            }
        else:
            return {
                "valid": False,
                "error": "Invalid or expired token"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "error": f"Token verification failed: {str(e)}"
        }


@router.delete("/logout", response_model=SuccessResponse)
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (invalidate current session).
    
    Note: Since we're using stateless JWT tokens, this endpoint
    doesn't actually invalidate tokens server-side. In a production
    environment, you might want to implement a token blacklist.
    """
    return SuccessResponse(
        success=True,
        message=f"User {current_user.get_display_name()} logged out successfully"
    ) 