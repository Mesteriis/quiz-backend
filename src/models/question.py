"""
Question model for the Quiz App.

This module contains the Question SQLAlchemy model and corresponding Pydantic schemas
for creating and managing survey questions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class QuestionType(str, Enum):
    """Types of questions that can be created."""

    RATING_1_10 = "RATING_1_10"
    YES_NO = "YES_NO"
    TEXT = "TEXT"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    IMAGE_UPLOAD = "IMAGE_UPLOAD"
    FILE_UPLOAD = "FILE_UPLOAD"
    GEOLOCATION = "GEOLOCATION"
    NFC_SCAN = "NFC_SCAN"


class Question(Base):
    """Question database model."""

    __tablename__ = "question"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False)

    # Basic information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    question_type = Column(String(20), nullable=False)

    # Options and configuration
    is_required = Column(Boolean, default=True, nullable=False)
    order = Column(Integer, default=0, nullable=False)
    options = Column(JSON, nullable=True)
    question_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    survey = relationship("Survey", back_populates="questions")
    responses = relationship(
        "Response", back_populates="question", cascade="all, delete-orphan"
    )


# Pydantic schemas
class QuestionBase(BaseModel):
    """Base Question schema with common fields."""

    title: str = Field(max_length=500, description="Question title")
    description: Optional[str] = Field(None, description="Question description")
    question_type: QuestionType = Field(description="Type of question")
    is_required: bool = Field(True, description="Is question required")
    order: int = Field(0, description="Question order in survey")
    options: Optional[Dict[str, Any]] = Field(
        None, description="Question options and configuration"
    )
    question_data: Optional[Dict[str, Any]] = Field(
        None, description="Additional question data and metadata"
    )


class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""

    survey_id: int = Field(description="ID of the survey this question belongs to")


class QuestionUpdate(BaseModel):
    """Schema for updating existing question."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    question_type: Optional[QuestionType] = None
    is_required: Optional[bool] = None
    order: Optional[int] = None
    options: Optional[Dict[str, Any]] = None
    question_data: Optional[Dict[str, Any]] = None


class QuestionRead(QuestionBase):
    """Schema for reading question data."""

    id: int
    survey_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionReadWithResponses(QuestionRead):
    """Schema for reading question data with responses included."""

    responses: List = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
