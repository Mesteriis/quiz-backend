"""
ConsentLog schemas for the Quiz App.

This module contains Pydantic schemas for ConsentLog model validation and serialization.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from .respondent import RespondentResponse
    from .survey import SurveyResponse


class ConsentLogBase(BaseModel):
    """Base ConsentLog schema with common fields."""

    consent_type: str = Field(..., description="Type of consent")
    is_granted: bool = Field(..., description="Whether consent is granted")
    consent_version: str = Field("1.0", description="Consent version")
    consent_source: str | None = Field(None, description="Source of consent")
    ip_address: str | None = Field(
        None, description="IP address when consent was given"
    )
    user_agent: str | None = Field(
        None, description="User agent when consent was given"
    )
    details: Dict[str, Any] | None = Field(
        None, description="Additional consent details"
    )


class ConsentLogCreate(ConsentLogBase):
    """Schema for creating a new consent log."""

    respondent_id: int = Field(..., description="Respondent ID")
    survey_id: int | None = Field(None, description="Survey ID if survey-specific")


class ConsentLogUpdate(ConsentLogBase):
    """Schema for updating an existing consent log."""

    revoked_at: datetime | None = Field(None, description="Revocation timestamp")


class ConsentLogResponse(ConsentLogBase):
    """Schema for consent log responses."""

    id: int = Field(..., description="Consent log ID")
    respondent_id: int = Field(..., description="Respondent ID")
    survey_id: int | None = Field(None, description="Survey ID if survey-specific")
    granted_at: datetime = Field(..., description="Grant timestamp")
    revoked_at: datetime | None = Field(None, description="Revocation timestamp")

    model_config = ConfigDict(from_attributes=True)


class ConsentLogWithDetails(ConsentLogResponse):
    """Schema for consent log with respondent and survey details."""

    respondent: Optional["RespondentResponse"] = None
    survey: Optional["SurveyResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class ConsentGrant(BaseModel):
    """Schema for granting consent."""

    consent_type: str = Field(..., description="Type of consent")
    consent_version: str = Field("1.0", description="Consent version")
    consent_source: str | None = Field(None, description="Source of consent")
    details: Dict[str, Any] | None = Field(
        None, description="Additional consent details"
    )
    ip_address: str | None = Field(None, description="IP address")
    user_agent: str | None = Field(None, description="User agent")


class ConsentRevoke(BaseModel):
    """Schema for revoking consent."""

    revocation_reason: str | None = Field(None, description="Reason for revocation")


class ConsentStatus(BaseModel):
    """Schema for consent status."""

    location: bool = Field(False, description="Location consent status")
    device_info: bool = Field(False, description="Device info consent status")
    personal_data: bool = Field(False, description="Personal data consent status")
    marketing: bool = Field(False, description="Marketing consent status")
    analytics: bool = Field(False, description="Analytics consent status")
    cookies: bool = Field(False, description="Cookies consent status")

    model_config = ConfigDict(from_attributes=True)


class ConsentLogStatistics(BaseModel):
    """Schema for consent log statistics."""

    total_consents: int = Field(..., description="Total consent logs")
    granted_consents: int = Field(..., description="Granted consents")
    revoked_consents: int = Field(..., description="Revoked consents")
    consent_types: Dict[str, int] = Field(..., description="Consent types distribution")
    consent_sources: Dict[str, int] = Field(
        ..., description="Consent sources distribution"
    )
    grant_rate: float = Field(..., description="Grant rate percentage")
    revocation_rate: float = Field(..., description="Revocation rate percentage")

    model_config = ConfigDict(from_attributes=True)


class ConsentLogSearch(BaseModel):
    """Schema for consent log search parameters."""

    respondent_id: int | None = Field(None, description="Filter by respondent ID")
    survey_id: int | None = Field(None, description="Filter by survey ID")
    consent_type: str | None = Field(None, description="Filter by consent type")
    is_granted: bool | None = Field(None, description="Filter by granted status")
    consent_version: str | None = Field(None, description="Filter by consent version")
    consent_source: str | None = Field(None, description="Filter by consent source")
    granted_from: datetime | None = Field(None, description="Filter by grant date from")
    granted_to: datetime | None = Field(None, description="Filter by grant date to")
    revoked_from: datetime | None = Field(
        None, description="Filter by revocation date from"
    )
    revoked_to: datetime | None = Field(
        None, description="Filter by revocation date to"
    )
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")


class ConsentLogActivity(BaseModel):
    """Schema for recent consent activity."""

    consent_id: int = Field(..., description="Consent log ID")
    respondent_id: int = Field(..., description="Respondent ID")
    consent_type: str = Field(..., description="Type of consent")
    is_granted: bool = Field(..., description="Whether consent is granted")
    granted_at: datetime = Field(..., description="Grant timestamp")
    revoked_at: datetime | None = Field(None, description="Revocation timestamp")

    model_config = ConfigDict(from_attributes=True)


class ConsentLogExport(BaseModel):
    """Schema for consent log export (GDPR compliance)."""

    consent_id: int = Field(..., description="Consent log ID")
    consent_type: str = Field(..., description="Type of consent")
    is_granted: bool = Field(..., description="Whether consent is granted")
    granted_at: str = Field(..., description="Grant timestamp (ISO format)")
    revoked_at: str | None = Field(
        None, description="Revocation timestamp (ISO format)"
    )
    consent_version: str = Field(..., description="Consent version")
    consent_source: str | None = Field(None, description="Source of consent")
    details: Dict[str, Any] | None = Field(
        None, description="Additional consent details"
    )
    survey_id: int | None = Field(None, description="Survey ID if survey-specific")

    model_config = ConfigDict(from_attributes=True)


class ConsentLogBulkGrant(BaseModel):
    """Schema for bulk consent granting."""

    respondent_ids: list[int] = Field(..., description="List of respondent IDs")
    consent_data: ConsentGrant = Field(..., description="Consent data")
    survey_id: int | None = Field(None, description="Survey ID if survey-specific")


class ConsentLogBulkRevoke(BaseModel):
    """Schema for bulk consent revocation."""

    respondent_ids: list[int] = Field(..., description="List of respondent IDs")
    consent_type: str = Field(..., description="Type of consent to revoke")
    revocation_reason: str | None = Field(None, description="Reason for revocation")
    survey_id: int | None = Field(None, description="Survey ID if survey-specific")


class ConsentLogBulkResult(BaseModel):
    """Schema for bulk consent operation result."""

    processed_count: int = Field(..., description="Number of processed consents")
    successful_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
    successful_ids: list[int] = Field(
        ..., description="List of successful respondent IDs"
    )
    failed_ids: list[int] = Field(..., description="List of failed respondent IDs")

    model_config = ConfigDict(from_attributes=True)


class ConsentLogAudit(BaseModel):
    """Schema for consent log audit trail."""

    respondent_id: int = Field(..., description="Respondent ID")
    consent_history: list[ConsentLogResponse] = Field(
        ..., description="Consent history"
    )
    current_status: ConsentStatus = Field(..., description="Current consent status")
    last_updated: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
