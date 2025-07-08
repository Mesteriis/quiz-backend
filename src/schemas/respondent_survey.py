"""
RespondentSurvey schemas for the Quiz App.

This module contains Pydantic schemas for RespondentSurvey model validation and serialization.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from .respondent import RespondentResponse
    from .survey import SurveyResponse


class RespondentSurveyBase(BaseModel):
    """Base RespondentSurvey schema with common fields."""

    status: str = Field("started", description="Survey status")
    progress_percentage: float = Field(
        0.0, ge=0.0, le=100.0, description="Progress percentage"
    )
    questions_answered: int = Field(0, ge=0, description="Number of questions answered")
    time_spent_seconds: int = Field(0, ge=0, description="Time spent in seconds")
    completion_source: str | None = Field(None, description="Source of completion")
    last_activity_at: datetime | None = Field(
        None, description="Last activity timestamp"
    )


class RespondentSurveyCreate(RespondentSurveyBase):
    """Schema for creating a new respondent survey participation."""

    respondent_id: int = Field(..., description="Respondent ID")
    survey_id: int = Field(..., description="Survey ID")


class RespondentSurveyUpdate(RespondentSurveyBase):
    """Schema for updating an existing respondent survey participation."""

    completed_at: datetime | None = Field(None, description="Completion timestamp")


class RespondentSurveyResponse(RespondentSurveyBase):
    """Schema for respondent survey responses."""

    id: int = Field(..., description="Participation ID")
    respondent_id: int = Field(..., description="Respondent ID")
    survey_id: int = Field(..., description="Survey ID")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveyWithDetails(RespondentSurveyResponse):
    """Schema for respondent survey with respondent and survey details."""

    respondent: Optional["RespondentResponse"] = None
    survey: Optional["SurveyResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveyProgress(BaseModel):
    """Schema for updating survey progress."""

    progress_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Progress percentage"
    )
    questions_answered: int = Field(
        ..., ge=0, description="Number of questions answered"
    )
    additional_time: int = Field(0, ge=0, description="Additional time spent")
    status: str | None = Field(None, description="Status update")


class RespondentSurveyCompletion(BaseModel):
    """Schema for survey completion data."""

    completion_source: str | None = Field(None, description="Source of completion")
    time_spent_seconds: int | None = Field(None, ge=0, description="Total time spent")
    final_score: float | None = Field(None, description="Final score if applicable")
    notes: str | None = Field(None, description="Completion notes")


class RespondentSurveyStatistics(BaseModel):
    """Schema for survey participation statistics."""

    total_participations: int = Field(..., description="Total participations")
    completed_participations: int = Field(..., description="Completed participations")
    abandoned_participations: int = Field(..., description="Abandoned participations")
    in_progress_participations: int = Field(
        ..., description="In progress participations"
    )
    completion_rate: float = Field(..., description="Completion rate percentage")
    abandonment_rate: float = Field(..., description="Abandonment rate percentage")
    average_completion_time: float = Field(
        ..., description="Average completion time in seconds"
    )
    average_progress_percentage: float = Field(
        ..., description="Average progress percentage"
    )

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveySearch(BaseModel):
    """Schema for respondent survey search parameters."""

    respondent_id: int | None = Field(None, description="Filter by respondent ID")
    survey_id: int | None = Field(None, description="Filter by survey ID")
    status: str | None = Field(None, description="Filter by status")
    progress_min: float | None = Field(
        None, ge=0.0, le=100.0, description="Minimum progress percentage"
    )
    progress_max: float | None = Field(
        None, ge=0.0, le=100.0, description="Maximum progress percentage"
    )
    completion_source: str | None = Field(
        None, description="Filter by completion source"
    )
    started_from: datetime | None = Field(None, description="Filter by start date from")
    started_to: datetime | None = Field(None, description="Filter by start date to")
    completed_from: datetime | None = Field(
        None, description="Filter by completion date from"
    )
    completed_to: datetime | None = Field(
        None, description="Filter by completion date to"
    )
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")


class RespondentSurveyActivity(BaseModel):
    """Schema for recent survey activity."""

    participation_id: int = Field(..., description="Participation ID")
    respondent_id: int = Field(..., description="Respondent ID")
    survey_id: int = Field(..., description="Survey ID")
    survey_title: str | None = Field(None, description="Survey title")
    status: str = Field(..., description="Current status")
    progress_percentage: float = Field(..., description="Progress percentage")
    last_activity_at: datetime = Field(..., description="Last activity timestamp")

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveyTimeline(BaseModel):
    """Schema for respondent survey timeline."""

    respondent_id: int = Field(..., description="Respondent ID")
    survey_participations: list[RespondentSurveyResponse] = Field(
        ..., description="Survey participations"
    )
    total_surveys: int = Field(..., description="Total surveys participated")
    completed_surveys: int = Field(..., description="Completed surveys")
    abandoned_surveys: int = Field(..., description="Abandoned surveys")
    average_completion_rate: float = Field(..., description="Average completion rate")

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveyBulkUpdate(BaseModel):
    """Schema for bulk updating survey participations."""

    participation_ids: list[int] = Field(..., description="List of participation IDs")
    update_data: RespondentSurveyUpdate = Field(..., description="Update data")

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveyBulkUpdateResult(BaseModel):
    """Schema for bulk update result."""

    updated_count: int = Field(..., description="Number of updated participations")
    failed_count: int = Field(..., description="Number of failed updates")
    updated_ids: list[int] = Field(..., description="List of successfully updated IDs")
    failed_ids: list[int] = Field(..., description="List of failed IDs")

    model_config = ConfigDict(from_attributes=True)
