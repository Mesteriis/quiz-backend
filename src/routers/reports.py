"""
Reports API router for the Quiz App.

This module contains FastAPI endpoints for generating
PDF reports for surveys and users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import text

from models.survey import Survey
from models.user import User
from schemas.user import UserResponse
from repositories.dependencies import get_survey_repository, get_user_repository
from repositories.survey import SurveyRepository
from repositories.user import UserRepository
from routers.auth import get_admin_user, get_current_user
from services.pdf_service import pdf_service

router = APIRouter()


@router.get("/surveys/{survey_id}/pdf")
async def generate_survey_pdf_report(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    survey_repo: SurveyRepository = Depends(get_survey_repository),
):
    """
    Generate PDF report for a survey (admin only).

    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        survey_repo: Survey repository

    Returns:
        PDF file as response
    """
    try:
        # Get survey data using repository
        survey = await survey_repo.get(survey_id)

        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
            )

        survey_data = {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "is_active": survey.is_active,
            "is_public": survey.is_public,
            "created_at": survey.created_at.isoformat(),
        }

        # Get responses data using raw SQL for complex joins
        responses_query = text(
            """
            SELECT
                r.id as response_id,
                r.answer,
                r.created_at,
                q.id as question_id,
                q.title as question_title,
                q.question_type,
                u.id as user_id,
                u.display_name as user_display_name,
                u.telegram_id
            FROM response r
            JOIN question q ON r.question_id = q.id
            LEFT JOIN user u ON r.user_id = u.id
            WHERE q.survey_id = :survey_id
            ORDER BY r.created_at DESC
        """
        )

        responses_result = await survey_repo.db.execute(
            responses_query, {"survey_id": survey_id}
        )
        responses_raw = responses_result.fetchall()

        responses_data = []
        for row in responses_raw:
            responses_data.append(
                {
                    "response_id": row.response_id,
                    "answer": row.answer,
                    "created_at": row.created_at.isoformat(),
                    "question": {
                        "id": row.question_id,
                        "title": row.question_title,
                        "type": row.question_type,
                    },
                    "user": {
                        "id": row.user_id,
                        "display_name": row.user_display_name,
                        "telegram_id": row.telegram_id,
                    }
                    if row.user_id
                    else None,
                }
            )

        # Get analytics data using raw SQL for complex aggregations
        analytics_query = text(
            """
            SELECT
                COUNT(DISTINCT r.user_session_id) as unique_respondents,
                COUNT(r.id) as total_responses,
                COUNT(DISTINCT r.user_id) as authenticated_users,
                COUNT(DISTINCT q.id) as total_questions,
                MIN(r.created_at) as first_response,
                MAX(r.created_at) as last_response
            FROM response r
            JOIN question q ON r.question_id = q.id
            WHERE q.survey_id = :survey_id
        """
        )

        analytics_result = await survey_repo.db.execute(
            analytics_query, {"survey_id": survey_id}
        )
        analytics_raw = analytics_result.fetchone()

        # Calculate completion rate
        completion_query = text(
            """
            SELECT
                COUNT(DISTINCT r.user_session_id) as started,
                COUNT(DISTINCT CASE WHEN complete_sessions.session_id IS NOT NULL THEN r.user_session_id END) as completed
            FROM response r
            JOIN question q ON r.question_id = q.id
            LEFT JOIN (
                SELECT r2.user_session_id as session_id
                FROM response r2
                JOIN question q2 ON r2.question_id = q2.id
                WHERE q2.survey_id = :survey_id
                GROUP BY r2.user_session_id
                HAVING COUNT(DISTINCT q2.id) = (
                    SELECT COUNT(id) FROM question WHERE survey_id = :survey_id
                )
            ) complete_sessions ON r.user_session_id = complete_sessions.session_id
            WHERE q.survey_id = :survey_id
        """
        )

        completion_result = await survey_repo.db.execute(
            completion_query, {"survey_id": survey_id}
        )
        completion_data = completion_result.fetchone()

        analytics_data = {
            "unique_respondents": analytics_raw.unique_respondents or 0,
            "total_responses": analytics_raw.total_responses or 0,
            "authenticated_users": analytics_raw.authenticated_users or 0,
            "total_questions": analytics_raw.total_questions or 0,
            "completion_rate": (
                completion_data.completed / completion_data.started * 100
                if completion_data.started > 0
                else 0
            ),
            "first_response": analytics_raw.first_response.isoformat()
            if analytics_raw.first_response
            else None,
            "last_response": analytics_raw.last_response.isoformat()
            if analytics_raw.last_response
            else None,
        }

        # Generate PDF
        pdf_bytes = pdf_service.generate_survey_report(
            survey_data, responses_data, analytics_data
        )

        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=survey_{survey_id}_report.pdf"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate survey PDF report: {e!s}",
        )


@router.get("/users/{user_id}/pdf")
async def generate_user_pdf_report(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Generate PDF report for a user (user can only generate for themselves unless admin).

    Args:
        user_id: User ID
        current_user: Current authenticated user
        user_repo: User repository

    Returns:
        PDF file as response
    """
    try:
        # Check permissions - users can only generate reports for themselves unless admin
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to generate report for this user",
            )

        # Get user data using repository
        user = await user_repo.get(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_data = {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "bio": user.bio,
            "is_verified": user.is_verified,
            "is_telegram_user": user.is_telegram_user,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

        # Get user responses using raw SQL
        responses_query = text(
            """
            SELECT
                r.id as response_id,
                r.answer,
                r.created_at,
                q.id as question_id,
                q.title as question_title,
                q.question_type,
                s.id as survey_id,
                s.title as survey_title,
                s.is_public
            FROM response r
            JOIN question q ON r.question_id = q.id
            JOIN survey s ON q.survey_id = s.id
            WHERE r.user_id = :user_id
            ORDER BY r.created_at DESC
        """
        )

        responses_result = await user_repo.db.execute(
            responses_query, {"user_id": user_id}
        )
        responses_raw = responses_result.fetchall()

        responses_data = []
        for row in responses_raw:
            responses_data.append(
                {
                    "response_id": row.response_id,
                    "answer": row.answer,
                    "created_at": row.created_at.isoformat(),
                    "question": {
                        "id": row.question_id,
                        "title": row.question_title,
                        "type": row.question_type,
                    },
                    "survey": {
                        "id": row.survey_id,
                        "title": row.survey_title,
                        "is_public": row.is_public,
                    },
                }
            )

        # Get user statistics
        stats_query = text(
            """
            SELECT
                COUNT(r.id) as total_responses,
                COUNT(DISTINCT s.id) as surveys_participated,
                MIN(r.created_at) as first_response,
                MAX(r.created_at) as last_response
            FROM response r
            JOIN question q ON r.question_id = q.id
            JOIN survey s ON q.survey_id = s.id
            WHERE r.user_id = :user_id
        """
        )

        stats_result = await user_repo.db.execute(stats_query, {"user_id": user_id})
        stats_raw = stats_result.fetchone()

        analytics_data = {
            "total_responses": stats_raw.total_responses or 0,
            "surveys_participated": stats_raw.surveys_participated or 0,
            "first_response": stats_raw.first_response.isoformat()
            if stats_raw.first_response
            else None,
            "last_response": stats_raw.last_response.isoformat()
            if stats_raw.last_response
            else None,
        }

        # Generate PDF
        pdf_bytes = pdf_service.generate_user_report(
            user_data, responses_data, analytics_data
        )

        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=user_{user_id}_report.pdf"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate user PDF report: {e!s}",
        )


@router.get("/my-responses/pdf")
async def generate_my_responses_pdf_report(
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Generate PDF report for current user's responses.

    Returns PDF with all responses made by the current user.
    """
    try:
        # Use the existing user report endpoint with current user ID
        return await generate_user_pdf_report(
            user_id=current_user.id,
            current_user=current_user,
            user_repo=user_repo,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate my responses PDF report: {e!s}",
        )
