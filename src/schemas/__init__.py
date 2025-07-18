"""
Schemas package for the Quiz App.

This module contains Pydantic schemas for API request/response validation.
"""

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    UserProfile,
    UserListResponse,
    UserSearchRequest,
    UserStatsResponse,
)
from .admin import (
    AdminSurveyCreate,
    AdminQuestionCreate,
    AdminSurveyList,
    AdminSurveyDetail,
    SurveyStats,
    AdminUserData,
    AdminUsersList,
    AdminAnalytics,
    AdminReportRequest,
    AdminReportResponse,
    AdminSurveyBulkOperation,
    AdminSurveyBulkResponse,
    AdminSettings,
    AdminSettingsUpdate,
    AdminActivityLog,
    AdminActivityLogList,
)
from .push_notification import (
    PushNotificationBase,
    PushNotificationCreate,
    PushNotificationUpdate,
    PushNotificationStatsResponse,
    PushSubscriptionListResponse,
    PushNotificationListResponse,
)
from .validation import (
    EmailValidationResponse,
    PhoneValidationResponse,
    EmailBatchValidationResponse,
    DomainMXResponse,
    EmailSuggestionsResponse,
    SMTPTestResponse,
    ValidationHealthResponse,
    TelegramAuthResponse,
    FileUploadResponse,
    ErrorResponse,
    SuccessResponse,
)
from .profile import (
    ProfileBase,
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfilePublic,
    ProfileWithUser,
    ProfileSearch,
    ProfileStatistics,
)
from .respondent import (
    RespondentBase,
    RespondentCreate,
    RespondentUpdate,
    RespondentResponse,
    RespondentPublic,
    RespondentWithUser,
    RespondentSearch,
    RespondentStatistics,
    RespondentMerge,
    RespondentMergeResult,
    RespondentActivity,
    RespondentDataExport,
)
from .respondent_survey import (
    RespondentSurveyBase,
    RespondentSurveyCreate,
    RespondentSurveyUpdate,
    RespondentSurveyResponse,
    RespondentSurveyWithDetails,
    RespondentSurveyProgress,
    RespondentSurveyCompletion,
    RespondentSurveyStatistics,
    RespondentSurveySearch,
    RespondentSurveyActivity,
    RespondentSurveyTimeline,
    RespondentSurveyBulkUpdate,
    RespondentSurveyBulkUpdateResult,
)
from .consent_log import (
    ConsentLogBase,
    ConsentLogCreate,
    ConsentLogUpdate,
    ConsentLogResponse,
    ConsentLogWithDetails,
    ConsentGrant,
    ConsentRevoke,
    ConsentStatus,
    ConsentLogStatistics,
    ConsentLogSearch,
    ConsentLogActivity,
    ConsentLogExport,
    ConsentLogBulkGrant,
    ConsentLogBulkRevoke,
    ConsentLogBulkResult,
    ConsentLogAudit,
)
from .respondent_event import (
    RespondentEventBase,
    RespondentEventCreate,
    RespondentEventUpdate,
    RespondentEventResponse,
    RespondentEventWithDetails,
    RespondentEventLog,
    RespondentEventStatistics,
    RespondentEventSearch,
    RespondentEventActivity,
    RespondentEventTimeline,
    RespondentEventExport,
    RespondentEventTrend,
    RespondentEventTrendAnalysis,
    RespondentEventBulkLog,
    RespondentEventBulkResult,
    RespondentEventCleanup,
    RespondentEventCleanupResult,
)
from .survey_data_requirements import (
    SurveyDataRequirementsBase,
    SurveyDataRequirementsCreate,
    SurveyDataRequirementsUpdate,
    SurveyDataRequirementsResponse,
    SurveyDataRequirementsWithSurvey,
    SurveyDataRequirementsStatistics,
    SurveyDataRequirementsValidation,
    SurveyDataRequirementsCompliance,
    SurveyDataRequirementsTemplate,
    SurveyDataRequirementsClone,
    SurveyDataRequirementsGDPRUpdate,
    SurveyDataRequirementsConsentUpdate,
    SurveyDataRequirementsSearch,
    SurveyDataRequirementsDefault,
    SurveyDataRequirementsBulkUpdate,
    SurveyDataRequirementsBulkResult,
    SurveyDataRequirementsAudit,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "UserProfile",
    "UserListResponse",
    "UserSearchRequest",
    "UserStatsResponse",
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
    # Push notification schemas
    "PushNotificationBase",
    "PushNotificationCreate",
    "PushNotificationUpdate",
    "PushNotificationStatsResponse",
    "PushSubscriptionListResponse",
    "PushNotificationListResponse",
    # Validation schemas
    "EmailValidationResponse",
    "PhoneValidationResponse",
    "EmailBatchValidationResponse",
    "DomainMXResponse",
    "EmailSuggestionsResponse",
    "SMTPTestResponse",
    "ValidationHealthResponse",
    "TelegramAuthResponse",
    "FileUploadResponse",
    "ErrorResponse",
    "SuccessResponse",
    # Profile schemas
    "ProfileBase",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfileResponse",
    "ProfilePublic",
    "ProfileWithUser",
    "ProfileSearch",
    "ProfileStatistics",
    # Respondent schemas
    "RespondentBase",
    "RespondentCreate",
    "RespondentUpdate",
    "RespondentResponse",
    "RespondentPublic",
    "RespondentWithUser",
    "RespondentSearch",
    "RespondentStatistics",
    "RespondentMerge",
    "RespondentMergeResult",
    "RespondentActivity",
    "RespondentDataExport",
    # Respondent survey schemas
    "RespondentSurveyBase",
    "RespondentSurveyCreate",
    "RespondentSurveyUpdate",
    "RespondentSurveyResponse",
    "RespondentSurveyWithDetails",
    "RespondentSurveyProgress",
    "RespondentSurveyCompletion",
    "RespondentSurveyStatistics",
    "RespondentSurveySearch",
    "RespondentSurveyActivity",
    "RespondentSurveyTimeline",
    "RespondentSurveyBulkUpdate",
    "RespondentSurveyBulkUpdateResult",
    # Consent log schemas
    "ConsentLogBase",
    "ConsentLogCreate",
    "ConsentLogUpdate",
    "ConsentLogResponse",
    "ConsentLogWithDetails",
    "ConsentGrant",
    "ConsentRevoke",
    "ConsentStatus",
    "ConsentLogStatistics",
    "ConsentLogSearch",
    "ConsentLogActivity",
    "ConsentLogExport",
    "ConsentLogBulkGrant",
    "ConsentLogBulkRevoke",
    "ConsentLogBulkResult",
    "ConsentLogAudit",
    # Respondent event schemas
    "RespondentEventBase",
    "RespondentEventCreate",
    "RespondentEventUpdate",
    "RespondentEventResponse",
    "RespondentEventWithDetails",
    "RespondentEventLog",
    "RespondentEventStatistics",
    "RespondentEventSearch",
    "RespondentEventActivity",
    "RespondentEventTimeline",
    "RespondentEventExport",
    "RespondentEventTrend",
    "RespondentEventTrendAnalysis",
    "RespondentEventBulkLog",
    "RespondentEventBulkResult",
    "RespondentEventCleanup",
    "RespondentEventCleanupResult",
    # Survey data requirements schemas
    "SurveyDataRequirementsBase",
    "SurveyDataRequirementsCreate",
    "SurveyDataRequirementsUpdate",
    "SurveyDataRequirementsResponse",
    "SurveyDataRequirementsWithSurvey",
    "SurveyDataRequirementsStatistics",
    "SurveyDataRequirementsValidation",
    "SurveyDataRequirementsCompliance",
    "SurveyDataRequirementsTemplate",
    "SurveyDataRequirementsClone",
    "SurveyDataRequirementsGDPRUpdate",
    "SurveyDataRequirementsConsentUpdate",
    "SurveyDataRequirementsSearch",
    "SurveyDataRequirementsDefault",
    "SurveyDataRequirementsBulkUpdate",
    "SurveyDataRequirementsBulkResult",
    "SurveyDataRequirementsAudit",
]
