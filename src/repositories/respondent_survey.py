"""
RespondentSurvey repository for the Quiz App.

This module provides the respondent survey repository with specific methods
for managing respondent participation in surveys.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.respondent_survey import RespondentSurvey
from schemas.respondent_survey import RespondentSurveyCreate, RespondentSurveyUpdate
from .base import BaseRepository


class RespondentSurveyRepository(
    BaseRepository[RespondentSurvey, RespondentSurveyCreate, RespondentSurveyUpdate]
):
    """
    RespondentSurvey repository with specific participation operations.

    Inherits from BaseRepository and adds specific methods
    for managing survey participation tracking.
    """

    def __init__(self, db: AsyncSession):
        """Initialize RespondentSurveyRepository with database session."""
        super().__init__(RespondentSurvey, db)

    async def get_participation(
        self, respondent_id: int, survey_id: int
    ) -> Optional[RespondentSurvey]:
        """
        Get participation record for respondent and survey.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID

        Returns:
            RespondentSurvey instance or None
        """
        query = select(RespondentSurvey).where(
            RespondentSurvey.respondent_id == respondent_id,
            RespondentSurvey.survey_id == survey_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_respondent_id(self, respondent_id: int) -> List[RespondentSurvey]:
        """
        Get all participations for a respondent.

        Args:
            respondent_id: Respondent ID

        Returns:
            List of RespondentSurvey instances
        """
        query = (
            select(RespondentSurvey)
            .where(RespondentSurvey.respondent_id == respondent_id)
            .order_by(RespondentSurvey.started_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_survey_id(self, survey_id: int) -> List[RespondentSurvey]:
        """
        Get all participations for a survey.

        Args:
            survey_id: Survey ID

        Returns:
            List of RespondentSurvey instances
        """
        query = (
            select(RespondentSurvey)
            .where(RespondentSurvey.survey_id == survey_id)
            .order_by(RespondentSurvey.started_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_with_details(
        self, respondent_id: int, survey_id: int
    ) -> Optional[RespondentSurvey]:
        """
        Get participation with respondent and survey details.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID

        Returns:
            RespondentSurvey with related data or None
        """
        query = (
            select(RespondentSurvey)
            .options(
                selectinload(RespondentSurvey.respondent),
                selectinload(RespondentSurvey.survey),
            )
            .where(
                RespondentSurvey.respondent_id == respondent_id,
                RespondentSurvey.survey_id == survey_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_progress(
        self, respondent_id: int, survey_id: int, progress_data: Dict[str, Any]
    ) -> Optional[RespondentSurvey]:
        """
        Update participation progress.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID
            progress_data: Progress update data

        Returns:
            Updated RespondentSurvey instance or None
        """
        participation = await self.get_participation(respondent_id, survey_id)
        if not participation:
            return None

        # Update fields
        if "questions_answered" in progress_data:
            participation.questions_answered = progress_data["questions_answered"]

        if "progress_percentage" in progress_data:
            participation.progress_percentage = progress_data["progress_percentage"]

        if "time_spent_seconds" in progress_data:
            participation.time_spent_seconds += progress_data.get("additional_time", 0)

        if "status" in progress_data:
            participation.status = progress_data["status"]

        participation.last_activity_at = datetime.utcnow()

        # Auto-update status based on progress
        if (
            participation.progress_percentage >= 100.0
            and participation.status != "completed"
        ):
            participation.status = "completed"
            participation.completed_at = datetime.utcnow()
        elif (
            participation.progress_percentage > 0 and participation.status == "started"
        ):
            participation.status = "in_progress"

        await self.db.commit()
        await self.db.refresh(participation)
        return participation

    async def complete_survey(
        self, respondent_id: int, survey_id: int, completion_data: Dict[str, Any] = None
    ) -> Optional[RespondentSurvey]:
        """
        Mark survey as completed.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID
            completion_data: Completion data

        Returns:
            Updated RespondentSurvey instance or None
        """
        participation = await self.get_participation(respondent_id, survey_id)
        if not participation:
            return None

        participation.status = "completed"
        participation.progress_percentage = 100.0
        participation.completed_at = datetime.utcnow()
        participation.last_activity_at = datetime.utcnow()

        if completion_data:
            if "completion_source" in completion_data:
                participation.completion_source = completion_data["completion_source"]
            if "time_spent_seconds" in completion_data:
                participation.time_spent_seconds = completion_data["time_spent_seconds"]

        await self.db.commit()
        await self.db.refresh(participation)
        return participation

    async def abandon_survey(
        self, respondent_id: int, survey_id: int
    ) -> Optional[RespondentSurvey]:
        """
        Mark survey as abandoned.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID

        Returns:
            Updated RespondentSurvey instance or None
        """
        participation = await self.get_participation(respondent_id, survey_id)
        if not participation:
            return None

        participation.status = "abandoned"
        participation.last_activity_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(participation)
        return participation

    async def get_completed_participations(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentSurvey]:
        """
        Get completed participations.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of completed RespondentSurvey instances
        """
        query = (
            select(RespondentSurvey)
            .where(RespondentSurvey.status == "completed")
            .order_by(RespondentSurvey.completed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_in_progress_participations(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentSurvey]:
        """
        Get in-progress participations.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of in-progress RespondentSurvey instances
        """
        query = (
            select(RespondentSurvey)
            .where(
                or_(
                    RespondentSurvey.status == "started",
                    RespondentSurvey.status == "in_progress",
                )
            )
            .order_by(RespondentSurvey.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_abandoned_participations(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentSurvey]:
        """
        Get abandoned participations.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of abandoned RespondentSurvey instances
        """
        query = (
            select(RespondentSurvey)
            .where(RespondentSurvey.status == "abandoned")
            .order_by(RespondentSurvey.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_participation_stats(self, survey_id: int = None) -> Dict[str, Any]:
        """
        Get participation statistics.

        Args:
            survey_id: Optional survey ID to filter by

        Returns:
            Dictionary with participation statistics
        """
        base_query = select(func.count(RespondentSurvey.id))

        if survey_id:
            base_query = base_query.where(RespondentSurvey.survey_id == survey_id)

        # Total participations
        total_result = await self.db.execute(base_query)
        total_participations = total_result.scalar() or 0

        # Completed participations
        completed_query = base_query.where(RespondentSurvey.status == "completed")
        completed_result = await self.db.execute(completed_query)
        completed_participations = completed_result.scalar() or 0

        # Abandoned participations
        abandoned_query = base_query.where(RespondentSurvey.status == "abandoned")
        abandoned_result = await self.db.execute(abandoned_query)
        abandoned_participations = abandoned_result.scalar() or 0

        # In progress participations
        in_progress_query = base_query.where(
            or_(
                RespondentSurvey.status == "started",
                RespondentSurvey.status == "in_progress",
            )
        )
        in_progress_result = await self.db.execute(in_progress_query)
        in_progress_participations = in_progress_result.scalar() or 0

        # Calculate rates
        completion_rate = (
            (completed_participations / total_participations * 100)
            if total_participations > 0
            else 0
        )
        abandonment_rate = (
            (abandoned_participations / total_participations * 100)
            if total_participations > 0
            else 0
        )

        # Average completion time
        avg_time_query = select(func.avg(RespondentSurvey.time_spent_seconds)).where(
            RespondentSurvey.status == "completed"
        )
        if survey_id:
            avg_time_query = avg_time_query.where(
                RespondentSurvey.survey_id == survey_id
            )

        avg_time_result = await self.db.execute(avg_time_query)
        average_completion_time = avg_time_result.scalar() or 0

        # Average progress
        avg_progress_query = select(func.avg(RespondentSurvey.progress_percentage))
        if survey_id:
            avg_progress_query = avg_progress_query.where(
                RespondentSurvey.survey_id == survey_id
            )

        avg_progress_result = await self.db.execute(avg_progress_query)
        average_progress_percentage = avg_progress_result.scalar() or 0

        return {
            "total_participations": total_participations,
            "completed_participations": completed_participations,
            "abandoned_participations": abandoned_participations,
            "in_progress_participations": in_progress_participations,
            "completion_rate": completion_rate,
            "abandonment_rate": abandonment_rate,
            "average_completion_time": average_completion_time,
            "average_progress_percentage": average_progress_percentage,
        }

    async def get_recent_activity(
        self, hours: int = 24, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentSurvey]:
        """
        Get recent participation activity.

        Args:
            hours: Number of hours to look back
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of recently active RespondentSurvey instances
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(RespondentSurvey)
            .where(RespondentSurvey.last_activity_at >= cutoff_time)
            .order_by(RespondentSurvey.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_survey_history(
        self, user_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentSurvey]:
        """
        Get survey participation history for a user across all their respondents.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentSurvey instances for user
        """
        from models.respondent import Respondent

        query = (
            select(RespondentSurvey)
            .join(Respondent, RespondentSurvey.respondent_id == Respondent.id)
            .where(Respondent.user_id == user_id)
            .order_by(RespondentSurvey.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
