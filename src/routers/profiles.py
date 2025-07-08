"""
Profiles API router for the Quiz App.

This module contains FastAPI endpoints for managing user profiles,
including creation, updates, search, and validation.
"""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from models.user import User
from repositories.dependencies import (
    get_profile_repository,
    get_user_repository,
)
from repositories.profile import ProfileRepository
from repositories.user import UserRepository
from routers.auth import get_current_user
from schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileWithUser,
    ProfileSearch,
    ProfileStatistics,
)
from services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


# Request/Response models
class ProfilePictureUpdateRequest(BaseModel):
    """Request model for updating profile picture."""

    picture_url: str


class ContactInfoUpdateRequest(BaseModel):
    """Request model for updating contact information."""

    phone: Optional[str] = None


class TelegramSyncRequest(BaseModel):
    """Request model for syncing Telegram data."""

    telegram_data: Dict[str, Any]


# Dependency for ProfileService
def get_profile_service(
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> ProfileService:
    """Get ProfileService instance."""
    return ProfileService(profile_repo, user_repo)


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Create a new profile for the current user.

    Creates a user profile with the provided information.
    """
    try:
        profile = await service.create_profile(
            user_id=current_user.id,
            profile_data=profile_data,
        )
        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}",
        )


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get the current user's profile.

    Returns the profile information for the authenticated user.
    """
    try:
        profile = await service.get_profile_by_user_id(current_user.id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}",
        )


@router.get("/me/with-user", response_model=ProfileWithUser)
async def get_my_profile_with_user(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get the current user's profile with user information.

    Returns the profile information along with user data.
    """
    try:
        profile = await service.get_profile_with_user(current_user.id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}",
        )


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Update the current user's profile.

    Updates profile information with the provided data.
    """
    try:
        profile = await service.update_profile(
            user_id=current_user.id,
            profile_data=profile_data,
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}",
        )


@router.delete("/me")
async def delete_my_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Delete the current user's profile.

    Removes the profile information for the authenticated user.
    """
    try:
        success = await service.delete_profile(current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return {
            "success": True,
            "message": "Profile deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}",
        )


@router.get("/search", response_model=List[ProfileResponse])
async def search_profiles(
    search_params: ProfileSearch = Depends(),
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Search profiles (admin only).

    Advanced search functionality for user profiles.
    """
    # TODO: Add admin check
    try:
        profiles = await service.search_profiles(search_params)
        return profiles

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search profiles: {str(e)}",
        )


@router.get("/statistics", response_model=ProfileStatistics)
async def get_profile_statistics(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get profile statistics (admin only).

    Returns comprehensive statistics about user profiles.
    """
    # TODO: Add admin check
    try:
        stats = await service.get_profile_statistics()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.put("/me/picture", response_model=ProfileResponse)
async def update_profile_picture(
    picture_data: ProfilePictureUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Update profile picture.

    Updates the profile picture URL for the current user.
    """
    try:
        profile = await service.update_profile_picture(
            user_id=current_user.id,
            picture_url=picture_data.picture_url,
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update picture: {str(e)}",
        )


@router.put("/me/contact", response_model=ProfileResponse)
async def update_contact_info(
    contact_data: ContactInfoUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Update contact information.

    Updates phone number and other contact details.
    """
    try:
        profile = await service.update_contact_info(
            user_id=current_user.id,
            phone=contact_data.phone,
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact info: {str(e)}",
        )


@router.post("/me/get-or-create", response_model=ProfileResponse)
async def get_or_create_profile(
    default_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get existing profile or create a new one.

    Returns existing profile or creates a new one with optional default data.
    """
    try:
        profile = await service.get_or_create_profile(
            user_id=current_user.id,
            default_data=default_data,
        )
        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get or create profile: {str(e)}",
        )


@router.post("/me/sync-telegram", response_model=ProfileResponse)
async def sync_telegram_data(
    telegram_data: TelegramSyncRequest,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Sync profile data from Telegram.

    Updates profile information with data from Telegram user.
    """
    try:
        profile = await service.sync_profile_from_telegram(
            user_id=current_user.id,
            telegram_data=telegram_data.telegram_data,
        )
        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Telegram data: {str(e)}",
        )


@router.get("/me/validation", response_model=Dict[str, Any])
async def validate_profile_completeness(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Validate profile completeness.

    Returns validation results and suggestions for profile improvement.
    """
    try:
        validation_result = await service.validate_profile_completeness(current_user.id)
        return validation_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate profile: {str(e)}",
        )


@router.get("/bulk", response_model=Dict[int, ProfileResponse])
async def get_profiles_bulk(
    user_ids: List[int],
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get profiles for multiple users (admin only).

    Returns profiles for the specified user IDs.
    """
    # TODO: Add admin check
    try:
        profiles = await service.get_profiles_for_users(user_ids)
        return profiles

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profiles: {str(e)}",
        )


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile_by_user_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get profile by user ID (admin only).

    Returns profile information for the specified user.
    """
    # TODO: Add admin check
    try:
        profile = await service.get_profile_by_user_id(user_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}",
        )
