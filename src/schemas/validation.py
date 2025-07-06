"""
Validation schemas for the Quiz App API.

This module contains Pydantic schemas for validating API requests,
including special validations for email, phone, and Telegram data.
"""

from datetime import datetime
import re
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class EmailValidationRequest(BaseModel):
    """Request schema for email validation."""

    email: str = Field(..., description="Email address to validate")
    check_mx: bool = Field(True, description="Whether to check MX records")
    check_smtp: bool = Field(False, description="Whether to test SMTP connectivity")


class EmailValidationResponse(BaseModel):
    """Response schema for email validation."""

    email: str = Field(..., description="Original email address")
    is_valid: bool = Field(..., description="Whether email is valid")
    mx_valid: bool = Field(False, description="Whether MX records are valid")
    smtp_valid: Optional[bool] = Field(None, description="Whether SMTP test passed")
    error_message: Optional[str] = Field(
        None, description="Error message if validation failed"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Suggested corrections for typos"
    )


class PhoneValidationRequest(BaseModel):
    """Request schema for phone validation."""

    phone: str = Field(..., description="Phone number to validate")
    country_code: Optional[str] = Field(None, description="Country code (e.g., US, RU)")


class PhoneValidationResponse(BaseModel):
    """Response schema for phone validation."""

    phone: str = Field(..., description="Original phone number")
    normalized_phone: str = Field(..., description="Normalized phone number")
    is_valid: bool = Field(..., description="Whether phone is valid")
    country_code: Optional[str] = Field(
        None, description="Detected or provided country code"
    )
    carrier: Optional[str] = Field(None, description="Phone carrier (if available)")
    error_message: Optional[str] = Field(
        None, description="Error message if validation failed"
    )


class EmailBatchValidationRequest(BaseModel):
    """Request schema for batch email validation."""

    emails: list[str] = Field(
        ..., min_items=1, max_items=100, description="List of emails to validate"
    )
    check_mx: bool = Field(True, description="Whether to check MX records")
    check_smtp: bool = Field(False, description="Whether to test SMTP connectivity")


class EmailBatchValidationResponse(BaseModel):
    """Response schema for batch email validation."""

    total_count: int = Field(..., description="Total number of emails validated")
    valid_count: int = Field(..., description="Number of valid emails")
    invalid_count: int = Field(..., description="Number of invalid emails")
    results: list[EmailValidationResponse] = Field(
        ..., description="Individual validation results"
    )


class DomainMXResponse(BaseModel):
    """Response schema for domain MX record check."""

    domain: str = Field(..., description="Domain name")
    mx_valid: bool = Field(..., description="Whether MX records exist")
    mx_records: list[dict] = Field(
        default_factory=list, description="MX record details"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if check failed"
    )


class EmailSuggestionsResponse(BaseModel):
    """Response schema for email suggestions."""

    original_email: str = Field(..., description="Original email with potential typos")
    suggestions: list[str] = Field(
        default_factory=list, description="Suggested corrections"
    )
    has_suggestions: bool = Field(..., description="Whether suggestions are available")


class SMTPTestResponse(BaseModel):
    """Response schema for SMTP connectivity test."""

    email: str = Field(..., description="Email address tested")
    smtp_valid: bool = Field(..., description="Whether SMTP test passed")
    smtp_server: Optional[str] = Field(None, description="SMTP server used")
    smtp_response: Optional[str] = Field(None, description="SMTP server response")
    error_message: Optional[str] = Field(
        None, description="Error message if test failed"
    )


class ValidationHealthResponse(BaseModel):
    """Response schema for validation health check."""

    status: str = Field(..., description="Overall health status")
    dns_available: bool = Field(..., description="Whether DNS resolution is available")
    format_validation_working: bool = Field(
        ..., description="Whether format validation is working"
    )
    mx_check_enabled: bool = Field(..., description="Whether MX checking is enabled")
    smtp_timeout: int = Field(..., description="SMTP timeout in seconds")
    services: dict = Field(..., description="Status of individual services")


class TelegramAuthRequest(BaseModel):
    """Schema for Telegram authentication request."""

    username: str = Field(
        ..., min_length=1, max_length=100, description="Telegram username"
    )

    @validator("username")
    def validate_username(cls, v):
        """Validate Telegram username format."""
        # Remove @ if present
        if v.startswith("@"):
            v = v[1:]

        # Check username format (letters, numbers, underscores, 5-32 chars)
        if not re.match(r"^[a-zA-Z0-9_]{5,32}$", v):
            raise ValueError("Invalid Telegram username format")

        return v


class TelegramAuthResponse(BaseModel):
    """Schema for Telegram authentication response."""

    username: str = Field(..., description="Telegram username")
    auth_token: str = Field(..., description="Authentication token")
    expires_at: datetime = Field(..., description="Token expiration time")
    is_verified: bool = Field(..., description="Whether user is verified")


