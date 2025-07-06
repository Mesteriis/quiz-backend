"""
Survey model for the Quiz App.

This module contains the Survey SQLModel with support for both
public and private surveys using access tokens.
"""

from datetime import datetime
import uuid

from sqlmodel import Field, Relationship, SQLModel
from .question import QuestionRead

class SurveyBase(SQLModel):
    """Base Survey model with common fields."""

    title: str = Field(max_length=200, description="Survey title")
    description: str | None = Field(
        default=None, max_length=1000, description="Survey description"
    )
    is_active: bool = Field(default=True, description="Whether survey is active")
    is_public: bool = Field(
        default=True, description="Whether survey is publicly accessible"
    )
    telegram_notifications: bool = Field(
        default=True, description="Enable Telegram notifications"
    )


class Survey(SurveyBase, table=True):
    """Survey database model."""

    id: int | None = Field(default=None, primary_key=True)
    access_token: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()),
        max_length=100,
        unique=True,
        index=True,
        description="Unique access token for private surveys",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    questions: list["Question"] = Relationship(
        back_populates="survey",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class SurveyCreate(SurveyBase):
    """Schema for creating a new survey."""

    pass


class SurveyUpdate(SQLModel):
    """Schema for updating an existing survey."""

    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = Field(default=None)
    is_public: bool | None = Field(default=None)
    telegram_notifications: bool | None = Field(default=None)


class SurveyRead(SurveyBase):
    """Schema for reading survey data."""

    id: int
    access_token: str
    created_at: datetime
    updated_at: datetime
    questions_count: int | None = Field(
        default=0, description="Number of questions in survey"
    )


class SurveyReadWithQuestions(SurveyRead):
    """Schema for reading survey with questions included."""

    questions: list[QuestionRead] = []
