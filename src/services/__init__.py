"""
Services package for the Quiz App.

This module contains business logic services for various
application features like email validation, user data processing, etc.
"""

from .email_validation import email_validator, validate_email
from .jwt_service import create_user_token, get_current_user_from_token, jwt_service
from .user_service import (
    create_or_get_telegram_user,
    get_current_user_from_token,
    user_service,
)

__all__ = [
    "email_validator",
    "validate_email",
    "jwt_service",
    "create_user_token",
    "get_current_user_from_token",
    "user_service",
    "create_or_get_telegram_user",
]
