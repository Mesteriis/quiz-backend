"""
RespondentEvent SQLAlchemy model for the Quiz App.

This module contains the RespondentEvent SQLAlchemy model and corresponding Pydantic schemas
for tracking respondent events and activity logging.
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class RespondentEvent(Base):
    """RespondentEvent database model."""

    __tablename__ = "respondent_events"

    id = Column(Integer, primary_key=True, index=True)
    respondent_id = Column(Integer, ForeignKey("respondents.id"), nullable=False)

    # === СОБЫТИЕ ===
    event_type = Column(String(50), nullable=False)
    # "created", "authorized", "merged", "survey_started", "survey_completed",
    # "consent_granted", "consent_revoked", "data_updated", "profile_linked"

    event_data = Column(JSON, nullable=True)
    # {"from_anonymous": true, "merged_respondent_id": 123, "survey_id": 456}

    # === КОНТЕКСТ СОБЫТИЯ ===
    event_source = Column(String(50), nullable=True)
    # "web", "telegram_webapp", "telegram_bot", "api", "system"

    # === ВРЕМЕННЫЕ МЕТКИ ===
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # === МЕТАДАННЫЕ ===
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)

    # === ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ===
    details = Column(JSON, nullable=True)
    # {"duration": 1234, "error_message": "...", "additional_context": {...}}

    # === RELATIONSHIPS ===
    respondent = relationship("Respondent", back_populates="events")

    def __repr__(self):
        return f"<RespondentEvent(id={self.id}, respondent_id={self.respondent_id}, event_type='{self.event_type}')>"

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_respondent_events_respondent", "respondent_id"),
        Index("ix_respondent_events_type", "event_type"),
        Index("ix_respondent_events_created", "created_at"),
        Index("ix_respondent_events_source", "event_source"),
        Index("ix_respondent_events_session", "session_id"),
            {"extend_existing": True},

    )


# Pydantic schemas
class RespondentEventBase(BaseModel):
    """Base RespondentEvent schema with common fields."""

    respondent_id: int = Field(description="Respondent ID")
    event_type: str = Field(max_length=50, description="Type of event")
    event_data: Dict[str, Any] | None = Field(None, description="Event data")
    event_source: str | None = Field(None, max_length=50, description="Source of event")
    ip_address: str | None = Field(None, max_length=45, description="IP address")
    user_agent: str | None = Field(None, description="User agent")
    session_id: str | None = Field(None, max_length=255, description="Session ID")
    details: Dict[str, Any] | None = Field(None, description="Additional details")


class RespondentEventCreate(RespondentEventBase):
    """Schema for creating a new respondent event."""

    pass


class RespondentEventRead(RespondentEventBase):
    """Schema for reading respondent event data."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RespondentEventWithDetails(RespondentEventRead):
    """Schema for reading respondent event with related data."""

    respondent: Any = Field(None, description="Respondent information")

    model_config = ConfigDict(from_attributes=True)


class RespondentEventSummary(BaseModel):
    """Schema for respondent event summary and analytics."""

    total_events: int
    event_types: Dict[str, int] = Field(description="Event type distribution")
    event_sources: Dict[str, int] = Field(description="Event source distribution")
    recent_events: list[Dict[str, Any]] = Field(description="Recent events")
    hourly_activity: Dict[str, int] = Field(description="Hourly activity distribution")
    daily_activity: Dict[str, int] = Field(description="Daily activity distribution")


class RespondentEventTimeline(BaseModel):
    """Schema for respondent event timeline."""

    respondent_id: int
    events: list[RespondentEventRead] = Field(
        description="Chronological list of events"
    )
    first_event: datetime
    last_event: datetime
    total_events: int
    event_types_count: Dict[str, int]


class RespondentEventFilter(BaseModel):
    """Schema for filtering respondent events."""

    event_types: list[str] | None = Field(None, description="Filter by event types")
    event_sources: list[str] | None = Field(None, description="Filter by event sources")
    start_date: datetime | None = Field(None, description="Start date filter")
    end_date: datetime | None = Field(None, description="End date filter")
    limit: int = Field(100, ge=1, le=1000, description="Limit number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class RespondentEventStats(BaseModel):
    """Schema for respondent event statistics."""

    period: str = Field(description="Time period (hour, day, week, month)")
    event_counts: Dict[str, int] = Field(description="Event counts by type")
    unique_respondents: int = Field(description="Unique respondents with events")
    total_events: int = Field(description="Total events in period")
    average_events_per_respondent: float = Field(
        description="Average events per respondent"
    )
    most_active_respondents: list[Dict[str, Any]] = Field(
        description="Most active respondents"
    )
    event_trends: Dict[str, list[int]] = Field(description="Event trends over time")


class EventTypes(BaseModel):
    """Schema for available event types."""

    created: str = "Respondent created"
    authorized: str = "User authorized/logged in"
    merged: str = "Respondent merged with another"
    survey_started: str = "Survey started"
    survey_completed: str = "Survey completed"
    survey_abandoned: str = "Survey abandoned"
    consent_granted: str = "Consent granted"
    consent_revoked: str = "Consent revoked"
    data_updated: str = "Data updated"
    profile_linked: str = "Profile linked to user"
    location_shared: str = "Location shared"
    error_occurred: str = "Error occurred"
