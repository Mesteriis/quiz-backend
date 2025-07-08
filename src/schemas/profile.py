"""
Profile schemas for the Quiz App.

This module contains Pydantic schemas for Profile model validation and serialization.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from .user import UserResponse


class ProfileBase(BaseModel):
    """Base Profile schema with common fields."""

    first_name: str | None = Field(None, description="First name")
    last_name: str | None = Field(None, description="Last name")
    bio: str | None = Field(None, description="Biography")
    profile_picture_url: str | None = Field(None, description="Profile picture URL")
    phone: str | None = Field(None, description="Phone number")


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""

    user_id: int = Field(..., description="User ID")


class ProfileUpdate(ProfileBase):
    """Schema for updating an existing profile."""

    pass


class ProfileResponse(ProfileBase):
    """Schema for profile responses."""

    id: int = Field(..., description="Profile ID")
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProfilePublic(BaseModel):
    """Public profile schema with limited fields."""

    id: int = Field(..., description="Profile ID")
    first_name: str | None = Field(None, description="First name")
    last_name: str | None = Field(None, description="Last name")
    bio: str | None = Field(None, description="Biography")
    profile_picture_url: str | None = Field(None, description="Profile picture URL")

    model_config = ConfigDict(from_attributes=True)


class ProfileWithUser(ProfileResponse):
    """Profile schema with user information."""

    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileSearch(BaseModel):
    """Schema for profile search parameters."""

    query: str | None = Field(None, description="Search query")
    first_name: str | None = Field(None, description="First name filter")
    last_name: str | None = Field(None, description="Last name filter")
    has_bio: bool | None = Field(None, description="Filter by bio presence")
    has_profile_picture: bool | None = Field(
        None, description="Filter by profile picture presence"
    )
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")


class ProfileStatistics(BaseModel):
    """Schema for profile statistics."""

    total_profiles: int = Field(..., description="Total number of profiles")
    profiles_with_bio: int = Field(..., description="Profiles with bio")
    profiles_with_picture: int = Field(..., description="Profiles with picture")
    profiles_with_phone: int = Field(..., description="Profiles with phone")
    completion_percentage: float = Field(
        ..., description="Average profile completion percentage"
    )

    model_config = ConfigDict(from_attributes=True)
