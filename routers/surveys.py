"""
Survey API router for the Quiz App.

This module contains FastAPI endpoints for managing surveys,
including public and private surveys with access token support.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import get_async_session
from models import (
    Survey, SurveyCreate, SurveyUpdate, SurveyRead, SurveyReadWithQuestions,
    Question, QuestionRead
)
from schemas import ErrorResponse, SuccessResponse


router = APIRouter()


@router.get("/active", response_model=List[dict])
async def get_active_public_surveys(
    session: AsyncSession = Depends(get_async_session),
    skip: int = Query(0, ge=0, description="Skip surveys"),
    limit: int = Query(10, ge=1, le=100, description="Limit results")
):
    """
    Get active public surveys.
    
    Returns a list of active public surveys that users can participate in.
    Private surveys are not included in this endpoint.
    """
    try:
        # Query for active public surveys with questions loaded
        stmt = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.is_active == True)
            .where(Survey.is_public == True)
            .offset(skip)
            .limit(limit)
            .order_by(Survey.created_at.desc())
        )
        
        result = await session.execute(stmt)
        surveys = result.scalars().all()
        
        # Convert to dict with questions count
        survey_list = []
        for survey in surveys:
            survey_dict = {
                "id": survey.id,
                "title": survey.title,
                "description": survey.description,
                "is_active": survey.is_active,
                "is_public": survey.is_public,
                "telegram_notifications": survey.telegram_notifications,
                "access_token": survey.access_token,
                "created_at": survey.created_at.isoformat() if survey.created_at else None,
                "updated_at": survey.updated_at.isoformat() if survey.updated_at else None,
                "questions": survey.questions,
                "questions_count": len(survey.questions) if survey.questions else 0
            }
            survey_list.append(survey_dict)
        
        return survey_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch active surveys: {str(e)}"
        )


@router.get("/{survey_id}", response_model=SurveyReadWithQuestions)
async def get_survey_by_id(
    survey_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get a specific public survey by ID.
    
    Returns the survey with all questions. Only works for public surveys.
    For private surveys, use the access token endpoint.
    """
    try:
        # Query for the survey with questions
        stmt = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.id == survey_id)
            .where(Survey.is_public == True)
            .where(Survey.is_active == True)
        )
        
        result = await session.execute(stmt)
        survey = result.scalar_one_or_none()
        
        if not survey:
            raise HTTPException(
                status_code=404,
                detail="Survey not found or not publicly accessible"
            )
        
        # Sort questions by order
        survey.questions.sort(key=lambda q: q.order)
        
        return survey
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch survey: {str(e)}"
        )


@router.get("/private/{access_token}", response_model=SurveyReadWithQuestions)
async def get_private_survey(
    access_token: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get a private survey by access token.
    
    Returns the survey with all questions using the unique access token.
    Works for both public and private surveys.
    """
    try:
        # Query for the survey with questions using access token
        stmt = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.access_token == access_token)
            .where(Survey.is_active == True)
        )
        
        result = await session.execute(stmt)
        survey = result.scalar_one_or_none()
        
        if not survey:
            raise HTTPException(
                status_code=404,
                detail="Survey not found or access token invalid"
            )
        
        # Sort questions by order
        survey.questions.sort(key=lambda q: q.order)
        
        return survey
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch private survey: {str(e)}"
        )


@router.get("/{survey_id}/questions", response_model=List[QuestionRead])
async def get_survey_questions(
    survey_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all questions for a specific public survey.
    
    Returns questions ordered by their order field.
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
                status_code=404,
                detail="Survey not found or not publicly accessible"
            )
        
        # Query for questions
        stmt = (
            select(Question)
            .where(Question.survey_id == survey_id)
            .order_by(Question.order)
        )
        
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        return questions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch survey questions: {str(e)}"
        )


@router.get("/private/{access_token}/questions", response_model=List[QuestionRead])
async def get_private_survey_questions(
    access_token: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all questions for a private survey using access token.
    
    Returns questions ordered by their order field.
    Works for both public and private surveys.
    """
    try:
        # First check if survey exists using access token
        survey_stmt = (
            select(Survey)
            .where(Survey.access_token == access_token)
            .where(Survey.is_active == True)
        )
        
        survey_result = await session.execute(survey_stmt)
        survey = survey_result.scalar_one_or_none()
        
        if not survey:
            raise HTTPException(
                status_code=404,
                detail="Survey not found or access token invalid"
            )
        
        # Query for questions
        stmt = (
            select(Question)
            .where(Question.survey_id == survey.id)
            .order_by(Question.order)
        )
        
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        return questions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch private survey questions: {str(e)}"
        )


@router.get("/{survey_id}/stats")
async def get_survey_stats(
    survey_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get basic statistics for a public survey.
    
    Returns response count and completion metrics.
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
                status_code=404,
                detail="Survey not found or not publicly accessible"
            )
        
        # Get response count
        from models import Response
        response_stmt = (
            select(Response)
            .join(Question)
            .where(Question.survey_id == survey_id)
        )
        
        response_result = await session.execute(response_stmt)
        responses = response_result.scalars().all()
        
        # Get unique users count
        unique_users = len(set(r.user_session_id for r in responses))
        
        # Get questions count
        question_stmt = (
            select(Question)
            .where(Question.survey_id == survey_id)
        )
        
        question_result = await session.execute(question_stmt)
        questions = question_result.scalars().all()
        
        return {
            "survey_id": survey_id,
            "survey_title": survey.title,
            "total_responses": len(responses),
            "unique_users": unique_users,
            "total_questions": len(questions),
            "is_active": survey.is_active,
            "is_public": survey.is_public
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch survey stats: {str(e)}"
        ) 