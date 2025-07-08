"""
Survey Participation service for the Quiz App.

This module provides business logic for managing respondent participation
in surveys, including progress tracking and completion management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.respondent_survey import RespondentSurveyRepository
from repositories.survey_data_requirements import SurveyDataRequirementsRepository
from repositories.consent_log import ConsentLogRepository
from repositories.respondent_event import RespondentEventRepository
from schemas.respondent_survey import (
    RespondentSurveyCreate,
    RespondentSurveyUpdate,
    RespondentSurveyResponse,
    RespondentSurveyCompletion,
    RespondentSurveyProgress,
)
from schemas.respondent_event import RespondentEventCreate


class SurveyParticipationService:
    """Service for managing survey participation."""

    def __init__(
        self,
        respondent_survey_repo: RespondentSurveyRepository,
        requirements_repo: SurveyDataRequirementsRepository,
        consent_repo: ConsentLogRepository,
        event_repo: RespondentEventRepository,
    ):
        self.respondent_survey_repo = respondent_survey_repo
        self.requirements_repo = requirements_repo
        self.consent_repo = consent_repo
        self.event_repo = event_repo

    async def start_survey(
        self,
        respondent_id: int,
        survey_id: int,
        source: str = "web",
        context: Optional[Dict[str, Any]] = None,
    ) -> RespondentSurveyResponse:
        """
        Start survey participation for a respondent.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID
            source: Source of participation (web, telegram, etc.)
            context: Optional context data

        Returns:
            RespondentSurveyResponse object
        """
        # Check if already participating
        existing_participation = (
            await self.respondent_survey_repo.get_by_respondent_and_survey(
                respondent_id, survey_id
            )
        )

        if existing_participation:
            # Update existing participation
            if existing_participation.status == "completed":
                raise HTTPException(
                    status_code=400,
                    detail="Survey already completed",
                )

            # Resume existing participation
            return RespondentSurveyResponse.model_validate(existing_participation)

        # Create new participation
        participation_data = RespondentSurveyCreate(
            respondent_id=respondent_id,
            survey_id=survey_id,
            status="started",
            completion_source=source,
            context_data=context,
        )

        participation = await self.respondent_survey_repo.create(
            obj_in=participation_data
        )

        # Log start event
        await self._log_participation_event(
            respondent_id,
            "survey_started",
            {
                "survey_id": survey_id,
                "participation_id": participation.id,
                "source": source,
            },
            source=source,
        )

        return RespondentSurveyResponse.model_validate(participation)

    async def update_progress(
        self,
        respondent_id: int,
        survey_id: int,
        progress_data: RespondentSurveyProgress,
    ) -> Optional[RespondentSurveyResponse]:
        """
        Update survey progress for a respondent.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID
            progress_data: Progress update data

        Returns:
            Updated participation if found, None otherwise
        """
        participation = await self.respondent_survey_repo.get_by_respondent_and_survey(
            respondent_id, survey_id
        )

        if not participation:
            return None

        # Calculate progress percentage
        progress_percentage = (
            (progress_data.questions_answered / progress_data.total_questions) * 100
            if progress_data.total_questions > 0
            else 0
        )

        # Update status based on progress
        status = "in_progress"
        if progress_percentage >= 100:
            status = "completed"
        elif progress_percentage >= 80:
            status = "almost_completed"

        update_data = RespondentSurveyUpdate(
            progress_percentage=progress_percentage,
            questions_answered=progress_data.questions_answered,
            last_question_id=progress_data.last_question_id,
            status=status,
        )

        updated_participation = await self.respondent_survey_repo.update(
            db_obj=participation, obj_in=update_data
        )

        # Log progress event
        await self._log_participation_event(
            respondent_id,
            "survey_progress_updated",
            {
                "survey_id": survey_id,
                "progress_percentage": progress_percentage,
                "questions_answered": progress_data.questions_answered,
                "status": status,
            },
        )

        return RespondentSurveyResponse.model_validate(updated_participation)

    async def complete_survey(
        self,
        respondent_id: int,
        survey_id: int,
        completion_data: RespondentSurveyCompletion,
    ) -> Optional[RespondentSurveyResponse]:
        """
        Complete survey participation.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID
            completion_data: Completion data

        Returns:
            Updated participation if found, None otherwise
        """
        participation = await self.respondent_survey_repo.get_by_respondent_and_survey(
            respondent_id, survey_id
        )

        if not participation:
            return None

        update_data = RespondentSurveyUpdate(
            status="completed",
            completion_time=completion_data.completion_time,
            final_score=completion_data.final_score,
            completion_source=completion_data.source,
            progress_percentage=100,
        )

        updated_participation = await self.respondent_survey_repo.update(
            db_obj=participation, obj_in=update_data
        )

        # Log completion event
        await self._log_participation_event(
            respondent_id,
            "survey_completed",
            {
                "survey_id": survey_id,
                "completion_time": completion_data.completion_time,
                "final_score": completion_data.final_score,
                "source": completion_data.source,
            },
            source=completion_data.source,
        )

        return RespondentSurveyResponse.model_validate(updated_participation)

    async def abandon_survey(
        self,
        respondent_id: int,
        survey_id: int,
        reason: Optional[str] = None,
    ) -> Optional[RespondentSurveyResponse]:
        """
        Mark survey as abandoned.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID
            reason: Optional reason for abandonment

        Returns:
            Updated participation if found, None otherwise
        """
        participation = await self.respondent_survey_repo.get_by_respondent_and_survey(
            respondent_id, survey_id
        )

        if not participation:
            return None

        update_data = RespondentSurveyUpdate(
            status="abandoned",
            abandonment_reason=reason,
        )

        updated_participation = await self.respondent_survey_repo.update(
            db_obj=participation, obj_in=update_data
        )

        # Log abandonment event
        await self._log_participation_event(
            respondent_id,
            "survey_abandoned",
            {
                "survey_id": survey_id,
                "reason": reason,
                "progress_percentage": participation.progress_percentage,
            },
        )

        return RespondentSurveyResponse.model_validate(updated_participation)

    async def get_participation_summary(
        self,
        respondent_id: int,
        survey_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Get participation summary for respondent and survey.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID

        Returns:
            Participation summary or None if not found
        """
        participation = await self.respondent_survey_repo.get_by_respondent_and_survey(
            respondent_id, survey_id
        )

        if not participation:
            return None

        return {
            "participation_id": participation.id,
            "status": participation.status,
            "progress_percentage": participation.progress_percentage,
            "questions_answered": participation.questions_answered,
            "started_at": participation.started_at,
            "completed_at": participation.completed_at,
            "completion_time": participation.completion_time,
            "final_score": participation.final_score,
            "last_question_id": participation.last_question_id,
        }

    async def check_data_requirements(
        self,
        respondent_id: int,
        survey_id: int,
    ) -> Dict[str, Any]:
        """
        Check if respondent meets data requirements for survey.

        Args:
            respondent_id: Respondent ID
            survey_id: Survey ID

        Returns:
            Requirements check result
        """
        # Get survey data requirements
        requirements = await self.requirements_repo.get_by_survey_id(survey_id)

        if not requirements:
            return {
                "requirements_met": True,
                "missing_requirements": [],
                "required_consents": [],
            }

        # Check consent requirements
        missing_consents = []
        if requirements.requires_location_consent:
            has_location_consent = await self.consent_repo.has_consent(
                respondent_id, "location", survey_id
            )
            if not has_location_consent:
                missing_consents.append("location")

        if requirements.requires_personal_data_consent:
            has_personal_consent = await self.consent_repo.has_consent(
                respondent_id, "personal_data", survey_id
            )
            if not has_personal_consent:
                missing_consents.append("personal_data")

        if requirements.requires_technical_data_consent:
            has_technical_consent = await self.consent_repo.has_consent(
                respondent_id, "technical_data", survey_id
            )
            if not has_technical_consent:
                missing_consents.append("technical_data")

        # TODO: Check other requirements (location data, personal data, etc.)

        return {
            "requirements_met": len(missing_consents) == 0,
            "missing_consents": missing_consents,
            "required_consents": missing_consents,
        }

    async def get_respondent_survey_history(
        self,
        respondent_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> List[RespondentSurveyResponse]:
        """
        Get survey history for a respondent.

        Args:
            respondent_id: Respondent ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of survey participations
        """
        participations = await self.respondent_survey_repo.get_by_respondent(
            respondent_id, limit=limit, offset=offset
        )

        return [RespondentSurveyResponse.model_validate(p) for p in participations]

    async def _log_participation_event(
        self,
        respondent_id: int,
        event_type: str,
        event_data: Dict[str, Any],
        source: str = "system",
    ) -> None:
        """Log participation event."""
        event_create = RespondentEventCreate(
            respondent_id=respondent_id,
            event_type=event_type,
            event_data=event_data,
            event_source=source,
        )

        await self.event_repo.create(obj_in=event_create)
