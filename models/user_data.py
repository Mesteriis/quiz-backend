"""
UserData model for the Quiz App.

This module contains the UserData SQLModel for collecting comprehensive
user information including fingerprinting and Telegram data.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlmodel import SQLModel, Field, Relationship, JSON, Column


class UserDataBase(SQLModel):
    """Base UserData model with common fields."""
    
    # Session and identification
    session_id: str = Field(max_length=100, unique=True, index=True, description="Unique session ID")
    
    # Network and browser data
    ip_address: str = Field(max_length=45, description="User IP address")
    user_agent: str = Field(max_length=1000, description="Browser user agent")
    referrer: str | None = Field(default=None, max_length=500, description="Referrer URL")
    fingerprint: str = Field(max_length=200, description="Browser fingerprint")
    
    # Location data
    geolocation: Dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Geolocation data (coordinates, city, etc.)"
    )
    
    # Device and browser information
    device_info: Dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="Device information (screen, OS, etc.)"
    )
    browser_info: Dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="Browser information (language, timezone, etc.)"
    )
    
    # Telegram data (optional)
    telegram_user_id: int | None = Field(default=None, description="Telegram user ID")
    telegram_username: str | None = Field(default=None, max_length=100, description="Telegram username")
    telegram_first_name: str | None = Field(default=None, max_length=100, description="Telegram first name")
    telegram_last_name: str | None = Field(default=None, max_length=100, description="Telegram last name")
    telegram_language_code: str | None = Field(default=None, max_length=10, description="Telegram language")
    telegram_photo_url: str | None = Field(default=None, max_length=500, description="Telegram avatar URL")


class UserData(UserDataBase, table=True):
    """UserData database model."""
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    responses: list["Response"] = Relationship(
        back_populates="user_data",
        sa_relationship_kwargs={
            "foreign_keys": "[Response.user_session_id]",
            "primaryjoin": "UserData.session_id == Response.user_session_id"
        }
    )


class UserDataCreate(UserDataBase):
    """Schema for creating new user data."""
    pass


class UserDataUpdate(SQLModel):
    """Schema for updating existing user data."""
    
    # Network and browser data
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=1000)
    referrer: str | None = Field(default=None, max_length=500)
    fingerprint: str | None = Field(default=None, max_length=200)
    
    # Location data
    geolocation: Dict[str, Any] | None = Field(default=None)
    
    # Device and browser information
    device_info: Dict[str, Any] | None = Field(default=None)
    browser_info: Dict[str, Any] | None = Field(default=None)
    
    # Telegram data
    telegram_user_id: int | None = Field(default=None)
    telegram_username: str | None = Field(default=None, max_length=100)
    telegram_first_name: str | None = Field(default=None, max_length=100)
    telegram_last_name: str | None = Field(default=None, max_length=100)
    telegram_language_code: str | None = Field(default=None, max_length=10)
    telegram_photo_url: str | None = Field(default=None, max_length=500)


class UserDataRead(UserDataBase):
    """Schema for reading user data."""
    
    id: int
    created_at: datetime
    updated_at: datetime


class UserDataReadWithResponses(UserDataRead):
    """Schema for reading user data with responses included."""
    
    responses: list["ResponseRead"] = []


class UserDataSummary(SQLModel):
    """Summary of user data for analytics."""
    
    total_users: int
    unique_ips: int
    countries: Dict[str, int] = Field(
        sa_column=Column(JSON),
        description="Country distribution"
    )
    devices: Dict[str, int] = Field(
        sa_column=Column(JSON),
        description="Device type distribution"
    )
    browsers: Dict[str, int] = Field(
        sa_column=Column(JSON),
        description="Browser distribution"
    )
    telegram_users: int


# Forward reference imports (avoid circular imports)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.response import Response, ResponseRead 