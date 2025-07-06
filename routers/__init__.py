"""
Routers package for the Quiz App API.

This module exports all FastAPI routers for use in the main application.
"""

from routers import surveys, responses, user_data, validation, auth, admin, reports

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
