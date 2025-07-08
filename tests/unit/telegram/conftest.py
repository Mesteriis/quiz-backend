"""
Фикстуры для тестирования домена Telegram.

Этот модуль содержит фикстуры для:
- Пользователей разных типов (regular, admin, premium)
- Данных Telegram Bot API (webhook, статус, уведомления)
- Данных Telegram WebApp (аутентификация, конфигурация, опросы)
- Моков сервисов Telegram (bot service, webapp service)
- Тестовых данных для различных сценариев
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from tests.factories import UserFactory, SurveyFactory, QuestionFactory


# === Пользователи и авторизация ===


@pytest.fixture
async def regular_user(async_session):
    """Обычный пользователь для тестов."""
    user = UserFactory(
        username="telegram_user",
        first_name="Telegram",
        last_name="User",
        email="telegram@example.com",
        is_active=True,
        is_admin=False,
        telegram_id=123456789,
        language_code="en",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(async_session):
    """Администратор для тестов."""
    user = UserFactory(
        username="telegram_admin",
        first_name="Telegram",
        last_name="Admin",
        email="admin@example.com",
        is_active=True,
        is_admin=True,
        telegram_id=987654321,
        language_code="en",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def premium_user(async_session):
    """Premium пользователь для тестов."""
    user = UserFactory(
        username="telegram_premium",
        first_name="Premium",
        last_name="User",
        email="premium@example.com",
        is_active=True,
        is_admin=False,
        telegram_id=555666777,
        language_code="en",
        is_premium=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(async_session):
    """Неактивный пользователь для тестов."""
    user = UserFactory(
        username="telegram_inactive",
        first_name="Inactive",
        last_name="User",
        email="inactive@example.com",
        is_active=False,
        is_admin=False,
        telegram_id=111222333,
        language_code="en",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


# === Telegram Bot API фикстуры ===


@pytest.fixture
def webhook_info_healthy():
    """Информация о здоровом webhook."""
    return {
        "url": "https://example.com/webhook/telegram",
        "has_custom_certificate": False,
        "pending_update_count": 0,
        "last_error_date": None,
        "last_error_message": None,
        "max_connections": 40,
        "allowed_updates": ["message", "callback_query", "inline_query"],
        "ip_address": "127.0.0.1",
        "last_synchronization_error_date": None,
        "status": "active",
    }


@pytest.fixture
def webhook_info_with_errors():
    """Информация о webhook с ошибками."""
    return {
        "url": "https://example.com/webhook/telegram",
        "has_custom_certificate": True,
        "pending_update_count": 5,
        "last_error_date": 1642680000,
        "last_error_message": "Connection timeout",
        "max_connections": 40,
        "allowed_updates": ["message", "callback_query"],
        "ip_address": "192.168.1.1",
        "last_synchronization_error_date": 1642679000,
        "status": "error",
    }


@pytest.fixture
def webhook_set_data():
    """Данные для установки webhook."""
    return {
        "url": "https://example.com/webhook/telegram",
        "certificate": None,
        "ip_address": "192.168.1.100",
        "max_connections": 50,
        "allowed_updates": [
            "message",
            "callback_query",
            "inline_query",
            "edited_message",
        ],
        "drop_pending_updates": True,
        "secret_token": "webhook_secret_token_123",
    }


@pytest.fixture
def telegram_message_update():
    """Telegram message update данные."""
    return {
        "update_id": 123456,
        "message": {
            "message_id": 1,
            "date": 1642680000,
            "chat": {
                "id": 123456789,
                "type": "private",
                "first_name": "Test",
                "last_name": "User",
            },
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
            },
            "text": "Hello, bot!",
        },
    }


@pytest.fixture
def telegram_callback_query_update():
    """Telegram callback query update данные."""
    return {
        "update_id": 123457,
        "callback_query": {
            "id": "callback_123",
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "message": {
                "message_id": 2,
                "date": 1642680000,
                "chat": {"id": 123456789, "type": "private"},
                "text": "Choose an option:",
            },
            "data": "survey_123_start",
        },
    }


@pytest.fixture
def telegram_inline_query_update():
    """Telegram inline query update данные."""
    return {
        "update_id": 123458,
        "inline_query": {
            "id": "inline_123",
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "query": "search surveys",
            "offset": "",
        },
    }


@pytest.fixture
def bot_status_healthy():
    """Здоровый статус бота."""
    return {
        "bot_info": {
            "id": 987654321,
            "username": "quiz_bot",
            "first_name": "Quiz Bot",
            "can_join_groups": True,
            "can_read_all_group_messages": False,
            "supports_inline_queries": True,
        },
        "status": {
            "status": "online",
            "uptime": "5d 12h 30m",
            "last_update": "2024-01-20T10:00:00Z",
            "webhook_status": "active",
            "message_count": 1250,
            "error_count": 0,
        },
    }


@pytest.fixture
def bot_status_with_metrics():
    """Статус бота с метриками."""
    return {
        "bot_info": {"id": 987654321, "username": "quiz_bot", "first_name": "Quiz Bot"},
        "status": {
            "status": "online",
            "uptime": "5d 12h 30m",
            "metrics": {
                "messages_today": 350,
                "unique_users_today": 85,
                "surveys_created_today": 12,
                "avg_response_time": 0.08,
                "error_rate": 0.02,
            },
            "performance": {
                "cpu_usage": 15.5,
                "memory_usage": 45.2,
                "active_connections": 25,
            },
        },
    }


@pytest.fixture
def bot_commands_list():
    """Список команд бота."""
    return [
        {"command": "start", "description": "Start using the bot"},
        {"command": "help", "description": "Get help information"},
        {"command": "create", "description": "Create a new survey"},
        {"command": "list", "description": "List your surveys"},
        {"command": "stats", "description": "View survey statistics"},
        {"command": "settings", "description": "Bot settings"},
    ]


@pytest.fixture
def bot_health_check():
    """Данные проверки здоровья бота."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-20T10:00:00Z",
        "checks": {"bot_api": True, "webhook": True, "database": True, "redis": True},
        "response_time": 0.05,
    }


