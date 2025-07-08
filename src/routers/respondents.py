"""
Respondents API router for the Quiz App.

This module contains FastAPI endpoints for managing respondents,
including creation, merging, consent management, and data export.
"""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from models.user import User
from repositories.dependencies import (
    get_respondent_repository,
    get_respondent_event_repository,
    get_consent_log_repository,
    get_user_repository,
)
from repositories.respondent import RespondentRepository
from repositories.respondent_event import RespondentEventRepository
from repositories.consent_log import ConsentLogRepository
from repositories.user import UserRepository
from routers.auth import get_current_user, get_optional_user
from schemas.respondent import (
    RespondentResponse,
    RespondentCreate,
    RespondentUpdate,
    RespondentSearch,
    RespondentStatistics,
    RespondentMergeResult,
    RespondentActivity,
    RespondentDataExport,
)
from schemas.consent_log import ConsentLogCreate, ConsentLogResponse
from services.respondent_service import RespondentService

router = APIRouter(prefix="/respondents", tags=["respondents"])


# Request/Response models
class CreateRespondentRequest(BaseModel):
    """Request model for creating respondent."""

    telegram_data: Optional[Dict[str, Any]] = None
    anonymous_data: Optional[Dict[str, Any]] = None


class ConsentRequest(BaseModel):
    """Request model for granting consent."""

    consent_type: str
    survey_id: Optional[int] = None
    consent_details: Optional[Dict[str, Any]] = None
    source: str = "web"


class LocationUpdateRequest(BaseModel):
    """Request model for updating location."""

    location_data: Dict[str, Any]
    consent_granted: bool = False


# Dependency for RespondentService
def get_respondent_service(
    respondent_repo: RespondentRepository = Depends(get_respondent_repository),
    event_repo: RespondentEventRepository = Depends(get_respondent_event_repository),
    consent_repo: ConsentLogRepository = Depends(get_consent_log_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> RespondentService:
    """Get RespondentService instance."""
    return RespondentService(respondent_repo, event_repo, consent_repo, user_repo)


@router.post(
    "/", response_model=RespondentResponse, status_code=status.HTTP_201_CREATED
)
async def create_or_get_respondent(
    request: Request,
    respondent_data: CreateRespondentRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    service: RespondentService = Depends(get_respondent_service),
):
    """
    Create or get existing respondent.

    Creates a new respondent or returns existing one based on session/fingerprint.
    Automatically links to authenticated user if available.
    """
    try:
        respondent = await service.create_or_get_respondent(
            request=request,
            user_id=current_user.id if current_user else None,
            telegram_data=respondent_data.telegram_data,
            anonymous_data=respondent_data.anonymous_data,
        )

        return respondent

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create respondent: {str(e)}",
        )


@router.get("/me", response_model=RespondentResponse)
async def get_my_respondent(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    service: RespondentService = Depends(get_respondent_service),
):
    """Get current user's respondent information."""
    if current_user:
        # Get authenticated user's primary respondent
        respondent_repo = service.respondent_repo
        respondent = await respondent_repo.get_primary_respondent_for_user(
            current_user.id
        )

        if respondent:
            return RespondentResponse.model_validate(respondent)

    # For anonymous users, try to find by session
    respondent_data = CreateRespondentRequest()
    respondent = await service.create_or_get_respondent(
        request=request,
        user_id=current_user.id if current_user else None,
    )

    return respondent


@router.get("/search", response_model=List[RespondentResponse])
async def search_respondents(
    search_params: RespondentSearch = Depends(),
    current_user: User = Depends(get_current_user),
    respondent_repo: RespondentRepository = Depends(get_respondent_repository),
):
    """
    Search respondents (admin only).

    Advanced search functionality for respondents with filtering options.
    """
    # TODO: Add admin check
    try:
        respondents = await respondent_repo.search_respondents(
            filters=search_params.dict(exclude_none=True),
            skip=search_params.skip,
            limit=search_params.limit,
        )

        return [RespondentResponse.model_validate(r) for r in respondents]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search respondents: {str(e)}",
        )


@router.get("/statistics", response_model=RespondentStatistics)
async def get_respondent_statistics(
    current_user: User = Depends(get_current_user),
    respondent_repo: RespondentRepository = Depends(get_respondent_repository),
):
    """
    Get respondent statistics (admin only).

    Returns comprehensive statistics about respondents in the system.
    """
    # TODO: Add admin check
    try:
        stats = await respondent_repo.get_respondent_stats()
        return RespondentStatistics.model_validate(stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.post("/merge", response_model=RespondentMergeResult)
async def auto_merge_respondents(
    current_user: User = Depends(get_current_user),
    service: RespondentService = Depends(get_respondent_service),
):
    """
    Automatically merge anonymous respondents for authenticated user.

    Merges anonymous respondents that belong to the current user based on
    browser fingerprints and IP addresses.
    """
    try:
        result = await service.auto_merge_respondents(current_user.id)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge respondents: {str(e)}",
        )


