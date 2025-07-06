"""
Response API router for the Quiz App.

This module contains FastAPI endpoints for managing user responses
with immediate save functionality and no edit capability.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import get_async_session
from models import Question, Response, ResponseCreate, ResponseRead, Survey

router = APIRouter()


@router.post("/", response_model=ResponseRead)
async def create_response(
    response_data: ResponseCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create a new response (immediate save).

    Saves the response immediately without validation for edit capability.
    Once saved, responses cannot be modified.
    """
    try:
        # First validate that the question exists
        question_stmt = (
            select(Question)
            .options(selectinload(Question.survey))
            .where(Question.id == response_data.question_id)
        )

        question_result = await session.execute(question_stmt)
        question = question_result.scalar_one_or_none()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Check if survey is active
        if not question.survey.is_active:
            raise HTTPException(status_code=400, detail="Survey is not active")

        # Check if response already exists for this question and user
        existing_response_stmt = (
            select(Response)
            .where(Response.question_id == response_data.question_id)
            .where(Response.user_session_id == response_data.user_session_id)
        )

        existing_result = await session.execute(existing_response_stmt)
        existing_response = existing_result.scalar_one_or_none()

        if existing_response:
            raise HTTPException(
                status_code=400,
                detail="Response already exists for this question. Editing is not allowed.",
            )

        # Validate response data based on question type
        if not _validate_response_data(question, response_data.answer):
            raise HTTPException(
                status_code=400, detail="Invalid response data for question type"
            )

        # Create the response
        response = Response(
            question_id=response_data.question_id,
            user_session_id=response_data.user_session_id,
            answer=response_data.answer,
        )

        session.add(response)
        await session.commit()
        await session.refresh(response)

        return response

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create response: {e!s}")


@router.get("/question/{question_id}", response_model=list[ResponseRead])
async def get_responses_by_question(
    question_id: int, session: AsyncSession = Depends(get_async_session)
):
    """
    Get all responses for a specific question.

    Only returns responses for public surveys.
    Admin endpoints provide access to private survey responses.
    """
    try:
        # First check if question exists and belongs to public survey
        question_stmt = (
            select(Question)
            .options(selectinload(Question.survey))
            .where(Question.id == question_id)
        )

        question_result = await session.execute(question_stmt)
        question = question_result.scalar_one_or_none()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        if not question.survey.is_public:
            raise HTTPException(
                status_code=403, detail="Cannot access responses for private survey"
            )

        # Query for responses
        stmt = (
            select(Response)
            .where(Response.question_id == question_id)
            .order_by(Response.created_at.desc())
        )

        result = await session.execute(stmt)
        responses = result.scalars().all()

        return responses

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch responses: {e!s}")


@router.get("/user/{user_session_id}", response_model=list[ResponseRead])
async def get_responses_by_user(
    user_session_id: str, session: AsyncSession = Depends(get_async_session)
):
    """
    Get all responses for a specific user session.

    Only returns responses for public surveys.
    """
    try:
        # Query for responses with question and survey info
        stmt = (
            select(Response)
            .join(Question)
            .join(Survey)
            .where(Response.user_session_id == user_session_id)
            .where(Survey.is_public == True)
            .order_by(Response.created_at.desc())
        )

        result = await session.execute(stmt)
        responses = result.scalars().all()

        return responses

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch user responses: {e!s}"
        )


