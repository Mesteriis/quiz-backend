"""
User Data API router for the Quiz App.

This module contains FastAPI endpoints for collecting and managing
comprehensive user data including fingerprinting and geolocation.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_async_session
from models import (
    UserData, UserDataCreate, UserDataUpdate, UserDataRead
)
from schemas import (
    UserSessionData, BrowserFingerprint, GeolocationData, DeviceInfo,
    SuccessResponse, ErrorResponse
)


router = APIRouter()


@router.post("/", response_model=UserDataRead)
async def create_user_data(
    user_data: UserDataCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create or update user data.
    
    Collects comprehensive user information including browser fingerprint,
    device info, geolocation, and optional Telegram data.
    """
    try:
        # Check if user data already exists for this session
        existing_stmt = (
            select(UserData)
            .where(UserData.session_id == user_data.session_id)
        )
        
        existing_result = await session.execute(existing_stmt)
        existing_user = existing_result.scalar_one_or_none()
        
        if existing_user:
            # Update existing user data
            for key, value in user_data.dict(exclude_unset=True).items():
                setattr(existing_user, key, value)
            
            await session.commit()
            await session.refresh(existing_user)
            return existing_user
        else:
            # Create new user data
            # Add IP address from request
            client_ip = request.client.host if request.client else "unknown"
            user_data.ip_address = client_ip
            
            db_user_data = UserData(**user_data.dict())
            session.add(db_user_data)
            await session.commit()
            await session.refresh(db_user_data)
            
            return db_user_data
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user data: {str(e)}"
        )


@router.get("/{session_id}", response_model=UserDataRead)
async def get_user_data(
    session_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get user data by session ID.
    
    Returns comprehensive user information for the given session.
    """
    try:
        stmt = (
            select(UserData)
            .where(UserData.session_id == session_id)
        )
        
        result = await session.execute(stmt)
        user_data = result.scalar_one_or_none()
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="User data not found"
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch user data: {str(e)}"
        )


@router.put("/{session_id}", response_model=UserDataRead)
async def update_user_data(
    session_id: str,
    user_data_update: UserDataUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update existing user data.
    
    Updates user information with new data while preserving existing fields.
    """
    try:
        stmt = (
            select(UserData)
            .where(UserData.session_id == session_id)
        )
        
        result = await session.execute(stmt)
        user_data = result.scalar_one_or_none()
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="User data not found"
            )
        
        # Update fields
        update_data = user_data_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user_data, key, value)
        
        await session.commit()
        await session.refresh(user_data)
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user data: {str(e)}"
        )


@router.post("/session", response_model=UserDataRead)
async def create_session_data(
    session_data: UserSessionData,
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create user data from comprehensive session information.
    
    Processes browser fingerprint, device info, geolocation, and Telegram data
    into a structured user data record.
    """
    try:
        # Extract IP address from request
        client_ip = request.client.host if request.client else "unknown"
        
        # Convert session data to user data format
        user_data = UserDataCreate(
            session_id=session_data.session_id,
            ip_address=client_ip,
            user_agent=session_data.fingerprint.user_agent,
            referrer=session_data.referrer,
            fingerprint=_generate_fingerprint_string(session_data.fingerprint),
            geolocation=session_data.geolocation.dict() if session_data.geolocation else None,
            device_info=session_data.device_info.dict(),
            browser_info=_extract_browser_info(session_data.fingerprint),
            telegram_user_id=session_data.telegram_data.user_id if session_data.telegram_data else None,
            telegram_username=session_data.telegram_data.username if session_data.telegram_data else None,
            telegram_first_name=session_data.telegram_data.first_name if session_data.telegram_data else None,
            telegram_last_name=session_data.telegram_data.last_name if session_data.telegram_data else None,
            telegram_language_code=session_data.telegram_data.language_code if session_data.telegram_data else None,
            telegram_photo_url=session_data.telegram_data.photo_url if session_data.telegram_data else None,
        )
        
        # Check if user data already exists
        existing_stmt = (
            select(UserData)
            .where(UserData.session_id == session_data.session_id)
        )
        
        existing_result = await session.execute(existing_stmt)
        existing_user = existing_result.scalar_one_or_none()
        
        if existing_user:
            # Update existing user data
            for key, value in user_data.dict(exclude_unset=True).items():
                setattr(existing_user, key, value)
            
            await session.commit()
            await session.refresh(existing_user)
            return existing_user
        else:
            # Create new user data
            db_user_data = UserData(**user_data.dict())
            session.add(db_user_data)
            await session.commit()
            await session.refresh(db_user_data)
            
            return db_user_data
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session data: {str(e)}"
        )


@router.get("/", response_model=List[UserDataRead])
async def list_user_data(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session)
):
    """
    List all user data (admin endpoint).
    
    Returns paginated list of all user data records.
    This endpoint should be protected by admin authentication.
    """
    try:
        stmt = (
            select(UserData)
            .offset(skip)
            .limit(limit)
            .order_by(UserData.created_at.desc())
        )
        
        result = await session.execute(stmt)
        user_data_list = result.scalars().all()
        
        return user_data_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch user data list: {str(e)}"
        )


@router.delete("/{session_id}", response_model=SuccessResponse)
async def delete_user_data(
    session_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete user data by session ID (admin endpoint).
    
    Removes all user data for the given session.
    This endpoint should be protected by admin authentication.
    """
    try:
        stmt = (
            select(UserData)
            .where(UserData.session_id == session_id)
        )
        
        result = await session.execute(stmt)
        user_data = result.scalar_one_or_none()
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="User data not found"
            )
        
        await session.delete(user_data)
        await session.commit()
        
        return SuccessResponse(
            message="User data deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user data: {str(e)}"
        )


def _generate_fingerprint_string(fingerprint: BrowserFingerprint) -> str:
    """
    Generate a unique fingerprint string from browser data.
    
    Args:
        fingerprint: Browser fingerprint data
        
    Returns:
        str: Unique fingerprint string
    """
    import hashlib
    
    fingerprint_data = [
        fingerprint.user_agent,
        fingerprint.screen_resolution,
        str(fingerprint.color_depth),
        fingerprint.timezone,
        fingerprint.language,
        fingerprint.platform,
        fingerprint.canvas_fingerprint or "",
        fingerprint.webgl_fingerprint or "",
        fingerprint.audio_fingerprint or "",
        ",".join(sorted(fingerprint.fonts)),
        ",".join(sorted(fingerprint.plugins))
    ]
    
    combined = "|".join(fingerprint_data)
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def _extract_browser_info(fingerprint: BrowserFingerprint) -> dict:
    """
    Extract browser information from fingerprint data.
    
    Args:
        fingerprint: Browser fingerprint data
        
    Returns:
        dict: Browser information
    """
    return {
        "user_agent": fingerprint.user_agent,
        "language": fingerprint.language,
        "platform": fingerprint.platform,
        "timezone": fingerprint.timezone,
        "screen_resolution": fingerprint.screen_resolution,
        "color_depth": fingerprint.color_depth,
        "fonts_count": len(fingerprint.fonts),
        "plugins_count": len(fingerprint.plugins),
        "has_canvas_support": bool(fingerprint.canvas_fingerprint),
        "has_webgl_support": bool(fingerprint.webgl_fingerprint),
        "has_audio_support": bool(fingerprint.audio_fingerprint)
    } 