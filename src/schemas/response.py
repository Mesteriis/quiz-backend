"""
Response schemas for the Quiz App.

This module contains Pydantic schemas for Response model validation and serialization.
Re-exports schemas from models.response for compatibility.
"""

from models.response import (
    ResponseBase,
    ResponseCreate,
    ResponseRead,
)

# Alias for compatibility with new architecture
ResponseResponse = ResponseRead

__all__ = [
    "ResponseBase",
    "ResponseCreate",
    "ResponseRead",
    "ResponseResponse",
]