class TelegramWebAppData(BaseModel):
    """Schema for Telegram WebApp initialization data."""

    user_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(default=None, description="Telegram username")
    first_name: str = Field(..., description="User first name")
    last_name: Optional[str] = Field(default=None, description="User last name")
    language_code: Optional[str] = Field(default=None, description="User language code")
    photo_url: Optional[str] = Field(default=None, description="User photo URL")
    auth_date: int = Field(..., description="Authentication timestamp")
    hash: str = Field(..., description="Data hash for verification")


class FileUploadRequest(BaseModel):
    """Schema for file upload request."""

    file_type: str = Field(..., description="File MIME type")
    file_size: int = Field(..., description="File size in bytes")
    file_name: str = Field(..., description="Original file name")

    @validator("file_size")
    def validate_file_size(cls, v):
        """Validate file size."""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f"File size cannot exceed {max_size} bytes")
        return v

    @validator("file_type")
    def validate_file_type(cls, v):
        """Validate file type."""
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if v not in allowed_types:
            raise ValueError(f"File type must be one of: {', '.join(allowed_types)}")
        return v


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""

    file_id: str = Field(..., description="Unique file identifier")
    file_name: str = Field(..., description="Stored file name")
    file_url: str = Field(..., description="Public file URL")
    file_size: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class BrowserFingerprint(BaseModel):
    """Schema for browser fingerprint data."""

    user_agent: str = Field(..., description="Browser user agent")
    screen_resolution: str = Field(..., description="Screen resolution")
    color_depth: int = Field(..., description="Color depth")
    timezone: str = Field(..., description="Timezone offset")
    language: str = Field(..., description="Browser language")
    platform: str = Field(..., description="Operating system")
    canvas_fingerprint: Optional[str] = Field(
        default=None, description="Canvas fingerprint"
    )
    webgl_fingerprint: Optional[str] = Field(
        default=None, description="WebGL fingerprint"
    )
    audio_fingerprint: Optional[str] = Field(
        default=None, description="Audio fingerprint"
    )
    fonts: list[str] = Field(default_factory=list, description="Available fonts")
    plugins: list[str] = Field(default_factory=list, description="Browser plugins")


class GeolocationData(BaseModel):
    """Schema for geolocation data."""

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    accuracy: Optional[float] = Field(default=None, description="Accuracy in meters")
    altitude: Optional[float] = Field(default=None, description="Altitude in meters")
    altitude_accuracy: Optional[float] = Field(
        default=None, description="Altitude accuracy"
    )
    heading: Optional[float] = Field(default=None, description="Heading in degrees")
    speed: Optional[float] = Field(default=None, description="Speed in m/s")
    timestamp: Optional[int] = Field(default=None, description="Timestamp of reading")


class DeviceInfo(BaseModel):
    """Schema for device information."""

    device_type: str = Field(..., description="Device type (desktop, mobile, tablet)")
    operating_system: str = Field(..., description="Operating system")
    browser_name: str = Field(..., description="Browser name")
    browser_version: str = Field(..., description="Browser version")
    viewport_width: int = Field(..., description="Viewport width")
    viewport_height: int = Field(..., description="Viewport height")
    screen_width: int = Field(..., description="Screen width")
    screen_height: int = Field(..., description="Screen height")
    pixel_ratio: float = Field(..., description="Device pixel ratio")
    touch_support: bool = Field(..., description="Touch support")
    connection_type: Optional[str] = Field(default=None, description="Connection type")


class UserSessionData(BaseModel):
    """Schema for comprehensive user session data."""

    session_id: str = Field(..., description="Unique session identifier")
    fingerprint: BrowserFingerprint = Field(..., description="Browser fingerprint")
    device_info: DeviceInfo = Field(..., description="Device information")
    geolocation: Optional[GeolocationData] = Field(
        default=None, description="Geolocation data"
    )
    telegram_data: Optional[TelegramWebAppData] = Field(
        default=None, description="Telegram data"
    )
    referrer: Optional[str] = Field(default=None, description="Referrer URL")
    entry_page: str = Field(..., description="Entry page URL")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Session start time"
    )


class ErrorResponse(BaseModel):
    """Schema for API error responses."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class SuccessResponse(BaseModel):
    """Schema for API success responses."""

    message: str = Field(..., description="Success message")
    data: Optional[dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


__all__ = [
    "EmailValidationRequest",
    "EmailValidationResponse",
    "PhoneValidationRequest",
    "PhoneValidationResponse",
    "EmailBatchValidationRequest",
    "EmailBatchValidationResponse",
    "DomainMXResponse",
    "EmailSuggestionsResponse",
    "SMTPTestResponse",
    "ValidationHealthResponse",
]
