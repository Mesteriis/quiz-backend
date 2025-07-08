"""
User Pydantic schemas for the Quiz App.

This module contains Pydantic schemas for user data validation,
serialization, and API request/response handling.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    """Base User schema with common fields."""

    username: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)

    # Telegram fields
    telegram_id: int | None = None
    telegram_username: str | None = Field(None, max_length=100)
    telegram_first_name: str | None = Field(None, max_length=100)
    telegram_last_name: str | None = Field(None, max_length=100)
    telegram_photo_url: str | None = Field(None, max_length=500)

    # Profile fields
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)

    # Localization fields
    language: str = Field("en", max_length=10)
    timezone: str = Field("UTC", max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    @field_validator("username", "email", mode="before")
    @classmethod
    def validate_required_fields(cls, v):
        """Validate required fields are not empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def validate_email_format(cls, v):
        """Validate email format."""
        if v is not None and v.strip():
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, v.strip()):
                raise ValueError("Invalid email format")
        return v


class UserUpdate(BaseModel):
    """Schema for updating existing user."""

    username: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)

    # Telegram fields
    telegram_username: str | None = Field(None, max_length=100)
    telegram_first_name: str | None = Field(None, max_length=100)
    telegram_last_name: str | None = Field(None, max_length=100)
    telegram_photo_url: str | None = Field(None, max_length=500)

    # Profile fields
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)

    # Localization fields
    language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=50)


class UserRead(UserBase):
    """Schema for reading user data."""

    id: int
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    """Schema for user profile information."""

    id: int
    username: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    telegram_username: str | None = None
    telegram_photo_url: str | None = None
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Schema for user response data."""

    id: int
    username: str | None = None
    email: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    telegram_id: int | None = None
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    telegram_last_name: str | None = None
    telegram_photo_url: str | None = None
    is_active: bool
    is_admin: bool
    is_verified: bool
    language: str
    timezone: str
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login."""

    identifier: str | None = Field(None, description="Username or email")
    telegram_id: int | None = Field(None, description="Telegram user ID")


class TelegramAuth(BaseModel):
    """Schema for Telegram authentication."""

    telegram_id: int
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    telegram_last_name: str | None = None
    telegram_photo_url: str | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str = Field(description="Valid refresh token")


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    users: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class UserSearchRequest(BaseModel):
    """Schema for user search request."""

    search_term: str = Field(min_length=2, max_length=100, description="Search term")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class UserActivationRequest(BaseModel):
    """Schema for user activation request."""

    user_id: int = Field(description="User ID to activate")
    is_active: bool = Field(description="Activation status")


class UserVerificationRequest(BaseModel):
    """Schema for user verification request."""

    user_id: int = Field(description="User ID to verify")
    is_verified: bool = Field(description="Verification status")


class UserRoleRequest(BaseModel):
    """Schema for user role change request."""

    user_id: int = Field(description="User ID to change role")
    is_admin: bool = Field(description="Admin status")


class UserStatsResponse(BaseModel):
    """Schema for user statistics response."""

    total_users: int
    active_users: int
    verified_users: int
    admin_users: int
    telegram_users: int
    recent_registrations: int  # Last 30 days

    model_config = ConfigDict(from_attributes=True)
