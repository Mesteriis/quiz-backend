"""
Respondent SQLAlchemy model for the Quiz App.

This module contains the Respondent SQLAlchemy model and corresponding Pydantic schemas
for managing survey respondents (both anonymous and authenticated users).
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Boolean,
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


class Respondent(Base):
    """Respondent database model."""

    __tablename__ = "respondents"

    id = Column(Integer, primary_key=True, index=True)

    # === ИДЕНТИФИКАЦИЯ ===
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    session_id = Column(String(255), unique=True, nullable=False)
    browser_fingerprint = Column(String(255), nullable=True)

    # === ЯВНЫЕ ДАННЫЕ (без разрешения) ===
    # Технические данные
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    browser_info = Column(JSON, nullable=True)
    # {"name": "Chrome", "version": "120.0", "language": "ru"}

    device_info = Column(JSON, nullable=True)
    # {"type": "mobile", "os": "iOS", "screen": {"width": 390, "height": 844}}

    # Геолокация по IP
    geo_info = Column(JSON, nullable=True)
    # {"country": "RU", "city": "Moscow", "timezone": "Europe/Moscow", "isp": "Beeline"}

    # Поведенческие данные
    referrer_info = Column(JSON, nullable=True)
    # {"source": "google", "medium": "organic", "campaign": null, "utm_params": {...}}

    # === КОНТЕКСТНЫЕ ДАННЫЕ TELEGRAM ===
    telegram_data = Column(JSON, nullable=True)
    # {"webapp_data": {...}, "chat_id": 123, "username": "user123"}

    # === ИСТОЧНИК ТРАФИКА ===
    entry_point = Column(String(50), nullable=True)
    # "web", "pwa", "telegram_webapp", "telegram_bot"

    # === ДАННЫЕ С РАЗРЕШЕНИЕМ (хранятся только при согласии) ===
    precise_location = Column(JSON, nullable=True)
    # {"lat": 55.7558, "lng": 37.6176, "accuracy": 10, "timestamp": "2024-01-01T12:00:00"}

    # === АНОНИМНЫЕ ДАННЫЕ ===
    anonymous_name = Column(String(100), nullable=True)
    anonymous_email = Column(String(255), nullable=True)

    # === ВРЕМЕННЫЕ МЕТКИ ===
    first_seen_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), nullable=False)

    # === СТАТУСЫ ===
    is_anonymous = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_merged = Column(Boolean, default=False, nullable=False)  # Был объединен с другим
    merged_into_id = Column(Integer, ForeignKey("respondents.id"), nullable=True)

    # === SOFT DELETE ===
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # === RELATIONSHIPS ===
    user = relationship("User", back_populates="respondents")
    responses = relationship("Response", back_populates="respondent")
    survey_participations = relationship(
        "RespondentSurvey", back_populates="respondent"
    )
    events = relationship("RespondentEvent", back_populates="respondent")
    consents = relationship("ConsentLog", back_populates="respondent")

    # Self-referential relationship for merging
    merged_from = relationship("Respondent", remote_side=[id])

    def __repr__(self):
        return f"<Respondent(id={self.id}, session_id='{self.session_id}', is_anonymous={self.is_anonymous})>"

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_respondents_fingerprint", "browser_fingerprint"),
        Index("ix_respondents_session", "session_id"),
        Index("ix_respondents_user_id", "user_id"),
        Index("ix_respondents_deleted", "is_deleted"),
        Index("ix_respondents_merged", "is_merged"),
        Index("ix_respondents_active", "is_active"),
        Index("ix_respondents_first_seen", "first_seen_at"),
        Index("ix_respondents_last_activity", "last_activity_at"),
        {"extend_existing": True},
    )


# Pydantic schemas
class RespondentBase(BaseModel):
    """Base Respondent schema with common fields."""

    session_id: str = Field(max_length=255, description="Unique session ID")
    browser_fingerprint: str | None = Field(
        None, max_length=255, description="Browser fingerprint"
    )
    ip_address: str | None = Field(None, max_length=45, description="IP address")
    user_agent: str | None = Field(None, description="User agent string")
    browser_info: Dict[str, Any] | None = Field(None, description="Browser information")
    device_info: Dict[str, Any] | None = Field(None, description="Device information")
    geo_info: Dict[str, Any] | None = Field(None, description="Geo information")
    referrer_info: Dict[str, Any] | None = Field(
        None, description="Referrer information"
    )
    telegram_data: Dict[str, Any] | None = Field(None, description="Telegram data")
    entry_point: str | None = Field(None, max_length=50, description="Entry point")
    precise_location: Dict[str, Any] | None = Field(
        None, description="Precise location"
    )
    anonymous_name: str | None = Field(
        None, max_length=100, description="Anonymous name"
    )
    anonymous_email: str | None = Field(
        None, max_length=255, description="Anonymous email"
    )
    is_anonymous: bool = Field(True, description="Is anonymous respondent")
    is_active: bool = Field(True, description="Is active respondent")


class RespondentCreate(RespondentBase):
    """Schema for creating a new respondent."""

    user_id: int | None = Field(None, description="User ID if authenticated")


class RespondentUpdate(BaseModel):
    """Schema for updating existing respondent."""

    browser_fingerprint: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=45)
    user_agent: str | None = None
    browser_info: Dict[str, Any] | None = None
    device_info: Dict[str, Any] | None = None
    geo_info: Dict[str, Any] | None = None
    referrer_info: Dict[str, Any] | None = None
    telegram_data: Dict[str, Any] | None = None
    entry_point: str | None = Field(None, max_length=50)
    precise_location: Dict[str, Any] | None = None
    anonymous_name: str | None = Field(None, max_length=100)
    anonymous_email: str | None = Field(None, max_length=255)
    is_anonymous: bool | None = None
    is_active: bool | None = None
    last_activity_at: datetime | None = None


class RespondentRead(RespondentBase):
    """Schema for reading respondent data."""

    id: int
    user_id: int | None
    first_seen_at: datetime
    last_activity_at: datetime
    is_merged: bool
    merged_into_id: int | None
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RespondentWithUser(RespondentRead):
    """Schema for reading respondent data with user information."""

    user: Any = Field(None, description="User information")

    model_config = ConfigDict(from_attributes=True)


class RespondentSummary(BaseModel):
    """Summary schema for respondent analytics."""

    total_respondents: int
    anonymous_respondents: int
    authenticated_respondents: int
    active_respondents: int
    merged_respondents: int
    entry_points: Dict[str, int] = Field(description="Entry point distribution")
    geo_distribution: Dict[str, int] = Field(description="Geographic distribution")
    device_types: Dict[str, int] = Field(description="Device type distribution")
    browsers: Dict[str, int] = Field(description="Browser distribution")


class RespondentMergeRequest(BaseModel):
    """Schema for merging respondents."""

    source_respondent_id: int = Field(description="Source respondent ID to merge from")
    target_respondent_id: int = Field(description="Target respondent ID to merge into")
    merge_reason: str = Field(description="Reason for merging")
    preserve_data: bool = Field(True, description="Whether to preserve source data")


class RespondentMergeResponse(BaseModel):
    """Schema for merge operation response."""

    success: bool
    merged_respondent_id: int
    source_respondent_id: int
    target_respondent_id: int
    merged_responses_count: int
    merged_consents_count: int
    message: str
