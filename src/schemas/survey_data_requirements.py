"""
SurveyDataRequirements schemas for the Quiz App.

This module contains Pydantic schemas for SurveyDataRequirements model validation and serialization.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from .survey import SurveyResponse


class SurveyDataRequirementsBase(BaseModel):
    """Base SurveyDataRequirements schema with common fields."""

    requires_location: bool = Field(
        False, description="Whether location data is required"
    )
    requires_precise_location: bool = Field(
        False, description="Whether precise location is required"
    )
    requires_personal_data: bool = Field(
        False, description="Whether personal data is required"
    )
    requires_technical_data: bool = Field(
        True, description="Whether technical data is required"
    )
    gdpr_compliant: bool = Field(True, description="Whether GDPR compliance is enabled")
    consent_required: Dict[str, Any] | None = Field(
        None, description="Consent requirements"
    )
    data_retention_days: int = Field(
        365, ge=1, description="Data retention period in days"
    )
    notes: str | None = Field(None, description="Additional notes")


class SurveyDataRequirementsCreate(SurveyDataRequirementsBase):
    """Schema for creating new survey data requirements."""

    survey_id: int = Field(..., description="Survey ID")


class SurveyDataRequirementsUpdate(SurveyDataRequirementsBase):
    """Schema for updating existing survey data requirements."""

    pass


class SurveyDataRequirementsResponse(SurveyDataRequirementsBase):
    """Schema for survey data requirements responses."""

    id: int = Field(..., description="Requirements ID")
    survey_id: int = Field(..., description="Survey ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsWithSurvey(SurveyDataRequirementsResponse):
    """Schema for survey data requirements with survey details."""

    survey: Optional["SurveyResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsStatistics(BaseModel):
    """Schema for survey data requirements statistics."""

    total_surveys_with_requirements: int = Field(
        ..., description="Total surveys with requirements"
    )
    location_surveys: int = Field(..., description="Surveys requiring location")
    location_percentage: float = Field(
        ..., description="Location requirement percentage"
    )
    precise_location_surveys: int = Field(
        ..., description="Surveys requiring precise location"
    )
    precise_location_percentage: float = Field(
        ..., description="Precise location requirement percentage"
    )
    personal_data_surveys: int = Field(
        ..., description="Surveys requiring personal data"
    )
    personal_data_percentage: float = Field(
        ..., description="Personal data requirement percentage"
    )
    technical_data_surveys: int = Field(
        ..., description="Surveys requiring technical data"
    )
    technical_data_percentage: float = Field(
        ..., description="Technical data requirement percentage"
    )
    gdpr_surveys: int = Field(..., description="GDPR compliant surveys")
    gdpr_percentage: float = Field(..., description="GDPR compliance percentage")
    consent_surveys: int = Field(..., description="Surveys with consent requirements")
    consent_percentage: float = Field(..., description="Consent requirement percentage")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsValidation(BaseModel):
    """Schema for survey data requirements validation."""

    is_valid: bool = Field(..., description="Whether requirements are valid")
    errors: list[str] = Field(..., description="List of validation errors")
    warnings: list[str] = Field(..., description="List of validation warnings")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsCompliance(BaseModel):
    """Schema for compliance report."""

    total_surveys: int = Field(..., description="Total surveys")
    compliant_surveys: int = Field(..., description="Compliant surveys")
    non_compliant_surveys: int = Field(..., description="Non-compliant surveys")
    compliance_rate: float = Field(..., description="Compliance rate percentage")
    compliance_issues: list[Dict[str, Any]] = Field(
        ..., description="List of compliance issues"
    )

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsTemplate(BaseModel):
    """Schema for data requirements template."""

    template_name: str = Field(..., description="Template name")
    template_description: str | None = Field(None, description="Template description")
    requirements: SurveyDataRequirementsBase = Field(
        ..., description="Requirements configuration"
    )

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsClone(BaseModel):
    """Schema for cloning data requirements."""

    source_survey_id: int = Field(..., description="Source survey ID")
    target_survey_id: int = Field(..., description="Target survey ID")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsGDPRUpdate(BaseModel):
    """Schema for GDPR compliance update."""

    gdpr_compliant: bool = Field(..., description="GDPR compliance status")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsConsentUpdate(BaseModel):
    """Schema for consent requirements update."""

    consent_required: Dict[str, Any] = Field(..., description="Consent requirements")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsSearch(BaseModel):
    """Schema for search parameters."""

    requires_location: bool | None = Field(
        None, description="Filter by location requirement"
    )
    requires_precise_location: bool | None = Field(
        None, description="Filter by precise location requirement"
    )
    requires_personal_data: bool | None = Field(
        None, description="Filter by personal data requirement"
    )
    requires_technical_data: bool | None = Field(
        None, description="Filter by technical data requirement"
    )
    gdpr_compliant: bool | None = Field(None, description="Filter by GDPR compliance")
    has_consent_requirements: bool | None = Field(
        None, description="Filter by consent requirements presence"
    )
    data_retention_min: int | None = Field(
        None, ge=1, description="Minimum data retention days"
    )
    data_retention_max: int | None = Field(
        None, ge=1, description="Maximum data retention days"
    )
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")


class SurveyDataRequirementsDefault(BaseModel):
    """Schema for default requirements."""

    requires_location: bool = Field(False, description="Default location requirement")
    requires_precise_location: bool = Field(
        False, description="Default precise location requirement"
    )
    requires_personal_data: bool = Field(
        False, description="Default personal data requirement"
    )
    requires_technical_data: bool = Field(
        True, description="Default technical data requirement"
    )
    gdpr_compliant: bool = Field(True, description="Default GDPR compliance")
    consent_required: Dict[str, Any] = Field(
        default_factory=lambda: {
            "location": False,
            "device_info": True,
            "personal_data": False,
            "marketing": False,
            "analytics": True,
            "cookies": True,
        },
        description="Default consent requirements",
    )
    data_retention_days: int = Field(365, description="Default data retention period")
    notes: str = Field(
        "Default requirements for new surveys", description="Default notes"
    )

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsBulkUpdate(BaseModel):
    """Schema for bulk updating requirements."""

    survey_ids: list[int] = Field(..., description="List of survey IDs")
    update_data: SurveyDataRequirementsUpdate = Field(..., description="Update data")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsBulkResult(BaseModel):
    """Schema for bulk update result."""

    updated_count: int = Field(..., description="Number of updated requirements")
    failed_count: int = Field(..., description="Number of failed updates")
    updated_ids: list[int] = Field(
        ..., description="List of successfully updated survey IDs"
    )
    failed_ids: list[int] = Field(..., description="List of failed survey IDs")

    model_config = ConfigDict(from_attributes=True)


class SurveyDataRequirementsAudit(BaseModel):
    """Schema for requirements audit."""

    survey_id: int = Field(..., description="Survey ID")
    requirements: SurveyDataRequirementsResponse = Field(
        ..., description="Current requirements"
    )
    validation: SurveyDataRequirementsValidation = Field(
        ..., description="Validation results"
    )
    compliance_status: str = Field(..., description="Compliance status")
    last_updated: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
