"""
RespondentEvent schemas for the Quiz App.

This module contains Pydantic schemas for RespondentEvent model validation and serialization.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from .respondent import RespondentResponse
    from .survey import SurveyResponse
    from .response import ResponseResponse


class RespondentEventBase(BaseModel):
    """Base RespondentEvent schema with common fields."""

    event_type: str = Field(..., description="Type of event")
    event_data: Dict[str, Any] | None = Field(None, description="Event data")
    metadata: Dict[str, Any] | None = Field(None, description="Additional metadata")


class RespondentEventCreate(RespondentEventBase):
    """Schema for creating a new respondent event."""

    respondent_id: int = Field(..., description="Respondent ID")
    survey_id: int | None = Field(None, description="Survey ID if survey-related")
    response_id: int | None = Field(None, description="Response ID if response-related")


class RespondentEventUpdate(RespondentEventBase):
    """Schema for updating an existing respondent event."""

    pass


class RespondentEventResponse(RespondentEventBase):
    """Schema for respondent event responses."""

    id: int = Field(..., description="Event ID")
    respondent_id: int = Field(..., description="Respondent ID")
    survey_id: int | None = Field(None, description="Survey ID if survey-related")
    response_id: int | None = Field(None, description="Response ID if response-related")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventWithDetails(RespondentEventResponse):
    """Schema for respondent event with related details."""

    respondent: Optional["RespondentResponse"] = None
    survey: Optional["SurveyResponse"] = None
    response: Optional["ResponseResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class RespondentEventLog(BaseModel):
    """Schema for logging a new event."""

    event_type: str = Field(..., description="Type of event")
    survey_id: int | None = Field(None, description="Survey ID if survey-related")
    response_id: int | None = Field(None, description="Response ID if response-related")
    event_data: Dict[str, Any] | None = Field(None, description="Event data")
    metadata: Dict[str, Any] | None = Field(None, description="Additional metadata")


class RespondentEventStatistics(BaseModel):
    """Schema for respondent event statistics."""

    total_events: int = Field(..., description="Total number of events")
    events_by_type: Dict[str, int] = Field(..., description="Events grouped by type")
    events_today: int = Field(..., description="Events today")
    most_active_respondents: list[Dict[str, Any]] = Field(
        ..., description="Most active respondents"
    )

    model_config = ConfigDict(from_attributes=True)


class RespondentEventSearch(BaseModel):
    """Schema for respondent event search parameters."""

    respondent_id: int | None = Field(None, description="Filter by respondent ID")
    event_type: str | None = Field(None, description="Filter by event type")
    survey_id: int | None = Field(None, description="Filter by survey ID")
    response_id: int | None = Field(None, description="Filter by response ID")
    date_from: datetime | None = Field(None, description="Filter by date from")
    date_to: datetime | None = Field(None, description="Filter by date to")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")


class RespondentEventActivity(BaseModel):
    """Schema for respondent activity summary."""

    respondent_id: int = Field(..., description="Respondent ID")
    total_events: int = Field(..., description="Total events")
    events_by_type: Dict[str, int] = Field(..., description="Events grouped by type")
    first_activity: datetime | None = Field(
        None, description="First activity timestamp"
    )
    last_activity: datetime | None = Field(None, description="Last activity timestamp")
    surveys_participated: int = Field(..., description="Number of surveys participated")
    days_period: int = Field(..., description="Period in days")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventTimeline(BaseModel):
    """Schema for respondent event timeline."""

    respondent_id: int = Field(..., description="Respondent ID")
    events: list[RespondentEventResponse] = Field(..., description="Timeline events")
    total_events: int = Field(..., description="Total events")
    event_types: list[str] = Field(..., description="Event types used")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventExport(BaseModel):
    """Schema for respondent event export (GDPR compliance)."""

    event_id: int = Field(..., description="Event ID")
    event_type: str = Field(..., description="Type of event")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    survey_id: int | None = Field(None, description="Survey ID if survey-related")
    response_id: int | None = Field(None, description="Response ID if response-related")
    event_data: Dict[str, Any] | None = Field(None, description="Event data")
    metadata: Dict[str, Any] | None = Field(None, description="Additional metadata")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventTrend(BaseModel):
    """Schema for event trend data."""

    date: str = Field(..., description="Date (ISO format)")
    count: int = Field(..., description="Event count for the date")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventTrendAnalysis(BaseModel):
    """Schema for event trend analysis."""

    event_type: str = Field(..., description="Type of event")
    trend_data: list[RespondentEventTrend] = Field(..., description="Trend data points")
    total_events: int = Field(..., description="Total events in period")
    average_daily: float = Field(..., description="Average daily events")
    peak_date: str | None = Field(None, description="Peak activity date")
    peak_count: int = Field(0, description="Peak activity count")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventBulkLog(BaseModel):
    """Schema for bulk event logging."""

    events: list[RespondentEventLog] = Field(..., description="List of events to log")
    respondent_id: int = Field(..., description="Respondent ID")


class RespondentEventBulkResult(BaseModel):
    """Schema for bulk event logging result."""

    logged_count: int = Field(..., description="Number of events logged")
    failed_count: int = Field(..., description="Number of failed events")
    event_ids: list[int] = Field(..., description="List of created event IDs")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventCleanup(BaseModel):
    """Schema for event cleanup operation."""

    days_to_keep: int = Field(..., ge=1, description="Number of days to keep events")
    event_types: list[str] | None = Field(
        None, description="Event types to clean (all if None)"
    )
    dry_run: bool = Field(True, description="Whether to perform a dry run")


class RespondentEventCleanupResult(BaseModel):
    """Schema for event cleanup result."""

    events_deleted: int = Field(..., description="Number of events deleted")
    oldest_deleted: datetime | None = Field(
        None, description="Oldest deleted event timestamp"
    )
    cleanup_timestamp: datetime = Field(..., description="Cleanup operation timestamp")

    model_config = ConfigDict(from_attributes=True)
