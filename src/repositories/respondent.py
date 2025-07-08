"""
Respondent repository for the Quiz App.

This module provides the respondent repository with specific methods
for respondent-related database operations including merging functionality.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.respondent import Respondent
from schemas.respondent import RespondentCreate, RespondentUpdate
from .base import BaseRepository


class RespondentRepository(
    BaseRepository[Respondent, RespondentCreate, RespondentUpdate]
):
    """
    Respondent repository with specific respondent operations.

    Inherits from BaseRepository and adds respondent-specific methods
    for managing survey respondents including merging functionality.
    """

    def __init__(self, db: AsyncSession):
        """Initialize RespondentRepository with database session."""
        super().__init__(Respondent, db)

    async def get_by_session_id(self, session_id: str) -> Optional[Respondent]:
        """
        Get respondent by session ID.

        Args:
            session_id: Session ID to search for

        Returns:
            Respondent instance or None
        """
        return await self.get_by_field(
            "session_id", session_id, load_relationships=True
        )

    async def get_by_fingerprint(self, fingerprint: str) -> List[Respondent]:
        """
        Get respondents by browser fingerprint.

        Args:
            fingerprint: Browser fingerprint to search for

        Returns:
            List of respondent instances with matching fingerprint
        """
        query = (
            select(Respondent)
            .where(
                Respondent.browser_fingerprint == fingerprint,
                Respondent.is_deleted == False,
            )
            .order_by(Respondent.first_seen_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int) -> List[Respondent]:
        """
        Get all respondents for a user.

        Args:
            user_id: User ID

        Returns:
            List of respondent instances for the user
        """
        query = (
            select(Respondent)
            .where(
                Respondent.user_id == user_id,
                Respondent.is_deleted == False,
            )
            .order_by(Respondent.first_seen_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_anonymous_respondents(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Respondent]:
        """
        Get anonymous respondents.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of anonymous respondent instances
        """
        query = (
            select(Respondent)
            .where(
                Respondent.is_anonymous == True,
                Respondent.is_deleted == False,
            )
            .order_by(Respondent.first_seen_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_authenticated_respondents(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Respondent]:
        """
        Get authenticated respondents.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of authenticated respondent instances
        """
        query = (
            select(Respondent)
            .where(
                Respondent.is_anonymous == False,
                Respondent.user_id.isnot(None),
                Respondent.is_deleted == False,
            )
            .order_by(Respondent.first_seen_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_respondents(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Respondent]:
        """
        Get active respondents.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active respondent instances
        """
        query = (
            select(Respondent)
            .where(
                Respondent.is_active == True,
                Respondent.is_deleted == False,
            )
            .order_by(Respondent.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_merged_respondents(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Respondent]:
        """
        Get merged respondents.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of merged respondent instances
        """
        query = (
            select(Respondent)
            .where(Respondent.is_merged == True)
            .order_by(Respondent.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def find_mergeable_respondents(self, user_id: int) -> List[Respondent]:
        """
        Find anonymous respondents that can be merged with a user.

        This method looks for anonymous respondents that might belong
        to the same user based on various criteria.

        Args:
            user_id: User ID to find mergeable respondents for

        Returns:
            List of mergeable anonymous respondent instances
        """
        # Get the user's authenticated respondents to analyze patterns
        user_respondents = await self.get_by_user_id(user_id)

        if not user_respondents:
            return []

        # Collect fingerprints and IPs from user's respondents
        fingerprints = set()
        ip_addresses = set()

        for resp in user_respondents:
            if resp.browser_fingerprint:
                fingerprints.add(resp.browser_fingerprint)
            if resp.ip_address:
                ip_addresses.add(resp.ip_address)

        if not fingerprints and not ip_addresses:
            return []

        # Find anonymous respondents with matching patterns
        conditions = []

        if fingerprints:
            conditions.append(Respondent.browser_fingerprint.in_(list(fingerprints)))

        if ip_addresses:
            conditions.append(Respondent.ip_address.in_(list(ip_addresses)))

        query = (
            select(Respondent)
            .where(
                Respondent.is_anonymous == True,
                Respondent.user_id.is_(None),
                Respondent.is_merged == False,
                Respondent.is_deleted == False,
                or_(*conditions) if conditions else False,
            )
            .order_by(Respondent.last_activity_at.desc())
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def merge_respondents(self, source_id: int, target_id: int) -> bool:
        """
        Merge two respondents by moving all data from source to target.

        Args:
            source_id: Source respondent ID (will be marked as merged)
            target_id: Target respondent ID (will receive all data)

        Returns:
            True if merge was successful, False otherwise
        """
        source = await self.get(source_id)
        target = await self.get(target_id)

        if not source or not target:
            return False

        try:
            # Update all responses to point to target respondent
            from models.response import Response

            response_update = (
                update(Response)
                .where(Response.respondent_id == source_id)
                .values(respondent_id=target_id)
            )
            await self.db.execute(response_update)

            # Update all survey participations
            from models.respondent_survey import RespondentSurvey

            participation_update = (
                update(RespondentSurvey)
                .where(RespondentSurvey.respondent_id == source_id)
                .values(respondent_id=target_id)
            )
            await self.db.execute(participation_update)

            # Update all consent logs
            from models.consent_log import ConsentLog

            consent_update = (
                update(ConsentLog)
                .where(ConsentLog.respondent_id == source_id)
                .values(respondent_id=target_id)
            )
            await self.db.execute(consent_update)

            # Update all events
            from models.respondent_event import RespondentEvent

            event_update = (
                update(RespondentEvent)
                .where(RespondentEvent.respondent_id == source_id)
                .values(respondent_id=target_id)
            )
            await self.db.execute(event_update)

            # Mark source as merged
            source.is_merged = True
            source.merged_into_id = target_id
            source.is_active = False

            # Update target's first seen date if source is older
            if source.first_seen_at < target.first_seen_at:
                target.first_seen_at = source.first_seen_at

            # Merge data fields (prefer target's data, fallback to source)
            if not target.anonymous_name and source.anonymous_name:
                target.anonymous_name = source.anonymous_name
            if not target.anonymous_email and source.anonymous_email:
                target.anonymous_email = source.anonymous_email
            if not target.precise_location and source.precise_location:
                target.precise_location = source.precise_location

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            return False

    async def auto_merge_for_user(self, user_id: int) -> List[int]:
        """
        Automatically merge anonymous respondents for a user.

        Args:
            user_id: User ID to auto-merge respondents for

        Returns:
            List of merged respondent IDs
        """
        # Find the primary authenticated respondent for this user
        primary_respondent = await self.get_primary_respondent_for_user(user_id)

        if not primary_respondent:
            return []

        # Find mergeable respondents
        mergeable = await self.find_mergeable_respondents(user_id)
        merged_ids = []

        for respondent in mergeable:
            if await self.merge_respondents(respondent.id, primary_respondent.id):
                merged_ids.append(respondent.id)

        return merged_ids

    async def get_primary_respondent_for_user(
        self, user_id: int
    ) -> Optional[Respondent]:
        """
        Get the primary respondent for a user (latest authenticated).

        Args:
            user_id: User ID

        Returns:
            Primary respondent instance or None
        """
        query = (
            select(Respondent)
            .where(
                Respondent.user_id == user_id,
                Respondent.is_anonymous == False,
                Respondent.is_merged == False,
                Respondent.is_deleted == False,
            )
            .order_by(Respondent.last_activity_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_activity(self, respondent_id: int) -> Optional[Respondent]:
        """
        Update respondent's last activity timestamp.

        Args:
            respondent_id: Respondent ID

        Returns:
            Updated respondent instance or None
        """
        respondent = await self.get(respondent_id)
        if respondent:
            respondent.last_activity_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(respondent)
        return respondent

    async def get_respondent_stats(self) -> Dict[str, Any]:
        """
        Get respondent statistics.

        Returns:
            Dictionary with respondent statistics
        """
        # Total counts
        total_query = select(func.count(Respondent.id)).where(
            Respondent.is_deleted == False
        )
        total_result = await self.db.execute(total_query)
        total_respondents = total_result.scalar() or 0

        # Anonymous count
        anonymous_query = select(func.count(Respondent.id)).where(
            Respondent.is_anonymous == True, Respondent.is_deleted == False
        )
        anonymous_result = await self.db.execute(anonymous_query)
        anonymous_respondents = anonymous_result.scalar() or 0

        # Authenticated count
        authenticated_query = select(func.count(Respondent.id)).where(
            Respondent.is_anonymous == False,
            Respondent.user_id.isnot(None),
            Respondent.is_deleted == False,
        )
        authenticated_result = await self.db.execute(authenticated_query)
        authenticated_respondents = authenticated_result.scalar() or 0

        # Active count
        active_query = select(func.count(Respondent.id)).where(
            Respondent.is_active == True, Respondent.is_deleted == False
        )
        active_result = await self.db.execute(active_query)
        active_respondents = active_result.scalar() or 0

        # Merged count
        merged_query = select(func.count(Respondent.id)).where(
            Respondent.is_merged == True
        )
        merged_result = await self.db.execute(merged_query)
        merged_respondents = merged_result.scalar() or 0

        return {
            "total_respondents": total_respondents,
            "anonymous_respondents": anonymous_respondents,
            "authenticated_respondents": authenticated_respondents,
            "active_respondents": active_respondents,
            "merged_respondents": merged_respondents,
        }

    async def soft_delete(self, respondent_id: int) -> Optional[Respondent]:
        """
        Soft delete a respondent.

        Args:
            respondent_id: Respondent ID

        Returns:
            Soft deleted respondent instance or None
        """
        respondent = await self.get(respondent_id)
        if respondent:
            respondent.is_deleted = True
            respondent.deleted_at = datetime.utcnow()
            respondent.is_active = False
            await self.db.commit()
            await self.db.refresh(respondent)
        return respondent
