"""
Respondent service for the Quiz App.

This module provides business logic for managing respondents,
including creation, merging, and data collection compliance.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import hashlib

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.respondent import RespondentRepository
from repositories.respondent_event import RespondentEventRepository
from repositories.consent_log import ConsentLogRepository
from repositories.user import UserRepository
from models.respondent import (
    RespondentCreate,
    RespondentRead,
    RespondentUpdate,
)
from models.respondent_event import RespondentEventCreate
from schemas.respondent import RespondentMergeResult
from schemas.consent_log import ConsentLogCreate


class RespondentService:
    """Service for managing respondents and data collection."""

    def __init__(
        self,
        respondent_repo: RespondentRepository,
        event_repo: RespondentEventRepository,
        consent_repo: ConsentLogRepository,
        user_repo: UserRepository,
    ):
        self.respondent_repo = respondent_repo
        self.event_repo = event_repo
        self.consent_repo = consent_repo
        self.user_repo = user_repo

    async def create_or_get_respondent(
        self,
        request: Request,
        user_id: Optional[int] = None,
        telegram_data: Optional[Dict[str, Any]] = None,
        anonymous_data: Optional[Dict[str, Any]] = None,
    ) -> RespondentRead:
        """
        Create or get existing respondent based on session/fingerprint.

        Args:
            request: FastAPI request object
            user_id: Optional authenticated user ID
            telegram_data: Optional Telegram user data
            anonymous_data: Optional anonymous user data

        Returns:
            RespondentRead object
        """
        # Generate session ID and browser fingerprint
        session_id = self._generate_session_id(request)
        browser_fingerprint = self._generate_browser_fingerprint(request)

        # Try to find existing respondent by session or fingerprint
        existing_respondent = await self.respondent_repo.get_by_session_id(session_id)

        if not existing_respondent and browser_fingerprint:
            # Look for respondent by fingerprint
            fingerprint_respondents = await self.respondent_repo.get_by_fingerprint(
                browser_fingerprint
            )
            if fingerprint_respondents:
                existing_respondent = fingerprint_respondents[0]

        if existing_respondent:
            # Update activity and return existing respondent
            await self.respondent_repo.update_activity(existing_respondent.id)

            # If user authenticated and respondent was anonymous, link them
            if user_id and existing_respondent.is_anonymous:
                await self._link_respondent_to_user(existing_respondent.id, user_id)

            return RespondentRead.model_validate(existing_respondent)

        # Create new respondent
        respondent_data = RespondentCreate(
            user_id=user_id,
            session_id=session_id,
            browser_fingerprint=browser_fingerprint,
            is_anonymous=user_id is None,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            browser_info=self._extract_browser_info(request),
            device_info=self._extract_device_info(request),
            geo_info=await self._get_geo_info(request),
            referrer_info=self._extract_referrer_info(request),
            telegram_data=telegram_data,
            entry_point=self._determine_entry_point(request, telegram_data),
            anonymous_name=anonymous_data.get("name") if anonymous_data else None,
            anonymous_email=anonymous_data.get("email") if anonymous_data else None,
        )

        respondent = await self.respondent_repo.create(obj_in=respondent_data)

        # Log creation event
        await self._log_event(
            respondent.id,
            "created",
            {
                "is_anonymous": respondent.is_anonymous,
                "entry_point": respondent.entry_point,
                "has_telegram_data": telegram_data is not None,
            },
            source=respondent.entry_point,
        )

        return RespondentRead.model_validate(respondent)

    async def auto_merge_respondents(self, user_id: int) -> RespondentMergeResult:
        """
        Automatically merge anonymous respondents for a user.

        Args:
            user_id: User ID to merge respondents for

        Returns:
            RespondentMergeResult with merge statistics
        """
        merged_ids = await self.respondent_repo.auto_merge_for_user(user_id)

        if merged_ids:
            # Log merge events
            for merged_id in merged_ids:
                await self._log_event(
                    merged_id,
                    "merged",
                    {
                        "merged_into_user_id": user_id,
                        "auto_merge": True,
                    },
                    source="system",
                )

        return RespondentMergeResult(
            target_respondent_id=user_id,
            merged_respondent_ids=merged_ids,
            merged_responses_count=0,  # TODO: Get actual count
            merged_consents_count=0,  # TODO: Get actual count
            merged_events_count=0,  # TODO: Get actual count
            merge_timestamp=datetime.utcnow(),
        )

    async def grant_consent(
        self,
        respondent_id: int,
        consent_type: str,
        survey_id: Optional[int] = None,
        consent_details: Optional[Dict[str, Any]] = None,
        source: str = "web",
    ) -> bool:
        """
        Grant consent for data collection.

        Args:
            respondent_id: Respondent ID
            consent_type: Type of consent
            survey_id: Optional survey ID
            consent_details: Optional consent details
            source: Consent source

        Returns:
            True if consent granted successfully
        """
        consent_data = ConsentLogCreate(
            respondent_id=respondent_id,
            survey_id=survey_id,
            consent_type=consent_type,
            is_granted=True,
            details=consent_details,
            consent_source=source,
        )

        consent = await self.consent_repo.create(obj_in=consent_data)

        # Log consent event
        await self._log_event(
            respondent_id,
            "consent_granted",
            {
                "consent_type": consent_type,
                "consent_id": consent.id,
                "survey_id": survey_id,
            },
            source=source,
        )

        return True

    async def revoke_consent(
        self,
        respondent_id: int,
        consent_type: str,
        survey_id: Optional[int] = None,
    ) -> bool:
        """
        Revoke previously granted consent.

        Args:
            respondent_id: Respondent ID
            consent_type: Type of consent to revoke
            survey_id: Optional survey ID

        Returns:
            True if consent revoked successfully
        """
        success = await self.consent_repo.revoke_consent(
            respondent_id, consent_type, survey_id
        )

        if success:
            # Log revocation event
            await self._log_event(
                respondent_id,
                "consent_revoked",
                {
                    "consent_type": consent_type,
                    "survey_id": survey_id,
                },
                source="user_request",
            )

        return success

    async def update_respondent_location(
        self,
        respondent_id: int,
        location_data: Dict[str, Any],
        consent_granted: bool = False,
    ) -> bool:
        """
        Update respondent location data.

        Args:
            respondent_id: Respondent ID
            location_data: Location data
            consent_granted: Whether precise location consent is granted

        Returns:
            True if updated successfully
        """
        respondent = await self.respondent_repo.get(respondent_id)
        if not respondent:
            return False

        if consent_granted:
            # Store precise location
            update_data = RespondentUpdate(precise_location=location_data)
        else:
            # Store only general geo info
            update_data = RespondentUpdate(geo_info=location_data)

        updated = await self.respondent_repo.update(
            db_obj=respondent, obj_in=update_data
        )

        if updated:
            await self._log_event(
                respondent_id,
                "location_updated",
                {
                    "precise_location": consent_granted,
                    "location_type": "precise" if consent_granted else "general",
                },
            )

        return updated is not None

    async def get_respondent_data_export(self, respondent_id: int) -> Dict[str, Any]:
        """
        Export all respondent data for GDPR compliance.

        Args:
            respondent_id: Respondent ID

        Returns:
            Complete data export
        """
        respondent = await self.respondent_repo.get(respondent_id)
        if not respondent:
            raise HTTPException(status_code=404, detail="Respondent not found")

        # Get related data
        events = await self.event_repo.get_events_by_respondent(respondent_id)
        consents = await self.consent_repo.get_by_respondent_id(respondent_id)

        # TODO: Get responses and survey participations

        return {
            "respondent_data": RespondentRead.model_validate(respondent).dict(),
            "events": [event.dict() for event in events],
            "consents": [consent.dict() for consent in consents],
            "responses": [],  # TODO: Add responses
            "survey_participations": [],  # TODO: Add participations
            "export_timestamp": datetime.utcnow().isoformat(),
        }

    async def delete_respondent_data(self, respondent_id: int) -> bool:
        """
        Delete all respondent data for GDPR compliance.

        Args:
            respondent_id: Respondent ID

        Returns:
            True if deleted successfully
        """
        # Soft delete respondent
        deleted = await self.respondent_repo.soft_delete(respondent_id)

        if deleted:
            await self._log_event(
                respondent_id,
                "data_deleted",
                {"deletion_type": "gdpr_request"},
                source="user_request",
            )

        return deleted is not None

    # Private helper methods

    async def _link_respondent_to_user(self, respondent_id: int, user_id: int) -> bool:
        """Link anonymous respondent to authenticated user."""
        respondent = await self.respondent_repo.get(respondent_id)
        if not respondent:
            return False

        update_data = RespondentUpdate(
            user_id=user_id,
            is_anonymous=False,
        )

        updated = await self.respondent_repo.update(
            db_obj=respondent, obj_in=update_data
        )

        if updated:
            await self._log_event(
                respondent_id,
                "user_linked",
                {"user_id": user_id, "was_anonymous": True},
            )

        return updated is not None

    async def _log_event(
        self,
        respondent_id: int,
        event_type: str,
        event_data: Dict[str, Any],
        source: str = "system",
    ) -> None:
        """Log respondent event."""
        event_create = RespondentEventCreate(
            respondent_id=respondent_id,
            event_type=event_type,
            event_data=event_data,
            event_source=source,
        )

        await self.event_repo.create(obj_in=event_create)

    def _generate_session_id(self, request: Request) -> str:
        """Generate unique session ID."""
        # Use combination of IP, User-Agent, and timestamp
        components = [
            self._get_client_ip(request),
            request.headers.get("user-agent", ""),
            str(datetime.utcnow().timestamp()),
            str(uuid.uuid4()),
        ]

        session_string = "|".join(components)
        return hashlib.sha256(session_string.encode()).hexdigest()[:32]

    def _generate_browser_fingerprint(self, request: Request) -> Optional[str]:
        """Generate browser fingerprint for tracking."""
        components = [
            request.headers.get("user-agent", ""),
            request.headers.get("accept-language", ""),
            request.headers.get("accept-encoding", ""),
            self._get_client_ip(request),
        ]

        # Filter out empty components
        components = [c for c in components if c]

        if len(components) < 2:
            return None

        fingerprint_string = "|".join(components)
        return hashlib.md5(fingerprint_string.encode()).hexdigest()

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _extract_browser_info(self, request: Request) -> Dict[str, Any]:
        """Extract browser information from request."""
        user_agent = request.headers.get("user-agent", "")

        return {
            "user_agent": user_agent,
            "language": request.headers.get("accept-language", ""),
            "encoding": request.headers.get("accept-encoding", ""),
        }

    def _extract_device_info(self, request: Request) -> Dict[str, Any]:
        """Extract device information from request."""
        user_agent = request.headers.get("user-agent", "").lower()

        device_type = "desktop"
        if "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent:
            device_type = "mobile"
        elif "tablet" in user_agent or "ipad" in user_agent:
            device_type = "tablet"

        return {
            "type": device_type,
            "user_agent": request.headers.get("user-agent", ""),
        }

    async def _get_geo_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get geographical information from IP."""
        # TODO: Implement IP geolocation service
        # For now, return basic info
        return {
            "ip": self._get_client_ip(request),
            "country": "unknown",
            "city": "unknown",
        }

    def _extract_referrer_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract referrer information."""
        referrer = request.headers.get("referer")
        if not referrer:
            return None

        return {
            "url": referrer,
            "source": "direct" if not referrer else "referrer",
        }

    def _determine_entry_point(
        self, request: Request, telegram_data: Optional[Dict[str, Any]]
    ) -> str:
        """Determine entry point for the respondent."""
        if telegram_data:
            return "telegram_webapp"

        user_agent = request.headers.get("user-agent", "").lower()
        if "telegram" in user_agent:
            return "telegram_bot"

        return "web"
