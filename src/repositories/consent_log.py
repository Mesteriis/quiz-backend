"""
ConsentLog repository for the Quiz App.

This module provides the consent log repository with specific methods
for managing user consent tracking and GDPR compliance.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.consent_log import ConsentLog
from schemas.consent_log import ConsentLogCreate, ConsentLogUpdate
from .base import BaseRepository


class ConsentLogRepository(
    BaseRepository[ConsentLog, ConsentLogCreate, ConsentLogUpdate]
):
    """
    ConsentLog repository with specific consent management operations.

    Inherits from BaseRepository and adds specific methods
    for managing user consent tracking and GDPR compliance.
    """

    def __init__(self, db: AsyncSession):
        """Initialize ConsentLogRepository with database session."""
        super().__init__(ConsentLog, db)

    async def has_consent(
        self, respondent_id: int, consent_type: str, survey_id: int = None
    ) -> bool:
        """
        Check if respondent has granted specific consent.

        Args:
            respondent_id: Respondent ID
            consent_type: Type of consent to check
            survey_id: Optional survey ID for survey-specific consent

        Returns:
            True if consent is granted and not revoked, False otherwise
        """
        query = select(ConsentLog).where(
            ConsentLog.respondent_id == respondent_id,
            ConsentLog.consent_type == consent_type,
            ConsentLog.is_granted == True,
            ConsentLog.revoked_at.is_(None),
        )

        if survey_id:
            query = query.where(ConsentLog.survey_id == survey_id)
        else:
            query = query.where(ConsentLog.survey_id.is_(None))

        result = await self.db.execute(query)
        consent = result.scalars().first()
        return consent is not None

    async def grant_consent(
        self,
        respondent_id: int,
        consent_type: str,
        consent_data: Dict[str, Any],
        survey_id: int = None,
    ) -> ConsentLog:
        """
        Grant consent for respondent.

        Args:
            respondent_id: Respondent ID
            consent_type: Type of consent
            consent_data: Consent data including details, source, etc.
            survey_id: Optional survey ID for survey-specific consent

        Returns:
            Created ConsentLog instance
        """
        # Check if consent already exists and revoke it first
        existing_consent = await self.get_latest_consent(
            respondent_id, consent_type, survey_id
        )

        if existing_consent and existing_consent.is_granted:
            # Revoke existing consent before granting new one
            await self.revoke_consent(existing_consent.id, "replaced_with_new")

        consent_create_data = {
            "respondent_id": respondent_id,
            "consent_type": consent_type,
            "is_granted": True,
            "survey_id": survey_id,
            **consent_data,
        }

        from schemas.consent_log import ConsentLogCreate

        consent_create = ConsentLogCreate(**consent_create_data)
        return await self.create(obj_in=consent_create)

    async def revoke_consent(
        self, consent_id: int, revocation_reason: str = None
    ) -> Optional[ConsentLog]:
        """
        Revoke existing consent.

        Args:
            consent_id: Consent ID to revoke
            revocation_reason: Reason for revocation

        Returns:
            Updated ConsentLog instance or None
        """
        consent = await self.get(consent_id)
        if not consent:
            return None

        consent.is_granted = False
        consent.revoked_at = datetime.utcnow()

        if revocation_reason:
            if not consent.details:
                consent.details = {}
            consent.details["revocation_reason"] = revocation_reason

        await self.db.commit()
        await self.db.refresh(consent)
        return consent

    async def revoke_consent_by_type(
        self, respondent_id: int, consent_type: str, survey_id: int = None
    ) -> List[ConsentLog]:
        """
        Revoke all consents of specific type for respondent.

        Args:
            respondent_id: Respondent ID
            consent_type: Type of consent to revoke
            survey_id: Optional survey ID for survey-specific consent

        Returns:
            List of revoked ConsentLog instances
        """
        consents = await self.get_consents_by_type(
            respondent_id, consent_type, survey_id, only_granted=True
        )

        revoked_consents = []
        for consent in consents:
            revoked = await self.revoke_consent(consent.id, "bulk_revocation")
            if revoked:
                revoked_consents.append(revoked)

        return revoked_consents

    async def get_consents(
        self, respondent_id: int, survey_id: int = None
    ) -> List[ConsentLog]:
        """
        Get all consents for respondent.

        Args:
            respondent_id: Respondent ID
            survey_id: Optional survey ID filter

        Returns:
            List of ConsentLog instances
        """
        query = (
            select(ConsentLog)
            .where(ConsentLog.respondent_id == respondent_id)
            .order_by(ConsentLog.granted_at.desc())
        )

        if survey_id:
            query = query.where(ConsentLog.survey_id == survey_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_consents_by_type(
        self,
        respondent_id: int,
        consent_type: str,
        survey_id: int = None,
        only_granted: bool = False,
    ) -> List[ConsentLog]:
        """
        Get consents by type for respondent.

        Args:
            respondent_id: Respondent ID
            consent_type: Type of consent
            survey_id: Optional survey ID filter
            only_granted: Whether to return only granted consents

        Returns:
            List of ConsentLog instances
        """
        query = (
            select(ConsentLog)
            .where(
                ConsentLog.respondent_id == respondent_id,
                ConsentLog.consent_type == consent_type,
            )
            .order_by(ConsentLog.granted_at.desc())
        )

        if survey_id:
            query = query.where(ConsentLog.survey_id == survey_id)

        if only_granted:
            query = query.where(
                ConsentLog.is_granted == True,
                ConsentLog.revoked_at.is_(None),
            )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_latest_consent(
        self, respondent_id: int, consent_type: str, survey_id: int = None
    ) -> Optional[ConsentLog]:
        """
        Get latest consent of specific type for respondent.

        Args:
            respondent_id: Respondent ID
            consent_type: Type of consent
            survey_id: Optional survey ID for survey-specific consent

        Returns:
            Latest ConsentLog instance or None
        """
        query = (
            select(ConsentLog)
            .where(
                ConsentLog.respondent_id == respondent_id,
                ConsentLog.consent_type == consent_type,
            )
            .order_by(ConsentLog.granted_at.desc())
        )

        if survey_id:
            query = query.where(ConsentLog.survey_id == survey_id)
        else:
            query = query.where(ConsentLog.survey_id.is_(None))

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_consent_status(self, respondent_id: int) -> Dict[str, bool]:
        """
        Get current consent status for all consent types for respondent.

        Args:
            respondent_id: Respondent ID

        Returns:
            Dictionary mapping consent types to boolean status
        """
        # Define all possible consent types
        consent_types = [
            "location",
            "device_info",
            "personal_data",
            "marketing",
            "analytics",
            "cookies",
        ]

        status = {}
        for consent_type in consent_types:
            status[consent_type] = await self.has_consent(respondent_id, consent_type)

        return status

    async def get_consents_with_details(self, respondent_id: int) -> List[ConsentLog]:
        """
        Get consents with respondent and survey details.

        Args:
            respondent_id: Respondent ID

        Returns:
            List of ConsentLog instances with related data
        """
        query = (
            select(ConsentLog)
            .options(
                selectinload(ConsentLog.respondent),
                selectinload(ConsentLog.survey),
            )
            .where(ConsentLog.respondent_id == respondent_id)
            .order_by(ConsentLog.granted_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_granted_consents(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[ConsentLog]:
        """
        Get all granted consents.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of granted ConsentLog instances
        """
        query = (
            select(ConsentLog)
            .where(
                ConsentLog.is_granted == True,
                ConsentLog.revoked_at.is_(None),
            )
            .order_by(ConsentLog.granted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_revoked_consents(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[ConsentLog]:
        """
        Get all revoked consents.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of revoked ConsentLog instances
        """
        query = (
            select(ConsentLog)
            .where(ConsentLog.revoked_at.isnot(None))
            .order_by(ConsentLog.revoked_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_consent_summary(self) -> Dict[str, Any]:
        """
        Get consent summary statistics.

        Returns:
            Dictionary with consent statistics
        """
        # Total consents
        total_query = select(func.count(ConsentLog.id))
        total_result = await self.db.execute(total_query)
        total_consents = total_result.scalar() or 0

        # Granted consents
        granted_query = select(func.count(ConsentLog.id)).where(
            ConsentLog.is_granted == True,
            ConsentLog.revoked_at.is_(None),
        )
        granted_result = await self.db.execute(granted_query)
        granted_consents = granted_result.scalar() or 0

        # Revoked consents
        revoked_query = select(func.count(ConsentLog.id)).where(
            ConsentLog.revoked_at.isnot(None)
        )
        revoked_result = await self.db.execute(revoked_query)
        revoked_consents = revoked_result.scalar() or 0

        # Consent types distribution
        consent_types_query = select(
            ConsentLog.consent_type,
            func.count(ConsentLog.id).label("count"),
        ).group_by(ConsentLog.consent_type)

        consent_types_result = await self.db.execute(consent_types_query)
        consent_types = {
            row.consent_type: row.count for row in consent_types_result.fetchall()
        }

        # Consent sources distribution
        consent_sources_query = select(
            ConsentLog.consent_source,
            func.count(ConsentLog.id).label("count"),
        ).group_by(ConsentLog.consent_source)

        consent_sources_result = await self.db.execute(consent_sources_query)
        consent_sources = {
            row.consent_source or "unknown": row.count
            for row in consent_sources_result.fetchall()
        }

        # Calculate rates
        grant_rate = (
            (granted_consents / total_consents * 100) if total_consents > 0 else 0
        )
        revocation_rate = (
            (revoked_consents / total_consents * 100) if total_consents > 0 else 0
        )

        return {
            "total_consents": total_consents,
            "granted_consents": granted_consents,
            "revoked_consents": revoked_consents,
            "consent_types": consent_types,
            "consent_sources": consent_sources,
            "grant_rate": grant_rate,
            "revocation_rate": revocation_rate,
        }

    async def get_recent_consent_activity(
        self, hours: int = 24, *, skip: int = 0, limit: int = 100
    ) -> List[ConsentLog]:
        """
        Get recent consent activity.

        Args:
            hours: Number of hours to look back
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of recent ConsentLog instances
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(ConsentLog)
            .where(ConsentLog.granted_at >= cutoff_time)
            .order_by(ConsentLog.granted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def bulk_revoke_by_respondent(self, respondent_id: int) -> int:
        """
        Bulk revoke all consents for a respondent.

        Args:
            respondent_id: Respondent ID

        Returns:
            Number of revoked consents
        """
        consents = await self.get_consents(respondent_id)
        revoked_count = 0

        for consent in consents:
            if consent.is_granted and not consent.revoked_at:
                revoked = await self.revoke_consent(consent.id, "bulk_deletion")
                if revoked:
                    revoked_count += 1

        return revoked_count

    async def export_user_consents(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Export all consent data for a user (GDPR compliance).

        Args:
            user_id: User ID

        Returns:
            List of consent data dictionaries
        """
        from models.respondent import Respondent

        query = (
            select(ConsentLog)
            .join(Respondent, ConsentLog.respondent_id == Respondent.id)
            .where(Respondent.user_id == user_id)
            .order_by(ConsentLog.granted_at.desc())
        )

        result = await self.db.execute(query)
        consents = result.scalars().all()

        export_data = []
        for consent in consents:
            export_data.append(
                {
                    "consent_id": consent.id,
                    "consent_type": consent.consent_type,
                    "is_granted": consent.is_granted,
                    "granted_at": consent.granted_at.isoformat(),
                    "revoked_at": consent.revoked_at.isoformat()
                    if consent.revoked_at
                    else None,
                    "consent_version": consent.consent_version,
                    "consent_source": consent.consent_source,
                    "details": consent.details,
                    "survey_id": consent.survey_id,
                }
            )

        return export_data
