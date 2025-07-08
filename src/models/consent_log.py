"""
ConsentLog SQLAlchemy model for the Quiz App.

This module contains the ConsentLog SQLAlchemy model and corresponding Pydantic schemas
for managing user consent tracking and GDPR compliance.
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


class ConsentLog(Base):
    """ConsentLog database model."""

    __tablename__ = "consent_logs"

    id = Column(Integer, primary_key=True, index=True)
    respondent_id = Column(Integer, ForeignKey("respondents.id"), nullable=False)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=True)

    # === ТИПЫ СОГЛАСИЙ ===
    consent_type = Column(String(50), nullable=False)
    # "location", "device_info", "personal_data", "marketing", "analytics", "cookies"

    # === СТАТУС СОГЛАСИЯ ===
    is_granted = Column(Boolean, nullable=False)
    granted_at = Column(DateTime, default=func.now(), nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # === МЕТАДАННЫЕ ===
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    consent_version = Column(String(20), default="1.0", nullable=False)

    # === ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ===
    details = Column(JSON, nullable=True)
    # {"precision": "city", "purpose": "survey_analytics", "data_retention_days": 365}

    # === ИСТОЧНИК СОГЛАСИЯ ===
    consent_source = Column(String(50), nullable=True)
    # "survey_start", "profile_page", "settings", "popup", "telegram_bot"

    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # === RELATIONSHIPS ===
    respondent = relationship("Respondent", back_populates="consents")
    survey = relationship("Survey")

    def __repr__(self):
        return f"<ConsentLog(id={self.id}, respondent_id={self.respondent_id}, consent_type='{self.consent_type}', is_granted={self.is_granted})>"

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_consent_logs_respondent", "respondent_id"),
        Index("ix_consent_logs_type", "consent_type"),
        Index("ix_consent_logs_granted", "granted_at"),
        Index("ix_consent_logs_revoked", "revoked_at"),
        Index("ix_consent_logs_survey", "survey_id"),
        Index("ix_consent_logs_status", "is_granted"),
        Index("ix_consent_logs_version", "consent_version"),
        Index("ix_consent_logs_source", "consent_source"),
            {"extend_existing": True},

    )


# Pydantic schemas
class ConsentLogBase(BaseModel):
    """Base ConsentLog schema with common fields."""

    respondent_id: int = Field(description="Respondent ID")
    survey_id: int | None = Field(
        None, description="Survey ID (if consent is survey-specific)"
    )
    consent_type: str = Field(max_length=50, description="Type of consent")
    is_granted: bool = Field(description="Whether consent is granted")
    ip_address: str | None = Field(None, max_length=45, description="IP address")
    user_agent: str | None = Field(None, description="User agent")
    consent_version: str = Field("1.0", max_length=20, description="Consent version")
    details: Dict[str, Any] | None = Field(
        None, description="Additional consent details"
    )
    consent_source: str | None = Field(
        None, max_length=50, description="Source of consent"
    )


class ConsentLogCreate(ConsentLogBase):
    """Schema for creating a new consent log."""

    pass


class ConsentLogUpdate(BaseModel):
    """Schema for updating existing consent log."""

    is_granted: bool | None = None
    revoked_at: datetime | None = None
    details: Dict[str, Any] | None = None


class ConsentLogRead(ConsentLogBase):
    """Schema for reading consent log data."""

    id: int
    granted_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsentLogWithDetails(ConsentLogRead):
    """Schema for reading consent log with related data."""

    respondent: Any = Field(None, description="Respondent information")
    survey: Any = Field(None, description="Survey information")

    model_config = ConfigDict(from_attributes=True)


class ConsentSummary(BaseModel):
    """Schema for consent summary and analytics."""

    total_consents: int
    granted_consents: int
    revoked_consents: int
    consent_types: Dict[str, int] = Field(description="Consent type distribution")
    consent_sources: Dict[str, int] = Field(description="Consent source distribution")
    consent_versions: Dict[str, int] = Field(description="Consent version distribution")
    grant_rate: float
    revocation_rate: float
    recent_activity: Dict[str, int] = Field(description="Recent consent activity")


class ConsentRequest(BaseModel):
    """Schema for requesting consent."""

    consent_type: str = Field(max_length=50, description="Type of consent requested")
    survey_id: int | None = Field(None, description="Survey ID (if applicable)")
    details: Dict[str, Any] | None = Field(None, description="Consent details")
    consent_source: str | None = Field(
        None, max_length=50, description="Source of consent"
    )


class ConsentResponse(BaseModel):
    """Schema for consent response."""

    consent_id: int
    respondent_id: int
    consent_type: str
    is_granted: bool
    granted_at: datetime
    message: str


class ConsentRevocation(BaseModel):
    """Schema for revoking consent."""

    consent_id: int = Field(description="Consent ID to revoke")
    revocation_reason: str | None = Field(None, description="Reason for revocation")


class ConsentTypes(BaseModel):
    """Schema for available consent types."""

    location: str = "Geolocation data collection"
    device_info: str = "Device and browser information"
    personal_data: str = "Personal data processing"
    marketing: str = "Marketing communications"
    analytics: str = "Analytics and tracking"
    cookies: str = "Cookies and similar technologies"


class ConsentStatus(BaseModel):
    """Schema for respondent consent status."""

    respondent_id: int
    consents: Dict[str, bool] = Field(description="Consent status by type")
    last_updated: datetime
    total_consents: int
    granted_consents: int
