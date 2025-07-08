"""
Models package for the Quiz App.

This module exports all SQLAlchemy database models
for use throughout the application.
"""

# Import all SQLAlchemy models to ensure they are registered
# Order matters: import base models first, then dependent models

# Import basic models first
from .user import User
from .profile import Profile
from .user_data import UserData

# Import respondent models
from .respondent import Respondent
from .respondent_survey import RespondentSurvey
from .consent_log import ConsentLog
from .respondent_event import RespondentEvent

# Import question models
from .question import Question

# Import survey models (depends on question)
from .survey import Survey
from .survey_data_requirements import SurveyDataRequirements

# Import response models (depends on question and survey)
from .response import Response

# Import push notification models
from .push_notification import (
    PushSubscription,
    PushNotification,
    NotificationTemplate,
    NotificationAnalytics,
)

# Export only SQLAlchemy models
__all__ = [
    # Core models
    "User",
    "Profile",
    "UserData",
    "Survey",
    "Question",
    "Response",
    # Respondent architecture models
    "Respondent",
    "RespondentSurvey",
    "ConsentLog",
    "RespondentEvent",
    "SurveyDataRequirements",
    # Push notification models
    "PushSubscription",
    "PushNotification",
    "NotificationTemplate",
    "NotificationAnalytics",
]
