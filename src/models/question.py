"""
Question model for the Quiz App.

This module contains the Question SQLModel with support for different
question types and optional image attachments.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class QuestionType(str, Enum):
    """Available question types."""

    RATING_1_10 = "rating_1_10"
    YES_NO = "yes_no"
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    IMAGE_UPLOAD = "image_upload"


class QuestionBase(SQLModel):
    """Base Question model with common fields."""

    title: str = Field(max_length=500, description="Question title")
    description: str | None = Field(
        default=None, max_length=2000, description="Question description"
    )
    image_url: str | None = Field(
        default=None, max_length=500, description="Attached image URL"
    )
    question_type: QuestionType = Field(description="Type of question")
    is_required: bool = Field(default=True, description="Whether answer is required")
    order: int = Field(default=0, description="Question order in survey")
    options: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional options for question (JSON)",
    )


class Question(QuestionBase, table=True):
    """Question database model."""

    id: int | None = Field(default=None, primary_key=True)
    survey_id: int = Field(foreign_key="survey.id", description="Survey ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    survey: "Survey" = Relationship(back_populates="questions")
    responses: list["Response"] = Relationship(
        back_populates="question",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""

    survey_id: int


class QuestionUpdate(SQLModel):
    """Schema for updating an existing question."""

    title: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    question_type: QuestionType | None = Field(default=None)
    is_required: bool | None = Field(default=None)
    order: int | None = Field(default=None)
    options: dict[str, Any] | None = Field(default=None)


class QuestionRead(QuestionBase):
    """Schema for reading question data."""

    id: int
    survey_id: int
    created_at: datetime
    updated_at: datetime


class QuestionReadWithResponses(QuestionRead):
    """Schema for reading question with responses included."""

    responses: list["ResponseRead"] = []


# Forward reference imports (avoid circular imports)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.response import Response, ResponseRead
    from models.survey import Survey
