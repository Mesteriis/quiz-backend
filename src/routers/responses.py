"""
Response API router for the Quiz App.

This module contains FastAPI endpoints for managing user responses
with immediate save functionality and no edit capability.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from models.question import Question
from models.response import Response, ResponseCreate, ResponseRead, ResponseValidate
from models.survey import Survey
from models.respondent import Respondent, RespondentCreate
from repositories.dependencies import (
    get_response_repository,
    get_question_repository,
    get_survey_repository,
    get_respondent_repository,
    get_respondent_event_repository,
    get_consent_log_repository,
    get_user_repository,
)
from repositories.response import ResponseRepository
from repositories.question import QuestionRepository
from repositories.survey import SurveyRepository
from repositories.respondent import RespondentRepository
from repositories.respondent_event import RespondentEventRepository
from repositories.consent_log import ConsentLogRepository
from repositories.user import UserRepository
from services.respondent_service import RespondentService

router = APIRouter()

logger = logging.getLogger(__name__)


async def get_respondent_service(
    respondent_repo: RespondentRepository = Depends(get_respondent_repository),
    event_repo: RespondentEventRepository = Depends(get_respondent_event_repository),
    consent_repo: ConsentLogRepository = Depends(get_consent_log_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> RespondentService:
    """Get RespondentService instance."""
    return RespondentService(
        respondent_repo=respondent_repo,
        event_repo=event_repo,
        consent_repo=consent_repo,
        user_repo=user_repo,
    )


@router.post("/", response_model=ResponseRead)
async def create_response(
    response_data: ResponseCreate,
    request: Request,
    response_repo: ResponseRepository = Depends(get_response_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    respondent_repo: RespondentRepository = Depends(get_respondent_repository),
    respondent_service: RespondentService = Depends(get_respondent_service),
):
    """
    Create a new response (immediate save).

    Saves the response immediately without validation for edit capability.
    Once saved, responses cannot be modified.
    """
    try:
        # First validate that the question exists
        question = await question_repo.get(response_data.question_id)

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # ФИКС: Сохраняем question_type заранее, чтобы избежать MissingGreenlet в логах
        question_type = question.question_type

        # Get survey to check if it's active
        survey = await question_repo.get_survey_by_question_id(
            response_data.question_id
        )

        if not survey or not survey.is_active:
            raise HTTPException(status_code=400, detail="Survey is not active")

        # Get or create respondent if not provided
        if not response_data.respondent_id:
            # Создаем минимального анонимного респондента через репозиторий
            respondent_data = RespondentCreate(
                session_id=response_data.user_session_id,
                is_anonymous=response_data.user_id is None,
                user_id=response_data.user_id,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent"),
                entry_point="web",
            )

            respondent = await respondent_repo.create(obj_in=respondent_data)
            response_data.respondent_id = respondent.id

        # Check if response already exists for this question and respondent
        existing_response = await response_repo.get_by_question_and_session(
            response_data.question_id, response_data.user_session_id
        )

        if existing_response:
            raise HTTPException(
                status_code=400,
                detail="Response already exists for this question. Editing is not allowed.",
            )

        # Validate response data based on question type
        validation_result = _validate_response_data(question_type, response_data.answer)

        if not validation_result:
            raise HTTPException(
                status_code=400, detail="Invalid response data for question type"
            )

        # Create the response
        response = await response_repo.create(obj_in=response_data)

        return ResponseRead.model_validate(response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create response: {e!s}")


@router.get("/question/{question_id}", response_model=list[ResponseRead])
async def get_responses_by_question(
    question_id: int,
    response_repo: ResponseRepository = Depends(get_response_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
):
    """
    Get all responses for a specific question.

    Only returns responses for public surveys.
    Admin endpoints provide access to private survey responses.
    """
    try:
        # First check if question exists and belongs to public survey
        question = await question_repo.get(question_id)

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Get survey to check if it's public
        survey = await question_repo.get_survey_by_question_id(question_id)
        if not survey or not survey.is_public:
            raise HTTPException(
                status_code=403, detail="Cannot access responses for private survey"
            )

        # Get responses for this question
        responses = await response_repo.get_by_question_id(question_id)

        return [ResponseRead.model_validate(response) for response in responses]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch responses: {e!s}")


@router.get("/user/{user_session_id}", response_model=list[ResponseRead])
async def get_responses_by_user(
    user_session_id: str,
    response_repo: ResponseRepository = Depends(get_response_repository),
):
    """
    Get all responses for a specific user session.

    Only returns responses for public surveys.
    """
    try:
        # Get responses for this user session (only public surveys)
        responses = await response_repo.get_by_user_session_public_only(user_session_id)

        return [ResponseRead.model_validate(response) for response in responses]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch user responses: {e!s}"
        )


@router.get("/survey/{survey_id}/progress/{user_session_id}")
async def get_survey_progress(
    survey_id: int,
    user_session_id: str,
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    response_repo: ResponseRepository = Depends(get_response_repository),
):
    """
    Get user progress for a specific survey.

    Returns completion status and answered questions.
    Only works for public surveys.
    """
    try:
        # First check if survey exists and is public
        survey = await survey_repo.get(survey_id)

        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        if not survey.is_public or not survey.is_active:
            raise HTTPException(
                status_code=404, detail="Survey not found or not publicly accessible"
            )

        # Get all questions for this survey
        questions = await question_repo.get_by_survey_id(survey_id)
        total_questions = len(questions)

        # Get user responses for this survey
        user_responses = await response_repo.get_by_user_session_and_survey(
            user_session_id, survey_id
        )

        answered_questions = len(user_responses)
        answered_question_ids = {response.question_id for response in user_responses}

        # Calculate progress
        completion_percentage = (
            (answered_questions / total_questions * 100) if total_questions > 0 else 0
        )

        # Get unanswered questions
        unanswered_questions = [
            {
                "id": q.id,
                "title": q.title,
                "order": q.order,
                "question_type": q.question_type,
            }
            for q in questions
            if q.id not in answered_question_ids
        ]

        # Sort unanswered questions by order
        sorted_unanswered = sorted(unanswered_questions, key=lambda x: x["order"])

        # Get next question ID (first unanswered question)
        next_question_id = sorted_unanswered[0]["id"] if sorted_unanswered else None

        return {
            "survey_id": survey_id,
            "user_session_id": user_session_id,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "completion_percentage": round(completion_percentage, 2),
            "is_completed": answered_questions == total_questions,
            "next_question_id": next_question_id,
            "unanswered_questions": sorted_unanswered,
            "last_response_at": max(
                (response.created_at for response in user_responses), default=None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get survey progress: {e!s}"
        )


@router.post("/validate-before-save")
async def validate_response_before_save(
    validation_data: ResponseValidate,
    question_repo: QuestionRepository = Depends(get_question_repository),
):
    """
    Validate response data before saving.

    Returns validation result without saving the response.
    Useful for client-side validation feedback.
    """
    try:
        # Get question
        question = await question_repo.get(validation_data.question_id)

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Get survey to check if it's active
        survey = await question_repo.get_survey_by_question_id(
            validation_data.question_id
        )
        if not survey or not survey.is_active:
            raise HTTPException(status_code=400, detail="Survey is not active")

        # Validate response data
        is_valid = _validate_response_data(
            question.question_type, validation_data.answer
        )
        validation_message = (
            None
            if is_valid
            else _get_validation_message(question, validation_data.answer)
        )

        return {
            "question_id": validation_data.question_id,
            "is_valid": is_valid,
            "validation_message": validation_message,
            "question_type": question.question_type,
            "question_title": question.title,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {e!s}")


def _validate_response_data(question_type: str, answer: dict[str, Any]) -> bool:
    """
    Validate response data based on question type.

    Args:
        question_type: Question type
        answer: Response answer data

    Returns:
        True if valid, False otherwise
    """
    try:
        if question_type in ["TEXT", "text"]:
            # Text questions require a string value
            value = answer.get("value")
            return isinstance(value, str) and len(value.strip()) > 0

        elif question_type in ["YES_NO", "boolean"]:
            # Boolean questions require a boolean value
            value = answer.get("value")
            # Accept both boolean and string boolean values
            if isinstance(value, bool):
                return True
            elif isinstance(value, str):
                return value.lower() in ["true", "false", "yes", "no"]
            return False

        elif question_type in ["RATING_1_10", "rating"]:
            # Rating questions require a numeric value within range
            value = answer.get("value")
            if not isinstance(value, (int, float)):
                return False

            # Default range for RATING_1_10 is 1-10
            min_rating = 1
            max_rating = 10
            return min_rating <= value <= max_rating

        elif question_type == "EMAIL":
            # Email questions require a valid email format
            email_value = answer.get("value")
            if not isinstance(email_value, str):
                return False

            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return re.match(email_pattern, email_value) is not None

        elif question_type == "PHONE":
            # Phone questions require a valid phone number format
            phone_value = answer.get("value")
            if not isinstance(phone_value, str):
                return False

            import re

            # Basic phone validation (digits, spaces, hyphens, plus, parentheses)
            phone_pattern = r"^\+?[\d\s\-\(\)]{7,15}$"
            return re.match(phone_pattern, phone_value) is not None

        elif question_type == "IMAGE_UPLOAD":
            # Image upload requires file data
            file_data = answer.get("file")
            if not file_data:
                return False

            # Check if file has required properties
            return (
                isinstance(file_data, dict)
                and "filename" in file_data
                and "content_type" in file_data
                and file_data.get("content_type", "").startswith("image/")
            )

        elif question_type == "FILE_UPLOAD":
            # File upload requires file data
            file_data = answer.get("file")
            if not file_data:
                return False

            # Check if file has required properties
            return (
                isinstance(file_data, dict)
                and "filename" in file_data
                and "content_type" in file_data
                and len(file_data.get("filename", "")) > 0
            )

        elif question_type == "GEOLOCATION":
            # Geolocation requires latitude and longitude
            location = answer.get("location")
            if not isinstance(location, dict):
                return False

            lat = location.get("latitude")
            lng = location.get("longitude")

            return (
                isinstance(lat, (int, float))
                and isinstance(lng, (int, float))
                and -90 <= lat <= 90
                and -180 <= lng <= 180
            )

        elif question_type == "NFC_SCAN":
            # NFC scan requires tag data
            nfc_data = answer.get("nfc_data")
            if not isinstance(nfc_data, dict):
                return False

            # Check if NFC data has required properties
            return (
                "tag_id" in nfc_data
                and "tag_type" in nfc_data
                and len(nfc_data.get("tag_id", "")) > 0
            )

        elif question_type == "multiple_choice":
            # Multiple choice requires a selected option
            selected = answer.get("selected")
            if not selected:
                return False

            # Check if selected option exists in question options
            question_data = question.question_data or {}
            options = question_data.get("options", [])
            return any(opt.get("id") == selected for opt in options)

        elif question_type == "date":
            # Date questions require a valid date string
            date_value = answer.get("value")
            if not isinstance(date_value, str):
                return False

            try:
                from datetime import datetime

                datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                return True
            except (ValueError, TypeError):
                return False

        elif question_type == "number":
            # Number questions require a numeric value
            value = answer.get("value")
            return isinstance(value, (int, float))

        else:
            # Unknown question type - assume valid for now
            return True

    except Exception:
        return False


def _get_validation_message(question: Question, answer: dict[str, Any]) -> str:
    """
    Get validation error message for invalid response.

    Args:
        question: Question instance
        answer: Response answer data

    Returns:
        Validation error message
    """
    question_type = question.question_type

    if question_type in ["TEXT", "text"]:
        if not answer.get("value"):
            return "Text response cannot be empty"
        return "Invalid text response"

    elif question_type in ["YES_NO", "boolean"]:
        return "Please select true or false"

    elif question_type in ["RATING_1_10", "rating"]:
        return "Rating must be between 1 and 10"

    elif question_type == "EMAIL":
        return "Please provide a valid email address"

    elif question_type == "PHONE":
        return "Please provide a valid phone number"

    elif question_type == "IMAGE_UPLOAD":
        return "Please upload a valid image file"

    elif question_type == "FILE_UPLOAD":
        return "Please upload a valid file"

    elif question_type == "GEOLOCATION":
        return "Please provide valid location coordinates"

    elif question_type == "NFC_SCAN":
        return "Please provide valid NFC tag data"

    elif question_type == "multiple_choice":
        if not answer.get("selected"):
            return "Please select an option"
        return "Selected option is not valid"

    elif question_type == "date":
        return "Please provide a valid date"

    elif question_type == "number":
        return "Please provide a valid number"

    else:
        return "Invalid response format"
