"""
Telegram Web Apps Router for Quiz App.

This module provides API endpoints specifically designed for
Telegram Web Apps integration.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from models.user import User
from services.jwt_service import get_current_user
from services.telegram_webapp import get_webapp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram/webapp", tags=["telegram-webapp"])


class WebAppAuthRequest(BaseModel):
    """Request model for Telegram Web App authentication."""

    init_data: str


class SurveyAnswerRequest(BaseModel):
    """Request model for submitting survey answers."""

    survey_id: int
    answers: dict[int, Any]  # question_id -> answer


@router.post("/auth")
async def authenticate_webapp_user(auth_request: WebAppAuthRequest):
    """
    Authenticate user from Telegram Web App init data.

    This endpoint validates the init data from Telegram and returns
    user information along with an access token.
    """
    try:
        webapp_service = get_webapp_service()
        auth_result = await webapp_service.authenticate_user(auth_request.init_data)

        return auth_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WebApp authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/config")
async def get_webapp_config(current_user: User = Depends(get_current_user)):
    """Get configuration for Telegram Web App."""
    try:
        webapp_service = get_webapp_service()
        config = webapp_service.generate_webapp_config(current_user.id)

        return config

    except Exception as e:
        logger.error(f"Error getting webapp config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get config")


@router.get("/surveys")
async def get_webapp_surveys(current_user: User = Depends(get_current_user)):
    """Get surveys formatted for Telegram Web App."""
    try:
        webapp_service = get_webapp_service()
        surveys = await webapp_service.get_webapp_surveys(current_user.id)

        return {"surveys": surveys, "total": len(surveys)}

    except Exception as e:
        logger.error(f"Error getting webapp surveys: {e}")
        raise HTTPException(status_code=500, detail="Failed to get surveys")


@router.get("/surveys/{survey_id}")
async def get_webapp_survey_details(
    survey_id: int, current_user: User = Depends(get_current_user)
):
    """Get detailed survey info for Telegram Web App."""
    try:
        webapp_service = get_webapp_service()
        survey_details = await webapp_service.get_webapp_survey_details(
            survey_id, current_user.id
        )

        return survey_details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting survey details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get survey details")


@router.post("/surveys/{survey_id}/submit")
async def submit_survey_answers(
    survey_id: int,
    answer_request: SurveyAnswerRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit survey answers from Telegram Web App."""
    try:
        # Import here to avoid circular imports
        from sqlalchemy import select

        from database import get_async_session
        from models.question import Question
        from models.response import Response

        async with get_async_session() as session:
            # Validate survey and questions
            questions_stmt = select(Question).where(Question.survey_id == survey_id)
            questions_result = await session.execute(questions_stmt)
            questions = {q.id: q for q in questions_result.scalars().all()}

            if not questions:
                raise HTTPException(status_code=404, detail="Survey not found")

            # Save responses
            saved_responses = []

            for question_id, answer in answer_request.answers.items():
                if question_id not in questions:
                    continue

                # Check if response already exists
                existing_response_stmt = select(Response).where(
                    Response.question_id == question_id,
                    Response.user_id == current_user.id,
                )
                existing_result = await session.execute(existing_response_stmt)
                existing_response = existing_result.scalar_one_or_none()

                if existing_response:
                    # Update existing response
                    existing_response.answer = {"value": answer}
                    saved_responses.append(existing_response)
                else:
                    # Create new response
                    new_response = Response(
                        question_id=question_id,
                        user_id=current_user.id,
                        user_session_id=f"webapp_{current_user.id}",
                        answer={"value": answer},
                    )
                    session.add(new_response)
                    saved_responses.append(new_response)

            await session.commit()

            # Send completion notification
            from services.realtime_notifications import get_notification_service

            notification_service = get_notification_service()

            completion_notification = (
                await notification_service.create_completion_notification(
                    survey_id, current_user.id
                )
            )
            await notification_service.send_notification(completion_notification)

            return {
                "success": True,
                "saved_responses": len(saved_responses),
                "message": "Ответы сохранены успешно",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting survey answers: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit answers")


@router.get("/main-button/{action}")
async def get_main_button_config(
    action: str,
    survey_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """Get main button configuration for Telegram Web App."""
    try:
        webapp_service = get_webapp_service()
        button_config = webapp_service.create_main_button_config(survey_id, action)

        return button_config

    except Exception as e:
        logger.error(f"Error getting main button config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get button config")


@router.post("/haptic-feedback")
async def trigger_haptic_feedback(
    feedback_type: str = "impact", current_user: User = Depends(get_current_user)
):
    """Get haptic feedback configuration for Telegram Web App."""
    try:
        webapp_service = get_webapp_service()
        haptic_config = webapp_service.create_haptic_feedback_config(feedback_type)

        return haptic_config

    except Exception as e:
        logger.error(f"Error getting haptic config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get haptic config")


@router.get("/user/profile")
async def get_webapp_user_profile(current_user: User = Depends(get_current_user)):
    """Get user profile for Telegram Web App."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "display_name": current_user.get_display_name(),
        "is_admin": current_user.is_admin,
        "telegram_id": current_user.telegram_id,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat()
        if current_user.created_at
        else None,
    }


@router.get("/user/stats")
async def get_webapp_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics for Telegram Web App."""
    try:
        from sqlalchemy import distinct, func, select

        from database import get_async_session
        from models.question import Question
        from models.response import Response
        from models.survey import Survey

        async with get_async_session() as session:
            # Count completed surveys
            completed_surveys_stmt = select(
                func.count(
                    distinct(
                        Response.question_id.in_(
                            select(Question.id).where(Question.survey_id == Survey.id)
                        )
                    )
                )
            ).where(Response.user_id == current_user.id)

            # Total responses
            total_responses_stmt = select(func.count(Response.id)).where(
                Response.user_id == current_user.id
            )

            # Available surveys
            available_surveys_stmt = select(func.count(Survey.id)).where(
                Survey.is_active == True, Survey.is_public == True
            )

            total_responses_result = await session.execute(total_responses_stmt)
            available_surveys_result = await session.execute(available_surveys_stmt)

            total_responses = total_responses_result.scalar() or 0
            available_surveys = available_surveys_result.scalar() or 0

            return {
                "total_responses": total_responses,
                "available_surveys": available_surveys,
                "completion_rate": (total_responses / available_surveys * 100)
                if available_surveys > 0
                else 0,
                "last_activity": current_user.updated_at.isoformat()
                if current_user.updated_at
                else None,
            }

    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user stats")


@router.get("/html/{survey_id}")
async def get_webapp_html(survey_id: int):
    """
    Get HTML page for Telegram Web App.

    This serves a simple HTML page that can be opened in Telegram Web App.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quiz App - Опрос #{survey_id}</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: var(--tg-theme-bg-color, #ffffff);
                color: var(--tg-theme-text-color, #000000);
            }}
            .container {{
                max-width: 400px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .survey-card {{
                background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .button {{
                background-color: var(--tg-theme-button-color, #0088cc);
                color: var(--tg-theme-button-text-color, #ffffff);
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                width: 100%;
                cursor: pointer;
                margin-top: 15px;
            }}
            .loading {{
                text-align: center;
                padding: 40px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Quiz App</h1>
                <p>Опрос #{survey_id}</p>
            </div>

            <div id="content" class="loading">
                <p>Загрузка...</p>
            </div>
        </div>

        <script>
            // Initialize Telegram Web App
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();

            // Set theme
            document.body.style.backgroundColor = window.Telegram.WebApp.themeParams.bg_color || '#ffffff';
            document.body.style.color = window.Telegram.WebApp.themeParams.text_color || '#000000';

            // Load survey data
            async function loadSurvey() {{
                try {{
                    // Get init data
                    const initData = window.Telegram.WebApp.initData;

                    if (!initData) {{
                        document.getElementById('content').innerHTML = '<p>❌ Ошибка: нет данных авторизации</p>';
                        return;
                    }}

                    // Authenticate user
                    const authResponse = await fetch('/telegram/webapp/auth', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ init_data: initData }})
                    }});

                    if (!authResponse.ok) {{
                        throw new Error('Ошибка авторизации');
                    }}

                    const authData = await authResponse.json();
                    const token = authData.access_token;

                    // Get survey details
                    const surveyResponse = await fetch(`/telegram/webapp/surveys/{survey_id}`, {{
                        headers: {{
                            'Authorization': `Bearer ${{token}}`
                        }}
                    }});

                    if (!surveyResponse.ok) {{
                        throw new Error('Опрос не найден');
                    }}

                    const surveyData = await surveyResponse.json();

                    // Display survey
                    displaySurvey(surveyData, token);

                }} catch (error) {{
                    console.error('Error:', error);
                    document.getElementById('content').innerHTML = `<p>❌ Ошибка: ${{error.message}}</p>`;
                }}
            }}

            function displaySurvey(surveyData, token) {{
                const survey = surveyData.survey;
                const questions = surveyData.questions;

                const content = `
                    <div class="survey-card">
                        <h2>${{survey.title}}</h2>
                        <p>${{survey.description || 'Нет описания'}}</p>
                        <p><strong>Вопросов:</strong> ${{surveyData.total_questions}}</p>
                        <p><strong>Прогресс:</strong> ${{Math.round(surveyData.completion_percentage)}}%</p>
                    </div>

                    <button class="button" onclick="openFullApp('${{token}}')">
                        🚀 Пройти опрос
                    </button>
                `;

                document.getElementById('content').innerHTML = content;

                // Configure main button
                window.Telegram.WebApp.MainButton.setText('🚀 Пройти опрос');
                window.Telegram.WebApp.MainButton.show();
                window.Telegram.WebApp.MainButton.onClick(() => openFullApp(token));
            }}

            function openFullApp(token) {{
                const url = `http://localhost:3000/surveys/{survey_id}?token=${{token}}&from=telegram`;
                window.Telegram.WebApp.openLink(url);
            }}

            // Load survey on page load
            loadSurvey();
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/test")
async def test_webapp():
    """Test endpoint for Telegram Web App development."""
    return {
        "status": "ok",
        "message": "Telegram Web App API is working",
        "timestamp": "datetime.now().isoformat()",
        "endpoints": [
            "POST /auth - Authenticate user",
            "GET /config - Get webapp config",
            "GET /surveys - Get surveys list",
            "GET /surveys/{id} - Get survey details",
            "POST /surveys/{id}/submit - Submit answers",
            "GET /main-button/{action} - Get button config",
            "GET /user/profile - Get user profile",
            "GET /user/stats - Get user stats",
            "GET /html/{survey_id} - Get HTML page",
        ],
    }