# === Telegram WebApp фикстуры ===


@pytest.fixture
def webapp_auth_data():
    """Данные аутентификации WebApp."""
    return {
        "init_data": "user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C%22language_code%22%3A%22en%22%7D&chat_instance=1234567890123456789&chat_type=private&auth_date=1642680000&hash=abc123def456"
    }


@pytest.fixture
def webapp_auth_response():
    """Ответ аутентификации WebApp."""
    return {
        "user": {
            "id": 123,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "telegram_id": 123456789,
            "language_code": "en",
            "is_premium": False,
            "added_to_attachment_menu": False,
        },
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "refresh_token_123",
        "token_type": "bearer",
        "expires_in": 3600,
        "webapp_session_id": "session_456",
    }


@pytest.fixture
def webapp_config_complete():
    """Полная конфигурация WebApp."""
    return {
        "theme": "dark",
        "user_id": 123,
        "api_url": "https://api.example.com",
        "bot_username": "quiz_bot",
        "version": "1.5.0",
        "features": {
            "haptic_feedback": True,
            "main_button": True,
            "back_button": True,
            "close_button": True,
            "settings_button": True,
            "expand": True,
            "vertical_swipes": True,
        },
        "ui_settings": {
            "auto_save": True,
            "notifications": True,
            "sound_effects": True,
            "animations": True,
            "dark_mode": True,
            "compact_mode": False,
        },
        "limits": {
            "max_surveys": 50,
            "max_questions_per_survey": 100,
            "max_responses_per_survey": 10000,
            "file_upload_size": 10485760,  # 10MB
        },
        "analytics": {
            "enabled": True,
            "real_time": True,
            "export_formats": ["json", "csv", "pdf"],
        },
    }


@pytest.fixture
def webapp_surveys_data():
    """Данные опросов WebApp."""
    return {
        "surveys": [
            {
                "id": 1,
                "title": "Customer Satisfaction Survey",
                "description": "Help us improve our service",
                "questions_count": 8,
                "responses_count": 156,
                "is_active": True,
                "is_completed": False,
                "progress": 65,
                "estimated_time": 5,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-20T15:30:00Z",
                "completion_rate": 0.78,
                "avg_rating": 4.2,
                "thumbnail": "https://example.com/thumbnails/survey_1.jpg",
            },
            {
                "id": 2,
                "title": "Product Feedback",
                "description": "Tell us about our new product",
                "questions_count": 12,
                "responses_count": 89,
                "is_active": True,
                "is_completed": False,
                "progress": 35,
                "estimated_time": 7,
                "created_at": "2024-01-18T09:00:00Z",
                "updated_at": "2024-01-20T12:45:00Z",
                "completion_rate": 0.65,
                "avg_rating": 3.9,
                "thumbnail": "https://example.com/thumbnails/survey_2.jpg",
            },
        ],
        "pagination": {
            "total": 15,
            "page": 1,
            "per_page": 10,
            "total_pages": 2,
            "has_next": True,
            "has_prev": False,
        },
        "filters": {"active_only": True, "sort_by": "created_at", "order": "desc"},
    }


