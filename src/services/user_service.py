"""
User service for the Quiz App.

This module provides user management functionality including
user creation, authentication, and profile management.
"""

from datetime import datetime
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserCreate, UserUpdate
from services.jwt_service import create_user_token, jwt_service

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and authentication."""

    async def get_user_by_id(
        self, session: AsyncSession, user_id: int
    ) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e!s}")
            return None

    async def get_user_by_telegram_id(
        self, session: AsyncSession, telegram_id: int
    ) -> Optional[User]:
        """Get user by Telegram ID."""
        try:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by Telegram ID {telegram_id}: {e!s}")
            return None

    async def get_user_by_username(
        self, session: AsyncSession, username: str
    ) -> Optional[User]:
        """Get user by username."""
        try:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e!s}")
            return None

    async def get_user_by_email(
        self, session: AsyncSession, email: str
    ) -> Optional[User]:
        """Get user by email."""
        try:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e!s}")
            return None

    async def create_user(
        self, session: AsyncSession, user_data: UserCreate
    ) -> Optional[User]:
        """Create a new user."""
        try:
            # Check if user already exists
            if user_data.telegram_id:
                existing_user = await self.get_user_by_telegram_id(
                    session, user_data.telegram_id
                )
                if existing_user:
                    logger.warning(
                        f"User with Telegram ID {user_data.telegram_id} already exists"
                    )
                    return existing_user

            if user_data.username:
                existing_user = await self.get_user_by_username(
                    session, user_data.username
                )
                if existing_user:
                    logger.warning(
                        f"User with username {user_data.username} already exists"
                    )
                    return None

            if user_data.email:
                existing_user = await self.get_user_by_email(session, user_data.email)
                if existing_user:
                    logger.warning(f"User with email {user_data.email} already exists")
                    return None

            # Create new user
            user = User(
                username=user_data.username,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                display_name=user_data.display_name,
                bio=user_data.bio,
                language=user_data.language,
                timezone=user_data.timezone,
                telegram_id=user_data.telegram_id,
                telegram_username=user_data.telegram_username,
                telegram_first_name=user_data.telegram_first_name,
                telegram_last_name=user_data.telegram_last_name,
                telegram_photo_url=user_data.telegram_photo_url,
                is_verified=bool(
                    user_data.telegram_id
                ),  # Telegram users are auto-verified
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"Created new user: {user.get_identifier()}")
            return user

        except Exception as e:
            logger.error(f"Error creating user: {e!s}")
            await session.rollback()
            return None

    async def update_user(
        self, session: AsyncSession, user_id: int, user_data: UserUpdate
    ) -> Optional[User]:
        """Update user information."""
        try:
            user = await self.get_user_by_id(session, user_id)
            if not user:
                return None

            # Update fields if provided
            if user_data.username is not None:
                user.username = user_data.username
            if user_data.email is not None:
                user.email = user_data.email
            if user_data.first_name is not None:
                user.first_name = user_data.first_name
            if user_data.last_name is not None:
                user.last_name = user_data.last_name
            if user_data.display_name is not None:
                user.display_name = user_data.display_name
            if user_data.bio is not None:
                user.bio = user_data.bio
            if user_data.language is not None:
                user.language = user_data.language
            if user_data.timezone is not None:
                user.timezone = user_data.timezone
            if user_data.is_active is not None:
                user.is_active = user_data.is_active

            user.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(user)

            logger.info(f"Updated user: {user.get_identifier()}")
            return user

        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e!s}")
            await session.rollback()
            return None

    async def authenticate_user(
        self, session: AsyncSession, identifier: str, telegram_id: Optional[int] = None
    ) -> Optional[User]:
        """
        Authenticate user by username, email, or Telegram ID.

        Args:
            session: Database session
            identifier: Username or email (if not Telegram user)
            telegram_id: Telegram ID (if Telegram user)

        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            user = None

            # Authenticate by Telegram ID
            if telegram_id:
                user = await self.get_user_by_telegram_id(session, telegram_id)
            # Authenticate by username or email
            elif identifier:
                # Try username first
                user = await self.get_user_by_username(session, identifier)
                if not user:
                    # Try email
                    user = await self.get_user_by_email(session, identifier)

            if user and user.is_active:
                # Update last login
                user.update_last_login()
                await session.commit()
                return user

            return None

        except Exception as e:
            logger.error(f"Error authenticating user: {e!s}")
            return None

    async def create_or_update_telegram_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        telegram_first_name: Optional[str] = None,
        telegram_last_name: Optional[str] = None,
        telegram_photo_url: Optional[str] = None,
    ) -> Optional[User]:
        """
        Create or update Telegram user.

        Args:
            session: Database session
            telegram_id: Telegram user ID
            telegram_username: Telegram username
            telegram_first_name: Telegram first name
            telegram_last_name: Telegram last name
            telegram_photo_url: Telegram photo URL

        Returns:
            User object
        """
        try:
            # Check if user exists
            user = await self.get_user_by_telegram_id(session, telegram_id)

            if user:
                # Update existing user
                user.telegram_username = telegram_username
                user.telegram_first_name = telegram_first_name
                user.telegram_last_name = telegram_last_name
                user.telegram_photo_url = telegram_photo_url
                user.updated_at = datetime.utcnow()

                await session.commit()
                await session.refresh(user)

                logger.info(f"Updated Telegram user: {user.get_identifier()}")
                return user
            else:
                # Create new user
                user_data = UserCreate(
                    telegram_id=telegram_id,
                    telegram_username=telegram_username,
                    telegram_first_name=telegram_first_name,
                    telegram_last_name=telegram_last_name,
                    telegram_photo_url=telegram_photo_url,
                )

                user = await self.create_user(session, user_data)
                return user

        except Exception as e:
            logger.error(f"Error creating/updating Telegram user {telegram_id}: {e!s}")
            await session.rollback()
            return None

    async def get_users(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """Get list of users with pagination."""
        try:
            result = await session.execute(
                select(User)
                .where(User.is_active == True)
                .offset(skip)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users: {e!s}")
            return []

    async def get_user_count(self, session: AsyncSession) -> int:
        """Get total number of active users."""
        try:
            result = await session.execute(select(User).where(User.is_active == True))
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting user count: {e!s}")
            return 0

    async def get_admins(self, session: AsyncSession) -> list[User]:
        """Get list of admin users."""
        try:
            result = await session.execute(
                select(User).where(User.is_admin == True).where(User.is_active == True)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting admin users: {e!s}")
            return []

    def generate_user_tokens(self, user: User) -> dict[str, str]:
        """Generate JWT tokens for user."""
        return create_user_token(
            user_id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            is_admin=user.is_admin,
        )

    async def get_user_from_token(
        self, session: AsyncSession, token: str
    ) -> Optional[User]:
        """Get user from JWT token."""
        try:
            user_data = jwt_service.get_user_from_token(token)
            if not user_data:
                return None

            user_id = user_data.get("user_id")
            if not user_id:
                return None

            user = await self.get_user_by_id(session, user_id)
            if user and user.is_active:
                return user

            return None

        except Exception as e:
            logger.error(f"Error getting user from token: {e!s}")
            return None


# Global user service instance
user_service = UserService()


async def get_current_user_from_token(
    session: AsyncSession, token: str
) -> Optional[User]:
    """
    Convenience function to get current user from token.

    Args:
        session: Database session
        token: JWT token

    Returns:
        User object if valid, None otherwise
    """
    return await user_service.get_user_from_token(session, token)


async def create_or_get_telegram_user(
    session: AsyncSession,
    telegram_id: int,
    telegram_username: Optional[str] = None,
    telegram_first_name: Optional[str] = None,
    telegram_last_name: Optional[str] = None,
    telegram_photo_url: Optional[str] = None,
) -> Optional[User]:
    """
    Convenience function to create or get Telegram user.

    Args:
        session: Database session
        telegram_id: Telegram user ID
        telegram_username: Telegram username
        telegram_first_name: Telegram first name
        telegram_last_name: Telegram last name
        telegram_photo_url: Telegram photo URL

    Returns:
        User object
    """
    return await user_service.create_or_update_telegram_user(
        session,
        telegram_id,
        telegram_username,
        telegram_first_name,
        telegram_last_name,
        telegram_photo_url,
    )
