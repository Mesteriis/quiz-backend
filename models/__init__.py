"""
Models package for the Quiz App.

This module exports all SQLModel database models and schemas
for use throughout the application.
"""

# Import all models to ensure they are registered with SQLModel
from models.survey import (
    Survey,
    SurveyBase,
    SurveyCreate,
    SurveyUpdate,
    SurveyRead,
    SurveyReadWithQuestions,
)

from models.question import (
    Question,
    QuestionType,
    QuestionBase,
    QuestionCreate,
    QuestionUpdate,
    QuestionRead,
    QuestionReadWithResponses,
)

from models.response import (
    Response,
    ResponseBase,
    ResponseCreate,
    ResponseRead,
    ResponseReadWithQuestion,
    ResponseSummary,
)

from models.user_data import (
    UserData,
    UserDataBase,
    UserDataCreate,
    UserDataUpdate,
    UserDataRead,
    UserDataReadWithResponses,
    UserDataSummary,
)

from models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
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