@pytest.fixture
def webapp_survey_details():
    """Детали опроса WebApp."""
    return {
        "survey": {
            "id": 1,
            "title": "Customer Satisfaction Survey",
            "description": "Help us improve our service by answering these questions",
            "is_active": True,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-20T15:30:00Z",
            "settings": {
                "allow_multiple_responses": False,
                "require_login": True,
                "collect_contact_info": False,
                "show_progress": True,
                "randomize_questions": False,
            },
        },
        "questions": [
            {
                "id": 1,
                "type": "multiple_choice",
                "title": "How would you rate our service?",
                "description": "Please select one option",
                "required": True,
                "order": 1,
                "options": [
                    {"id": 1, "text": "Excellent", "value": 5},
                    {"id": 2, "text": "Good", "value": 4},
                    {"id": 3, "text": "Fair", "value": 3},
                    {"id": 4, "text": "Poor", "value": 2},
                    {"id": 5, "text": "Very Poor", "value": 1},
                ],
            },
            {
                "id": 2,
                "type": "text",
                "title": "What can we improve?",
                "description": "Please provide your suggestions",
                "required": False,
                "order": 2,
                "max_length": 500,
            },
        ],
        "progress": {
            "total_questions": 8,
            "answered_questions": 0,
            "completion_percentage": 0,
        },
        "user_response": None,
    }


@pytest.fixture
def webapp_survey_answers():
    """Ответы на опрос WebApp."""
    return {
        "survey_id": 1,
        "answers": [
            {
                "question_id": 1,
                "answer_type": "multiple_choice",
                "value": "Excellent",
                "option_id": 1,
            },
            {
                "question_id": 2,
                "answer_type": "text",
                "value": "Great service, very satisfied!",
            },
            {"question_id": 3, "answer_type": "rating", "value": 5},
        ],
        "completion_time": 180,
        "user_agent": "TelegramWebApp/1.0",
        "submit_type": "complete",
    }


@pytest.fixture
def webapp_user_profile():
    """Профиль пользователя WebApp."""
    return {
        "user": {
            "id": 123,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "telegram_id": 123456789,
            "language_code": "en",
            "is_premium": False,
            "joined_at": "2024-01-15T10:00:00Z",
            "last_active": "2024-01-20T16:45:00Z",
        },
        "statistics": {
            "surveys_created": 5,
            "surveys_completed": 12,
            "total_responses": 89,
            "average_completion_time": 4.5,
            "favorite_survey_type": "multiple_choice",
        },
        "achievements": [
            {
                "id": "first_survey",
                "name": "First Survey Creator",
                "description": "Created your first survey",
                "earned_at": "2024-01-15T11:00:00Z",
            },
            {
                "id": "active_user",
                "name": "Active User",
                "description": "Used the app for 7 consecutive days",
                "earned_at": "2024-01-22T10:00:00Z",
            },
        ],
    }


@pytest.fixture
def webapp_user_stats():
    """Статистика пользователя WebApp."""
    return {
        "activity": {
            "daily_active_days": 15,
            "weekly_active_weeks": 4,
            "monthly_active_months": 2,
            "streak_days": 7,
            "longest_streak": 12,
        },
        "engagement": {
            "avg_session_duration": 8.5,
            "total_sessions": 45,
            "surveys_per_session": 2.3,
            "bounce_rate": 0.15,
        },
        "productivity": {
            "surveys_created_this_week": 2,
            "surveys_created_this_month": 8,
            "avg_questions_per_survey": 6.5,
            "avg_responses_per_survey": 25.3,
        },
        "trends": {
            "most_active_day": "Tuesday",
            "most_active_hour": 14,
            "preferred_survey_length": "short",
            "most_used_question_type": "multiple_choice",
        },
    }


# === Уведомления ===


@pytest.fixture
def notification_data():
    """Данные уведомления."""
    return {
        "user_id": 123,
        "message": "Your survey has received new responses!",
        "type": "info",
        "action_url": "/surveys/123/results",
        "priority": "normal",
    }


@pytest.fixture
def notification_with_keyboard():
    """Уведомление с inline клавиатурой."""
    return {
        "user_id": 123,
        "message": "Survey completed! What would you like to do next?",
        "type": "success",
        "inline_keyboard": [
            [
                {"text": "View Results", "callback_data": "view_results_123"},
                {"text": "Share Survey", "callback_data": "share_survey_123"},
            ],
            [{"text": "Create New Survey", "callback_data": "create_new_survey"}],
        ],
    }


@pytest.fixture
def admin_notification_data():
    """Данные административного уведомления."""
    return {
        "message": "System alert: High load detected",
        "type": "warning",
        "priority": "high",
        "broadcast": True,
        "target_admins": True,
    }


@pytest.fixture
def broadcast_notification_data():
    """Данные массового уведомления."""
    return {
        "message": "🎉 New feature available: Advanced analytics for your surveys!",
        "type": "announcement",
        "target_audience": "all_users",
        "schedule_time": None,
        "include_unsubscribed": False,
    }


# === Моки сервисов ===


