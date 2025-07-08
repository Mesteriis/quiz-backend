"""
Profile SQLAlchemy model for the Quiz App.

This module contains the Profile SQLAlchemy model and corresponding Pydantic schemas
for managing user profile information separately from authentication data.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class Profile(Base):
    """Profile database model."""

    __tablename__ = "profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)

    # Personal information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)

    # Contact information
    phone = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id})>"


# Pydantic schemas
class ProfileBase(BaseModel):
    """Base Profile schema with common fields."""

    first_name: str | None = Field(None, max_length=100, description="First name")
    last_name: str | None = Field(None, max_length=100, description="Last name")
    bio: str | None = Field(None, description="Biography")
    profile_picture_url: str | None = Field(
        None, max_length=500, description="Profile picture URL"
    )
    phone: str | None = Field(None, max_length=20, description="Phone number")


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""

    user_id: int = Field(description="User ID this profile belongs to")


class ProfileUpdate(BaseModel):
    """Schema for updating existing profile."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    bio: str | None = None
    profile_picture_url: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=20)


class ProfileRead(ProfileBase):
    """Schema for reading profile data."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileWithUser(ProfileRead):
    """Schema for reading profile data with user information."""

    user: Any = Field(description="User information")

    model_config = ConfigDict(from_attributes=True)
