"""
JWT service for the Quiz App.

This module provides JWT token generation, validation, and user authentication
functionality for both regular users and Telegram users.
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

logger = logging.getLogger(__name__)


class JWTService:
    """Service for JWT token management and user authentication."""

    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days

        # Password hashing context (for future use)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(
        self,
        user_id: int,
        telegram_id: Optional[int] = None,
        username: Optional[str] = None,
        is_admin: bool = False,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create JWT access token for user authentication.

        Args:
            user_id: User ID
            telegram_id: Telegram ID (if Telegram user)
            username: Username (if available)
            is_admin: Whether user is admin
            expires_delta: Custom expiration time

        Returns:
            str: JWT access token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        # Token payload
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "is_admin": is_admin,
        }

        # Add optional fields
        if telegram_id:
            payload["telegram_id"] = telegram_id
        if username:
            payload["username"] = username

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            logger.error(f"Error creating access token: {e!s}")
            raise

    def create_refresh_token(
        self, user_id: int, telegram_id: Optional[int] = None
    ) -> str:
        """
        Create JWT refresh token for token renewal.

        Args:
            user_id: User ID
            telegram_id: Telegram ID (if Telegram user)

        Returns:
            str: JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }

        if telegram_id:
            payload["telegram_id"] = telegram_id

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            logger.error(f"Error creating refresh token: {e!s}")
            raise

    def verify_token(self, token: str) -> Optional[dict[str, Any]]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token to verify

        Returns:
            dict: Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("Token has expired")
                return None

            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {e!s}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e!s}")
            return None

    def get_user_from_token(self, token: str) -> Optional[dict[str, Any]]:
        """
        Extract user information from JWT token.

        Args:
            token: JWT token

        Returns:
            dict: User information if token is valid, None otherwise
        """
        payload = self.verify_token(token)
        if not payload:
            return None

        return {
            "user_id": payload.get("user_id"),
            "telegram_id": payload.get("telegram_id"),
            "username": payload.get("username"),
            "is_admin": payload.get("is_admin", False),
            "token_type": payload.get("type", "access"),
        }

    def create_telegram_auth_token(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        telegram_first_name: Optional[str] = None,
        telegram_last_name: Optional[str] = None,
        telegram_photo_url: Optional[str] = None,
    ) -> str:
        """
        Create temporary token for Telegram authentication.

        Args:
            telegram_id: Telegram user ID
            telegram_username: Telegram username
            telegram_first_name: Telegram first name
            telegram_last_name: Telegram last name
            telegram_photo_url: Telegram photo URL

        Returns:
            str: Temporary authentication token
        """
        expire = datetime.utcnow() + timedelta(minutes=10)  # Short expiration

        payload = {
            "telegram_id": telegram_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "telegram_auth",
        }

        # Add optional Telegram data
        if telegram_username:
            payload["telegram_username"] = telegram_username
        if telegram_first_name:
            payload["telegram_first_name"] = telegram_first_name
        if telegram_last_name:
            payload["telegram_last_name"] = telegram_last_name
        if telegram_photo_url:
            payload["telegram_photo_url"] = telegram_photo_url

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            logger.error(f"Error creating Telegram auth token: {e!s}")
            raise

    def verify_telegram_auth_token(self, token: str) -> Optional[dict[str, Any]]:
        """
        Verify Telegram authentication token.

        Args:
            token: Telegram auth token

        Returns:
            dict: Telegram user data if valid, None otherwise
        """
        payload = self.verify_token(token)
        if not payload or payload.get("type") != "telegram_auth":
            return None

        return {
            "telegram_id": payload.get("telegram_id"),
            "telegram_username": payload.get("telegram_username"),
            "telegram_first_name": payload.get("telegram_first_name"),
            "telegram_last_name": payload.get("telegram_last_name"),
            "telegram_photo_url": payload.get("telegram_photo_url"),
        }

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired."""
        payload = self.verify_token(token)
        if not payload:
            return True

        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            return True

        return False

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """Get token expiration time."""
        payload = self.verify_token(token)
        if not payload:
            return None

        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp)

        return None


# Global JWT service instance
jwt_service = JWTService()


def create_user_token(
    user_id: int,
    telegram_id: Optional[int] = None,
    username: Optional[str] = None,
    is_admin: bool = False,
) -> dict[str, str]:
    """
    Convenience function to create both access and refresh tokens.

    Args:
        user_id: User ID
        telegram_id: Telegram ID (if Telegram user)
        username: Username (if available)
        is_admin: Whether user is admin

    Returns:
        dict: Dictionary with access_token and refresh_token
    """
    access_token = jwt_service.create_access_token(
        user_id=user_id, telegram_id=telegram_id, username=username, is_admin=is_admin
    )

    refresh_token = jwt_service.create_refresh_token(
        user_id=user_id, telegram_id=telegram_id
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def get_current_user_from_token(token: str) -> Optional[dict[str, Any]]:
    """
    Convenience function to get current user from token.

    Args:
        token: JWT token

    Returns:
        dict: User information if valid, None otherwise
    """
    return jwt_service.get_user_from_token(token)


def get_current_user(token: str) -> Optional[dict[str, Any]]:
    """
    Alias for get_current_user_from_token for backward compatibility.

    Args:
        token: JWT token

    Returns:
        dict: User information if valid, None otherwise
    """
    return jwt_service.get_user_from_token(token)
