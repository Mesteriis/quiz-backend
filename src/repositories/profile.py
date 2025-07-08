"""
Profile repository for the Quiz App.

This module provides the profile repository with specific methods
for profile-related database operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.profile import Profile
from schemas.profile import ProfileCreate, ProfileUpdate
from .base import BaseRepository


class ProfileRepository(BaseRepository[Profile, ProfileCreate, ProfileUpdate]):
    """
    Profile repository with specific profile operations.

    Inherits from BaseRepository and adds profile-specific methods
    for user profile management.
    """

    def __init__(self, db: AsyncSession):
        """Initialize ProfileRepository with database session."""
        super().__init__(Profile, db)

    async def get_by_user_id(self, user_id: int) -> Optional[Profile]:
        """
        Get profile by user ID.

        Args:
            user_id: User ID to search for

        Returns:
            Profile instance or None
        """
        return await self.get_by_field("user_id", user_id)

    async def get_with_user(self, profile_id: int) -> Optional[Profile]:
        """
        Get profile with user information.

        Args:
            profile_id: Profile ID

        Returns:
            Profile instance with user or None
        """
        query = (
            select(Profile)
            .options(selectinload(Profile.user))
            .where(Profile.id == profile_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_user_id_with_user(self, user_id: int) -> Optional[Profile]:
        """
        Get profile by user ID with user information.

        Args:
            user_id: User ID

        Returns:
            Profile instance with user or None
        """
        query = (
            select(Profile)
            .options(selectinload(Profile.user))
            .where(Profile.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_for_user(self, user_id: int, profile_data: dict) -> Profile:
        """
        Create profile for user.

        Args:
            user_id: User ID
            profile_data: Profile data dictionary

        Returns:
            Created profile instance
        """
        profile_data["user_id"] = user_id
        from schemas.profile import ProfileCreate

        profile_create = ProfileCreate(**profile_data)
        return await self.create(obj_in=profile_create)

    async def search_profiles(
        self, search_term: str, *, skip: int = 0, limit: int = 100
    ) -> List[Profile]:
        """
        Search profiles by name or bio.

        Args:
            search_term: Search term to match
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching profile instances
        """
        from sqlalchemy import or_

        search_pattern = f"%{search_term}%"
        query = (
            select(Profile)
            .where(
                or_(
                    Profile.first_name.ilike(search_pattern),
                    Profile.last_name.ilike(search_pattern),
                    Profile.bio.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_profiles_with_pictures(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Profile]:
        """
        Get profiles that have profile pictures.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of profiles with pictures
        """
        query = (
            select(Profile)
            .where(Profile.profile_picture_url.isnot(None))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_profiles_with_phone(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Profile]:
        """
        Get profiles that have phone numbers.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of profiles with phone numbers
        """
        query = (
            select(Profile).where(Profile.phone.isnot(None)).offset(skip).limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_profile_picture(
        self, user_id: int, picture_url: str
    ) -> Optional[Profile]:
        """
        Update profile picture URL for user.

        Args:
            user_id: User ID
            picture_url: New picture URL

        Returns:
            Updated profile instance or None
        """
        profile = await self.get_by_user_id(user_id)
        if profile:
            profile.profile_picture_url = picture_url
            await self.db.commit()
            await self.db.refresh(profile)
        return profile

    async def get_complete_profiles(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Profile]:
        """
        Get profiles that have both first and last name.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of complete profiles
        """
        query = (
            select(Profile)
            .where(
                Profile.first_name.isnot(None),
                Profile.last_name.isnot(None),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
