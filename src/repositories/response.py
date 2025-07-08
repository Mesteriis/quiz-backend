"""
Response repository for the Quiz App.

This module provides the response repository with specific methods
for response-related database operations.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.response import Response, ResponseCreate, ResponseRead
from .base import BaseRepository


class ResponseRepository(BaseRepository[Response, ResponseCreate, dict]):
    """
    Response repository with specific response operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize ResponseRepository with database session."""
        super().__init__(Response, db)

    async def get_by_question_id(self, question_id: int) -> List[Response]:
        """
        Get responses by question ID.

        Args:
            question_id: Question ID

        Returns:
            List of responses for question
        """
        query = (
            select(Response)
            .where(Response.question_id == question_id)
            .order_by(Response.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int) -> List[Response]:
        """
        Get responses by user ID.

        Args:
            user_id: User ID

        Returns:
            List of responses from user
        """
        query = (
            select(Response)
            .where(Response.user_id == user_id)
            .order_by(Response.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user_session_public_only(
        self, user_session_id: str
    ) -> List[Response]:
        """
        Get responses by user session ID (only public surveys).

        Args:
            user_session_id: User session ID

        Returns:
            List of responses from public surveys
        """
        from models.question import Question
        from models.survey import Survey

        query = (
            select(Response)
            .join(Question, Response.question_id == Question.id)
            .join(Survey, Question.survey_id == Survey.id)
            .where(
                Response.user_session_id == user_session_id,
                Survey.is_public == True,
            )
            .order_by(Response.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_question_and_session(self, question_id: int, user_session_id: str):
        """
        Get response by question ID and user session ID.

        Args:
            question_id: Question ID
            user_session_id: User session ID

        Returns:
            Response or None
        """
        query = select(Response).where(
            Response.question_id == question_id,
            Response.user_session_id == user_session_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_user_session_and_survey(
        self, user_session_id: str, survey_id: int
    ) -> List[Response]:
        """
        Get responses by user session and survey.

        Args:
            user_session_id: User session ID
            survey_id: Survey ID

        Returns:
            List of responses for user and survey
        """
        from models.question import Question

        query = (
            select(Response)
            .join(Question, Response.question_id == Question.id)
            .where(
                Response.user_session_id == user_session_id,
                Question.survey_id == survey_id,
            )
            .order_by(Response.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_question_and_user(self, question_id: int, user_id: int):
        """
        Get response by question ID and user ID.

        Args:
            question_id: Question ID
            user_id: User ID

        Returns:
            Response or None
        """
        query = select(Response).where(
            Response.question_id == question_id,
            Response.user_id == user_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_survey_id(self, survey_id: int) -> List[Response]:
        """
        Get responses by survey ID.

        Args:
            survey_id: Survey ID

        Returns:
            List of responses for survey
        """
        from models.question import Question

        query = (
            select(Response)
            .join(Question, Response.question_id == Question.id)
            .where(Question.survey_id == survey_id)
            .order_by(Response.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_responses_for_survey(
        self, user_id: int, survey_id: int
    ) -> List[Response]:
        """
        Get user responses for a specific survey.

        Args:
            user_id: User ID
            survey_id: Survey ID

        Returns:
            List of user responses for survey
        """
        from models.question import Question

        query = (
            select(Response)
            .join(Question, Response.question_id == Question.id)
            .where(
                Response.user_id == user_id,
                Question.survey_id == survey_id,
            )
            .order_by(Response.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_responses_by_survey(self, survey_id: int) -> int:
        """
        Count responses by survey ID.

        Args:
            survey_id: Survey ID

        Returns:
            Number of responses for survey
        """
        from models.question import Question
        from sqlalchemy import func

        query = (
            select(func.count(Response.id))
            .join(Question, Response.question_id == Question.id)
            .where(Question.survey_id == survey_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
