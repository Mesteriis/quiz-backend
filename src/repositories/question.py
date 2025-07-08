"""
Question repository for the Quiz App.

This module provides the question repository with specific methods
for question-related database operations.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.question import Question, QuestionCreate, QuestionUpdate
from .base import BaseRepository


class QuestionRepository(BaseRepository[Question, QuestionCreate, QuestionUpdate]):
    """
    Question repository with specific question operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize QuestionRepository with database session."""
        super().__init__(Question, db)

    async def get_by_survey_id(self, survey_id: int) -> List[Question]:
        """
        Get questions by survey ID.

        Args:
            survey_id: Survey ID

        Returns:
            List of questions for survey
        """
        query = (
            select(Question)
            .where(Question.survey_id == survey_id)
            .order_by(Question.order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_required_questions(self, survey_id: int) -> List[Question]:
        """
        Get required questions for a survey.

        Args:
            survey_id: Survey ID

        Returns:
            List of required questions
        """
        query = (
            select(Question)
            .where(Question.survey_id == survey_id, Question.is_required == True)
            .order_by(Question.order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_survey_by_question_id(self, question_id: int):
        """
        Get survey by question ID.

        Args:
            question_id: Question ID

        Returns:
            Survey instance or None
        """
        from models.survey import Survey
        from sqlalchemy.orm import selectinload

        query = (
            select(Question)
            .options(selectinload(Question.survey))
            .where(Question.id == question_id)
        )
        result = await self.db.execute(query)
        question = result.scalars().first()
        return question.survey if question else None
