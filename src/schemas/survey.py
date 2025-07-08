"""
Survey schemas for the Quiz App.

This module contains Pydantic schemas for Survey model validation and serialization.
Re-exports schemas from models.survey for compatibility.
"""

from models.survey import (
    SurveyBase,
    SurveyCreate,
    SurveyUpdate,
    SurveyRead,
    SurveyReadWithQuestions,
)

# Alias for compatibility with new architecture
SurveyResponse = SurveyRead
SurveyWithQuestions = SurveyReadWithQuestions

__all__ = [
    "SurveyBase",
    "SurveyCreate",
    "SurveyUpdate",
    "SurveyRead",
    "SurveyResponse",
    "SurveyReadWithQuestions",
    "SurveyWithQuestions",
]
