"""
Survey repository for the Quiz App.

This module provides the survey repository with specific methods
for survey-related database operations.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.survey import Survey, SurveyCreate, SurveyUpdate
from .base import BaseRepository


class SurveyRepository(BaseRepository[Survey, SurveyCreate, SurveyUpdate]):
    """
    Survey repository with specific survey operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize SurveyRepository with database session."""
        super().__init__(Survey, db)

    async def get_active_surveys(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Survey]:
        """
        Get active surveys.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active surveys
        """
        query = select(Survey).where(Survey.is_active == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_public_surveys(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Survey]:
        """
        Get public surveys.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of public surveys
        """
        query = select(Survey).where(Survey.is_public == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_access_token(self, access_token: str) -> Optional[Survey]:
        """
        Get survey by access token.

        Args:
            access_token: Access token

        Returns:
            Survey or None
        """
        return await self.get_by_field("access_token", access_token)

    async def get_active_public_surveys(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Survey]:
        """
        Get active public surveys.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active public surveys
        """
        query = (
            select(Survey)
            .where(Survey.is_active == True)
            .where(Survey.is_public == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_survey_stats(self, survey_id: int) -> Dict[str, Any]:
        """
        Get survey statistics.

        Args:
            survey_id: Survey ID

        Returns:
            Dictionary with survey statistics
        """
        try:
            # Get basic response statistics
            stats_query = text(
                """
                SELECT
                    COUNT(DISTINCT r.user_session_id) as unique_respondents,
                    COUNT(r.id) as total_responses,
                    COUNT(DISTINCT r.user_id) as authenticated_users,
                    COUNT(DISTINCT q.id) as total_questions,
                    MIN(r.created_at) as first_response,
                    MAX(r.created_at) as last_response
                FROM response r
                JOIN question q ON r.question_id = q.id
                WHERE q.survey_id = :survey_id
            """
            )

            result = await self.db.execute(stats_query, {"survey_id": survey_id})
            stats_row = result.fetchone()

            # Get completion rate
            completion_query = text(
                """
                SELECT
                    COUNT(DISTINCT r.user_session_id) as started,
                    COUNT(DISTINCT complete_sessions.session_id) as completed
                FROM response r
                JOIN question q ON r.question_id = q.id
                LEFT JOIN (
                    SELECT r2.user_session_id as session_id
                    FROM response r2
                    JOIN question q2 ON r2.question_id = q2.id
                    WHERE q2.survey_id = :survey_id
                    GROUP BY r2.user_session_id
                    HAVING COUNT(DISTINCT q2.id) = (
                        SELECT COUNT(id) FROM question WHERE survey_id = :survey_id
                    )
                ) complete_sessions ON r.user_session_id = complete_sessions.session_id
                WHERE q.survey_id = :survey_id
            """
            )

            completion_result = await self.db.execute(
                completion_query, {"survey_id": survey_id}
            )
            completion_row = completion_result.fetchone()

            return {
                "unique_respondents": stats_row.unique_respondents or 0,
                "total_responses": stats_row.total_responses or 0,
                "authenticated_users": stats_row.authenticated_users or 0,
                "total_questions": stats_row.total_questions or 0,
                "completion_rate": (
                    completion_row.completed / completion_row.started * 100
                    if completion_row.started > 0
                    else 0
                ),
                "first_response": stats_row.first_response.isoformat()
                if stats_row.first_response
                else None,
                "last_response": stats_row.last_response.isoformat()
                if stats_row.last_response
                else None,
            }

        except Exception as e:
            # Return empty stats if there's an error
            return {
                "unique_respondents": 0,
                "total_responses": 0,
                "authenticated_users": 0,
                "total_questions": 0,
                "completion_rate": 0,
                "first_response": None,
                "last_response": None,
            }

    async def get_by_created_by(self, created_by: int) -> List[Survey]:
        """
        Get surveys created by a specific user.

        Args:
            created_by: User ID

        Returns:
            List of surveys created by the user
        """
        query = select(Survey).where(Survey.created_by == created_by)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_surveys_with_responses(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Survey]:
        """
        Get surveys that have responses.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of surveys with responses
        """
        query = text(
            """
            SELECT DISTINCT s.*
            FROM survey s
            JOIN question q ON s.id = q.survey_id
            JOIN response r ON q.id = r.question_id
            ORDER BY s.created_at DESC
            LIMIT :limit OFFSET :skip
        """
        )

        result = await self.db.execute(query, {"limit": limit, "skip": skip})
        rows = result.fetchall()

        # Convert to Survey objects
        surveys = []
        for row in rows:
            survey_data = {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "is_active": row.is_active,
                "is_public": row.is_public,
                "telegram_notifications": row.telegram_notifications,
                "access_token": row.access_token,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "created_by": row.created_by,
            }
            surveys.append(Survey(**survey_data))

        return surveys
