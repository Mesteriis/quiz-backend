"""
SurveyDataRequirements SQLAlchemy model for the Quiz App.

This module contains the SurveyDataRequirements SQLAlchemy model and corresponding Pydantic schemas
for managing data collection requirements for surveys.
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
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class SurveyDataRequirements(Base):
    """SurveyDataRequirements database model."""

    __tablename__ = "survey_data_requirements"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False)

    # === ТРЕБОВАНИЯ К ГЕОЛОКАЦИИ ===
    requires_location = Column(Boolean, default=False, nullable=False)
    location_is_required = Column(
        Boolean, default=False, nullable=False
    )  # Обязательно или можно пропустить
    location_precision = Column(String(20), nullable=True)
    # "country", "city", "precise"

    # === ТРЕБОВАНИЯ К ЛИЧНЫМ ДАННЫМ ===
    requires_name = Column(Boolean, default=False, nullable=False)
    name_is_required = Column(Boolean, default=False, nullable=False)

    requires_email = Column(Boolean, default=False, nullable=False)
    email_is_required = Column(Boolean, default=False, nullable=False)

    requires_phone = Column(Boolean, default=False, nullable=False)
    phone_is_required = Column(Boolean, default=False, nullable=False)

    # === ТРЕБОВАНИЯ К ТЕХНИЧЕСКИМ ДАННЫМ ===
    requires_device_info = Column(Boolean, default=False, nullable=False)
    device_info_is_required = Column(Boolean, default=False, nullable=False)

    requires_browser_info = Column(Boolean, default=False, nullable=False)
    browser_info_is_required = Column(Boolean, default=False, nullable=False)

    # === ТРЕБОВАНИЯ К СОГЛАСИЯМ ===
    requires_analytics_consent = Column(Boolean, default=False, nullable=False)
    analytics_consent_is_required = Column(Boolean, default=False, nullable=False)

    requires_marketing_consent = Column(Boolean, default=False, nullable=False)
    marketing_consent_is_required = Column(Boolean, default=False, nullable=False)

    # === ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ ===
    custom_requirements = Column(JSON, nullable=True)
    # {"camera_access": {"required": true, "mandatory": false}, "microphone": {...}}

    # === УВЕДОМЛЕНИЯ И СООБЩЕНИЯ ===
    data_collection_notice = Column(String(500), nullable=True)
    privacy_policy_url = Column(String(500), nullable=True)
    terms_of_service_url = Column(String(500), nullable=True)

    # === НАСТРОЙКИ СБОРА ДАННЫХ ===
    data_retention_days = Column(Integer, default=365, nullable=False)
    allow_data_export = Column(Boolean, default=True, nullable=False)
    allow_data_deletion = Column(Boolean, default=True, nullable=False)

    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # === RELATIONSHIPS ===
    survey = relationship("Survey", back_populates="data_requirements")

    def __repr__(self):
        return f"<SurveyDataRequirements(id={self.id}, survey_id={self.survey_id})>"

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_survey_requirements_survey", "survey_id"),
        Index("ix_survey_requirements_location", "requires_location"),
        Index(
            "ix_survey_requirements_personal",
            "requires_name",
            "requires_email",
            "requires_phone",
        ),
        Index(
            "ix_survey_requirements_technical",
            "requires_device_info",
            "requires_browser_info",
        ),
        Index(
            "ix_survey_requirements_consent",
            "requires_analytics_consent",
            "requires_marketing_consent",
        ),
        {"extend_existing": True},
    )


# Pydantic schemas
class SurveyDataRequirementsBase(BaseModel):
    """Base SurveyDataRequirements schema with common fields."""

    survey_id: int = Field(description="Survey ID")

    # Location requirements
    requires_location: bool = Field(False, description="Requires location data")
    location_is_required: bool = Field(False, description="Location is mandatory")
    location_precision: str | None = Field(
        None, max_length=20, description="Location precision"
    )

    # Personal data requirements
    requires_name: bool = Field(False, description="Requires name")
    name_is_required: bool = Field(False, description="Name is mandatory")
    requires_email: bool = Field(False, description="Requires email")
    email_is_required: bool = Field(False, description="Email is mandatory")
    requires_phone: bool = Field(False, description="Requires phone")
    phone_is_required: bool = Field(False, description="Phone is mandatory")

    # Technical data requirements
    requires_device_info: bool = Field(False, description="Requires device info")
    device_info_is_required: bool = Field(False, description="Device info is mandatory")
    requires_browser_info: bool = Field(False, description="Requires browser info")
    browser_info_is_required: bool = Field(
        False, description="Browser info is mandatory"
    )

    # Consent requirements
    requires_analytics_consent: bool = Field(
        False, description="Requires analytics consent"
    )
    analytics_consent_is_required: bool = Field(
        False, description="Analytics consent is mandatory"
    )
    requires_marketing_consent: bool = Field(
        False, description="Requires marketing consent"
    )
    marketing_consent_is_required: bool = Field(
        False, description="Marketing consent is mandatory"
    )

    # Additional settings
    custom_requirements: Dict[str, Any] | None = Field(
        None, description="Custom requirements"
    )
    data_collection_notice: str | None = Field(
        None, max_length=500, description="Data collection notice"
    )
    privacy_policy_url: str | None = Field(
        None, max_length=500, description="Privacy policy URL"
    )
    terms_of_service_url: str | None = Field(
        None, max_length=500, description="Terms of service URL"
    )
    data_retention_days: int = Field(
        365, ge=1, description="Data retention period in days"
    )
    allow_data_export: bool = Field(True, description="Allow data export")
    allow_data_deletion: bool = Field(True, description="Allow data deletion")


class SurveyDataRequirementsCreate(SurveyDataRequirementsBase):
    """Schema for creating new survey data requirements."""

    pass


class SurveyDataRequirementsUpdate(BaseModel):
    """Schema for updating existing survey data requirements."""

    requires_location: bool | None = None
    location_is_required: bool | None = None
    location_precision: str | None = Field(None, max_length=20)
    requires_name: bool | None = None
    name_is_required: bool | None = None
    requires_email: bool | None = None
    email_is_required: bool | None = None
    requires_phone: bool | None = None
    phone_is_required: bool | None = None
    requires_device_info: bool | None = None
    device_info_is_required: bool | None = None
    requires_browser_info: bool | None = None
    browser_info_is_required: bool | None = None
    requires_analytics_consent: bool | None = None
    analytics_consent_is_required: bool | None = None
    requires_marketing_consent: bool | None = None
    marketing_consent_is_required: bool | None = None
    custom_requirements: Dict[str, Any] | None = None
    data_collection_notice: str | None = Field(None, max_length=500)
    privacy_policy_url: str | None = Field(None, max_length=500)
    terms_of_service_url: str | None = Field(None, max_length=500)
    data_retention_days: int | None = Field(None, ge=1)
    allow_data_export: bool | None = None
    allow_data_deletion: bool | None = None


class SurveyDataRequirementsRead(SurveyDataRequirementsBase):
    """Schema for reading survey data requirements."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsWithSurvey(SurveyDataRequirementsRead):
    """Schema for reading survey data requirements with survey information."""

    survey: Any = Field(None, description="Survey information")

    model_config = ConfigDict(from_attributes=True)


