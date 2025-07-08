"""
Repository dependencies for the Quiz App.

This module provides dependency functions for injecting repositories
into FastAPI endpoints using the Depends pattern.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session

# Import repositories
from .user import UserRepository
from .survey import SurveyRepository
from .question import QuestionRepository
from .response import ResponseRepository
from .user_data import UserDataRepository
from .push_notification import (
    PushSubscriptionRepository,
    PushNotificationRepository,
    NotificationTemplateRepository,
    NotificationAnalyticsRepository,
)

# New Respondent architecture repositories
from .profile import ProfileRepository
from .respondent import RespondentRepository
from .respondent_survey import RespondentSurveyRepository
from .consent_log import ConsentLogRepository
from .respondent_event import RespondentEventRepository
from .survey_data_requirements import SurveyDataRequirementsRepository


# User Repository Dependency
def get_user_repository(
    db: AsyncSession = Depends(get_async_session),
) -> UserRepository:
    """
    Get UserRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(db)


# Survey Repository Dependency
def get_survey_repository(
    db: AsyncSession = Depends(get_async_session),
) -> SurveyRepository:
    """
    Get SurveyRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        SurveyRepository instance
    """
    return SurveyRepository(db)


# Question Repository Dependency
def get_question_repository(
    db: AsyncSession = Depends(get_async_session),
) -> QuestionRepository:
    """
    Get QuestionRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        QuestionRepository instance
    """
    return QuestionRepository(db)


# Response Repository Dependency
def get_response_repository(
    db: AsyncSession = Depends(get_async_session),
) -> ResponseRepository:
    """
    Get ResponseRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        ResponseRepository instance
    """
    return ResponseRepository(db)


# User Data Repository Dependency
def get_user_data_repository(
    db: AsyncSession = Depends(get_async_session),
) -> UserDataRepository:
    """
    Get UserDataRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        UserDataRepository instance
    """
    return UserDataRepository(db)


# Push Subscription Repository Dependency
def get_push_subscription_repository(
    db: AsyncSession = Depends(get_async_session),
) -> PushSubscriptionRepository:
    """
    Get PushSubscriptionRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        PushSubscriptionRepository instance
    """
    return PushSubscriptionRepository(db)


# Push Notification Repository Dependency
def get_push_notification_repository(
    db: AsyncSession = Depends(get_async_session),
) -> PushNotificationRepository:
    """
    Get PushNotificationRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        PushNotificationRepository instance
    """
    return PushNotificationRepository(db)


# Notification Template Repository Dependency
def get_notification_template_repository(
    db: AsyncSession = Depends(get_async_session),
) -> NotificationTemplateRepository:
    """
    Get NotificationTemplateRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        NotificationTemplateRepository instance
    """
    return NotificationTemplateRepository(db)


# Notification Analytics Repository Dependency
def get_notification_analytics_repository(
    db: AsyncSession = Depends(get_async_session),
) -> NotificationAnalyticsRepository:
    """
    Get NotificationAnalyticsRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        NotificationAnalyticsRepository instance
    """
    return NotificationAnalyticsRepository(db)


# Profile Repository Dependency
def get_profile_repository(
    db: AsyncSession = Depends(get_async_session),
) -> ProfileRepository:
    """
    Get ProfileRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        ProfileRepository instance
    """
    return ProfileRepository(db)


# Respondent Repository Dependency
def get_respondent_repository(
    db: AsyncSession = Depends(get_async_session),
) -> RespondentRepository:
    """
    Get RespondentRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        RespondentRepository instance
    """
    return RespondentRepository(db)


# RespondentSurvey Repository Dependency
def get_respondent_survey_repository(
    db: AsyncSession = Depends(get_async_session),
) -> RespondentSurveyRepository:
    """
    Get RespondentSurveyRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        RespondentSurveyRepository instance
    """
    return RespondentSurveyRepository(db)


# ConsentLog Repository Dependency
def get_consent_log_repository(
    db: AsyncSession = Depends(get_async_session),
) -> ConsentLogRepository:
    """
    Get ConsentLogRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        ConsentLogRepository instance
    """
    return ConsentLogRepository(db)


# RespondentEvent Repository Dependency
def get_respondent_event_repository(
    db: AsyncSession = Depends(get_async_session),
) -> RespondentEventRepository:
    """
    Get RespondentEventRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        RespondentEventRepository instance
    """
    return RespondentEventRepository(db)


# SurveyDataRequirements Repository Dependency
def get_survey_data_requirements_repository(
    db: AsyncSession = Depends(get_async_session),
) -> SurveyDataRequirementsRepository:
    """
    Get SurveyDataRequirementsRepository instance as a dependency.

    Args:
        db: Database session

    Returns:
        SurveyDataRequirementsRepository instance
    """
    return SurveyDataRequirementsRepository(db)
