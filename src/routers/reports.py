"""
Reports API router for the Quiz App.

This module contains FastAPI endpoints for generating
PDF reports for surveys and users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models.survey import Survey
from models.user import User
from routers.auth import get_admin_user, get_current_user
from services.pdf_service import pdf_service

router = APIRouter()


@router.get("/surveys/{survey_id}/pdf")
async def generate_survey_pdf_report(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate PDF report for a survey (admin only).

    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        session: Database session

    Returns:
        PDF file as response
    """
    try:
        # Get survey data
        result = await session.execute(select(Survey).where(Survey.id == survey_id))
        survey = result.scalar_one_or_none()

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

        # Get responses data
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

        responses_result = await session.execute(
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

        # Get analytics data
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

        analytics_result = await session.execute(
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

        completion_result = await session.execute(
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
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate PDF report for a user's responses.

    Users can only generate reports for themselves, unless they are admin.

    Args:
        user_id: User ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        PDF file as response
    """
    try:
        # Check permissions
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only generate reports for your own responses",
            )

        # Get user data
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_data = user.to_dict()

        # Get user responses
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
                s.title as survey_title
            FROM response r
            JOIN question q ON r.question_id = q.id
            JOIN survey s ON q.survey_id = s.id
            WHERE r.user_id = :user_id
            ORDER BY r.created_at DESC
        """
        )

        responses_result = await session.execute(responses_query, {"user_id": user_id})
        responses_raw = responses_result.fetchall()

        user_responses = []
        for row in responses_raw:
            user_responses.append(
                {
                    "response_id": row.response_id,
                    "answer": row.answer,
                    "created_at": row.created_at.isoformat(),
                    "question": {
                        "id": row.question_id,
                        "title": row.question_title,
                        "type": row.question_type,
                    },
                    "survey": {"id": row.survey_id, "title": row.survey_title},
                }
            )

        # Generate PDF
        pdf_bytes = pdf_service.generate_user_report(user_data, user_responses)

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
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate PDF report for current user's responses.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        PDF file as response
    """
    try:
        user_data = current_user.to_dict()

        # Get user responses
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
                s.title as survey_title
            FROM response r
            JOIN question q ON r.question_id = q.id
            JOIN survey s ON q.survey_id = s.id
            WHERE r.user_id = :user_id
            ORDER BY r.created_at DESC
        """
        )

        responses_result = await session.execute(
            responses_query, {"user_id": current_user.id}
        )
        responses_raw = responses_result.fetchall()

        user_responses = []
        for row in responses_raw:
            user_responses.append(
                {
                    "response_id": row.response_id,
                    "answer": row.answer,
                    "created_at": row.created_at.isoformat(),
                    "question": {
                        "id": row.question_id,
                        "title": row.question_title,
                        "type": row.question_type,
                    },
                    "survey": {"id": row.survey_id, "title": row.survey_title},
                }
            )

        # Generate PDF
        pdf_bytes = pdf_service.generate_user_report(user_data, user_responses)

        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=my_responses_report.pdf"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate your responses PDF report: {e!s}",
        )