@pytest.fixture
def mock_telegram_service():
    """Мок Telegram сервиса."""
    service = MagicMock()

    # Bot API моки
    service.bot = MagicMock()
    service.bot.get_webhook_info = MagicMock()
    service.bot.set_webhook = MagicMock(return_value=True)
    service.bot.delete_webhook = MagicMock(return_value=True)
    service.bot.get_me = MagicMock()
    service.bot.get_my_commands = MagicMock()
    service.bot.set_my_commands = MagicMock(return_value=True)
    service.bot.set_my_description = MagicMock(return_value=True)
    service.bot.set_my_short_description = MagicMock(return_value=True)

    # Диспетчер
    service.dp = MagicMock()
    service.dp.feed_update = AsyncMock()

    # Методы сервиса
    service.get_bot_status = MagicMock()
    service.get_bot_configuration = MagicMock()
    service.health_check = AsyncMock()
    service.send_notification = AsyncMock()
    service.send_admin_notification = AsyncMock()
    service.send_broadcast = AsyncMock()
    service.schedule_notification = AsyncMock()

    return service


@pytest.fixture
def mock_webapp_service():
    """Мок WebApp сервиса."""
    service = MagicMock()

    # Аутентификация
    service.authenticate_user = AsyncMock()
    service.refresh_token = AsyncMock()
    service.logout_user = AsyncMock()

    # Конфигурация
    service.generate_webapp_config = MagicMock()
    service.update_webapp_config = AsyncMock()
    service.get_localization = MagicMock()

    # Опросы
    service.get_webapp_surveys = AsyncMock()
    service.get_webapp_survey_details = AsyncMock()
    service.create_webapp_survey = AsyncMock()
    service.submit_survey_answers = AsyncMock()
    service.update_survey_answers = AsyncMock()

    # Интерфейс
    service.get_main_button_config = MagicMock()
    service.trigger_haptic_feedback = AsyncMock()
    service.render_webapp_html = MagicMock()

    # Пользователь
    service.get_webapp_user_profile = AsyncMock()
    service.get_webapp_user_stats = AsyncMock()

    return service


# === Данные для ошибок ===


@pytest.fixture
def invalid_token_data():
    """Данные с невалидным токеном."""
    return {
        "invalid_token": "invalid_bot_token_123",
        "error_message": "Unauthorized: bot token is invalid",
    }


@pytest.fixture
def webhook_error_data():
    """Данные ошибки webhook."""
    return {
        "error": "webhook_error",
        "message": "Failed to set webhook",
        "details": "Invalid URL format",
    }


@pytest.fixture
def webapp_auth_error_data():
    """Данные ошибки аутентификации WebApp."""
    return {
        "error": "auth_error",
        "message": "Invalid init data",
        "details": "Hash verification failed",
    }


@pytest.fixture
def service_unavailable_data():
    """Данные для недоступного сервиса."""
    return {
        "error": "service_unavailable",
        "message": "Service temporarily unavailable",
        "retry_after": 30,
    }


# === Данные для edge cases ===


@pytest.fixture
def large_message_data():
    """Данные большого сообщения."""
    return {
        "message": "A" * 5000,  # Очень длинное сообщение
        "type": "info",
    }


@pytest.fixture
def concurrent_users_data():
    """Данные для конкурентных пользователей."""
    return [
        {"user_id": i, "telegram_id": 100000 + i, "username": f"user_{i}"}
        for i in range(1, 101)  # 100 пользователей
    ]


@pytest.fixture
def unicode_message_data():
    """Данные с Unicode символами."""
    return {
        "message": "🎉 Survey completed! 🌟 Thanks for your feedback! 💫",
        "type": "success",
        "emoji_count": 3,
    }


@pytest.fixture
def memory_intensive_data():
    """Данные интенсивные по памяти."""
    return {
        "surveys": [
            {
                "id": i,
                "title": f"Survey {i}",
                "questions": [
                    {
                        "id": j,
                        "title": f"Question {j}",
                        "options": [f"Option {k}" for k in range(1, 51)],  # 50 опций
                    }
                    for j in range(1, 101)  # 100 вопросов
                ],
            }
            for i in range(1, 11)  # 10 опросов
        ]
    }


@pytest.fixture
def network_timeout_data():
    """Данные для тестирования таймаутов."""
    return {"timeout": 30, "retry_count": 3, "backoff_factor": 2}


@pytest.fixture
def test_settings():
    """Тестовые настройки."""
    return MagicMock(
        telegram_bot_token="test_bot_token_123",
        telegram_webhook_url="https://example.com/webhook/test",
        telegram_webhook_secret="test_webhook_secret",
        webapp_url="https://example.com/webapp",
        max_connections=40,
        allowed_updates=["message", "callback_query", "inline_query"],
    )
