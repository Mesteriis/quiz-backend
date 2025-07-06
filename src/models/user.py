"""
User model for the Quiz App.

This module defines the User model for storing user information,
including authentication via JWT tokens and Telegram ID.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .response import Response


class User(SQLModel, table=True):
    """
    User model for authentication and user management.

    Users can be authenticated via JWT tokens or Telegram ID.
    Supports both regular users and administrators.
    """

    id: int | None = Field(default=None, primary_key=True)

    # Authentication fields
    username: str | None = Field(default=None, index=True, unique=True)
    email: str | None = Field(default=None, index=True, unique=True)

    # Telegram integration
    telegram_id: int | None = Field(default=None, index=True, unique=True)
    telegram_username: str | None = Field(default=None, index=True)
    telegram_first_name: str | None = Field(default=None)
    telegram_last_name: str | None = Field(default=None)
    telegram_photo_url: str | None = Field(default=None)

    # Profile information
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    display_name: str | None = Field(default=None)
    bio: str | None = Field(default=None)

    # User status
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    is_verified: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = Field(default=None)

    # Settings
    language: str = Field(default="en")
    timezone: str = Field(default="UTC")

    # Relationships
    responses: list["Response"] = Relationship(back_populates="user")

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.get_display_name()}>"

    def get_display_name(self) -> str:
        """Get the display name for the user."""
        if self.display_name:
            return self.display_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.telegram_first_name and self.telegram_last_name:
            return f"{self.telegram_first_name} {self.telegram_last_name}"
        if self.telegram_first_name:
            return self.telegram_first_name
        if self.username:
            return self.username
        if self.telegram_username:
            return f"@{self.telegram_username}"
        return f"User {self.id}"

    def get_identifier(self) -> str:
        """Get unique identifier for the user."""
        if self.telegram_id:
            return f"tg:{self.telegram_id}"
        if self.username:
            return f"username:{self.username}"
        if self.email:
            return f"email:{self.email}"
        return f"id:{self.id}"

    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_telegram_user(self) -> bool:
        """Check if user is authenticated via Telegram."""
        return self.telegram_id is not None

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "telegram_id": self.telegram_id,
            "telegram_username": self.telegram_username,
            "display_name": self.get_display_name(),
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "language": self.language,
            "timezone": self.timezone,
        }


class UserCreate(SQLModel):
    """Schema for creating a new user."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = Field(default=None)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    language: str = Field(default="en")
    timezone: str = Field(default="UTC")

    # Telegram data
    telegram_id: int | None = Field(default=None)
    telegram_username: str | None = Field(default=None)
    telegram_first_name: str | None = Field(default=None)
    telegram_last_name: str | None = Field(default=None)
    telegram_photo_url: str | None = Field(default=None)


class UserUpdate(SQLModel):
    """Schema for updating user information."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = Field(default=None)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None)
    timezone: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class UserResponse(SQLModel):
    """Schema for user responses."""

    id: int
    username: str | None = None
    email: str | None = None
    telegram_id: int | None = None
    telegram_username: str | None = None
    display_name: str
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None = None
    language: str
    timezone: str


class UserProfile(SQLModel):
    """Schema for user profile information."""

    id: int
    display_name: str
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    telegram_username: str | None = None
    is_verified: bool
    created_at: datetime
    responses_count: int = 0
