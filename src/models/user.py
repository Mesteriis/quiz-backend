"""
User SQLAlchemy model for the Quiz App.

This module contains only the User SQLAlchemy model
for database operations and schema definition.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """User database model."""

    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # Authentication fields
    username = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)

    # Telegram fields
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    telegram_username = Column(String(100), nullable=True, index=True)
    telegram_first_name = Column(String(100), nullable=True)
    telegram_last_name = Column(String(100), nullable=True)
    telegram_photo_url = Column(String(500), nullable=True)

    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(100), nullable=True)
    bio = Column(String(500), nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamp fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login = Column(DateTime, nullable=True)

    # Localization fields
    language = Column(String(10), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    respondents = relationship("Respondent", back_populates="user")
    responses = relationship("Response", back_populates="user")
    push_subscriptions = relationship(
        "PushSubscription", back_populates="user", cascade="all, delete-orphan"
    )
    created_surveys = relationship("Survey", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def __str__(self):
        return f"User {self.username or self.email or self.id}"

    def get_display_name(self) -> str:
        """
        Get the display name for the user.

        Returns the best available name in order of preference:
        1. display_name field
        2. first_name + last_name
        3. telegram_first_name + telegram_last_name
        4. username
        5. telegram_username
        6. email (local part)
        7. fallback to "User {id}"
        """
        if self.display_name:
            return self.display_name

        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name

        if self.telegram_first_name and self.telegram_last_name:
            return f"{self.telegram_first_name} {self.telegram_last_name}"
        elif self.telegram_first_name:
            return self.telegram_first_name

        if self.username:
            return self.username

        if self.telegram_username:
            return f"@{self.telegram_username}"

        if self.email:
            return self.email.split("@")[0]

        return f"User {self.id}"

    def get_full_name(self) -> str:
        """Get the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.telegram_first_name and self.telegram_last_name:
            return f"{self.telegram_first_name} {self.telegram_last_name}"
        elif self.telegram_first_name:
            return self.telegram_first_name
        else:
            return self.get_display_name()

    def is_telegram_user(self) -> bool:
        """Check if this user is authenticated via Telegram."""
        return self.telegram_id is not None

    def has_complete_profile(self) -> bool:
        """Check if user has a complete profile."""
        return bool(
            self.first_name and self.last_name and (self.email or self.telegram_id)
        )

    def get_primary_identifier(self) -> str:
        """Get the primary identifier for the user."""
        return (
            self.email or self.username or f"telegram:{self.telegram_id}"
            if self.telegram_id
            else f"user:{self.id}"
        )
