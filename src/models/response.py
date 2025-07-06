"""
Response model for the Quiz App.

This module contains the Response SQLModel for storing user answers
to survey questions with immediate save functionality.
"""

from datetime import datetime
from typing import Any, Optional

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class ResponseBase(SQLModel):
    """Base Response model with common fields."""

    user_session_id: str = Field(max_length=100, description="User session identifier")
    user_id: int | None = Field(default=None, description="User ID (if authenticated)")
    answer: dict[str, Any] = Field(
        sa_column=Column(JSON), description="User answer data (JSON)"
    )


class Response(ResponseBase, table=True):
    """Response database model."""

    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id", description="Question ID")
    user_id: int | None = Field(
        default=None, foreign_key="user.id", description="User ID (if authenticated)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    question: "Question" = Relationship(back_populates="responses")
    user: Optional["User"] = Relationship(back_populates="responses")
    user_data: Optional["UserData"] = Relationship(
        back_populates="responses",
        sa_relationship_kwargs={
            "foreign_keys": "[Response.user_session_id]",
            "primaryjoin": "Response.user_session_id == UserData.session_id",
        },
    )


class ResponseCreate(ResponseBase):
    """Schema for creating a new response."""

    question_id: int


class ResponseRead(ResponseBase):
    """Schema for reading response data."""

    id: int
    question_id: int
    created_at: datetime


class ResponseReadWithQuestion(ResponseRead):
    """Schema for reading response with question included."""

    question: "QuestionRead"


class ResponseSummary(SQLModel):
    """Summary statistics for responses to a question."""

    question_id: int
    question_title: str
    question_type: str
    total_responses: int
    response_data: dict[str, Any] = Field(
        sa_column=Column(JSON), description="Aggregated response statistics"
    )


# Forward reference imports (avoid circular imports)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.question import Question, QuestionRead
    from models.user import User
    from models.user_data import UserData
