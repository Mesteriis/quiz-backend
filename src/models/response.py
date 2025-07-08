"""
Response model for the Quiz App.

This module contains the Response SQLAlchemy model and corresponding Pydantic schemas
for storing user responses to survey questions.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import relationship

from database import Base


class Response(Base):
    """Response database model."""

    __tablename__ = "response"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user_session_id = Column(String(100), nullable=False)
    respondent_id = Column(Integer, ForeignKey("respondents.id"), nullable=True)

    # Response data
    answer = Column(JSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    question = relationship("Question", back_populates="responses")
    user = relationship("User", back_populates="responses")
    user_data = relationship(
        "UserData",
        foreign_keys=[user_session_id],
        primaryjoin="Response.user_session_id == UserData.session_id",
        back_populates="responses",
    )
    respondent = relationship("Respondent", back_populates="responses")


# Pydantic schemas
class ResponseBase(BaseModel):
    """Base Response schema with common fields."""

    answer: Dict[str, Any] = Field(description="Response answer data")


class ResponseCreate(ResponseBase):
    """Schema for creating a new response."""

    question_id: int = Field(description="ID of the question being answered")
    user_id: Optional[int] = Field(None, description="ID of the user (if logged in)")
    user_session_id: str = Field(description="Session ID of the user")
    respondent_id: Optional[int] = Field(None, description="ID of the respondent")


class ResponseValidate(BaseModel):
    """Schema for validating response data."""

    question_id: int
    answer: Dict[str, Any]
    user_session_id: Optional[str] = None


class ResponseRead(ResponseBase):
    """Schema for reading response data."""

    id: int
    question_id: int
    user_id: Optional[int]
    user_session_id: str
    respondent_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResponseReadWithQuestion(ResponseRead):
    """Schema for reading response data with question included."""

    question: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ResponseSummary(BaseModel):
    """Summary of responses for analytics."""

    total_responses: int
    unique_users: int
    responses_by_question: Dict[int, int] = Field(
        description="Response count by question ID"
    )
    average_completion_time: Optional[float] = Field(
        None, description="Average time to complete"
    )
    completion_rate: float = Field(description="Percentage of completed surveys")
