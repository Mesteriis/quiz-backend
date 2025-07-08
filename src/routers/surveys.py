"""
Survey API router for the Quiz App.

This module contains FastAPI endpoints for managing surveys,
including public and private surveys with access token support.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from models.question import Question, QuestionRead
from models.survey import (
    Survey,
    SurveyCreate,
    SurveyRead,
    SurveyReadWithQuestions,
    SurveyUpdate,
)
from models.user import User
from repositories.dependencies import (
    get_survey_repository,
    get_question_repository,
    get_user_repository,
)
from repositories.survey import SurveyRepository
from repositories.question import QuestionRepository
from repositories.user import UserRepository
from routers.auth import get_current_user

router = APIRouter()
security = HTTPBearer()


@router.get("/active", response_model=list[dict])
async def get_active_public_surveys(
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    skip: int = Query(0, ge=0, description="Skip surveys"),
    limit: int = Query(10, ge=1, le=100, description="Limit results"),
):
    """
    Get active public surveys.

    Returns a list of active public surveys that users can participate in.
    Private surveys are not included in this endpoint.
    """
    try:
        # Query for active public surveys using repository method
        surveys = await survey_repo.get_active_public_surveys(skip=skip, limit=limit)

        # Convert to dict with questions count
        survey_list = []
        for survey in surveys:
            # Get questions for this survey
            questions = await question_repo.get_by_survey_id(survey.id)

            survey_dict = {
                "id": survey.id,
                "title": survey.title,
                "description": survey.description,
                "is_active": survey.is_active,
                "is_public": survey.is_public,
                "telegram_notifications": survey.telegram_notifications,
                "access_token": survey.access_token,
                "created_at": survey.created_at.isoformat()
                if survey.created_at
                else None,
                "updated_at": survey.updated_at.isoformat()
                if survey.updated_at
                else None,
                "questions": [QuestionRead.model_validate(q) for q in questions],
                "questions_count": len(questions),
            }
            survey_list.append(survey_dict)

        return survey_list

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch active surveys: {e!s}"
        )


@router.get("/{survey_id}", response_model=SurveyReadWithQuestions)
async def get_survey_by_id(
    survey_id: int,
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
):
    """
    Get a specific public survey by ID.

    Returns the survey with all questions. Only works for public surveys.
    For private surveys, use the access token endpoint.
    """
    try:
        # Get survey using repository
        survey = await survey_repo.get(survey_id)

        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        # Check if survey is public and active
        if not survey.is_public or not survey.is_active:
            raise HTTPException(
                status_code=404, detail="Survey not found or not publicly accessible"
            )

        # Get questions for this survey
        questions = await question_repo.get_by_survey_id(survey_id)

        # Sort questions by order
        questions.sort(key=lambda q: q.order)

        # Create response with questions
        survey_with_questions = SurveyReadWithQuestions(
            **SurveyRead.model_validate(survey).model_dump(),
            questions=[QuestionRead.model_validate(q).model_dump() for q in questions],
        )

        return survey_with_questions

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch survey: {e!s}")


@router.get("/private/{access_token}", response_model=SurveyReadWithQuestions)
async def get_private_survey(
    access_token: str,
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
):
    """
    Get a private survey by access token.

    Returns the survey with all questions using the unique access token.
    Works for both public and private surveys.
    """
    try:
        # Get survey by access token using repository
        survey = await survey_repo.get_by_access_token(access_token)

        if not survey or not survey.is_active:
            raise HTTPException(
                status_code=404, detail="Survey not found or access token invalid"
            )

        # Get questions for this survey
        questions = await question_repo.get_by_survey_id(survey.id)

        # Sort questions by order
        questions.sort(key=lambda q: q.order)

        # Create response with questions
        survey_with_questions = SurveyReadWithQuestions(
            **SurveyRead.model_validate(survey).model_dump(),
            questions=[QuestionRead.model_validate(q).model_dump() for q in questions],
        )

        return survey_with_questions

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch private survey: {e!s}"
        )


@router.get("/{survey_id}/questions", response_model=list[QuestionRead])
async def get_survey_questions(
    survey_id: int,
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
):
    """
    Get all questions for a specific public survey.

    Returns questions sorted by order.
    """
    try:
        # Check if survey exists and is public
        survey = await survey_repo.get(survey_id)

        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        if not survey.is_public or not survey.is_active:
            raise HTTPException(
                status_code=404, detail="Survey not found or not publicly accessible"
            )

        # Get questions for this survey
        questions = await question_repo.get_by_survey_id(survey_id)

        # Sort questions by order
        questions.sort(key=lambda q: q.order)

        return [QuestionRead.model_validate(q) for q in questions]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch survey questions: {e!s}"
        )


@router.get("/private/{access_token}/questions", response_model=list[QuestionRead])
async def get_private_survey_questions(
    access_token: str,
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
):
    """
    Get all questions for a private survey by access token.

    Returns questions sorted by order for surveys accessed via token.
    """
    try:
        # Get survey by access token
        survey = await survey_repo.get_by_access_token(access_token)

        if not survey or not survey.is_active:
            raise HTTPException(
                status_code=404, detail="Survey not found or access token invalid"
            )

        # Get questions for this survey
        questions = await question_repo.get_by_survey_id(survey.id)

        # Sort questions by order
        questions.sort(key=lambda q: q.order)

        return [QuestionRead.model_validate(q) for q in questions]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch private survey questions: {e!s}"
        )


@router.get("/{survey_id}/stats")
async def get_survey_stats(
    survey_id: int,
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Get survey statistics.

    Returns basic stats about survey responses and completion.
    """
    try:
        # Check if survey exists and is public
        survey = await survey_repo.get(survey_id)

        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        if not survey.is_public:
            raise HTTPException(
                status_code=404, detail="Survey not found or not publicly accessible"
            )

        # Get survey statistics using repository method
        stats = await survey_repo.get_survey_stats(survey_id)

        return {
            "survey_id": survey_id,
            "survey_title": survey.title,
            "is_active": survey.is_active,
            "is_public": survey.is_public,
            "created_at": survey.created_at.isoformat() if survey.created_at else None,
            **stats,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch survey stats: {e!s}"
        )


