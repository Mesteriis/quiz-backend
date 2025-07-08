"""
Routers package for the Quiz App API.

This module exports all FastAPI routers for use in the main application.
"""

from . import (
    admin,
    auth,
    monitoring,
    notifications,
    profiles,
    push_notifications,
    reports,
    respondents,
    responses,
    surveys,
    telegram,
    telegram_webapp,
    user_data,
    validation,
)

# Export all routers
__all__ = [
    "admin",
    "auth",
    "monitoring",
    "notifications",
    "profiles",
    "push_notifications",
    "reports",
    "respondents",
    "responses",
    "surveys",
    "telegram",
    "telegram_webapp",
    "user_data",
    "validation",
]
