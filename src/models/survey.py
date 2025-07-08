"""
Survey model for the Quiz App.

This module contains the Survey SQLAlchemy model and corresponding Pydantic schemas
for creating and managing surveys/quizzes.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database import Base


class Survey(Base):
    """Survey database model."""

    __tablename__ = "survey"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)

    # Basic information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    access_token = Column(String(100), nullable=True, index=True)

    # Telegram notifications
    telegram_notifications = Column(Boolean, default=False, nullable=False)

    # Creator
    created_by = Column(Integer, ForeignKey("user.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    questions = relationship(
        "Question", back_populates="survey", cascade="all, delete-orphan"
    )
    creator = relationship("User", back_populates="created_surveys")
    respondent_participations = relationship(
        "RespondentSurvey", back_populates="survey"
    )
    data_requirements = relationship(
        "SurveyDataRequirements", back_populates="survey", uselist=False
    )


# Pydantic schemas
class SurveyBase(BaseModel):
    """Base Survey schema with common fields."""

    title: str = Field(max_length=500, description="Survey title")
    description: Optional[str] = Field(None, description="Survey description")
    is_active: bool = Field(True, description="Is survey active")
    is_public: bool = Field(True, description="Is survey public")
    access_token: Optional[str] = Field(
        None, max_length=100, description="Access token for private surveys"
    )
    telegram_notifications: bool = Field(
        False, description="Enable Telegram notifications"
    )


class SurveyCreate(SurveyBase):
    """Schema for creating a new survey."""

    created_by: Optional[int] = Field(
        None, description="ID of the user creating the survey"
    )


class SurveyUpdate(BaseModel):
    """Schema for updating existing survey."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    access_token: Optional[str] = Field(None, max_length=100)
    telegram_notifications: Optional[bool] = None


class SurveyRead(SurveyBase):
    """Schema for reading survey data."""

    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveyReadWithQuestions(SurveyRead):
    """Schema for reading survey data with questions included."""

    questions: list[dict] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