@router.get("/survey/{survey_id}/progress/{user_session_id}")
async def get_survey_progress(
    survey_id: int,
    user_session_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get user progress for a specific survey.

    Returns completion status and answered questions.
    Only works for public surveys.
    """
    try:
        # First check if survey exists and is public
        survey_stmt = (
            select(Survey)
            .where(Survey.id == survey_id)
            .where(Survey.is_public == True)
            .where(Survey.is_active == True)
        )

        survey_result = await session.execute(survey_stmt)
        survey = survey_result.scalar_one_or_none()

        if not survey:
            raise HTTPException(
                status_code=404, detail="Survey not found or not publicly accessible"
            )

        # Get all questions for the survey
        questions_stmt = (
            select(Question)
            .where(Question.survey_id == survey_id)
            .order_by(Question.order)
        )

        questions_result = await session.execute(questions_stmt)
        questions = questions_result.scalars().all()

        # Get user responses for this survey
        responses_stmt = (
            select(Response)
            .join(Question)
            .where(Question.survey_id == survey_id)
            .where(Response.user_session_id == user_session_id)
        )

        responses_result = await session.execute(responses_stmt)
        responses = responses_result.scalars().all()

        # Calculate progress
        answered_questions = [r.question_id for r in responses]
        total_questions = len(questions)
        answered_count = len(answered_questions)

        # Find next unanswered question
        next_question_id = None
        for question in questions:
            if question.id not in answered_questions:
                next_question_id = question.id
                break

        return {
            "survey_id": survey_id,
            "user_session_id": user_session_id,
            "total_questions": total_questions,
            "answered_questions": answered_count,
            "completion_percentage": (answered_count / total_questions * 100)
            if total_questions > 0
            else 0,
            "is_completed": answered_count == total_questions,
            "next_question_id": next_question_id,
            "answered_question_ids": answered_questions,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch survey progress: {e!s}"
        )


@router.post("/validate-before-save")
async def validate_response_before_save(
    question_id: int,
    answer: dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
):
    """
    Validate response data before saving.

    This endpoint can be used to validate response data
    before making the actual save request.
    """
    try:
        # Get question info
        question_stmt = select(Question).where(Question.id == question_id)

        question_result = await session.execute(question_stmt)
        question = question_result.scalar_one_or_none()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Validate response data
        is_valid = _validate_response_data(question, answer)

        return {
            "question_id": question_id,
            "is_valid": is_valid,
            "question_type": question.question_type,
            "is_required": question.is_required,
            "validation_message": _get_validation_message(question, answer)
            if not is_valid
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to validate response: {e!s}"
        )


def _validate_response_data(question: Question, answer: dict[str, Any]) -> bool:
    """
    Validate response data based on question type.

    Args:
        question: The question object
        answer: The response data

    Returns:
        bool: True if valid, False otherwise
    """
    from models.question import QuestionType

    question_type = question.question_type

    # Check if answer is provided for required questions
    if question.is_required and not answer.get("value"):
        return False

    # Type-specific validation
    if question_type == QuestionType.RATING_1_10:
        value = answer.get("value")
        if not isinstance(value, (int, float)) or not (1 <= value <= 10):
            return False

    elif question_type == QuestionType.YES_NO:
        value = answer.get("value")
        if value not in [True, False, "yes", "no", "да", "нет"]:
            return False

    elif question_type == QuestionType.TEXT:
        value = answer.get("value")
        if not isinstance(value, str) or len(value.strip()) == 0:
            return False

    elif question_type == QuestionType.EMAIL:
        value = answer.get("value")
        if not isinstance(value, str) or "@" not in value:
            return False

    elif question_type == QuestionType.PHONE:
        value = answer.get("value")
        if not isinstance(value, str) or len(value.strip()) < 10:
            return False

    elif question_type == QuestionType.IMAGE_UPLOAD:
        value = answer.get("value")
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            return False

    return True


def _get_validation_message(question: Question, answer: dict[str, Any]) -> str:
    """
    Get validation error message for invalid response.

    Args:
        question: The question object
        answer: The response data

    Returns:
        str: Validation error message
    """
    from models.question import QuestionType

    question_type = question.question_type

    if question.is_required and not answer.get("value"):
        return "This question is required"

    if question_type == QuestionType.RATING_1_10:
        return "Rating must be between 1 and 10"
    elif question_type == QuestionType.YES_NO:
        return "Please select Yes or No"
    elif question_type == QuestionType.TEXT:
        return "Please provide a text response"
    elif question_type == QuestionType.EMAIL:
        return "Please provide a valid email address"
    elif question_type == QuestionType.PHONE:
        return "Please provide a valid phone number"
    elif question_type == QuestionType.IMAGE_UPLOAD:
        return "Please provide a valid image URL"

    return "Invalid response data"
