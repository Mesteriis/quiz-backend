"""
UserData repository for the Quiz App.

This module provides the user data repository with specific methods
for user data related database operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_data import UserData, UserDataCreate, UserDataUpdate
from .base import BaseRepository


class UserDataRepository(BaseRepository[UserData, UserDataCreate, UserDataUpdate]):
    """
    UserData repository with specific user data operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize UserDataRepository with database session."""
        super().__init__(UserData, db)

    async def get_by_user_id(self, user_id: int) -> Optional[UserData]:
        """
        Get user data by user ID.

        Args:
            user_id: User ID

        Returns:
            UserData or None
        """
        return await self.get_by_field("user_id", user_id)

    async def get_by_ip_address(self, ip_address: str) -> List[UserData]:
        """
        Get user data by IP address.

        Args:
            ip_address: IP address

        Returns:
            List of user data with IP address
        """
        query = (
            select(UserData)
            .where(UserData.ip_address == ip_address)
            .order_by(UserData.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_fingerprint(self, fingerprint: str) -> List[UserData]:
        """
        Get user data by fingerprint.

        Args:
            fingerprint: Browser fingerprint

        Returns:
            List of user data with fingerprint
        """
        query = (
            select(UserData)
            .where(UserData.fingerprint == fingerprint)
            .order_by(UserData.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_session_id(self, session_id: str) -> Optional[UserData]:
        """
        Get user data by session ID.

        Args:
            session_id: Session ID

        Returns:
            UserData or None
        """
        return await self.get_by_field("session_id", session_id)

    async def remove(self, id: int) -> Optional[UserData]:
        """
        Remove user data by ID.

        Args:
            id: UserData ID

        Returns:
            Deleted UserData or None
        """
        return await self.delete(id=id)