@router.post("/", response_model=SurveyRead, status_code=201)
async def create_survey(
    survey_data: SurveyCreate,
    current_user: User = Depends(get_current_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Create a new survey (authenticated users only).

    Creates a new survey with the provided data.
    Only authenticated users can create surveys.
    """
    try:
        # Валидация данных
        if not survey_data.title or len(survey_data.title.strip()) == 0:
            raise HTTPException(status_code=422, detail="Survey title is required")

        if len(survey_data.title) > 200:
            raise HTTPException(
                status_code=422, detail="Survey title too long (max 200 characters)"
            )

        # Set created_by to current user
        survey_data.created_by = current_user.id

        # Генерируем access_token для приватных опросов
        if not survey_data.is_public and not survey_data.access_token:
            import secrets

            survey_data.access_token = secrets.token_urlsafe(32)

        # Create survey using repository
        survey = await survey_repo.create(obj_in=survey_data)

        return SurveyRead.model_validate(survey)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create survey: {e!s}")


@router.put("/{survey_id}", response_model=SurveyRead)
async def update_survey(
    survey_id: int,
    survey_data: SurveyUpdate,
    current_user: User = Depends(get_current_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Update a survey (authenticated users only).

    Updates survey with new data.
    Users can only update their own surveys unless they're admin.
    """
    try:
        # Get existing survey
        survey = await survey_repo.get(survey_id)

        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        # Check permissions (admin can edit any survey, others only their own)
        if not current_user.is_admin and survey.created_by != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this survey"
            )

        # Update survey using repository
        updated_survey = await survey_repo.update(db_obj=survey, obj_in=survey_data)

        return SurveyRead.model_validate(updated_survey)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update survey: {e!s}")


@router.delete("/{survey_id}", status_code=204)
async def delete_survey(
    survey_id: int,
    current_user: User = Depends(get_current_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Delete a survey (authenticated users only).

    Deletes the survey and all associated questions and responses.
    Users can only delete their own surveys unless they're admin.
    """
    try:
        # Get existing survey
        survey = await survey_repo.get(survey_id)

        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        # Check permissions (admin can delete any survey, others only their own)
        if not current_user.is_admin and survey.created_by != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this survey"
            )

        # Delete survey using repository
        await survey_repo.remove(survey_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete survey: {e!s}")
