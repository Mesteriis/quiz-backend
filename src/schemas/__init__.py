"""
Schemas package for the Quiz App.

This module exports all Pydantic validation schemas
for use throughout the application.
"""

from schemas.admin import (
    # Admin activity logging
    AdminActivityLog,
    AdminActivityLogList,
    # Admin analytics
    AdminAnalytics,
    AdminQuestionCreate,
    # Admin reporting
    AdminReportRequest,
    AdminReportResponse,
    # Admin settings
    AdminSettings,
    AdminSettingsUpdate,
    # Admin bulk operations
    AdminSurveyBulkOperation,
    AdminSurveyBulkResponse,
    # Admin survey management
    AdminSurveyCreate,
    AdminSurveyDetail,
    AdminSurveyList,
    # Admin user management
    AdminUserData,
    AdminUsersList,
    SurveyStats,
)
from schemas.validation import (
    # User data collection
    BrowserFingerprint,
    DeviceInfo,
    # Email validation
    EmailValidationRequest,
    EmailValidationResponse,
    # Generic responses
    ErrorResponse,
    # File upload
    FileUploadRequest,
    FileUploadResponse,
    GeolocationData,
    # Phone validation
    PhoneValidationRequest,
    PhoneValidationResponse,
    SuccessResponse,
    # Telegram authentication
    TelegramAuthRequest,
    TelegramAuthResponse,
    TelegramWebAppData,
    UserSessionData,
)

# Export all schemas
__all__ = [
    # Validation schemas
    "EmailValidationRequest",
    "EmailValidationResponse",
    "PhoneValidationRequest",
    "PhoneValidationResponse",
    "TelegramAuthRequest",
    "TelegramAuthResponse",
    "TelegramWebAppData",
    "FileUploadRequest",
    "FileUploadResponse",
    "BrowserFingerprint",
    "GeolocationData",
    "DeviceInfo",
    "UserSessionData",
    "ErrorResponse",
    "SuccessResponse",
    # Admin schemas
    "AdminSurveyCreate",
    "AdminQuestionCreate",
    "AdminSurveyList",
    "AdminSurveyDetail",
    "SurveyStats",
    "AdminUserData",
    "AdminUsersList",
    "AdminAnalytics",
    "AdminReportRequest",
    "AdminReportResponse",
    "AdminSurveyBulkOperation",
    "AdminSurveyBulkResponse",
    "AdminSettings",
    "AdminSettingsUpdate",
    "AdminActivityLog",
    "AdminActivityLogList",
]
