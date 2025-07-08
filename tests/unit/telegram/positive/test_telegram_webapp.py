"""
Позитивные тесты для Telegram WebApp API.

Этот модуль содержит все успешные сценарии работы с Telegram WebApp:
- Аутентификация пользователей WebApp
- Конфигурация и настройки WebApp
- Управление опросами в WebApp
- Пользовательский интерфейс и взаимодействие
- Интеграция с Telegram Bot API
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory, SurveyFactory, QuestionFactory


class TestTelegramWebAppAuthentication:
    """Позитивные тесты аутентификации WebApp."""

    async def test_authenticate_user_complete_flow(
        self, api_client: AsyncClient, async_session
    ):
        """Тест полного потока аутентификации WebApp пользователя."""
        # Arrange
        auth_data = {
            "init_data": "user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C%22language_code%22%3A%22en%22%7D&chat_instance=1234567890123456789&chat_type=private&auth_date=1642680000&hash=abc123def456"
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.authenticate_user = AsyncMock(
                return_value={
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
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("authenticate_webapp_user"), json=auth_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert data["webapp_session_id"] == "session_456"

        user = data["user"]
        assert user["telegram_id"] == 123456789
        assert user["username"] == "testuser"
        assert user["first_name"] == "Test"
        assert user["last_name"] == "User"
        assert user["language_code"] == "en"

    async def test_authenticate_user_with_premium_features(
        self, api_client: AsyncClient
    ):
        """Тест аутентификации пользователя с Premium функциями."""
        # Arrange
        auth_data = {
            "init_data": "user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Premium%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22premiumuser%22%2C%22is_premium%22%3Atrue%7D&chat_instance=1234567890123456789&chat_type=private&auth_date=1642680000&hash=abc123def456"
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.authenticate_user = AsyncMock(
                return_value={
                    "user": {
                        "id": 124,
                        "username": "premiumuser",
                        "first_name": "Premium",
                        "last_name": "User",
                        "telegram_id": 123456789,
                        "is_premium": True,
                        "added_to_attachment_menu": True,
                    },
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "premium_features": {
                        "advanced_analytics": True,
                        "unlimited_surveys": True,
                        "priority_support": True,
                        "custom_branding": True,
                    },
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("authenticate_webapp_user"), json=auth_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["user"]["is_premium"] is True
        assert "premium_features" in data
        assert data["premium_features"]["advanced_analytics"] is True
        assert data["premium_features"]["unlimited_surveys"] is True

    async def test_refresh_webapp_token(self, api_client: AsyncClient, regular_user):
        """Тест обновления токена WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        refresh_data = {
            "refresh_token": "refresh_token_123",
            "webapp_session_id": "session_456",
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.refresh_token = AsyncMock(
                return_value={
                    "access_token": "new_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "new_refresh_token_789",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "webapp_session_id": "session_456",
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("refresh_webapp_token"), json=refresh_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["access_token"].startswith("new_")
        assert data["refresh_token"].startswith("new_")
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    async def test_logout_webapp_user(self, api_client: AsyncClient, regular_user):
        """Тест выхода пользователя из WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        logout_data = {"webapp_session_id": "session_456", "clear_data": True}

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.logout_user = AsyncMock(
                return_value={
                    "success": True,
                    "message": "User logged out successfully",
                    "cleared_data": True,
                    "session_duration": "02:15:30",
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("logout_webapp_user"), json=logout_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["cleared_data"] is True
        assert data["session_duration"] == "02:15:30"


class TestTelegramWebAppConfiguration:
    """Позитивные тесты конфигурации WebApp."""

    async def test_get_webapp_config_complete(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест получения полной конфигурации WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.generate_webapp_config = MagicMock(
                return_value={
                    "theme": "dark",
                    "user_id": regular_user.id,
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
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_config"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["theme"] == "dark"
        assert data["user_id"] == regular_user.id
        assert data["api_url"] == "https://api.example.com"
        assert data["bot_username"] == "quiz_bot"
        assert data["version"] == "1.5.0"

        features = data["features"]
        assert features["haptic_feedback"] is True
        assert features["main_button"] is True
        assert features["expand"] is True

        ui_settings = data["ui_settings"]
        assert ui_settings["auto_save"] is True
        assert ui_settings["dark_mode"] is True

        limits = data["limits"]
        assert limits["max_surveys"] == 50
        assert limits["max_questions_per_survey"] == 100

        analytics = data["analytics"]
        assert analytics["enabled"] is True
        assert analytics["real_time"] is True

    async def test_update_webapp_config(self, api_client: AsyncClient, regular_user):
        """Тест обновления конфигурации WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        config_update = {
            "theme": "light",
            "ui_settings": {
                "auto_save": False,
                "notifications": False,
                "sound_effects": False,
                "animations": False,
                "compact_mode": True,
            },
            "language": "ru",
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.update_webapp_config = AsyncMock(
                return_value={
                    "success": True,
                    "updated_fields": ["theme", "ui_settings", "language"],
                    "config": {
                        "theme": "light",
                        "ui_settings": {
                            "auto_save": False,
                            "notifications": False,
                            "sound_effects": False,
                            "animations": False,
                            "compact_mode": True,
                        },
                        "language": "ru",
                    },
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.put(
                api_client.url_for("update_webapp_config"), json=config_update
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "theme" in data["updated_fields"]
        assert "ui_settings" in data["updated_fields"]
        assert "language" in data["updated_fields"]

        config = data["config"]
        assert config["theme"] == "light"
        assert config["ui_settings"]["compact_mode"] is True
        assert config["language"] == "ru"

    async def test_get_webapp_localization(self, api_client: AsyncClient, regular_user):
        """Тест получения локализации WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_localization = MagicMock(
                return_value={
                    "language": "en",
                    "strings": {
                        "welcome_message": "Welcome to Quiz Bot!",
                        "create_survey": "Create Survey",
                        "my_surveys": "My Surveys",
                        "settings": "Settings",
                        "help": "Help",
                        "survey_created": "Survey created successfully!",
                        "survey_updated": "Survey updated successfully!",
                        "survey_deleted": "Survey deleted successfully!",
                        "loading": "Loading...",
                        "error": "An error occurred",
                        "confirm_delete": "Are you sure you want to delete this survey?",
                        "yes": "Yes",
                        "no": "No",
                        "cancel": "Cancel",
                        "save": "Save",
                        "close": "Close",
                    },
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_localization"), params={"language": "en"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "en"
        assert "strings" in data
        assert data["strings"]["welcome_message"] == "Welcome to Quiz Bot!"
        assert data["strings"]["create_survey"] == "Create Survey"
        assert (
            data["strings"]["confirm_delete"]
            == "Are you sure you want to delete this survey?"
        )


class TestTelegramWebAppSurveys:
    """Позитивные тесты управления опросами в WebApp."""

    async def test_get_webapp_surveys_with_pagination(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест получения опросов с пагинацией."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_surveys = AsyncMock(
                return_value={
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
                    "filters": {
                        "active_only": True,
                        "sort_by": "created_at",
                        "order": "desc",
                    },
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_surveys"),
                params={"page": 1, "per_page": 10, "active_only": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "surveys" in data
        assert "pagination" in data
        assert len(data["surveys"]) == 2

        survey = data["surveys"][0]
        assert survey["title"] == "Customer Satisfaction Survey"
        assert survey["questions_count"] == 8
        assert survey["responses_count"] == 156
        assert survey["completion_rate"] == 0.78
        assert survey["avg_rating"] == 4.2

        pagination = data["pagination"]
        assert pagination["total"] == 15
        assert pagination["page"] == 1
        assert pagination["total_pages"] == 2
        assert pagination["has_next"] is True

    async def test_get_webapp_survey_details(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест получения детальной информации об опросе."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_survey_details = AsyncMock(
                return_value={
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
                    "user_response": None,  # Пользователь еще не отвечал
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_survey_details", survey_id=1)
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "survey" in data
        assert "questions" in data
        assert "progress" in data

        survey = data["survey"]
        assert survey["title"] == "Customer Satisfaction Survey"
        assert survey["is_active"] is True

        questions = data["questions"]
        assert len(questions) == 2
        assert questions[0]["type"] == "multiple_choice"
        assert questions[0]["required"] is True
        assert len(questions[0]["options"]) == 5

        progress = data["progress"]
        assert progress["total_questions"] == 8
        assert progress["answered_questions"] == 0
        assert progress["completion_percentage"] == 0

    async def test_create_webapp_survey(self, api_client: AsyncClient, regular_user):
        """Тест создания опроса через WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        survey_data = {
            "title": "New Product Survey",
            "description": "Help us understand your needs",
            "questions": [
                {
                    "type": "multiple_choice",
                    "title": "What is your age group?",
                    "required": True,
                    "options": [
                        {"text": "18-25", "value": "18-25"},
                        {"text": "26-35", "value": "26-35"},
                        {"text": "36-45", "value": "36-45"},
                        {"text": "46+", "value": "46+"},
                    ],
                },
                {
                    "type": "text",
                    "title": "Any additional comments?",
                    "required": False,
                    "max_length": 300,
                },
            ],
            "settings": {
                "allow_multiple_responses": False,
                "require_login": True,
                "show_progress": True,
                "randomize_questions": False,
            },
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.create_webapp_survey = AsyncMock(
                return_value={
                    "survey": {
                        "id": 123,
                        "title": "New Product Survey",
                        "description": "Help us understand your needs",
                        "created_at": "2024-01-20T16:00:00Z",
                        "is_active": True,
                        "questions_count": 2,
                        "share_url": "https://t.me/quiz_bot/app?survey=123",
                        "qr_code": "https://example.com/qr/survey_123.png",
                    },
                    "success": True,
                    "message": "Survey created successfully!",
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("create_webapp_survey"), json=survey_data
            )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Survey created successfully!"

        survey = data["survey"]
        assert survey["id"] == 123
        assert survey["title"] == "New Product Survey"
        assert survey["questions_count"] == 2
        assert survey["is_active"] is True
        assert "share_url" in survey
        assert "qr_code" in survey


class TestTelegramWebAppSurveySubmission:
    """Позитивные тесты отправки ответов на опросы."""

    async def test_submit_survey_answers_complete(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки полных ответов на опрос."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        answers_data = {
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
            "completion_time": 180,  # 3 minutes
            "user_agent": "TelegramWebApp/1.0",
            "submit_type": "complete",
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.submit_survey_answers = AsyncMock(
                return_value={
                    "success": True,
                    "response_id": 456,
                    "survey_id": 1,
                    "completion_percentage": 100,
                    "answers_count": 3,
                    "completion_time": 180,
                    "submitted_at": "2024-01-20T16:30:00Z",
                    "status": "completed",
                    "thank_you_message": "Thank you for your feedback!",
                    "next_actions": {
                        "view_results": True,
                        "share_survey": True,
                        "create_new": True,
                    },
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("submit_webapp_survey_answers"), json=answers_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["response_id"] == 456
        assert data["survey_id"] == 1
        assert data["completion_percentage"] == 100
        assert data["answers_count"] == 3
        assert data["completion_time"] == 180
        assert data["status"] == "completed"
        assert data["thank_you_message"] == "Thank you for your feedback!"

        next_actions = data["next_actions"]
        assert next_actions["view_results"] is True
        assert next_actions["share_survey"] is True
        assert next_actions["create_new"] is True

    async def test_submit_survey_answers_partial(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест отправки частичных ответов на опрос."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        answers_data = {
            "survey_id": 1,
            "answers": [
                {
                    "question_id": 1,
                    "answer_type": "multiple_choice",
                    "value": "Good",
                    "option_id": 2,
                }
            ],
            "completion_time": 60,  # 1 minute
            "submit_type": "partial",
            "save_progress": True,
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.submit_survey_answers = AsyncMock(
                return_value={
                    "success": True,
                    "response_id": 457,
                    "survey_id": 1,
                    "completion_percentage": 25,
                    "answers_count": 1,
                    "completion_time": 60,
                    "submitted_at": "2024-01-20T16:31:00Z",
                    "status": "in_progress",
                    "message": "Progress saved successfully!",
                    "remaining_questions": 3,
                    "next_question_id": 2,
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("submit_webapp_survey_answers"), json=answers_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["response_id"] == 457
        assert data["completion_percentage"] == 25
        assert data["answers_count"] == 1
        assert data["status"] == "in_progress"
        assert data["message"] == "Progress saved successfully!"
        assert data["remaining_questions"] == 3
        assert data["next_question_id"] == 2

    async def test_update_survey_answers(self, api_client: AsyncClient, regular_user):
        """Тест обновления ответов на опрос."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        update_data = {
            "response_id": 456,
            "answers": [
                {
                    "question_id": 2,
                    "answer_type": "text",
                    "value": "Updated feedback - even better now!",
                }
            ],
            "completion_time": 240,  # 4 minutes total
            "submit_type": "update",
        }

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.update_survey_answers = AsyncMock(
                return_value={
                    "success": True,
                    "response_id": 456,
                    "survey_id": 1,
                    "updated_answers": 1,
                    "completion_percentage": 100,
                    "updated_at": "2024-01-20T16:35:00Z",
                    "status": "completed",
                    "message": "Answers updated successfully!",
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.put(
                api_client.url_for("update_webapp_survey_answers"), json=update_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["response_id"] == 456
        assert data["updated_answers"] == 1
        assert data["completion_percentage"] == 100
        assert data["status"] == "completed"
        assert data["message"] == "Answers updated successfully!"


class TestTelegramWebAppUserInterface:
    """Позитивные тесты пользовательского интерфейса WebApp."""

    async def test_get_main_button_config(self, api_client: AsyncClient, regular_user):
        """Тест получения конфигурации главной кнопки."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_main_button_config = MagicMock(
                return_value={
                    "visible": True,
                    "text": "Submit Survey",
                    "color": "#2481cc",
                    "text_color": "#ffffff",
                    "is_active": True,
                    "is_progress_visible": False,
                    "context": "survey_completion",
                    "action": "submit_survey",
                    "survey_id": 1,
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_main_button_config"), params={"survey_id": 1}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["visible"] is True
        assert data["text"] == "Submit Survey"
        assert data["color"] == "#2481cc"
        assert data["text_color"] == "#ffffff"
        assert data["is_active"] is True
        assert data["context"] == "survey_completion"
        assert data["action"] == "submit_survey"
        assert data["survey_id"] == 1

    async def test_trigger_haptic_feedback(self, api_client: AsyncClient, regular_user):
        """Тест запуска тактильной обратной связи."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        haptic_data = {"type": "impact", "style": "medium", "context": "button_press"}

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.trigger_haptic_feedback = AsyncMock(
                return_value={
                    "success": True,
                    "type": "impact",
                    "style": "medium",
                    "triggered_at": "2024-01-20T16:40:00Z",
                    "supported": True,
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.post(
                api_client.url_for("trigger_haptic_feedback"), json=haptic_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["type"] == "impact"
        assert data["style"] == "medium"
        assert data["supported"] is True

    async def test_get_webapp_html_interface(self, api_client: AsyncClient):
        """Тест получения HTML интерфейса WebApp."""
        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.render_webapp_html = MagicMock(
                return_value="""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Quiz Bot WebApp</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://telegram.org/js/telegram-web-app.js"></script>
                </head>
                <body>
                    <div id="app">
                        <h1>Welcome to Quiz Bot!</h1>
                        <p>Create and manage your surveys easily.</p>
                    </div>
                    <script>
                        Telegram.WebApp.ready();
                    </script>
                </body>
                </html>
                """
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_html"))

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"

        html_content = response.text
        assert "Quiz Bot WebApp" in html_content
        assert "telegram-web-app.js" in html_content
        assert "Telegram.WebApp.ready()" in html_content

    async def test_get_webapp_user_profile(self, api_client: AsyncClient, regular_user):
        """Тест получения профиля пользователя WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_user_profile = AsyncMock(
                return_value={
                    "user": {
                        "id": regular_user.id,
                        "username": regular_user.username,
                        "first_name": regular_user.first_name,
                        "last_name": regular_user.last_name,
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
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_user_profile")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        assert "statistics" in data
        assert "achievements" in data

        user = data["user"]
        assert user["id"] == regular_user.id
        assert user["telegram_id"] == 123456789
        assert user["is_premium"] is False

        statistics = data["statistics"]
        assert statistics["surveys_created"] == 5
        assert statistics["surveys_completed"] == 12
        assert statistics["total_responses"] == 89
        assert statistics["average_completion_time"] == 4.5

        achievements = data["achievements"]
        assert len(achievements) == 2
        assert achievements[0]["id"] == "first_survey"
        assert achievements[1]["id"] == "active_user"

    async def test_get_webapp_user_stats(self, api_client: AsyncClient, regular_user):
        """Тест получения статистики пользователя WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_user_stats = AsyncMock(
                return_value={
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
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_user_stats"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "activity" in data
        assert "engagement" in data
        assert "productivity" in data
        assert "trends" in data

        activity = data["activity"]
        assert activity["daily_active_days"] == 15
        assert activity["streak_days"] == 7
        assert activity["longest_streak"] == 12

        engagement = data["engagement"]
        assert engagement["avg_session_duration"] == 8.5
        assert engagement["total_sessions"] == 45
        assert engagement["bounce_rate"] == 0.15

        productivity = data["productivity"]
        assert productivity["surveys_created_this_week"] == 2
        assert productivity["avg_questions_per_survey"] == 6.5

        trends = data["trends"]
        assert trends["most_active_day"] == "Tuesday"
        assert trends["most_active_hour"] == 14
        assert trends["preferred_survey_length"] == "short"
