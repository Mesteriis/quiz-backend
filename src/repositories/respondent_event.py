"""
RespondentEvent repository for the Quiz App.

This module provides the respondent event repository with specific methods
for managing respondent events and activity tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.respondent_event import RespondentEvent
from schemas.respondent_event import RespondentEventCreate, RespondentEventUpdate
from .base import BaseRepository


class RespondentEventRepository(
    BaseRepository[RespondentEvent, RespondentEventCreate, RespondentEventUpdate]
):
    """
    RespondentEvent repository with specific event management operations.

    Inherits from BaseRepository and adds specific methods
    for managing respondent events and activity tracking.
    """

    def __init__(self, db: AsyncSession):
        """Initialize RespondentEventRepository with database session."""
        super().__init__(RespondentEvent, db)

    async def log_event(
        self,
        respondent_id: int,
        event_type: str,
        event_data: Dict[str, Any],
        survey_id: int = None,
        response_id: int = None,
    ) -> RespondentEvent:
        """
        Log a new event for respondent.

        Args:
            respondent_id: Respondent ID
            event_type: Type of event
            event_data: Event data and metadata
            survey_id: Optional survey ID
            response_id: Optional response ID

        Returns:
            Created RespondentEvent instance
        """
        event_create_data = {
            "respondent_id": respondent_id,
            "event_type": event_type,
            "survey_id": survey_id,
            "response_id": response_id,
            **event_data,
        }

        from schemas.respondent_event import RespondentEventCreate

        event_create = RespondentEventCreate(**event_create_data)
        return await self.create(obj_in=event_create)

    async def get_events_by_respondent(
        self, respondent_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentEvent]:
        """
        Get all events for a respondent.

        Args:
            respondent_id: Respondent ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentEvent instances
        """
        query = (
            select(RespondentEvent)
            .where(RespondentEvent.respondent_id == respondent_id)
            .order_by(RespondentEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_events_by_type(
        self, event_type: str, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentEvent]:
        """
        Get all events of specific type.

        Args:
            event_type: Type of event
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentEvent instances
        """
        query = (
            select(RespondentEvent)
            .where(RespondentEvent.event_type == event_type)
            .order_by(RespondentEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_events_by_survey(
        self, survey_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentEvent]:
        """
        Get all events for a survey.

        Args:
            survey_id: Survey ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentEvent instances
        """
        query = (
            select(RespondentEvent)
            .where(RespondentEvent.survey_id == survey_id)
            .order_by(RespondentEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_events_with_details(
        self, respondent_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentEvent]:
        """
        Get events with respondent, survey, and response details.

        Args:
            respondent_id: Respondent ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentEvent instances with related data
        """
        query = (
            select(RespondentEvent)
            .options(
                selectinload(RespondentEvent.respondent),
                selectinload(RespondentEvent.survey),
                selectinload(RespondentEvent.response),
            )
            .where(RespondentEvent.respondent_id == respondent_id)
            .order_by(RespondentEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_events(
        self, hours: int = 24, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentEvent]:
        """
        Get recent events.

        Args:
            hours: Number of hours to look back
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of recent RespondentEvent instances
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(RespondentEvent)
            .where(RespondentEvent.created_at >= cutoff_time)
            .order_by(RespondentEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_event_statistics(self) -> Dict[str, Any]:
        """
        Get event statistics.

        Returns:
            Dictionary with event statistics
        """
        # Total events
        total_query = select(func.count(RespondentEvent.id))
        total_result = await self.db.execute(total_query)
        total_events = total_result.scalar() or 0

        # Events by type
        events_by_type_query = select(
            RespondentEvent.event_type,
            func.count(RespondentEvent.id).label("count"),
        ).group_by(RespondentEvent.event_type)

        events_by_type_result = await self.db.execute(events_by_type_query)
        events_by_type = {
            row.event_type: row.count for row in events_by_type_result.fetchall()
        }

        # Events today
        from datetime import date

        today = datetime.combine(date.today(), datetime.min.time())

        events_today_query = select(func.count(RespondentEvent.id)).where(
            RespondentEvent.created_at >= today
        )
        events_today_result = await self.db.execute(events_today_query)
        events_today = events_today_result.scalar() or 0

        # Most active respondents
        most_active_query = (
            select(
                RespondentEvent.respondent_id,
                func.count(RespondentEvent.id).label("event_count"),
            )
            .group_by(RespondentEvent.respondent_id)
            .order_by(func.count(RespondentEvent.id).desc())
            .limit(10)
        )

        most_active_result = await self.db.execute(most_active_query)
        most_active_respondents = [
            {"respondent_id": row.respondent_id, "event_count": row.event_count}
            for row in most_active_result.fetchall()
        ]

        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "events_today": events_today,
            "most_active_respondents": most_active_respondents,
        }

    async def get_respondent_activity_summary(
        self, respondent_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get activity summary for a respondent.

        Args:
            respondent_id: Respondent ID
            days: Number of days to look back

        Returns:
            Dictionary with respondent activity summary
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # Total events
        total_query = select(func.count(RespondentEvent.id)).where(
            RespondentEvent.respondent_id == respondent_id,
            RespondentEvent.created_at >= cutoff_time,
        )
        total_result = await self.db.execute(total_query)
        total_events = total_result.scalar() or 0

        # Events by type
        events_by_type_query = (
            select(
                RespondentEvent.event_type,
                func.count(RespondentEvent.id).label("count"),
            )
            .where(
                RespondentEvent.respondent_id == respondent_id,
                RespondentEvent.created_at >= cutoff_time,
            )
            .group_by(RespondentEvent.event_type)
        )

        events_by_type_result = await self.db.execute(events_by_type_query)
        events_by_type = {
            row.event_type: row.count for row in events_by_type_result.fetchall()
        }

        # First and last activity
        first_activity_query = select(func.min(RespondentEvent.created_at)).where(
            RespondentEvent.respondent_id == respondent_id
        )
        first_activity_result = await self.db.execute(first_activity_query)
        first_activity = first_activity_result.scalar()

        last_activity_query = select(func.max(RespondentEvent.created_at)).where(
            RespondentEvent.respondent_id == respondent_id
        )
        last_activity_result = await self.db.execute(last_activity_query)
        last_activity = last_activity_result.scalar()

        # Survey participation count
        survey_participation_query = select(
            func.count(func.distinct(RespondentEvent.survey_id))
        ).where(
            RespondentEvent.respondent_id == respondent_id,
            RespondentEvent.survey_id.isnot(None),
        )
        survey_participation_result = await self.db.execute(survey_participation_query)
        surveys_participated = survey_participation_result.scalar() or 0

        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "first_activity": first_activity,
            "last_activity": last_activity,
            "surveys_participated": surveys_participated,
            "days_period": days,
        }

    async def search_events(
        self,
        *,
        respondent_id: int = None,
        event_type: str = None,
        survey_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RespondentEvent]:
        """
        Search events with multiple filters.

        Args:
            respondent_id: Optional respondent ID filter
            event_type: Optional event type filter
            survey_id: Optional survey ID filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered RespondentEvent instances
        """
        query = select(RespondentEvent)

        # Apply filters
        filters = []

        if respondent_id:
            filters.append(RespondentEvent.respondent_id == respondent_id)

        if event_type:
            filters.append(RespondentEvent.event_type == event_type)

        if survey_id:
            filters.append(RespondentEvent.survey_id == survey_id)

        if date_from:
            filters.append(RespondentEvent.created_at >= date_from)

        if date_to:
            filters.append(RespondentEvent.created_at <= date_to)

        if filters:
            query = query.where(and_(*filters))

        query = (
            query.order_by(RespondentEvent.created_at.desc()).offset(skip).limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_events(
        self, user_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[RespondentEvent]:
        """
        Get all events for a user across all their respondents.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentEvent instances for user
        """
        from models.respondent import Respondent

        query = (
            select(RespondentEvent)
            .join(Respondent, RespondentEvent.respondent_id == Respondent.id)
            .where(Respondent.user_id == user_id)
            .order_by(RespondentEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_events_by_date_range(
        self,
        date_from: datetime,
        date_to: datetime,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RespondentEvent]:
        """
        Get events within date range.

        Args:
            date_from: Start date
            date_to: End date
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentEvent instances
        """
        query = (
            select(RespondentEvent)
            .where(
                RespondentEvent.created_at >= date_from,
                RespondentEvent.created_at <= date_to,
            )
            .order_by(RespondentEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_timeline_events(
        self,
        respondent_id: int,
        *,
        event_types: List[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RespondentEvent]:
        """
        Get timeline events for a respondent.

        Args:
            respondent_id: Respondent ID
            event_types: Optional list of event types to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RespondentEvent instances for timeline
        """
        query = select(RespondentEvent).where(
            RespondentEvent.respondent_id == respondent_id
        )

        if event_types:
            query = query.where(RespondentEvent.event_type.in_(event_types))

        query = (
            query.order_by(RespondentEvent.created_at.desc()).offset(skip).limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_old_events(self, days: int = 365) -> int:
        """
        Delete events older than specified days.

        Args:
            days: Number of days to keep events

        Returns:
            Number of deleted events
        """
        from datetime import timedelta
        from sqlalchemy import delete

        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # Count events to be deleted
        count_query = select(func.count(RespondentEvent.id)).where(
            RespondentEvent.created_at < cutoff_time
        )
        count_result = await self.db.execute(count_query)
        events_to_delete = count_result.scalar() or 0

        # Delete old events
        delete_query = delete(RespondentEvent).where(
            RespondentEvent.created_at < cutoff_time
        )
        await self.db.execute(delete_query)
        await self.db.commit()

        return events_to_delete

    async def export_user_events(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Export all event data for a user (GDPR compliance).

        Args:
            user_id: User ID

        Returns:
            List of event data dictionaries
        """
        events = await self.get_user_events(user_id, limit=10000)

        export_data = []
        for event in events:
            export_data.append(
                {
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "created_at": event.created_at.isoformat(),
                    "survey_id": event.survey_id,
                    "response_id": event.response_id,
                    "event_data": event.event_data,
                    "metadata": event.metadata,
                }
            )

        return export_data

    async def get_event_trend(
        self, event_type: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get event trend data for analytics.

        Args:
            event_type: Type of event
            days: Number of days to analyze

        Returns:
            List of daily event counts
        """
        from datetime import timedelta, date
        from sqlalchemy import func, cast, Date

        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                cast(RespondentEvent.created_at, Date).label("date"),
                func.count(RespondentEvent.id).label("count"),
            )
            .where(
                RespondentEvent.event_type == event_type,
                RespondentEvent.created_at >= start_date,
            )
            .group_by(cast(RespondentEvent.created_at, Date))
            .order_by(cast(RespondentEvent.created_at, Date))
        )

        result = await self.db.execute(query)
        trend_data = []
        for row in result.fetchall():
            trend_data.append(
                {
                    "date": row.date.isoformat(),
                    "count": row.count,
                }
            )

        return trend_data