@router.post("/{respondent_id}/consent", response_model=Dict[str, Any])
async def grant_consent(
    respondent_id: int,
    consent_data: ConsentRequest,
    service: RespondentService = Depends(get_respondent_service),
):
    """
    Grant consent for data collection.

    Grants specific type of consent for the respondent.
    """
    try:
        success = await service.grant_consent(
            respondent_id=respondent_id,
            consent_type=consent_data.consent_type,
            survey_id=consent_data.survey_id,
            consent_details=consent_data.consent_details,
            source=consent_data.source,
        )

        return {
            "success": success,
            "message": "Consent granted successfully",
            "consent_type": consent_data.consent_type,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant consent: {str(e)}",
        )


@router.delete("/{respondent_id}/consent/{consent_type}")
async def revoke_consent(
    respondent_id: int,
    consent_type: str,
    survey_id: Optional[int] = None,
    service: RespondentService = Depends(get_respondent_service),
):
    """
    Revoke previously granted consent.

    Revokes specific type of consent for the respondent.
    """
    try:
        success = await service.revoke_consent(
            respondent_id=respondent_id,
            consent_type=consent_type,
            survey_id=survey_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent not found or already revoked",
            )

        return {
            "success": True,
            "message": "Consent revoked successfully",
            "consent_type": consent_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke consent: {str(e)}",
        )


@router.put("/{respondent_id}/location")
async def update_location(
    respondent_id: int,
    location_data: LocationUpdateRequest,
    service: RespondentService = Depends(get_respondent_service),
):
    """
    Update respondent location data.

    Updates location information with appropriate consent handling.
    """
    try:
        success = await service.update_respondent_location(
            respondent_id=respondent_id,
            location_data=location_data.location_data,
            consent_granted=location_data.consent_granted,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respondent not found",
            )

        return {
            "success": True,
            "message": "Location updated successfully",
            "precise_location": location_data.consent_granted,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update location: {str(e)}",
        )


@router.get("/{respondent_id}/activity", response_model=RespondentActivity)
async def get_respondent_activity(
    respondent_id: int,
    days: int = 30,
    respondent_repo: RespondentRepository = Depends(get_respondent_repository),
    event_repo: RespondentEventRepository = Depends(get_respondent_event_repository),
):
    """
    Get respondent activity summary.

    Returns activity statistics for the specified time period.
    """
    try:
        # Get basic respondent info
        respondent = await respondent_repo.get(respondent_id)
        if not respondent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respondent not found",
            )

        # Get activity summary
        activity = await event_repo.get_respondent_activity_summary(respondent_id, days)

        # TODO: Add survey participations and responses count
        activity_data = RespondentActivity(
            respondent_id=respondent_id,
            total_surveys=0,  # TODO: Get from RespondentSurvey repo
            completed_surveys=0,  # TODO: Get from RespondentSurvey repo
            abandoned_surveys=0,  # TODO: Get from RespondentSurvey repo
            total_responses=0,  # TODO: Get from Response repo
            total_events=activity.get("total_events", 0),
            first_activity=activity.get("first_activity"),
            last_activity=activity.get("last_activity"),
        )

        return activity_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity: {str(e)}",
        )


@router.get("/{respondent_id}/export", response_model=RespondentDataExport)
async def export_respondent_data(
    respondent_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    service: RespondentService = Depends(get_respondent_service),
):
    """
    Export all respondent data (GDPR compliance).

    Returns complete data export for the respondent.
    Only the respondent themselves or admin can access this.
    """
    try:
        # TODO: Add authorization check (user owns respondent or is admin)

        export_data = await service.get_respondent_data_export(respondent_id)

        return RespondentDataExport(
            respondent_id=respondent_id,
            user_id=export_data["respondent_data"].get("user_id"),
            personal_data=export_data["respondent_data"],
            survey_data=export_data.get("survey_participations", []),
            response_data=export_data.get("responses", []),
            consent_data=export_data.get("consents", []),
            event_data=export_data.get("events", []),
            export_timestamp=export_data["export_timestamp"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}",
        )


@router.delete("/{respondent_id}")
async def delete_respondent_data(
    respondent_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    service: RespondentService = Depends(get_respondent_service),
):
    """
    Delete all respondent data (GDPR compliance).

    Performs soft delete of all respondent data.
    Only the respondent themselves or admin can do this.
    """
    try:
        # TODO: Add authorization check (user owns respondent or is admin)

        success = await service.delete_respondent_data(respondent_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respondent not found",
            )

        return {
            "success": True,
            "message": "Respondent data deleted successfully",
            "respondent_id": respondent_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data: {str(e)}",
        )
