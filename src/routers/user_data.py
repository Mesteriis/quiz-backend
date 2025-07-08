"""
User Data API router for the Quiz App.

This module contains FastAPI endpoints for collecting and managing
comprehensive user data including fingerprinting and geolocation.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from models.user_data import UserData, UserDataCreate, UserDataRead, UserDataUpdate
from repositories.dependencies import get_user_data_repository
from repositories.user_data import UserDataRepository
from schemas.validation import BrowserFingerprint, UserSessionData
from schemas.admin import SuccessResponse

router = APIRouter()


@router.post("/", response_model=UserDataRead)
async def create_user_data(
    user_data: UserDataCreate,
    request: Request,
    user_data_repo: UserDataRepository = Depends(get_user_data_repository),
):
    """
    Create or update user data.

    Collects comprehensive user information including browser fingerprint,
    device info, geolocation, and optional Telegram data.
    """
    try:
        # Check if user data already exists for this session
        existing_user = await user_data_repo.get_by_session_id(user_data.session_id)

        if existing_user:
            # Update existing user data
            updated_user = await user_data_repo.update(
                db_obj=existing_user, obj_in=user_data
            )
            return UserDataRead.model_validate(updated_user)
        else:
            # Create new user data
            # Add IP address from request
            client_ip = request.client.host if request.client else "unknown"
            user_data.ip_address = client_ip

            new_user_data = await user_data_repo.create(obj_in=user_data)
            return UserDataRead.model_validate(new_user_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create user data: {e!s}"
        )


@router.get("/{session_id}", response_model=UserDataRead)
async def get_user_data(
    session_id: str,
    user_data_repo: UserDataRepository = Depends(get_user_data_repository),
):
    """
    Get user data by session ID.

    Returns comprehensive user information for the given session.
    """
    try:
        user_data = await user_data_repo.get_by_session_id(session_id)

        if not user_data:
            raise HTTPException(status_code=404, detail="User data not found")

        return UserDataRead.model_validate(user_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user data: {e!s}")


@router.put("/{session_id}", response_model=UserDataRead)
async def update_user_data(
    session_id: str,
    user_data_update: UserDataUpdate,
    user_data_repo: UserDataRepository = Depends(get_user_data_repository),
):
    """
    Update existing user data.

    Updates user information with new data while preserving existing fields.
    """
    try:
        user_data = await user_data_repo.get_by_session_id(session_id)

        if not user_data:
            raise HTTPException(status_code=404, detail="User data not found")

        # Update user data using repository
        updated_user_data = await user_data_repo.update(
            db_obj=user_data, obj_in=user_data_update
        )

        return UserDataRead.model_validate(updated_user_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update user data: {e!s}"
        )


@router.post("/session", response_model=UserDataRead)
async def create_session_data(
    session_data: UserSessionData,
    request: Request,
    user_data_repo: UserDataRepository = Depends(get_user_data_repository),
):
    """
    Create user data from comprehensive session information.

    Processes browser fingerprint, device info, geolocation, and Telegram data
    into a structured user data record.
    """
    try:
        # Extract IP address from request
        client_ip = request.client.host if request.client else "unknown"

        # Extract Telegram data
        tg_id = None
        telegram_data = None

        if session_data.telegram_data:
            tg_id = session_data.telegram_data.user_id
            # Store all Telegram data in JSON format
            telegram_data = session_data.telegram_data.model_dump()

        # Convert session data to user data format
        user_data = UserDataCreate(
            session_id=session_data.session_id,
            ip_address=client_ip,
            user_agent=session_data.fingerprint.user_agent,
            referrer=session_data.referrer,
            entry_page=session_data.entry_page,
            fingerprint=_generate_fingerprint_string(session_data.fingerprint),
            geolocation=session_data.geolocation.model_dump()
            if session_data.geolocation
            else None,
            device_info=session_data.device_info.model_dump(),
            browser_info=_extract_browser_info(session_data.fingerprint),
            # New Telegram data structure
            tg_id=tg_id,
            telegram_data=telegram_data,
        )

        # Check if user data already exists
        existing_user = await user_data_repo.get_by_session_id(session_data.session_id)

        if existing_user:
            # Update existing user data
            updated_user = await user_data_repo.update(
                db_obj=existing_user, obj_in=user_data
            )
            return UserDataRead.model_validate(updated_user)
        else:
            # Create new user data
            new_user_data = await user_data_repo.create(obj_in=user_data)
            return UserDataRead.model_validate(new_user_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create session data: {e!s}"
        )


@router.get("/", response_model=list[UserDataRead])
async def list_user_data(
    skip: int = 0,
    limit: int = 100,
    user_data_repo: UserDataRepository = Depends(get_user_data_repository),
):
    """
    Get list of all user data with pagination.

    Returns paginated list of user data records.
    """
    try:
        user_data_list = await user_data_repo.get_multi(skip=skip, limit=limit)
        return [UserDataRead.model_validate(user_data) for user_data in user_data_list]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list user data: {e!s}")


@router.delete("/{session_id}", response_model=SuccessResponse)
async def delete_user_data(
    session_id: str,
    user_data_repo: UserDataRepository = Depends(get_user_data_repository),
):
    """
    Delete user data by session ID.

    Permanently removes user data record from the database.
    """
    try:
        user_data = await user_data_repo.get_by_session_id(session_id)

        if not user_data:
            raise HTTPException(status_code=404, detail="User data not found")

        await user_data_repo.remove(user_data.id)

        return SuccessResponse(
            success=True,
            message=f"User data for session {session_id} deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete user data: {e!s}"
        )


def _generate_fingerprint_string(fingerprint: BrowserFingerprint) -> str:
    """
    Generate a unique fingerprint string from browser fingerprint data.

    Args:
        fingerprint: Browser fingerprint data

    Returns:
        Fingerprint string
    """
    components = [
        fingerprint.user_agent or "",
        fingerprint.language or "",
        fingerprint.timezone or "",
        fingerprint.screen_resolution or "",
        str(fingerprint.color_depth) if fingerprint.color_depth else "",
        fingerprint.platform or "",
        fingerprint.canvas_fingerprint or "",
        fingerprint.webgl_fingerprint or "",
        fingerprint.audio_fingerprint or "",
        ",".join(fingerprint.fonts or []),
        ",".join(fingerprint.plugins or []),
        str(fingerprint.screen_width) if fingerprint.screen_width else "",
        str(fingerprint.screen_height) if fingerprint.screen_height else "",
    ]

    # Create a hash of the components
    import hashlib

    fingerprint_string = "|".join(str(comp) for comp in components)
    return hashlib.md5(fingerprint_string.encode()).hexdigest()


def _extract_browser_info(fingerprint: BrowserFingerprint) -> dict:
    """
    Extract structured browser information from fingerprint data.

    Args:
        fingerprint: Browser fingerprint data

    Returns:
        Dictionary with browser information
    """
    return {
        "user_agent": fingerprint.user_agent,
        "language": fingerprint.language,
        "timezone": fingerprint.timezone,
        "screen_resolution": fingerprint.screen_resolution,
        "color_depth": fingerprint.color_depth,
        "platform": fingerprint.platform,
        "canvas_fingerprint": fingerprint.canvas_fingerprint,
        "webgl_fingerprint": fingerprint.webgl_fingerprint,
        "audio_fingerprint": fingerprint.audio_fingerprint,
        "fonts": fingerprint.fonts,
        "plugins": fingerprint.plugins,
        "screen_width": fingerprint.screen_width,
        "screen_height": fingerprint.screen_height,
    }
