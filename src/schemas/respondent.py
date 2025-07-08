"""
Respondent schemas for the Quiz App.

This module contains Pydantic schemas for Respondent model validation and serialization.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from .user import UserResponse


class RespondentBase(BaseModel):
    """Base Respondent schema with common fields."""

    is_anonymous: bool = Field(True, description="Whether respondent is anonymous")
    session_id: str | None = Field(None, description="Session ID for tracking")
    browser_fingerprint: str | None = Field(None, description="Browser fingerprint")
    ip_address: str | None = Field(None, description="IP address")
    user_agent: str | None = Field(None, description="User agent string")
    geolocation: Dict[str, Any] | None = Field(None, description="Geolocation data")
    precise_location: Dict[str, Any] | None = Field(
        None, description="Precise location data"
    )
    device_info: Dict[str, Any] | None = Field(None, description="Device information")
    telegram_data: Dict[str, Any] | None = Field(None, description="Telegram data")
    custom_data: Dict[str, Any] | None = Field(None, description="Custom data")
    notes: str | None = Field(None, description="Additional notes")


class RespondentCreate(RespondentBase):
    """Schema for creating a new respondent."""

    user_id: int | None = Field(None, description="User ID if authenticated")


class RespondentUpdate(RespondentBase):
    """Schema for updating an existing respondent."""

    user_id: int | None = Field(None, description="User ID if authenticated")
    is_merged: bool | None = Field(None, description="Whether respondent is merged")
    merged_at: datetime | None = Field(None, description="Merge timestamp")


class RespondentResponse(RespondentBase):
    """Schema for respondent responses."""

    id: int = Field(..., description="Respondent ID")
    user_id: int | None = Field(None, description="User ID if authenticated")
    is_merged: bool = Field(False, description="Whether respondent is merged")
    merged_at: datetime | None = Field(None, description="Merge timestamp")
    merged_from_id: int | None = Field(
        None, description="Original respondent ID if merged"
    )
    deleted_at: datetime | None = Field(None, description="Soft delete timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class RespondentPublic(BaseModel):
    """Public respondent schema with limited fields."""

    id: int = Field(..., description="Respondent ID")
    is_anonymous: bool = Field(..., description="Whether respondent is anonymous")
    session_id: str | None = Field(None, description="Session ID for tracking")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class RespondentWithUser(RespondentResponse):
    """Respondent schema with user information."""

    user: Optional["UserResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class RespondentSearch(BaseModel):
    """Schema for respondent search parameters."""

    is_anonymous: bool | None = Field(None, description="Filter by anonymous status")
    user_id: int | None = Field(None, description="Filter by user ID")
    session_id: str | None = Field(None, description="Filter by session ID")
    browser_fingerprint: str | None = Field(
        None, description="Filter by browser fingerprint"
    )
    ip_address: str | None = Field(None, description="Filter by IP address")
    has_geolocation: bool | None = Field(
        None, description="Filter by geolocation presence"
    )
    has_precise_location: bool | None = Field(
        None, description="Filter by precise location presence"
    )
    has_telegram_data: bool | None = Field(
        None, description="Filter by Telegram data presence"
    )
    is_merged: bool | None = Field(None, description="Filter by merge status")
    date_from: datetime | None = Field(None, description="Filter by creation date from")
    date_to: datetime | None = Field(None, description="Filter by creation date to")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")


class RespondentStatistics(BaseModel):
    """Schema for respondent statistics."""

    total_respondents: int = Field(..., description="Total number of respondents")
    anonymous_respondents: int = Field(..., description="Anonymous respondents")
    authenticated_respondents: int = Field(..., description="Authenticated respondents")
    merged_respondents: int = Field(..., description="Merged respondents")
    with_geolocation: int = Field(..., description="Respondents with geolocation")
    with_precise_location: int = Field(
        ..., description="Respondents with precise location"
    )
    with_telegram_data: int = Field(..., description="Respondents with Telegram data")
    unique_sessions: int = Field(..., description="Unique sessions")
    unique_ips: int = Field(..., description="Unique IP addresses")

    model_config = ConfigDict(from_attributes=True)


class RespondentMerge(BaseModel):
    """Schema for respondent merge operation."""

    target_respondent_id: int = Field(..., description="Target respondent ID")
    source_respondent_ids: list[int] = Field(
        ..., description="Source respondent IDs to merge"
    )
    merge_data: bool = Field(True, description="Whether to merge data")
    merge_responses: bool = Field(True, description="Whether to merge responses")
    merge_consents: bool = Field(True, description="Whether to merge consents")
    merge_events: bool = Field(True, description="Whether to merge events")
    notes: str | None = Field(None, description="Merge notes")


class RespondentMergeResult(BaseModel):
    """Schema for respondent merge operation result."""

    target_respondent_id: int = Field(..., description="Target respondent ID")
    merged_respondent_ids: list[int] = Field(..., description="Merged respondent IDs")
    merged_responses_count: int = Field(..., description="Number of merged responses")
    merged_consents_count: int = Field(..., description="Number of merged consents")
    merged_events_count: int = Field(..., description="Number of merged events")
    merge_timestamp: datetime = Field(..., description="Merge timestamp")

    model_config = ConfigDict(from_attributes=True)


class RespondentActivity(BaseModel):
    """Schema for respondent activity summary."""

    respondent_id: int = Field(..., description="Respondent ID")
    total_surveys: int = Field(..., description="Total surveys participated")
    completed_surveys: int = Field(..., description="Completed surveys")
    abandoned_surveys: int = Field(..., description="Abandoned surveys")
    total_responses: int = Field(..., description="Total responses")
    total_events: int = Field(..., description="Total events")
    first_activity: datetime | None = Field(
        None, description="First activity timestamp"
    )
    last_activity: datetime | None = Field(None, description="Last activity timestamp")

    model_config = ConfigDict(from_attributes=True)


class RespondentDataExport(BaseModel):
    """Schema for respondent data export (GDPR compliance)."""

    respondent_id: int = Field(..., description="Respondent ID")
    user_id: int | None = Field(None, description="User ID if authenticated")
    personal_data: Dict[str, Any] = Field(..., description="Personal data")
    survey_data: list[Dict[str, Any]] = Field(
        ..., description="Survey participation data"
    )
    response_data: list[Dict[str, Any]] = Field(..., description="Response data")
    consent_data: list[Dict[str, Any]] = Field(..., description="Consent data")
    event_data: list[Dict[str, Any]] = Field(..., description="Event data")
    export_timestamp: datetime = Field(..., description="Export timestamp")

    model_config = ConfigDict(from_attributes=True)
