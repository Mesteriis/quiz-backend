"""
Routers package for the Quiz App API.

This module exports all FastAPI routers for use in the main application.
"""

from . import admin, auth, reports, responses, surveys, user_data, validation

# Export all routers
__all__ = [
    "auth",
    "surveys",
    "responses",
    "user_data",
    "validation",
    "admin",
    "reports",
]
