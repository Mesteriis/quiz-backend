"""
Models package for the Quiz App.

This module exports all SQLModel database models and schemas
for use throughout the application.
"""

# Import all models to ensure they are registered with SQLModel
# Order matters: import base models first, then dependent models

# Import basic models first
from .user import (
    User,
    UserCreate,
    UserProfile,
    UserResponse,
    UserUpdate,
)
from .user_data import (
    UserData,
    UserDataBase,
    UserDataCreate,
    UserDataRead,
    UserDataReadWithResponses,
    UserDataSummary,
    UserDataUpdate,
)

# Import question models
from .question import (
    Question,
    QuestionBase,
    QuestionCreate,
    QuestionRead,
    QuestionReadWithResponses,
    QuestionType,
    QuestionUpdate,
)

# Import survey models (depends on question)
from .survey import (
    Survey,
    SurveyBase,
    SurveyCreate,
    SurveyRead,
    SurveyReadWithQuestions,
    SurveyUpdate,
)

# Import response models (depends on question and survey)
from .response import (
    Response,
    ResponseBase,
    ResponseCreate,
    ResponseRead,
    ResponseReadWithQuestion,
    ResponseSummary,
)

# Export all models for easy import
__all__ = [
    # Survey models
    "Survey",
    "SurveyBase",
    "SurveyCreate",
    "SurveyUpdate",
    "SurveyRead",
    "SurveyReadWithQuestions",
    # Question models
    "Question",
    "QuestionType",
    "QuestionBase",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionRead",
    "QuestionReadWithResponses",
    # Response models
    "Response",
    "ResponseBase",
    "ResponseCreate",
    "ResponseRead",
    "ResponseReadWithQuestion",
    "ResponseSummary",
    # UserData models
    "UserData",
    "UserDataBase",
    "UserDataCreate",
    "UserDataUpdate",
    "UserDataRead",
    "UserDataReadWithResponses",
    "UserDataSummary",
    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
]
