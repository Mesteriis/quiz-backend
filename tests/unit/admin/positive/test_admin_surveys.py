"""
Позитивные тесты для Admin Survey Management.

Этот модуль содержит все успешные сценарии управления опросами через админ интерфейс:
- CRUD операции с опросами (создание, чтение, обновление, удаление)
- Массовые операции с опросами
- Аналитика и отчеты по опросам
- Управление вопросами и ответами
- Публикация и архивирование опросов
- Копирование и шаблоны опросов
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import SurveyFactory, QuestionFactory, ResponseFactory, UserFactory


class TestAdminSurveyManagement:
    """Позитивные тесты базового управления опросами."""

    async def test_get_all_surveys_comprehensive(
        self, api_client: AsyncClient, admin_user, async_session
    ):
        """Тест получения всех опросов с полной информацией."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Создаем тестовые данные
        surveys = [
            SurveyFactory(title="Public Survey", is_public=True, is_active=True),
            SurveyFactory(title="Private Survey", is_public=False, is_active=True),
            SurveyFactory(title="Draft Survey", is_public=False, is_active=False),
        ]
        for survey in surveys:
            async_session.add(survey)
        await async_session.commit()

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_all_surveys = AsyncMock(
                return_value=[
                    {
                        "id": 1,
                        "title": "Customer Satisfaction Survey",
                        "description": "Annual customer satisfaction survey",
                        "is_public": True,
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T10:00:00Z",
                        "created_by": "admin",
                        "questions_count": 15,
                        "responses_count": 234,
                        "completion_rate": 0.78,
                        "avg_completion_time": 4.2,
                        "tags": ["satisfaction", "customer", "annual"],
                        "category": "customer_feedback",
                        "language": "en",
                        "estimated_duration": 5,
                        "target_audience": "all_customers",
                    },
                    {
                        "id": 2,
                        "title": "Product Feedback Survey",
                        "description": "Feedback on new product features",
                        "is_public": False,
                        "is_active": True,
                        "created_at": "2024-01-18T14:30:00Z",
                        "updated_at": "2024-01-19T09:15:00Z",
                        "created_by": "product_admin",
                        "questions_count": 8,
                        "responses_count": 89,
                        "completion_rate": 0.85,
                        "avg_completion_time": 3.1,
                        "tags": ["product", "feedback", "features"],
                        "category": "product_development",
                        "language": "en",
                        "estimated_duration": 3,
                        "target_audience": "beta_users",
                    },
                ]
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.get(
                api_client.url_for("get_all_admin_surveys"),
                params={"include_stats": True, "include_tags": True},
            )

        # Assert
        assert response.status_code == 200
        surveys = response.json()

        assert len(surveys) == 2

        # Проверяем первый опрос
        survey1 = surveys[0]
        assert survey1["title"] == "Customer Satisfaction Survey"
        assert survey1["is_public"] is True
        assert survey1["questions_count"] == 15
        assert survey1["responses_count"] == 234
        assert survey1["completion_rate"] == 0.78
        assert survey1["avg_completion_time"] == 4.2
        assert "satisfaction" in survey1["tags"]
        assert survey1["category"] == "customer_feedback"
        assert survey1["estimated_duration"] == 5

        # Проверяем второй опрос
        survey2 = surveys[1]
        assert survey2["title"] == "Product Feedback Survey"
        assert survey2["is_public"] is False
        assert survey2["questions_count"] == 8
        assert survey2["completion_rate"] == 0.85
        assert survey2["target_audience"] == "beta_users"

    async def test_get_surveys_with_filters(self, api_client: AsyncClient, admin_user):
        """Тест получения опросов с фильтрацией."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_filtered_surveys = AsyncMock(
                return_value={
                    "surveys": [
                        {
                            "id": 1,
                            "title": "Active Public Survey",
                            "is_public": True,
                            "is_active": True,
                            "category": "customer_feedback",
                            "created_at": "2024-01-20T10:00:00Z",
                            "responses_count": 156,
                        }
                    ],
                    "pagination": {
                        "total": 1,
                        "pages": 1,
                        "current_page": 1,
                        "per_page": 10,
                        "has_next": False,
                        "has_prev": False,
                    },
                    "filters_applied": {
                        "status": "active",
                        "visibility": "public",
                        "category": "customer_feedback",
                        "date_range": "last_30_days",
                    },
                }
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.get(
                api_client.url_for("get_all_admin_surveys"),
                params={
                    "status": "active",
                    "visibility": "public",
                    "category": "customer_feedback",
                    "date_range": "last_30_days",
                    "page": 1,
                    "per_page": 10,
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["surveys"]) == 1
        assert data["surveys"][0]["title"] == "Active Public Survey"
        assert data["surveys"][0]["is_public"] is True
        assert data["surveys"][0]["is_active"] is True

        # Проверяем пагинацию
        pagination = data["pagination"]
        assert pagination["total"] == 1
        assert pagination["current_page"] == 1
        assert pagination["has_next"] is False

        # Проверяем примененные фильтры
        filters = data["filters_applied"]
        assert filters["status"] == "active"
        assert filters["visibility"] == "public"
        assert filters["category"] == "customer_feedback"

    async def test_create_survey_comprehensive(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест создания опроса с полной конфигурацией."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.create_survey = AsyncMock(
                return_value={
                    "id": 26,
                    "title": "New Comprehensive Survey",
                    "description": "A comprehensive survey with all features",
                    "is_public": True,
                    "is_active": False,
                    "created_at": "2024-01-20T16:30:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "created_by": "admin",
                    "settings": {
                        "allow_multiple_responses": False,
                        "require_authentication": True,
                        "collect_email": True,
                        "show_progress_bar": True,
                        "randomize_questions": False,
                        "auto_save_responses": True,
                        "send_confirmation_email": True,
                        "response_limit": 1000,
                        "expiration_date": "2024-03-20T16:30:00Z",
                    },
                    "appearance": {
                        "theme": "modern",
                        "primary_color": "#3498db",
                        "background_color": "#ffffff",
                        "font_family": "Arial",
                        "logo_url": "https://example.com/logo.png",
                        "custom_css": ".survey-container { padding: 20px; }",
                    },
                    "notifications": {
                        "send_to_admin": True,
                        "admin_email": "admin@example.com",
                        "send_to_participants": True,
                        "notification_frequency": "daily",
                        "custom_message": "Thank you for participating!",
                    },
                    "analytics": {
                        "track_completion_time": True,
                        "track_drop_off_points": True,
                        "generate_reports": True,
                        "export_options": ["csv", "pdf", "json"],
                    },
                }
            )
            mock_service.return_value = mock_survey_service

            survey_data = {
                "title": "New Comprehensive Survey",
                "description": "A comprehensive survey with all features",
                "is_public": True,
                "is_active": False,
                "settings": {
                    "allow_multiple_responses": False,
                    "require_authentication": True,
                    "collect_email": True,
                    "show_progress_bar": True,
                    "response_limit": 1000,
                    "expiration_date": "2024-03-20T16:30:00Z",
                },
                "appearance": {
                    "theme": "modern",
                    "primary_color": "#3498db",
                    "background_color": "#ffffff",
                    "font_family": "Arial",
                    "logo_url": "https://example.com/logo.png",
                },
                "notifications": {
                    "send_to_admin": True,
                    "admin_email": "admin@example.com",
                    "send_to_participants": True,
                    "notification_frequency": "daily",
                },
                "analytics": {
                    "track_completion_time": True,
                    "track_drop_off_points": True,
                    "generate_reports": True,
                    "export_options": ["csv", "pdf", "json"],
                },
            }

            response = await api_client.post(
                api_client.url_for("create_admin_survey"), json=survey_data
            )

        # Assert
        assert response.status_code == 201
        created_survey = response.json()

        assert created_survey["id"] == 26
        assert created_survey["title"] == "New Comprehensive Survey"
        assert created_survey["is_public"] is True
        assert created_survey["is_active"] is False

        # Проверяем настройки
        settings = created_survey["settings"]
        assert settings["allow_multiple_responses"] is False
        assert settings["require_authentication"] is True
        assert settings["response_limit"] == 1000
        assert settings["auto_save_responses"] is True

        # Проверяем внешний вид
        appearance = created_survey["appearance"]
        assert appearance["theme"] == "modern"
        assert appearance["primary_color"] == "#3498db"
        assert appearance["font_family"] == "Arial"

        # Проверяем уведомления
        notifications = created_survey["notifications"]
        assert notifications["send_to_admin"] is True
        assert notifications["notification_frequency"] == "daily"

        # Проверяем аналитику
        analytics = created_survey["analytics"]
        assert analytics["track_completion_time"] is True
        assert "csv" in analytics["export_options"]

    async def test_update_survey_comprehensive(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест обновления опроса с полной конфигурацией."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.update_survey = AsyncMock(
                return_value={
                    "id": 1,
                    "title": "Updated Survey Title",
                    "description": "Updated description with new content",
                    "is_public": False,
                    "is_active": True,
                    "created_at": "2024-01-15T10:00:00Z",
                    "updated_at": "2024-01-20T16:30:00Z",
                    "created_by": "admin",
                    "updated_by": "admin",
                    "version": 2,
                    "change_log": [
                        {
                            "timestamp": "2024-01-20T16:30:00Z",
                            "user": "admin",
                            "changes": [
                                {
                                    "field": "title",
                                    "old": "Original Title",
                                    "new": "Updated Survey Title",
                                },
                                {"field": "is_public", "old": True, "new": False},
                                {"field": "is_active", "old": False, "new": True},
                            ],
                        }
                    ],
                    "settings": {
                        "allow_multiple_responses": True,
                        "require_authentication": False,
                        "collect_email": False,
                        "show_progress_bar": False,
                        "response_limit": 500,
                        "expiration_date": "2024-02-20T16:30:00Z",
                    },
                }
            )
            mock_service.return_value = mock_survey_service

            update_data = {
                "title": "Updated Survey Title",
                "description": "Updated description with new content",
                "is_public": False,
                "is_active": True,
                "settings": {
                    "allow_multiple_responses": True,
                    "require_authentication": False,
                    "collect_email": False,
                    "show_progress_bar": False,
                    "response_limit": 500,
                    "expiration_date": "2024-02-20T16:30:00Z",
                },
            }

            response = await api_client.put(
                api_client.url_for("update_admin_survey", survey_id=1), json=update_data
            )

        # Assert
        assert response.status_code == 200
        updated_survey = response.json()

        assert updated_survey["id"] == 1
        assert updated_survey["title"] == "Updated Survey Title"
        assert updated_survey["description"] == "Updated description with new content"
        assert updated_survey["is_public"] is False
        assert updated_survey["is_active"] is True
        assert updated_survey["version"] == 2

        # Проверяем журнал изменений
        change_log = updated_survey["change_log"]
        assert len(change_log) == 1
        changes = change_log[0]["changes"]
        assert len(changes) == 3
        assert changes[0]["field"] == "title"
        assert changes[0]["old"] == "Original Title"
        assert changes[0]["new"] == "Updated Survey Title"

        # Проверяем обновленные настройки
        settings = updated_survey["settings"]
        assert settings["allow_multiple_responses"] is True
        assert settings["require_authentication"] is False
        assert settings["response_limit"] == 500

    async def test_delete_survey_with_cleanup(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест удаления опроса с очисткой связанных данных."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.delete_survey = AsyncMock(
                return_value={
                    "success": True,
                    "deleted_survey": {
                        "id": 1,
                        "title": "Survey to Delete",
                        "questions_count": 5,
                        "responses_count": 23,
                    },
                    "cleanup_summary": {
                        "questions_deleted": 5,
                        "responses_deleted": 23,
                        "files_deleted": 2,
                        "notifications_cancelled": 8,
                        "scheduled_tasks_removed": 1,
                    },
                    "backup_created": {
                        "backup_id": "backup_survey_1_20240120",
                        "file_path": "/backups/survey_1_20240120.json",
                        "size": "2.5KB",
                        "created_at": "2024-01-20T16:30:00Z",
                    },
                    "deleted_at": "2024-01-20T16:30:00Z",
                    "deleted_by": "admin",
                }
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.delete(
                api_client.url_for("delete_admin_survey", survey_id=1),
                params={"create_backup": True, "force_delete": False},
            )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True

        # Проверяем информацию об удаленном опросе
        deleted_survey = result["deleted_survey"]
        assert deleted_survey["id"] == 1
        assert deleted_survey["title"] == "Survey to Delete"
        assert deleted_survey["questions_count"] == 5
        assert deleted_survey["responses_count"] == 23

        # Проверяем сводку очистки
        cleanup = result["cleanup_summary"]
        assert cleanup["questions_deleted"] == 5
        assert cleanup["responses_deleted"] == 23
        assert cleanup["files_deleted"] == 2
        assert cleanup["notifications_cancelled"] == 8
        assert cleanup["scheduled_tasks_removed"] == 1

        # Проверяем создание бэкапа
        backup = result["backup_created"]
        assert backup["backup_id"] == "backup_survey_1_20240120"
        assert backup["size"] == "2.5KB"
        assert "backup" in backup["file_path"]


class TestAdminSurveyBulkOperations:
    """Позитивные тесты массовых операций с опросами."""

    async def test_bulk_update_surveys(self, api_client: AsyncClient, admin_user):
        """Тест массового обновления опросов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.bulk_update_surveys = AsyncMock(
                return_value={
                    "success": True,
                    "updated_count": 3,
                    "failed_count": 0,
                    "updated_surveys": [
                        {"id": 1, "title": "Survey 1", "is_active": True},
                        {"id": 2, "title": "Survey 2", "is_active": True},
                        {"id": 3, "title": "Survey 3", "is_active": True},
                    ],
                    "failed_surveys": [],
                    "operation_summary": {
                        "total_requested": 3,
                        "successfully_updated": 3,
                        "failed_updates": 0,
                        "fields_updated": ["is_active", "updated_at"],
                        "execution_time": 0.45,
                    },
                }
            )
            mock_service.return_value = mock_survey_service

            bulk_update_data = {
                "survey_ids": [1, 2, 3],
                "updates": {"is_active": True, "updated_by": "admin"},
                "operation_type": "update_status",
            }

            response = await api_client.post(
                api_client.url_for("bulk_update_admin_surveys"), json=bulk_update_data
            )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["updated_count"] == 3
        assert result["failed_count"] == 0

        # Проверяем обновленные опросы
        updated_surveys = result["updated_surveys"]
        assert len(updated_surveys) == 3
        for survey in updated_surveys:
            assert survey["is_active"] is True

        # Проверяем сводку операции
        summary = result["operation_summary"]
        assert summary["total_requested"] == 3
        assert summary["successfully_updated"] == 3
        assert summary["failed_updates"] == 0
        assert "is_active" in summary["fields_updated"]
        assert summary["execution_time"] == 0.45

    async def test_bulk_delete_surveys(self, api_client: AsyncClient, admin_user):
        """Тест массового удаления опросов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.bulk_delete_surveys = AsyncMock(
                return_value={
                    "success": True,
                    "deleted_count": 2,
                    "failed_count": 1,
                    "deleted_surveys": [
                        {"id": 1, "title": "Survey 1", "responses_count": 5},
                        {"id": 2, "title": "Survey 2", "responses_count": 0},
                    ],
                    "failed_surveys": [
                        {
                            "id": 3,
                            "title": "Survey 3",
                            "error": "Survey has active responses",
                        }
                    ],
                    "cleanup_summary": {
                        "total_questions_deleted": 12,
                        "total_responses_deleted": 5,
                        "total_files_deleted": 3,
                        "backups_created": 2,
                    },
                    "operation_summary": {
                        "total_requested": 3,
                        "successfully_deleted": 2,
                        "failed_deletions": 1,
                        "execution_time": 1.23,
                    },
                }
            )
            mock_service.return_value = mock_survey_service

            bulk_delete_data = {
                "survey_ids": [1, 2, 3],
                "create_backups": True,
                "force_delete": False,
            }

            response = await api_client.post(
                api_client.url_for("bulk_delete_admin_surveys"), json=bulk_delete_data
            )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["deleted_count"] == 2
        assert result["failed_count"] == 1

        # Проверяем удаленные опросы
        deleted_surveys = result["deleted_surveys"]
        assert len(deleted_surveys) == 2
        assert deleted_surveys[0]["id"] == 1
        assert deleted_surveys[1]["id"] == 2

        # Проверяем неудачные удаления
        failed_surveys = result["failed_surveys"]
        assert len(failed_surveys) == 1
        assert failed_surveys[0]["id"] == 3
        assert "active responses" in failed_surveys[0]["error"]

        # Проверяем сводку очистки
        cleanup = result["cleanup_summary"]
        assert cleanup["total_questions_deleted"] == 12
        assert cleanup["total_responses_deleted"] == 5
        assert cleanup["backups_created"] == 2

    async def test_bulk_export_surveys(self, api_client: AsyncClient, admin_user):
        """Тест массового экспорта опросов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.bulk_export_surveys = AsyncMock(
                return_value={
                    "export_id": "bulk_export_20240120_163000",
                    "status": "completed",
                    "format": "json",
                    "surveys_count": 5,
                    "file_url": "https://example.com/exports/bulk_surveys_20240120_163000.json",
                    "file_size": "15.2MB",
                    "created_at": "2024-01-20T16:30:00Z",
                    "expires_at": "2024-01-27T16:30:00Z",
                    "included_data": {
                        "survey_metadata": True,
                        "questions": True,
                        "responses": True,
                        "analytics": True,
                        "files": False,
                    },
                    "export_summary": {
                        "total_surveys": 5,
                        "total_questions": 67,
                        "total_responses": 1234,
                        "total_records": 1306,
                        "compression_ratio": 0.73,
                    },
                }
            )
            mock_service.return_value = mock_survey_service

            export_data = {
                "survey_ids": [1, 2, 3, 4, 5],
                "format": "json",
                "include_data": {
                    "survey_metadata": True,
                    "questions": True,
                    "responses": True,
                    "analytics": True,
                    "files": False,
                },
                "compression": True,
            }

            response = await api_client.post(
                api_client.url_for("bulk_export_admin_surveys"), json=export_data
            )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["export_id"] == "bulk_export_20240120_163000"
        assert result["status"] == "completed"
        assert result["format"] == "json"
        assert result["surveys_count"] == 5
        assert result["file_size"] == "15.2MB"

        # Проверяем включенные данные
        included_data = result["included_data"]
        assert included_data["survey_metadata"] is True
        assert included_data["questions"] is True
        assert included_data["responses"] is True
        assert included_data["analytics"] is True
        assert included_data["files"] is False

        # Проверяем сводку экспорта
        summary = result["export_summary"]
        assert summary["total_surveys"] == 5
        assert summary["total_questions"] == 67
        assert summary["total_responses"] == 1234
        assert summary["compression_ratio"] == 0.73


class TestAdminSurveyAnalytics:
    """Позитивные тесты аналитики опросов."""

    async def test_get_survey_detailed_analytics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения детальной аналитики опроса."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_survey_detailed_analytics = AsyncMock(
                return_value={
                    "survey_id": 1,
                    "survey_title": "Customer Satisfaction Survey",
                    "analytics_period": {
                        "start_date": "2024-01-01T00:00:00Z",
                        "end_date": "2024-01-20T23:59:59Z",
                        "duration_days": 20,
                    },
                    "response_analytics": {
                        "total_responses": 234,
                        "completed_responses": 186,
                        "partial_responses": 48,
                        "completion_rate": 0.795,
                        "average_completion_time": 4.2,
                        "median_completion_time": 3.8,
                        "bounce_rate": 0.15,
                        "drop_off_points": [
                            {"question_id": 5, "drop_off_rate": 0.08},
                            {"question_id": 12, "drop_off_rate": 0.12},
                        ],
                    },
                    "engagement_metrics": {
                        "unique_visitors": 312,
                        "return_visitors": 67,
                        "conversion_rate": 0.596,
                        "average_time_on_page": 6.8,
                        "pages_per_session": 1.3,
                        "social_shares": 23,
                        "email_forwards": 45,
                    },
                    "question_performance": [
                        {
                            "question_id": 1,
                            "question_text": "How satisfied are you with our service?",
                            "question_type": "rating",
                            "response_count": 186,
                            "completion_rate": 1.0,
                            "average_response_time": 2.1,
                            "skip_rate": 0.0,
                            "satisfaction_score": 4.2,
                        },
                        {
                            "question_id": 2,
                            "question_text": "What can we improve?",
                            "question_type": "text",
                            "response_count": 156,
                            "completion_rate": 0.839,
                            "average_response_time": 8.5,
                            "skip_rate": 0.161,
                            "average_word_count": 12.3,
                        },
                    ],
                    "demographic_breakdown": {
                        "age_groups": {
                            "18-25": 45,
                            "26-35": 78,
                            "36-45": 62,
                            "46-55": 34,
                            "56+": 15,
                        },
                        "gender": {
                            "male": 98,
                            "female": 112,
                            "other": 8,
                            "prefer_not_to_say": 16,
                        },
                        "locations": {
                            "North America": 145,
                            "Europe": 67,
                            "Asia": 18,
                            "Other": 4,
                        },
                    },
                    "temporal_analysis": {
                        "responses_by_hour": {
                            "0": 2,
                            "1": 1,
                            "2": 0,
                            "3": 0,
                            "4": 0,
                            "5": 0,
                            "6": 3,
                            "7": 8,
                            "8": 12,
                            "9": 18,
                            "10": 22,
                            "11": 19,
                            "12": 15,
                            "13": 17,
                            "14": 24,
                            "15": 28,
                            "16": 31,
                            "17": 26,
                            "18": 18,
                            "19": 12,
                            "20": 8,
                            "21": 5,
                            "22": 3,
                            "23": 2,
                        },
                        "responses_by_day": {
                            "Monday": 45,
                            "Tuesday": 52,
                            "Wednesday": 48,
                            "Thursday": 38,
                            "Friday": 29,
                            "Saturday": 12,
                            "Sunday": 10,
                        },
                        "peak_response_time": "15:00-16:00",
                        "best_response_day": "Tuesday",
                    },
                }
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.get(
                api_client.url_for("get_admin_survey_detailed_analytics", survey_id=1),
                params={"include_demographics": True, "include_temporal": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["survey_id"] == 1
        assert data["survey_title"] == "Customer Satisfaction Survey"

        # Проверяем аналитику ответов
        response_analytics = data["response_analytics"]
        assert response_analytics["total_responses"] == 234
        assert response_analytics["completion_rate"] == 0.795
        assert response_analytics["average_completion_time"] == 4.2
        assert len(response_analytics["drop_off_points"]) == 2

        # Проверяем метрики вовлеченности
        engagement = data["engagement_metrics"]
        assert engagement["unique_visitors"] == 312
        assert engagement["conversion_rate"] == 0.596
        assert engagement["social_shares"] == 23

        # Проверяем производительность вопросов
        question_perf = data["question_performance"]
        assert len(question_perf) == 2
        assert question_perf[0]["completion_rate"] == 1.0
        assert question_perf[1]["skip_rate"] == 0.161

        # Проверяем демографический анализ
        demographics = data["demographic_breakdown"]
        assert demographics["age_groups"]["26-35"] == 78
        assert demographics["gender"]["female"] == 112
        assert demographics["locations"]["North America"] == 145

        # Проверяем временной анализ
        temporal = data["temporal_analysis"]
        assert temporal["responses_by_hour"]["15"] == 28
        assert temporal["responses_by_day"]["Tuesday"] == 52
        assert temporal["peak_response_time"] == "15:00-16:00"
        assert temporal["best_response_day"] == "Tuesday"

    async def test_get_survey_comparison_analytics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения сравнительной аналитики опросов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_survey_comparison_analytics = AsyncMock(
                return_value={
                    "comparison_id": "compare_20240120_163000",
                    "surveys_compared": [
                        {"id": 1, "title": "Survey A", "created_at": "2024-01-01"},
                        {"id": 2, "title": "Survey B", "created_at": "2024-01-10"},
                    ],
                    "comparison_metrics": {
                        "response_rates": {
                            "survey_1": {"total": 234, "completed": 186, "rate": 0.795},
                            "survey_2": {"total": 156, "completed": 142, "rate": 0.910},
                        },
                        "completion_times": {
                            "survey_1": {"avg": 4.2, "median": 3.8},
                            "survey_2": {"avg": 3.1, "median": 2.9},
                        },
                        "satisfaction_scores": {
                            "survey_1": {
                                "avg": 4.2,
                                "distribution": [2, 8, 24, 98, 54],
                            },
                            "survey_2": {
                                "avg": 4.5,
                                "distribution": [1, 4, 15, 76, 46],
                            },
                        },
                        "engagement_levels": {
                            "survey_1": {"bounce_rate": 0.15, "time_on_page": 6.8},
                            "survey_2": {"bounce_rate": 0.09, "time_on_page": 7.2},
                        },
                    },
                    "statistical_analysis": {
                        "significance_tests": {
                            "completion_rate": {"p_value": 0.032, "significant": True},
                            "satisfaction_score": {
                                "p_value": 0.156,
                                "significant": False,
                            },
                            "completion_time": {"p_value": 0.008, "significant": True},
                        },
                        "effect_sizes": {
                            "completion_rate": {
                                "cohens_d": 0.45,
                                "interpretation": "medium",
                            },
                            "satisfaction_score": {
                                "cohens_d": 0.12,
                                "interpretation": "small",
                            },
                        },
                    },
                    "recommendations": [
                        {
                            "type": "improvement",
                            "metric": "completion_rate",
                            "suggestion": "Consider implementing progress indicators like Survey B",
                            "expected_improvement": "15-20%",
                        },
                        {
                            "type": "optimization",
                            "metric": "completion_time",
                            "suggestion": "Reduce question complexity based on Survey B's approach",
                            "expected_improvement": "20-25%",
                        },
                    ],
                }
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.get(
                api_client.url_for("get_admin_survey_comparison_analytics"),
                params={"survey_ids": "1,2", "include_statistics": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["comparison_id"] == "compare_20240120_163000"
        assert len(data["surveys_compared"]) == 2

        # Проверяем метрики сравнения
        metrics = data["comparison_metrics"]
        assert metrics["response_rates"]["survey_1"]["rate"] == 0.795
        assert metrics["response_rates"]["survey_2"]["rate"] == 0.910
        assert metrics["completion_times"]["survey_1"]["avg"] == 4.2
        assert metrics["completion_times"]["survey_2"]["avg"] == 3.1

        # Проверяем статистический анализ
        stats = data["statistical_analysis"]
        assert stats["significance_tests"]["completion_rate"]["significant"] is True
        assert stats["significance_tests"]["satisfaction_score"]["significant"] is False
        assert stats["effect_sizes"]["completion_rate"]["interpretation"] == "medium"

        # Проверяем рекомендации
        recommendations = data["recommendations"]
        assert len(recommendations) == 2
        assert recommendations[0]["type"] == "improvement"
        assert recommendations[0]["expected_improvement"] == "15-20%"

    async def test_get_survey_predictive_analytics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения предиктивной аналитики опроса."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.admin.get_survey_service") as mock_service:
            mock_survey_service = MagicMock()
            mock_survey_service.get_survey_predictive_analytics = AsyncMock(
                return_value={
                    "survey_id": 1,
                    "prediction_model": "ensemble_v2.1",
                    "prediction_accuracy": 0.87,
                    "last_updated": "2024-01-20T16:30:00Z",
                    "response_predictions": {
                        "next_7_days": {
                            "predicted_responses": 125,
                            "confidence_interval": [98, 152],
                            "confidence_level": 0.95,
                        },
                        "next_30_days": {
                            "predicted_responses": 456,
                            "confidence_interval": [389, 523],
                            "confidence_level": 0.95,
                        },
                        "total_expected": {
                            "predicted_responses": 890,
                            "confidence_interval": [756, 1024],
                            "confidence_level": 0.95,
                        },
                    },
                    "completion_predictions": {
                        "predicted_completion_rate": 0.82,
                        "current_completion_rate": 0.795,
                        "improvement_factors": [
                            {"factor": "question_optimization", "impact": 0.03},
                            {"factor": "ui_improvements", "impact": 0.02},
                        ],
                    },
                    "demographic_predictions": {
                        "age_group_participation": {
                            "18-25": {"predicted": 89, "trend": "increasing"},
                            "26-35": {"predicted": 156, "trend": "stable"},
                            "36-45": {"predicted": 123, "trend": "decreasing"},
                        },
                        "geographic_distribution": {
                            "North America": {"predicted": 287, "trend": "increasing"},
                            "Europe": {"predicted": 134, "trend": "stable"},
                            "Asia": {"predicted": 45, "trend": "increasing"},
                        },
                    },
                    "optimization_suggestions": [
                        {
                            "area": "question_ordering",
                            "current_score": 0.72,
                            "optimized_score": 0.89,
                            "improvement": 0.17,
                            "implementation_effort": "low",
                        },
                        {
                            "area": "response_incentives",
                            "current_score": 0.65,
                            "optimized_score": 0.78,
                            "improvement": 0.13,
                            "implementation_effort": "medium",
                        },
                    ],
                    "risk_factors": [
                        {
                            "factor": "survey_fatigue",
                            "risk_level": "medium",
                            "probability": 0.35,
                            "impact": "completion_rate_drop",
                            "mitigation": "Reduce survey frequency",
                        },
                        {
                            "factor": "seasonal_trends",
                            "risk_level": "low",
                            "probability": 0.15,
                            "impact": "response_volume_drop",
                            "mitigation": "Adjust launch timing",
                        },
                    ],
                }
            )
            mock_service.return_value = mock_survey_service

            response = await api_client.get(
                api_client.url_for(
                    "get_admin_survey_predictive_analytics", survey_id=1
                ),
                params={"include_suggestions": True, "include_risks": True},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["survey_id"] == 1
        assert data["prediction_model"] == "ensemble_v2.1"
        assert data["prediction_accuracy"] == 0.87

        # Проверяем предсказания ответов
        response_pred = data["response_predictions"]
        assert response_pred["next_7_days"]["predicted_responses"] == 125
        assert response_pred["next_30_days"]["predicted_responses"] == 456
        assert response_pred["total_expected"]["predicted_responses"] == 890

        # Проверяем предсказания завершения
        completion_pred = data["completion_predictions"]
        assert completion_pred["predicted_completion_rate"] == 0.82
        assert completion_pred["current_completion_rate"] == 0.795
        assert len(completion_pred["improvement_factors"]) == 2

        # Проверяем демографические предсказания
        demographic_pred = data["demographic_predictions"]
        assert demographic_pred["age_group_participation"]["26-35"]["trend"] == "stable"
        assert (
            demographic_pred["geographic_distribution"]["Asia"]["trend"] == "increasing"
        )

        # Проверяем предложения по оптимизации
        suggestions = data["optimization_suggestions"]
        assert len(suggestions) == 2
        assert suggestions[0]["area"] == "question_ordering"
        assert suggestions[0]["improvement"] == 0.17
        assert suggestions[1]["implementation_effort"] == "medium"

        # Проверяем факторы риска
        risks = data["risk_factors"]
        assert len(risks) == 2
        assert risks[0]["factor"] == "survey_fatigue"
        assert risks[0]["risk_level"] == "medium"
        assert risks[1]["probability"] == 0.15
