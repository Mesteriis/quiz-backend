"""
Telegram Web Apps Service for Quiz App.

This module provides functionality for Telegram Web Apps (TWA) integration,
allowing users to access the full quiz functionality directly within Telegram.
"""

from datetime import datetime
import hashlib
import hmac
import json
import logging
from typing import Any, Optional
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_async_session
from models.question import Question
from models.response import Response
from models.survey import Survey
from models.user import User
from services.jwt_service import create_access_token
from services.user_service import user_service

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramWebAppService:
    """Service for managing Telegram Web Apps functionality."""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.webapp_url = getattr(
            settings, "telegram_webapp_url", "http://localhost:3000/telegram"
        )

    def validate_init_data(self, init_data: str) -> dict[str, Any]:
        """
        Validate Telegram Web App init data.

        This ensures the data comes from Telegram and hasn't been tampered with.
        """
        try:
            # Parse the init data
            parsed_data = dict(parse_qsl(init_data))

            # Extract hash and other data
            received_hash = parsed_data.pop("hash", None)
            if not received_hash:
                raise ValueError("No hash provided")

            # Create data check string
            data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
            data_check_string = "\n".join(data_check_arr)

            # Calculate expected hash
            secret_key = hmac.new(
                b"WebAppData", self.bot_token.encode(), hashlib.sha256
            ).digest()

            expected_hash = hmac.new(
                secret_key, data_check_string.encode(), hashlib.sha256
            ).hexdigest()

            # Verify hash
            if not hmac.compare_digest(received_hash, expected_hash):
                raise ValueError("Invalid hash")

            # Check auth_date (should be recent)
            auth_date = int(parsed_data.get("auth_date", 0))
            current_time = int(datetime.now().timestamp())

            if current_time - auth_date > 86400:  # 24 hours
                raise ValueError("Auth data is too old")

            # Parse user data if present
            if "user" in parsed_data:
                parsed_data["user"] = json.loads(unquote(parsed_data["user"]))

            return parsed_data

        except Exception as e:
            logger.error(f"Failed to validate init data: {e}")
            raise HTTPException(status_code=401, detail="Invalid init data")

    async def authenticate_user(self, init_data: str) -> dict[str, Any]:
        """
        Authenticate user from Telegram Web App init data.

        Returns user info and access token.
        """
        try:
            # Validate init data
            validated_data = self.validate_init_data(init_data)

            if "user" not in validated_data:
                raise HTTPException(status_code=400, detail="No user data provided")

            telegram_user = validated_data["user"]

            async with get_async_session() as session:
                # Create or get user
                user = await self._create_or_get_user(session, telegram_user)

                # Generate access token
                access_token = create_access_token({"sub": str(user.id)})

                return {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "is_admin": user.is_admin,
                        "telegram_id": user.telegram_id,
                    },
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")

    async def _create_or_get_user(
        self, session: AsyncSession, telegram_user: dict[str, Any]
    ) -> User:
        """Create or retrieve user from Telegram data."""
        telegram_id = telegram_user.get("id")

        if not telegram_id:
            raise HTTPException(status_code=400, detail="Invalid user data")

        # Try to get existing user
        user = await user_service.get_user_by_telegram_id(session, telegram_id)

        if user:
            # Update user info if needed
            updated = False

            if user.first_name != telegram_user.get("first_name"):
                user.first_name = telegram_user.get("first_name", "")
                updated = True

            if user.last_name != telegram_user.get("last_name"):
                user.last_name = telegram_user.get("last_name", "")
                updated = True

            if user.username != telegram_user.get("username"):
                user.username = telegram_user.get("username", "")
                updated = True

            if updated:
                await session.commit()
                await session.refresh(user)

            return user

        # Create new user
        username = telegram_user.get("username", f"tg_user_{telegram_id}")
        email = f"{username}@telegram.local"  # Placeholder email

        new_user = User(
            username=username,
            email=email,
            first_name=telegram_user.get("first_name", ""),
            last_name=telegram_user.get("last_name", ""),
            telegram_id=telegram_id,
            is_verified=True,  # Telegram users are pre-verified
            hashed_password="telegram_auth",  # Placeholder
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        logger.info(f"Created new user from Telegram: {username} (ID: {telegram_id})")
        return new_user

    async def get_webapp_surveys(self, user_id: int) -> list[dict[str, Any]]:
        """Get surveys formatted for Telegram Web App."""
        async with get_async_session() as session:
            # Get active public surveys
            stmt = (
                select(Survey)
                .where(Survey.is_active == True, Survey.is_public == True)
                .order_by(Survey.created_at.desc())
            )

            result = await session.execute(stmt)
            surveys = result.scalars().all()

            formatted_surveys = []

            for survey in surveys:
                # Count questions
                questions_stmt = select(Question).where(Question.survey_id == survey.id)
                questions_result = await session.execute(questions_stmt)
                questions_count = len(questions_result.scalars().all())

                # Count user's responses
                responses_stmt = select(Response).where(
                    Response.user_id == user_id,
                    Response.question_id.in_(
                        select(Question.id).where(Question.survey_id == survey.id)
                    ),
                )
                responses_result = await session.execute(responses_stmt)
                user_responses = len(responses_result.scalars().all())

                # Determine completion status
                completion_percentage = (
                    (user_responses / questions_count * 100)
                    if questions_count > 0
                    else 0
                )
                is_completed = completion_percentage >= 100

                formatted_surveys.append(
                    {
                        "id": survey.id,
                        "title": survey.title,
                        "description": survey.description,
                        "questions_count": questions_count,
                        "user_responses": user_responses,
                        "completion_percentage": completion_percentage,
                        "is_completed": is_completed,
                        "created_at": survey.created_at.isoformat(),
                        "access_token": survey.access_token,
                    }
                )

            return formatted_surveys

    async def get_webapp_survey_details(
        self, survey_id: int, user_id: int
    ) -> dict[str, Any]:
        """Get detailed survey info for Telegram Web App."""
        async with get_async_session() as session:
            # Get survey with questions
            survey_stmt = select(Survey).where(Survey.id == survey_id)
            survey_result = await session.execute(survey_stmt)
            survey = survey_result.scalar_one_or_none()

            if not survey:
                raise HTTPException(status_code=404, detail="Survey not found")

            # Get questions
            questions_stmt = (
                select(Question)
                .where(Question.survey_id == survey_id)
                .order_by(Question.order)
            )
            questions_result = await session.execute(questions_stmt)
            questions = questions_result.scalars().all()

            # Get user's responses
            responses_stmt = select(Response).where(
                Response.user_id == user_id,
                Response.question_id.in_([q.id for q in questions]),
            )
            responses_result = await session.execute(responses_stmt)
            responses = {r.question_id: r for r in responses_result.scalars().all()}

            # Format questions with user responses
            formatted_questions = []
            for question in questions:
                user_response = responses.get(question.id)

                formatted_questions.append(
                    {
                        "id": question.id,
                        "title": question.title,
                        "description": question.description,
                        "type": question.question_type.value,
                        "is_required": question.is_required,
                        "order": question.order,
                        "options": question.options,
                        "user_answer": user_response.answer if user_response else None,
                        "answered_at": user_response.created_at.isoformat()
                        if user_response
                        else None,
                    }
                )

            return {
                "survey": {
                    "id": survey.id,
                    "title": survey.title,
                    "description": survey.description,
                    "is_active": survey.is_active,
                    "is_public": survey.is_public,
                    "created_at": survey.created_at.isoformat(),
                },
                "questions": formatted_questions,
                "total_questions": len(questions),
                "answered_questions": len(
                    [q for q in formatted_questions if q["user_answer"]]
                ),
                "completion_percentage": len(
                    [q for q in formatted_questions if q["user_answer"]]
                )
                / len(questions)
                * 100
                if questions
                else 0,
            }

    def generate_webapp_config(self, user_id: int) -> dict[str, Any]:
        """Generate configuration for Telegram Web App frontend."""
        return {
            "api_base_url": settings.api_base_url or "http://localhost:8000",
            "webapp_version": "1.0.0",
            "user_id": user_id,
            "features": {
                "surveys": True,
                "realtime_notifications": True,
                "offline_mode": False,
                "push_notifications": True,
            },
            "ui_config": {
                "theme": "telegram",
                "primary_color": "#0088cc",
                "dark_mode": True,
                "animations": True,
            },
            "limits": {
                "max_questions_per_page": 5,
                "cache_duration": 3600,
                "auto_save_interval": 30,
            },
        }

    def create_main_button_config(
        self, survey_id: int | None = None, action: str = "list"
    ) -> dict[str, Any]:
        """Create configuration for Telegram Web App main button."""
        configs = {
            "list": {
                "text": "📋 Выбрать опрос",
                "color": "#0088cc",
                "text_color": "#ffffff",
                "is_visible": True,
                "is_active": True,
            },
            "start_survey": {
                "text": "🚀 Начать опрос",
                "color": "#2ea043",
                "text_color": "#ffffff",
                "is_visible": True,
                "is_active": True,
            },
            "continue_survey": {
                "text": "▶️ Продолжить",
                "color": "#fb8500",
                "text_color": "#ffffff",
                "is_visible": True,
                "is_active": True,
            },
            "complete_survey": {
                "text": "✅ Завершить опрос",
                "color": "#2ea043",
                "text_color": "#ffffff",
                "is_visible": True,
                "is_active": True,
            },
            "view_results": {
                "text": "📊 Посмотреть результаты",
                "color": "#6f42c1",
                "text_color": "#ffffff",
                "is_visible": True,
                "is_active": True,
            },
        }

        return configs.get(action, configs["list"])

    def create_haptic_feedback_config(self, type_: str = "impact") -> dict[str, Any]:
        """Create haptic feedback configuration for Telegram Web App."""
        return {
            "type": type_,  # impact, notification, selection
            "style": "medium" if type_ == "impact" else "success",
        }


# Global service instance
_webapp_service: Optional[TelegramWebAppService] = None


def get_webapp_service() -> TelegramWebAppService:
    """Get or create Telegram Web App service instance."""
    global _webapp_service

    if _webapp_service is None:
        _webapp_service = TelegramWebAppService()

    return _webapp_service
