"""
Admin API router for the Quiz App.

This module contains FastAPI endpoints for administrative functionality
including survey management, user management, and system statistics.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from database import get_async_session
from models.survey import Survey, SurveyCreate, SurveyUpdate, SurveyRead
from models.question import Question, QuestionCreate, QuestionUpdate, QuestionRead
from models.response import Response, ResponseSummary
from models.user import User, UserResponse
from models.user_data import UserData
from routers.auth import get_admin_user
from schemas.admin import SuccessResponse


router = APIRouter()


@router.get("/dashboard", response_model=dict)
async def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get admin dashboard statistics.
    
    Returns overview of surveys, questions, responses, and users.
    """
    try:
        # Get counts
        surveys_count = await session.execute(select(func.count(Survey.id)))
        questions_count = await session.execute(select(func.count(Question.id)))
        responses_count = await session.execute(select(func.count(Response.id)))
        users_count = await session.execute(select(func.count(User.id)))
        
        # Get recent surveys
        recent_surveys = await session.execute(
            select(Survey).order_by(Survey.created_at.desc()).limit(5)
        )
        
        # Get recent users
        recent_users = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(5)
        )
        
        return {
            "statistics": {
                "surveys_total": surveys_count.scalar(),
                "questions_total": questions_count.scalar(),
                "responses_total": responses_count.scalar(),
                "users_total": users_count.scalar()
            },
            "recent_surveys": [
                {
                    "id": survey.id,
                    "title": survey.title,
                    "is_active": survey.is_active,
                    "is_public": survey.is_public,
                    "created_at": survey.created_at.isoformat()
                } for survey in recent_surveys.scalars().all()
            ],
            "recent_users": [
                {
                    "id": user.id,
                    "display_name": user.get_display_name(),
                    "is_telegram_user": user.is_telegram_user(),
                    "created_at": user.created_at.isoformat()
                } for user in recent_users.scalars().all()
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/surveys", response_model=List[SurveyRead])
async def get_all_surveys(
    skip: int = 0,
    limit: int = 100,
    include_private: bool = True,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all surveys including private ones (admin only).
    
    Args:
        skip: Number of surveys to skip
        limit: Maximum number of surveys to return
        include_private: Whether to include private surveys
        admin_user: Current admin user
        session: Database session
        
    Returns:
        List of surveys
    """
    try:
        query = select(Survey)
        
        if not include_private:
            query = query.where(Survey.is_public == True)
        
        query = query.offset(skip).limit(limit).order_by(Survey.created_at.desc())
        
        result = await session.execute(query)
        surveys = result.scalars().all()
        
        return [SurveyRead.from_orm(survey) for survey in surveys]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get surveys: {str(e)}"
        )


@router.post("/surveys", response_model=SurveyRead)
async def create_survey(
    survey_data: SurveyCreate,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new survey (admin only).
    
    Args:
        survey_data: Survey creation data
        admin_user: Current admin user
        session: Database session
        
    Returns:
        Created survey
    """
    try:
        survey = Survey(**survey_data.dict())
        session.add(survey)
        await session.commit()
        await session.refresh(survey)
        
        return SurveyRead.from_orm(survey)
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create survey: {str(e)}"
        )


@router.put("/surveys/{survey_id}", response_model=SurveyRead)
async def update_survey(
    survey_id: int,
    survey_data: SurveyUpdate,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update a survey (admin only).
    
    Args:
        survey_id: Survey ID
        survey_data: Survey update data
        admin_user: Current admin user
        session: Database session
        
    Returns:
        Updated survey
    """
    try:
        result = await session.execute(select(Survey).where(Survey.id == survey_id))
        survey = result.scalar_one_or_none()
        
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        # Update survey fields
        update_data = survey_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(survey, field, value)
        
        await session.commit()
        await session.refresh(survey)
        
        return SurveyRead.from_orm(survey)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update survey: {str(e)}"
        )


@router.delete("/surveys/{survey_id}", response_model=SuccessResponse)
async def delete_survey(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a survey (admin only).
    
    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        session: Database session
        
    Returns:
        Success response
    """
    try:
        result = await session.execute(select(Survey).where(Survey.id == survey_id))
        survey = result.scalar_one_or_none()
        
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        await session.delete(survey)
        await session.commit()
        
        return SuccessResponse(
            success=True,
            message=f"Survey '{survey.title}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete survey: {str(e)}"
        )


@router.get("/surveys/{survey_id}/responses", response_model=List[dict])
async def get_survey_responses(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all responses for a survey (admin only).
    
    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        session: Database session
        
    Returns:
        List of responses with user information
    """
    try:
        # Verify survey exists
        result = await session.execute(select(Survey).where(Survey.id == survey_id))
        survey = result.scalar_one_or_none()
        
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        # Get responses with user and question data
        query = text("""
            SELECT 
                r.id as response_id,
                r.answer,
                r.created_at,
                q.id as question_id,
                q.title as question_title,
                q.question_type,
                u.id as user_id,
                u.display_name as user_display_name,
                u.telegram_id,
                ud.session_id,
                ud.ip_address,
                ud.location_data
            FROM response r
            JOIN question q ON r.question_id = q.id
            LEFT JOIN user u ON r.user_id = u.id
            LEFT JOIN userdata ud ON r.user_session_id = ud.session_id
            WHERE q.survey_id = :survey_id
            ORDER BY r.created_at DESC
        """)
        
        result = await session.execute(query, {"survey_id": survey_id})
        responses = result.fetchall()
        
        # Format responses
        formatted_responses = []
        for row in responses:
            formatted_responses.append({
                "response_id": row.response_id,
                "answer": row.answer,
                "created_at": row.created_at.isoformat(),
                "question": {
                    "id": row.question_id,
                    "title": row.question_title,
                    "type": row.question_type
                },
                "user": {
                    "id": row.user_id,
                    "display_name": row.user_display_name,
                    "telegram_id": row.telegram_id
                } if row.user_id else None,
                "user_data": {
                    "session_id": row.session_id,
                    "ip_address": row.ip_address,
                    "location_data": row.location_data
                }
            })
        
        return formatted_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get survey responses: {str(e)}"
        )


@router.get("/surveys/{survey_id}/analytics", response_model=dict)
async def get_survey_analytics(
    survey_id: int,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get analytics for a survey (admin only).
    
    Args:
        survey_id: Survey ID
        admin_user: Current admin user
        session: Database session
        
    Returns:
        Survey analytics data
    """
    try:
        # Verify survey exists
        result = await session.execute(select(Survey).where(Survey.id == survey_id))
        survey = result.scalar_one_or_none()
        
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        # Get analytics data
        analytics_query = text("""
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
        """)
        
        result = await session.execute(analytics_query, {"survey_id": survey_id})
        analytics = result.fetchone()
        
        # Get completion rate
        completion_query = text("""
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
        """)
        
        completion_result = await session.execute(completion_query, {"survey_id": survey_id})
        completion_data = completion_result.fetchone()
        
        return {
            "survey_id": survey_id,
            "survey_title": survey.title,
            "analytics": {
                "unique_respondents": analytics.unique_respondents or 0,
                "total_responses": analytics.total_responses or 0,
                "authenticated_users": analytics.authenticated_users or 0,
                "total_questions": analytics.total_questions or 0,
                "completion_rate": (
                    completion_data.completed / completion_data.started * 100 
                    if completion_data.started > 0 else 0
                ),
                "first_response": analytics.first_response.isoformat() if analytics.first_response else None,
                "last_response": analytics.last_response.isoformat() if analytics.last_response else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get survey analytics: {str(e)}"
        )


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all users (admin only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        search: Search term for filtering users
        admin_user: Current admin user
        session: Database session
        
    Returns:
        List of users
    """
    try:
        query = select(User)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.username.ilike(search_pattern)) |
                (User.email.ilike(search_pattern)) |
                (User.display_name.ilike(search_pattern)) |
                (User.telegram_username.ilike(search_pattern))
            )
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [UserResponse(**user.to_dict()) for user in users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )


@router.put("/users/{user_id}/admin", response_model=SuccessResponse)
async def toggle_user_admin(
    user_id: int,
    make_admin: bool,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Toggle user admin status (admin only).
    
    Args:
        user_id: User ID
        make_admin: Whether to make user admin
        admin_user: Current admin user
        session: Database session
        
    Returns:
        Success response
    """
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_admin = make_admin
        await session.commit()
        
        return SuccessResponse(
            success=True,
            message=f"User {user.get_display_name()} {'promoted to' if make_admin else 'demoted from'} admin"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user admin status: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a user (admin only).
    
    Args:
        user_id: User ID
        admin_user: Current admin user
        session: Database session
        
    Returns:
        Success response
    """
    try:
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        display_name = user.get_display_name()
        await session.delete(user)
        await session.commit()
        
        return SuccessResponse(
            success=True,
            message=f"User {display_name} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/system/health", response_model=dict)
async def system_health(
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get system health information (admin only).
    
    Returns:
        System health data including database status
    """
    try:
        # Test database connection
        await session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        } 