class DataRequirementsSummary(BaseModel):
    """Schema for data requirements summary."""

    total_surveys: int
    location_required_surveys: int
    personal_data_required_surveys: int
    technical_data_required_surveys: int
    consent_required_surveys: int
    requirement_distribution: Dict[str, int] = Field(
        description="Distribution of requirements"
    )
    average_retention_days: float
    gdpr_compliant_surveys: int


class LocationPrecisionTypes(BaseModel):
    """Schema for location precision types."""

    country: str = "Country-level location"
    city: str = "City-level location"
    precise: str = "Precise GPS coordinates"


class DataRequirementsTemplate(BaseModel):
    """Schema for data requirements template."""

    name: str = Field(description="Template name")
    description: str = Field(description="Template description")
    requirements: SurveyDataRequirementsBase = Field(
        description="Requirements configuration"
    )


class DataRequirementsValidation(BaseModel):
    """Schema for validating data requirements."""

    is_valid: bool
    validation_errors: list[str] = Field(description="List of validation errors")
    warnings: list[str] = Field(description="List of warnings")
    recommendations: list[str] = Field(description="List of recommendations")


class DataCollectionCompliance(BaseModel):
    """Schema for data collection compliance check."""

    survey_id: int
    is_gdpr_compliant: bool
    is_ccpa_compliant: bool
    compliance_score: float = Field(ge=0.0, le=1.0, description="Compliance score")
    compliance_issues: list[str] = Field(description="List of compliance issues")
    recommendations: list[str] = Field(description="List of recommendations")
