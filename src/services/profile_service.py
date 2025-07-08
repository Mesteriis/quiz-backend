"""
Profile service for the Quiz App.

This module provides business logic for managing user profiles,
including creation, updates, and profile data management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.profile import ProfileRepository
from repositories.user import UserRepository
from schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileWithUser,
    ProfileSearch,
    ProfileStatistics,
)


class ProfileService:
    """Service for managing user profiles."""

    def __init__(
        self,
        profile_repo: ProfileRepository,
        user_repo: UserRepository,
    ):
        self.profile_repo = profile_repo
        self.user_repo = user_repo

    async def create_profile(
        self, user_id: int, profile_data: ProfileCreate
    ) -> ProfileResponse:
        """
        Create a new profile for a user.

        Args:
            user_id: User ID
            profile_data: Profile creation data

        Returns:
            Created profile
        """
        # Verify user exists
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if profile already exists
        existing_profile = await self.profile_repo.get_by_user_id(user_id)
        if existing_profile:
            raise HTTPException(
                status_code=400, detail="Profile already exists for this user"
            )

        # Set user_id in profile data
        profile_data.user_id = user_id

        # Create profile
        profile = await self.profile_repo.create(obj_in=profile_data)

        return ProfileResponse.model_validate(profile)

    async def get_profile_by_user_id(self, user_id: int) -> Optional[ProfileResponse]:
        """
        Get profile by user ID.

        Args:
            user_id: User ID

        Returns:
            Profile if found, None otherwise
        """
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return None

        return ProfileResponse.model_validate(profile)

    async def get_profile_with_user(self, user_id: int) -> Optional[ProfileWithUser]:
        """
        Get profile with user information.

        Args:
            user_id: User ID

        Returns:
            Profile with user data if found, None otherwise
        """
        profile = await self.profile_repo.get_with_user(user_id)
        if not profile:
            return None

        return ProfileWithUser.model_validate(profile)

    async def update_profile(
        self, user_id: int, profile_data: ProfileUpdate
    ) -> Optional[ProfileResponse]:
        """
        Update user profile.

        Args:
            user_id: User ID
            profile_data: Profile update data

        Returns:
            Updated profile if found, None otherwise
        """
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return None

        updated_profile = await self.profile_repo.update(
            db_obj=profile, obj_in=profile_data
        )

        if updated_profile:
            return ProfileResponse.model_validate(updated_profile)

        return None

    async def delete_profile(self, user_id: int) -> bool:
        """
        Delete user profile.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return False

        await self.profile_repo.remove(profile.id)
        return True

    async def search_profiles(
        self, search_params: ProfileSearch
    ) -> List[ProfileResponse]:
        """
        Search profiles based on criteria.

        Args:
            search_params: Search parameters

        Returns:
            List of matching profiles
        """
        profiles = await self.profile_repo.search_profiles(
            search_query=search_params.search_query,
            skip=search_params.skip,
            limit=search_params.limit,
        )

        return [ProfileResponse.model_validate(profile) for profile in profiles]

    async def get_profile_statistics(self) -> ProfileStatistics:
        """
        Get profile statistics.

        Returns:
            Profile statistics
        """
        stats = await self.profile_repo.get_profile_statistics()
        return ProfileStatistics.model_validate(stats)

    async def update_profile_picture(
        self, user_id: int, picture_url: str
    ) -> Optional[ProfileResponse]:
        """
        Update profile picture URL.

        Args:
            user_id: User ID
            picture_url: New picture URL

        Returns:
            Updated profile if found, None otherwise
        """
        profile_data = ProfileUpdate(profile_picture_url=picture_url)
        return await self.update_profile(user_id, profile_data)

    async def get_or_create_profile(
        self, user_id: int, default_data: Optional[Dict[str, Any]] = None
    ) -> ProfileResponse:
        """
        Get existing profile or create a new one with default data.

        Args:
            user_id: User ID
            default_data: Default profile data if creating

        Returns:
            Existing or newly created profile
        """
        # Try to get existing profile
        existing_profile = await self.get_profile_by_user_id(user_id)
        if existing_profile:
            return existing_profile

        # Create new profile with default data
        create_data = ProfileCreate(
            user_id=user_id,
            first_name=default_data.get("first_name") if default_data else None,
            last_name=default_data.get("last_name") if default_data else None,
            bio=default_data.get("bio") if default_data else None,
            phone=default_data.get("phone") if default_data else None,
        )

        return await self.create_profile(user_id, create_data)

    async def sync_profile_from_telegram(
        self, user_id: int, telegram_data: Dict[str, Any]
    ) -> ProfileResponse:
        """
        Sync profile data from Telegram user information.

        Args:
            user_id: User ID
            telegram_data: Telegram user data

        Returns:
            Updated or created profile
        """
        # Extract relevant data from Telegram
        first_name = telegram_data.get("first_name")
        last_name = telegram_data.get("last_name")
        photo_url = telegram_data.get("photo_url")

        # Get existing profile or create new one
        profile = await self.get_profile_by_user_id(user_id)

        if profile:
            # Update existing profile with Telegram data (only if fields are empty)
            update_data = ProfileUpdate()

            if not profile.first_name and first_name:
                update_data.first_name = first_name

            if not profile.last_name and last_name:
                update_data.last_name = last_name

            if not profile.profile_picture_url and photo_url:
                update_data.profile_picture_url = photo_url

            # Update only if there's something to update
            if any(
                getattr(update_data, field) is not None
                for field in ["first_name", "last_name", "profile_picture_url"]
            ):
                updated_profile = await self.update_profile(user_id, update_data)
                if updated_profile:
                    return updated_profile

            return profile

        else:
            # Create new profile with Telegram data
            create_data = ProfileCreate(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                profile_picture_url=photo_url,
            )

            return await self.create_profile(user_id, create_data)

    async def validate_profile_completeness(self, user_id: int) -> Dict[str, Any]:
        """
        Validate profile completeness and suggest improvements.

        Args:
            user_id: User ID

        Returns:
            Validation results and suggestions
        """
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            return {
                "exists": False,
                "completeness": 0,
                "missing_fields": ["first_name", "last_name", "bio", "phone"],
                "suggestions": ["Create a profile to get started"],
            }

        # Calculate completeness
        fields = ["first_name", "last_name", "bio", "profile_picture_url", "phone"]
        filled_fields = []
        missing_fields = []

        for field in fields:
            value = getattr(profile, field)
            if value and value.strip() if isinstance(value, str) else value:
                filled_fields.append(field)
            else:
                missing_fields.append(field)

        completeness = (len(filled_fields) / len(fields)) * 100

        # Generate suggestions
        suggestions = []
        if not profile.first_name:
            suggestions.append("Add your first name")
        if not profile.last_name:
            suggestions.append("Add your last name")
        if not profile.bio:
            suggestions.append("Write a short bio about yourself")
        if not profile.profile_picture_url:
            suggestions.append("Upload a profile picture")
        if not profile.phone:
            suggestions.append("Add your phone number for contact")

        return {
            "exists": True,
            "completeness": round(completeness, 1),
            "filled_fields": filled_fields,
            "missing_fields": missing_fields,
            "suggestions": suggestions,
        }

    async def get_profiles_for_users(
        self, user_ids: List[int]
    ) -> Dict[int, ProfileResponse]:
        """
        Get profiles for multiple users.

        Args:
            user_ids: List of user IDs

        Returns:
            Dictionary mapping user_id to profile
        """
        profiles = await self.profile_repo.get_by_user_ids(user_ids)

        result = {}
        for profile in profiles:
            result[profile.user_id] = ProfileResponse.model_validate(profile)

        return result

    async def update_contact_info(
        self, user_id: int, phone: Optional[str] = None
    ) -> Optional[ProfileResponse]:
        """
        Update contact information.

        Args:
            user_id: User ID
            phone: Phone number

        Returns:
            Updated profile if found, None otherwise
        """
        update_data = ProfileUpdate()

        if phone is not None:
            update_data.phone = phone

        return await self.update_profile(user_id, update_data)
