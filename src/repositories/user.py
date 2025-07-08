"""
User repository for the Quiz App.

This module provides the user repository with specific methods
for user-related database operations.
"""

from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.user import UserCreate, UserUpdate
from .base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    User repository with specific user operations.

    Inherits from BaseRepository and adds user-specific methods
    for authentication and user management.
    """

    def __init__(self, db: AsyncSession):
        """Initialize UserRepository with database session."""
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username to search for

        Returns:
            User instance or None
        """
        return await self.get_by_field("username", username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: Email to search for

        Returns:
            User instance or None
        """
        return await self.get_by_field("email", email)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Get user by Telegram ID.

        Args:
            telegram_id: Telegram ID to search for

        Returns:
            User instance or None
        """
        return await self.get_by_field("telegram_id", telegram_id)

    async def get_by_identifier(self, identifier: str) -> Optional[User]:
        """
        Get user by username or email.

        Args:
            identifier: Username or email to search for

        Returns:
            User instance or None
        """
        query = select(User).where(
            or_(User.username == identifier, User.email == identifier)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_active_users(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get active users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active user instances
        """
        query = select(User).where(User.is_active == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_admin_users(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get admin users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of admin user instances
        """
        query = select(User).where(User.is_admin == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_verified_users(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Get verified users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of verified user instances
        """
        query = select(User).where(User.is_verified == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_users(
        self, search_term: str, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Search users by username, email, or display name.

        Args:
            search_term: Search term to match
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching user instances
        """
        search_pattern = f"%{search_term}%"
        query = (
            select(User)
            .where(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.display_name.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def activate_user(self, user_id: int) -> Optional[User]:
        """
        Activate user by ID.

        Args:
            user_id: User ID to activate

        Returns:
            Updated user instance or None
        """
        user = await self.get(user_id)
        if user:
            user.is_active = True
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Deactivate user by ID.

        Args:
            user_id: User ID to deactivate

        Returns:
            Updated user instance or None
        """
        user = await self.get(user_id)
        if user:
            user.is_active = False
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def verify_user(self, user_id: int) -> Optional[User]:
        """
        Verify user by ID.

        Args:
            user_id: User ID to verify

        Returns:
            Updated user instance or None
        """
        user = await self.get(user_id)
        if user:
            user.is_verified = True
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def update_last_login(self, user_id: int) -> Optional[User]:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID to update

        Returns:
            Updated user instance or None
        """
        from datetime import datetime

        user = await self.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(user)
        return user
