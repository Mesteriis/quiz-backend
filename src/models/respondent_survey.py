"""
RespondentSurvey SQLAlchemy model for the Quiz App.

This module contains the RespondentSurvey SQLAlchemy model and corresponding Pydantic schemas
for managing respondent participation in surveys.
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class RespondentSurvey(Base):
    """RespondentSurvey database model."""

    __tablename__ = "respondent_surveys"

    id = Column(Integer, primary_key=True, index=True)
    respondent_id = Column(Integer, ForeignKey("respondents.id"), nullable=False)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False)

    # === СТАТУСЫ ПРОХОЖДЕНИЯ ===
    status = Column(String(20), default="started", nullable=False)
    # "started", "in_progress", "completed", "abandoned"

    # === ПРОГРЕСС ===
    progress_percentage = Column(Float, default=0.0, nullable=False)
    questions_answered = Column(Integer, default=0, nullable=False)
    total_questions = Column(Integer, nullable=False)

    # === ВРЕМЕННЫЕ МЕТКИ ===
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=func.now(), nullable=False)

    # === МЕТАДАННЫЕ ===
    time_spent_seconds = Column(Integer, default=0, nullable=False)
    completion_source = Column(String(50), nullable=True)
    # "web", "telegram_webapp", "telegram_bot"

    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # === RELATIONSHIPS ===
    respondent = relationship("Respondent", back_populates="survey_participations")
    survey = relationship("Survey", back_populates="respondent_participations")

    def __repr__(self):
        return f"<RespondentSurvey(id={self.id}, respondent_id={self.respondent_id}, survey_id={self.survey_id}, status='{self.status}')>"

    # === ИНДЕКСЫ ===
    __table_args__ = (
        UniqueConstraint("respondent_id", "survey_id", name="uq_respondent_survey"),
        Index("ix_respondent_surveys_status", "status"),
        Index("ix_respondent_surveys_started", "started_at"),
        Index("ix_respondent_surveys_completed", "completed_at"),
        Index("ix_respondent_surveys_progress", "progress_percentage"),
        Index("ix_respondent_surveys_last_activity", "last_activity_at"),
            {"extend_existing": True},

    )


# Pydantic schemas
class RespondentSurveyBase(BaseModel):
    """Base RespondentSurvey schema with common fields."""

    respondent_id: int = Field(description="Respondent ID")
    survey_id: int = Field(description="Survey ID")
    status: str = Field("started", max_length=20, description="Participation status")
    progress_percentage: float = Field(
        0.0, ge=0.0, le=100.0, description="Progress percentage"
    )
    questions_answered: int = Field(0, ge=0, description="Number of questions answered")
    total_questions: int = Field(ge=0, description="Total number of questions")
    time_spent_seconds: int = Field(0, ge=0, description="Time spent in seconds")
    completion_source: str | None = Field(
        None, max_length=50, description="Completion source"
    )


class RespondentSurveyCreate(RespondentSurveyBase):
    """Schema for creating a new respondent survey participation."""

    pass


class RespondentSurveyUpdate(BaseModel):
    """Schema for updating existing respondent survey participation."""

    status: str | None = Field(None, max_length=20)
    progress_percentage: float | None = Field(None, ge=0.0, le=100.0)
    questions_answered: int | None = Field(None, ge=0)
    total_questions: int | None = Field(None, ge=0)
    time_spent_seconds: int | None = Field(None, ge=0)
    completion_source: str | None = Field(None, max_length=50)
    completed_at: datetime | None = None
    last_activity_at: datetime | None = None


class RespondentSurveyRead(RespondentSurveyBase):
    """Schema for reading respondent survey participation data."""

    id: int
    started_at: datetime
    completed_at: datetime | None
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveyWithDetails(RespondentSurveyRead):
    """Schema for reading respondent survey participation with related data."""

    respondent: Any = Field(None, description="Respondent information")
    survey: Any = Field(None, description="Survey information")

    model_config = ConfigDict(from_attributes=True)


class RespondentSurveyStats(BaseModel):
    """Schema for respondent survey statistics."""

    total_participations: int
    completed_participations: int
    abandoned_participations: int
    in_progress_participations: int
    average_completion_time: float
    average_progress_percentage: float
    completion_rate: float
    abandonment_rate: float
    source_distribution: Dict[str, int] = Field(
        description="Completion source distribution"
    )
    status_distribution: Dict[str, int] = Field(description="Status distribution")


class RespondentSurveyProgressUpdate(BaseModel):
    """Schema for updating survey progress."""

    questions_answered: int = Field(ge=0, description="Number of questions answered")
    progress_percentage: float = Field(
        ge=0.0, le=100.0, description="Progress percentage"
    )
    time_spent_seconds: int = Field(ge=0, description="Additional time spent")
    last_activity_at: datetime | None = None


class RespondentSurveyCompletion(BaseModel):
    """Schema for completing a survey."""

    completion_source: str = Field(max_length=50, description="Source of completion")
    time_spent_seconds: int = Field(ge=0, description="Total time spent")
    completed_at: datetime | None = None
