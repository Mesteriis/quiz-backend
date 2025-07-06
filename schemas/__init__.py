"""
Schemas package for the Quiz App.

This module exports all Pydantic validation schemas
for use throughout the application.
"""

from schemas.validation import (
    # Email validation
    EmailValidationRequest,
    EmailValidationResponse,
    
    # Phone validation
    PhoneValidationRequest,
    PhoneValidationResponse,
    
    # Telegram authentication
    TelegramAuthRequest,
    TelegramAuthResponse,
    TelegramWebAppData,
    
    # File upload
    FileUploadRequest,
    FileUploadResponse,
    
    # User data collection
    BrowserFingerprint,
    GeolocationData,
    DeviceInfo,
    UserSessionData,
    
    # Generic responses
    ErrorResponse,
    SuccessResponse,
)

from schemas.admin import (
    # Admin survey management
    AdminSurveyCreate,
    AdminQuestionCreate,
    AdminSurveyList,
    AdminSurveyDetail,
    SurveyStats,
    
    # Admin user management
    AdminUserData,
    AdminUsersList,
    
    # Admin analytics
    AdminAnalytics,
    
    # Admin reporting
    AdminReportRequest,
    AdminReportResponse,
    
    # Admin bulk operations
    AdminSurveyBulkOperation,
    AdminSurveyBulkResponse,
    
    # Admin settings
    AdminSettings,
    AdminSettingsUpdate,
    
    # Admin activity logging
    AdminActivityLog,
    AdminActivityLogList,
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
