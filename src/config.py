"""
Configuration settings for the Quiz App.

This module contains all application settings using Pydantic Settings
for environment variable validation and type safety.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = Field(default="Quiz App", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(
        default="development", description="Environment (development/production)"
    )
    debug: bool = Field(default=True, description="Debug mode")
    secret_key: str = Field("super-key", description="Secret key for JWT tokens")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./quiz.db", description="Database connection URL"
    )
    database_echo: bool = Field(
        default=False, description="Enable SQLAlchemy query logging"
    )

    # FastAPI
    api_prefix: str = Field(default="/api", description="API prefix")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )
    docs_url: Optional[str] = Field(default="/docs", description="Swagger docs URL")
    redoc_url: Optional[str] = Field(default="/redoc", description="ReDoc URL")

    # Telegram Bot
    telegram_bot_token: Optional[str] = Field(
        default=None, description="Telegram bot token"
    )
    telegram_webhook_url: Optional[str] = Field(
        default=None, description="Telegram webhook URL"
    )
    telegram_admin_chat_id: Optional[str] = Field(
        default=None, description="Admin chat ID"
    )

    # Email Validation
    smtp_timeout: int = Field(default=10, description="SMTP validation timeout")
    mx_check_enabled: bool = Field(
        default=True, description="Enable MX record checking"
    )

    # File Upload
    max_file_size: int = Field(
        default=10485760, description="Max file size in bytes (10MB)"
    )
    upload_dir: str = Field(
        default="./backend/static/images", description="Upload directory"
    )
    allowed_extensions: list[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp"],
        description="Allowed file extensions",
    )

    # Security
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")

    # PWA
    pwa_name: str = Field(default="Quiz App", description="PWA name")
    pwa_short_name: str = Field(default="Quiz", description="PWA short name")
    pwa_description: str = Field(
        default="Interactive Quiz Application", description="PWA description"
    )
    pwa_theme_color: str = Field(
        default="#8B5CF6", description="PWA theme color (purple)"
    )
    pwa_background_color: str = Field(
        default="#1F2937", description="PWA background color (dark)"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour")

    # Push Notifications (VAPID)
    VAPID_PRIVATE_KEY: str = Field(
        default="BEl62iUYgUivxIkv69yViEuiBIa40HI0DLb6RDJ5-8N4Am6-YCwdI-V0OKdcUb8qXJ6rN4V8CuGKzqfJbZquJEa4",
        description="VAPID private key for push notifications",
    )
    VAPID_PUBLIC_KEY: str = Field(
        default="BEl62iUYgUivxIkv69yViEuiBIa40HI0DLb6RDJ5-8N4Am6-YCwdI-V0OKdcUb8qXJ6rN4V8CuGKzqfJbZquJEa4",
        description="VAPID public key for push notifications",
    )
    VAPID_EMAIL: str = Field(
        default="noreply@quizapp.com", description="Contact email for VAPID claims"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.database_url.replace("+aiosqlite", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
