"""
UserData model for the Quiz App.

This module contains the UserData SQLAlchemy model and corresponding Pydantic schemas
for collecting comprehensive user information including fingerprinting and Telegram data.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import relationship

from database import Base


class UserData(Base):
    """UserData database model."""

    __tablename__ = "userdata"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)

    # Session and identification
    session_id = Column(String(100), unique=True, index=True, nullable=False)

    # Network and browser data
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(1000), nullable=False)
    referrer = Column(String(500), nullable=True)
    entry_page = Column(String(500), nullable=True)
    fingerprint = Column(String(200), nullable=False)

    # Location data
    geolocation = Column(JSON, nullable=True)

    # Device and browser information
    device_info = Column(JSON, nullable=False)
    browser_info = Column(JSON, nullable=False)

    # Telegram data - only tg_id separately, rest in JSON
    tg_id = Column(Integer, nullable=True, index=True)
    telegram_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    responses = relationship(
        "Response",
        foreign_keys="Response.user_session_id",
        primaryjoin="UserData.session_id == Response.user_session_id",
        back_populates="user_data",
    )


# Pydantic schemas
class UserDataBase(BaseModel):
    """Base UserData schema with common fields."""

    # Session and identification
    session_id: str = Field(max_length=100, description="Unique session ID")

    # Network and browser data
    ip_address: str = Field(max_length=45, description="User IP address")
    user_agent: str = Field(max_length=1000, description="Browser user agent")
    referrer: Optional[str] = Field(None, max_length=500, description="Referrer URL")
    entry_page: Optional[str] = Field(
        None, max_length=500, description="Entry page URL"
    )
    fingerprint: str = Field(max_length=200, description="Browser fingerprint")

    # Location data
    geolocation: Optional[Dict[str, Any]] = Field(
        None, description="Geolocation data (coordinates, city, etc.)"
    )

    # Device and browser information
    device_info: Dict[str, Any] = Field(
        description="Device information (screen, OS, etc.)"
    )
    browser_info: Dict[str, Any] = Field(
        description="Browser information (language, timezone, etc.)"
    )

    # Telegram data - only tg_id separately, rest in JSON
    tg_id: Optional[int] = Field(None, description="Telegram user ID")
    telegram_data: Optional[Dict[str, Any]] = Field(
        None,
        description="All Telegram user data in JSON format (flexible for API changes)",
    )


class UserDataCreate(UserDataBase):
    """Schema for creating new user data."""

    pass


class UserDataUpdate(BaseModel):
    """Schema for updating existing user data."""

    # Network and browser data
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=1000)
    referrer: Optional[str] = Field(None, max_length=500)
    entry_page: Optional[str] = Field(None, max_length=500)
    fingerprint: Optional[str] = Field(None, max_length=200)

    # Location data
    geolocation: Optional[Dict[str, Any]] = None

    # Device and browser information
    device_info: Optional[Dict[str, Any]] = None
    browser_info: Optional[Dict[str, Any]] = None

    # Telegram data - only tg_id separately, rest in JSON
    tg_id: Optional[int] = None
    telegram_data: Optional[Dict[str, Any]] = None


class UserDataRead(UserDataBase):
    """Schema for reading user data."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDataReadWithResponses(UserDataRead):
    """Schema for reading user data with responses included."""

    responses: list = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserDataSummary(BaseModel):
    """Summary of user data for analytics."""

    total_users: int
    unique_ips: int
    countries: Dict[str, int] = Field(description="Country distribution")
    devices: Dict[str, int] = Field(description="Device type distribution")
    browsers: Dict[str, int] = Field(description="Browser distribution")
    telegram_users: int = Field(description="Users with Telegram data")


# Forward reference imports (avoid circular imports)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.response import Response, ResponseRead
