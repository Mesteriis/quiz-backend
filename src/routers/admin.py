"""
Admin API router for the Quiz App.

This module contains FastAPI endpoints for administrative functionality
including survey management, user management, and system statistics.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, text

from models.question import Question
from models.response import Response
from models.survey import Survey
from models.user import User
from schemas.survey import SurveyCreate, SurveyRead, SurveyUpdate
from schemas.user import UserResponse
from repositories.dependencies import get_user_repository, get_survey_repository
from repositories.user import UserRepository
from repositories.survey import SurveyRepository
from routers.auth import get_admin_user
from schemas.admin import SuccessResponse

router = APIRouter()


@router.get("/dashboard", response_model=dict)
async def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    user_repo: UserRepository = Depends(get_user_repository),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Get admin dashboard statistics.

    Returns overview of surveys, questions, responses, and users.
    """
    try:
        # Get counts using SQL for better performance
        surveys_count = await survey_repo.db.execute(select(func.count(Survey.id)))
        questions_count = await survey_repo.db.execute(select(func.count(Question.id)))
        responses_count = await survey_repo.db.execute(select(func.count(Response.id)))
        users_count = await user_repo.db.execute(select(func.count(User.id)))

        # Get recent surveys
        recent_surveys = await survey_repo.get_multi(skip=0, limit=5)

        # Get recent users
        recent_users = await user_repo.get_multi(skip=0, limit=5)

        return {
            "statistics": {
                "surveys_total": surveys_count.scalar(),
                "questions_total": questions_count.scalar(),
                "responses_total": responses_count.scalar(),
                "users_total": users_count.scalar(),
            },
            "recent_surveys": [
                {
                    "id": survey.id,
                    "title": survey.title,
                    "is_active": survey.is_active,
                    "is_public": survey.is_public,
                    "created_at": survey.created_at.isoformat(),
                }
                for survey in recent_surveys
            ],
            "recent_users": [
                {
                    "id": user.id,
                    "display_name": user.display_name
                    or user.username
                    or f"User {user.id}",
                    "is_telegram_user": user.telegram_id is not None,
                    "created_at": user.created_at.isoformat(),
                }
                for user in recent_users
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {e!s}",
        )


@router.get("/surveys", response_model=list[SurveyRead])
async def get_all_surveys(
    skip: int = 0,
    limit: int = 100,
    include_private: bool = True,
    admin_user: User = Depends(get_admin_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Get all surveys including private ones (admin only).

    Args:
        skip: Number of surveys to skip
        limit: Maximum number of surveys to return
        include_private: Whether to include private surveys
        admin_user: Current admin user
        survey_repo: Survey repository

    Returns:
        List of surveys
    """
    try:
        if include_private:
            # Get all surveys
            surveys = await survey_repo.get_multi(skip=skip, limit=limit)
        else:
            # Get only public surveys - use raw query for complex filtering
            query = (
                select(Survey)
                .where(Survey.is_public == True)
                .offset(skip)
                .limit(limit)
                .order_by(Survey.created_at.desc())
            )
            result = await survey_repo.db.execute(query)
            surveys = result.scalars().all()

        return [SurveyRead.model_validate(survey) for survey in surveys]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get surveys: {e!s}",
        )


@router.post("/surveys", response_model=SurveyRead)
async def create_survey(
    survey_data: SurveyCreate,
    admin_user: User = Depends(get_admin_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Create a new survey (admin only).

    Args:
        survey_data: Survey creation data
        admin_user: Current admin user
        survey_repo: Survey repository

    Returns:
        Created survey
    """
    try:
        survey = await survey_repo.create(obj_in=survey_data)
        return SurveyRead.model_validate(survey)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create survey: {e!s}",
        )


@router.put("/surveys/{survey_id}", response_model=SurveyRead)
async def update_survey(
    survey_id: int,
    survey_data: SurveyUpdate,
    admin_user: User = Depends(get_admin_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Update a survey (admin only).

    Args:
        survey_id: Survey ID
        survey_data: Survey update data
        admin_user: Current admin user
        survey_repo: Survey repository

    Returns:
        Updated survey
    """
    try:
        survey = await survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
            )

        updated_survey = await survey_repo.update(db_obj=survey, obj_in=survey_data)
        return SurveyRead.model_validate(updated_survey)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update survey: {e!s}",
        )


@router.delete("/surveys/{survey_id}", response_model=SuccessResponse)
async def delete_survey(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Delete a survey (admin only).

    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        survey_repo: Survey repository

    Returns:
        Success response
    """
    try:
        survey = await survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
            )

        await survey_repo.remove(survey_id)

        return SuccessResponse(
            success=True,
            message=f"Survey '{survey.title}' deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete survey: {e!s}",
        )


@router.get("/surveys/{survey_id}/responses", response_model=list[dict])
async def get_survey_responses(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Get all responses for a survey (admin only).

    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        survey_repo: Survey repository

    Returns:
        List of responses
    """
    try:
        # Check if survey exists
        survey = await survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
            )

        # Simple SQLAlchemy query instead of raw SQL
        query = (
            select(
                Response.id.label("response_id"),
                Response.answer,
                Response.user_session_id,
                Response.created_at,
                Question.id.label("question_id"),
                Question.title.label("question_title"),
                Question.question_type,
                Question.order.label("question_order"),
                User.id.label("user_id"),
                User.display_name.label("user_display_name"),
                User.username.label("user_username"),
                User.telegram_id,
            )
            .select_from(Response)
            .join(Question, Response.question_id == Question.id)
            .outerjoin(User, Response.user_id == User.id)
            .where(Question.survey_id == survey_id)
            .order_by(Question.order, Response.created_at.desc())
        )

        result = await survey_repo.db.execute(query)
        responses_raw = result.all()

        # Return simple list of responses
        responses_list = []
        for row in responses_raw:
            response_data = {
                "id": row.response_id,
                "question_id": row.question_id,
                "question_title": row.question_title,
                "question_type": row.question_type,
                "question_order": row.question_order,
                "answer": row.answer,
                "user_session_id": row.user_session_id,
                "created_at": row.created_at.isoformat(),
                "user_id": row.user_id,
                "user_display_name": row.user_display_name,
                "username": row.user_username,
                "telegram_id": row.telegram_id,
            }
            responses_list.append(response_data)

        # Sort by question order and creation date
        responses_list.sort(key=lambda x: (x["question_order"], x["created_at"]))

        return responses_list

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get survey responses: {e!s}",
        )


@router.get("/surveys/{survey_id}/analytics", response_model=dict)
async def get_survey_analytics(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Get survey analytics (admin only).

    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        survey_repo: Survey repository

    Returns:
        Survey analytics data
    """
    try:
        # Check if survey exists
        survey = await survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
            )

        # Get analytics using SQLAlchemy query
        analytics_query = (
            select(
                func.count(func.distinct(Response.user_session_id)).label(
                    "unique_respondents"
                ),
                func.count(Response.id).label("total_responses"),
                func.count(func.distinct(Response.user_id)).label(
                    "authenticated_users"
                ),
                func.count(func.distinct(Question.id)).label("total_questions"),
                func.min(Response.created_at).label("first_response"),
                func.max(Response.created_at).label("last_response"),
            )
            .select_from(Response)
            .join(Question, Response.question_id == Question.id)
            .where(Question.survey_id == survey_id)
        )

        result = await survey_repo.db.execute(analytics_query)
        analytics_row = result.first()

        # Calculate completion rate - simplified version
        started_query = (
            select(func.count(func.distinct(Response.user_session_id)))
            .select_from(Response)
            .join(Question, Response.question_id == Question.id)
            .where(Question.survey_id == survey_id)
        )
        started_result = await survey_repo.db.execute(started_query)
        started_count = started_result.scalar() or 0

        # Get total questions count
        questions_query = select(func.count(Question.id)).where(
            Question.survey_id == survey_id
        )
        questions_result = await survey_repo.db.execute(questions_query)
        total_questions_count = questions_result.scalar() or 0

        # For now, assume 100% completion rate if there are responses
        # TODO: Implement proper completion rate calculation
        completion_rate = (
            100.0 if started_count > 0 and total_questions_count > 0 else 0.0
        )

        return {
            "survey_id": survey_id,
            "survey_title": survey.title,
            "unique_users": analytics_row.unique_respondents or 0,
            "total_responses": analytics_row.total_responses or 0,
            "authenticated_users": analytics_row.authenticated_users or 0,
            "total_questions": analytics_row.total_questions or 0,
            "completion_rate": completion_rate,
            "questions_analytics": [],  # Add empty list for compatibility
            "first_response": analytics_row.first_response.isoformat()
            if analytics_row.first_response
            else None,
            "last_response": analytics_row.last_response.isoformat()
            if analytics_row.last_response
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get survey analytics: {e!s}",
        )


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Get all users (admin only).

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        search: Search term for filtering users
        admin_user: Current admin user
        user_repo: User repository

    Returns:
        List of users
    """
    try:
        if search:
            users = await user_repo.search_users(search, skip=skip, limit=limit)
        else:
            users = await user_repo.get_multi(skip=skip, limit=limit)

        return [UserResponse.model_validate(user) for user in users]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {e!s}",
        )


@router.put("/users/{user_id}/admin", response_model=SuccessResponse)
async def toggle_user_admin(
    user_id: int,
    make_admin: bool,
    admin_user: User = Depends(get_admin_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Toggle user admin status (admin only).

    Args:
        user_id: User ID
        make_admin: Whether to make user admin
        admin_user: Current admin user
        user_repo: User repository

    Returns:
        Success response
    """
    try:
        user = await user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update admin status
        user.is_admin = make_admin
        await user_repo.db.commit()
        await user_repo.db.refresh(user)

        action = "granted" if make_admin else "revoked"
        return SuccessResponse(
            success=True,
            message=f"Admin privileges {action} for user {user.username or user.id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user admin status: {e!s}",
        )


@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Delete a user (admin only).

    Args:
        user_id: User ID
        admin_user: Current admin user
        user_repo: User repository

    Returns:
        Success response
    """
    try:
        user = await user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Prevent admin from deleting themselves
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        await user_repo.remove(user_id)

        return SuccessResponse(
            success=True,
            message=f"User {user.username or user.id} deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {e!s}",
        )


@router.get("/system/health", response_model=dict)
async def system_health(
    admin_user: User = Depends(get_admin_user),
    user_repo: UserRepository = Depends(get_user_repository),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Get system health information (admin only).

    Args:
        admin_user: Current admin user
        user_repo: User repository
        survey_repo: Survey repository

    Returns:
        System health status
    """
    try:
        # Test database connections
        users_count = await user_repo.db.execute(select(func.count(User.id)))
        surveys_count = await survey_repo.db.execute(select(func.count(Survey.id)))

        return {
            "status": "healthy",
            "database": "connected",
            "users_count": users_count.scalar(),
            "surveys_count": surveys_count.scalar(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
