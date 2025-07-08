"""
Тесты для Reports роутера.

Тесты покрывают генерацию PDF отчетов, аналитики, экспорт данных
и все основные операции с отчетами.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from datetime import datetime, timedelta
from io import BytesIO

from tests.factories import (
    UserFactory,
    AdminUserFactory,
    VerifiedUserFactory,
    SurveyFactory,
    PublicSurveyFactory,
    create_test_users_batch,
    create_test_surveys_batch,
    create_survey_responses,
    AuthenticatedRespondentFactory,
)


class TestReportsRouter:
    """Тестовый класс для Reports роутера."""

    @pytest.mark.asyncio
    async def test_generate_survey_report_success(
        self, api_client, async_session, mock_pdf_service, sample_survey_data
    ):
        """Тест успешной генерации PDF отчета по опросу."""
        # Arrange
        survey = sample_survey_data
        expected_pdf = b"PDF_CONTENT_HERE"

        mock_pdf_service.generate_survey_report.return_value = expected_pdf

        # Act
        response = await api_client.post(
            api_client.url_for("generate_survey_report"),
            json={"survey_id": survey.id, "format": "pdf"},
        )

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == expected_pdf
        mock_pdf_service.generate_survey_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_survey_report_with_custom_options(
        self,
        api_client,
        async_session,
        mock_pdf_service,
        sample_survey_data,
        pdf_generation_options,
    ):
        """Тест генерации PDF отчета с кастомными опциями."""
        # Arrange
        survey = sample_survey_data
        expected_pdf = b"CUSTOM_PDF_CONTENT"

        mock_pdf_service.generate_survey_report.return_value = expected_pdf

        # Act
        response = await api_client.post(
            api_client.url_for("generate_survey_report"),
            json={
                "survey_id": survey.id,
                "format": "pdf",
                "options": pdf_generation_options,
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.content == expected_pdf
        mock_pdf_service.generate_survey_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_user_report_success(
        self, api_client, async_session, mock_pdf_service, sample_user_data
    ):
        """Тест успешной генерации PDF отчета пользователя."""
        # Arrange
        user = sample_user_data
        expected_pdf = b"USER_PDF_CONTENT"

        mock_pdf_service.generate_user_report.return_value = expected_pdf

        # Act
        response = await api_client.post(
            api_client.url_for("generate_user_report"),
            json={"user_id": user.id, "format": "pdf"},
        )

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == expected_pdf
        mock_pdf_service.generate_user_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_analytics_report_success(
        self, api_client, async_session, mock_pdf_service, sample_analytics_data
    ):
        """Тест успешной генерации аналитического отчета."""
        # Arrange
        expected_pdf = b"ANALYTICS_PDF_CONTENT"

        mock_pdf_service.generate_analytics_report.return_value = expected_pdf

        # Act
        response = await api_client.post(
            api_client.url_for("generate_analytics_report"),
            json={
                "date_from": "2024-01-01",
                "date_to": "2024-01-31",
                "format": "pdf",
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.content == expected_pdf
        mock_pdf_service.generate_analytics_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_templates(
        self, api_client, mock_pdf_service, pdf_templates
    ):
        """Тест получения доступных шаблонов отчетов."""
        # Arrange
        mock_pdf_service.get_available_templates.return_value = pdf_templates

        # Act
        response = await api_client.get(api_client.url_for("get_report_templates"))

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "survey_report" in data
        assert "user_report" in data
        assert "analytics_report" in data
        mock_pdf_service.get_available_templates.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_report_success(
        self, api_client, async_session, mock_file_storage, sample_pdf_content
    ):
        """Тест успешного скачивания отчета."""
        # Arrange
        report_id = "test-report-123"

        mock_file_storage.get_file.return_value = sample_pdf_content
        mock_file_storage.file_exists.return_value = True

        # Act
        response = await api_client.get(
            api_client.url_for("download_report", report_id=report_id)
        )

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == sample_pdf_content
        mock_file_storage.get_file.assert_called_once_with(report_id)

    @pytest.mark.asyncio
    async def test_get_report_status_success(self, api_client, mock_pdf_service):
        """Тест получения статуса генерации отчета."""
        # Arrange
        report_id = "test-report-456"
        expected_status = {
            "id": report_id,
            "status": "completed",
            "progress": 100,
            "created_at": datetime.utcnow().isoformat(),
            "download_url": f"/api/reports/download/{report_id}",
        }

        mock_pdf_service.get_generation_status.return_value = expected_status

        # Act
        response = await api_client.get(
            api_client.url_for("get_report_status", report_id=report_id)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert data["status"] == "completed"
        assert data["progress"] == 100
        mock_pdf_service.get_generation_status.assert_called_once_with(report_id)

    @pytest.mark.asyncio
    async def test_generate_bulk_reports_success(
        self, api_client, async_session, mock_pdf_service, bulk_responses_data
    ):
        """Тест генерации массовых отчетов."""
        # Arrange
        bulk_data = bulk_responses_data
        survey_ids = [bulk_data["survey"].id]

        mock_pdf_service.generate_bulk_reports.return_value = {
            "job_id": "bulk-job-123",
            "status": "started",
            "estimated_completion": datetime.utcnow() + timedelta(minutes=5),
        }

        # Act
        response = await api_client.post(
            api_client.url_for("generate_bulk_reports"),
            json={
                "survey_ids": survey_ids,
                "format": "pdf",
                "send_email": True,
            },
        )

        # Assert
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["job_id"] == "bulk-job-123"
        assert data["status"] == "started"
        mock_pdf_service.generate_bulk_reports.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_survey_data_csv(
        self,
        api_client,
        async_session,
        mock_reports_service,
        sample_survey_with_questions,
    ):
        """Тест экспорта данных опроса в CSV."""
        # Arrange
        survey_data = sample_survey_with_questions
        survey = survey_data["survey"]

        csv_content = "question,answer,user\nQ1,A1,user1\nQ2,A2,user2"
        mock_reports_service.export_survey_data.return_value = csv_content

        # Act
        response = await api_client.get(
            api_client.url_for("export_survey_data"),
            params={"survey_id": survey.id, "format": "csv"},
        )

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert csv_content in response.text
        mock_reports_service.export_survey_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_survey_analytics(
        self,
        api_client,
        async_session,
        mock_analytics_service,
        comprehensive_analytics_data,
    ):
        """Тест получения аналитики опроса."""
        # Arrange
        analytics_data = comprehensive_analytics_data
        survey = analytics_data[0]["survey"]

        expected_analytics = {
            "survey_id": survey.id,
            "total_responses": 15,
            "completion_rate": 85.5,
            "average_time": 180,
            "demographics": {"age_groups": {"18-25": 5, "26-35": 10}},
        }

        mock_analytics_service.get_survey_analytics.return_value = expected_analytics

        # Act
        response = await api_client.get(
            api_client.url_for("get_survey_analytics", survey_id=survey.id)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["survey_id"] == survey.id
        assert data["total_responses"] == 15
        assert data["completion_rate"] == 85.5
        mock_analytics_service.get_survey_analytics.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_custom_report_success(
        self,
        api_client,
        async_session,
        mock_pdf_service,
        sample_survey_data,
        sample_user_data,
    ):
        """Тест генерации кастомного отчета."""
        # Arrange
        survey = sample_survey_data
        user = sample_user_data

        custom_config = {
            "title": "Custom Report Title",
            "include_charts": True,
            "include_demographics": True,
            "filters": {"date_from": "2024-01-01", "date_to": "2024-01-31"},
        }

        expected_pdf = b"CUSTOM_REPORT_PDF"
        mock_pdf_service.generate_custom_report.return_value = expected_pdf

        # Act
        response = await api_client.post(
            api_client.url_for("generate_custom_report"),
            json={
                "survey_id": survey.id,
                "user_id": user.id,
                "config": custom_config,
                "format": "pdf",
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.content == expected_pdf
        mock_pdf_service.generate_custom_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_report_generation(
        self, api_client, async_session, mock_pdf_service, sample_survey_data
    ):
        """Тест планирования генерации отчета."""
        # Arrange
        survey = sample_survey_data

        schedule_config = {
            "frequency": "weekly",
            "day_of_week": "monday",
            "time": "09:00",
            "email_recipients": ["admin@example.com"],
        }

        expected_schedule = {
            "id": "schedule-123",
            "survey_id": survey.id,
            "frequency": "weekly",
            "status": "active",
            "next_run": datetime.utcnow() + timedelta(days=7),
        }

        mock_pdf_service.schedule_report_generation.return_value = expected_schedule

        # Act
        response = await api_client.post(
            api_client.url_for("schedule_report"),
            json={
                "survey_id": survey.id,
                "schedule": schedule_config,
                "format": "pdf",
            },
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "schedule-123"
        assert data["survey_id"] == survey.id
        assert data["frequency"] == "weekly"
        assert data["status"] == "active"
        mock_pdf_service.schedule_report_generation.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_report_history(
        self, api_client, async_session, mock_reports_service, sample_user_data
    ):
        """Тест получения истории отчетов."""
        # Arrange
        user = sample_user_data

        expected_history = [
            {
                "id": "report-1",
                "title": "Survey Report",
                "created_at": datetime.utcnow().isoformat(),
                "status": "completed",
                "file_size": 1024,
            },
            {
                "id": "report-2",
                "title": "User Report",
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "status": "completed",
                "file_size": 2048,
            },
        ]

        mock_reports_service.get_user_report_history.return_value = expected_history

        # Act
        response = await api_client.get(
            api_client.url_for("get_report_history"),
            params={"user_id": user.id, "limit": 10},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "report-1"
        assert data[1]["id"] == "report-2"
        mock_reports_service.get_user_report_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_report_success(
        self, api_client, async_session, mock_file_storage, sample_user_data
    ):
        """Тест успешного удаления отчета."""
        # Arrange
        user = sample_user_data
        report_id = "report-to-delete"

        mock_file_storage.file_exists.return_value = True
        mock_file_storage.delete_file.return_value = True

        # Act
        response = await api_client.delete(
            api_client.url_for("delete_report", report_id=report_id)
        )

        # Assert
        assert response.status_code == 204
        mock_file_storage.delete_file.assert_called_once_with(report_id)

    @pytest.mark.asyncio
    async def test_get_report_metadata(self, api_client, mock_pdf_service):
        """Тест получения метаданных отчета."""
        # Arrange
        report_id = "metadata-report-123"

        expected_metadata = {
            "id": report_id,
            "title": "Sample Report",
            "created_at": datetime.utcnow().isoformat(),
            "file_size": 2048,
            "format": "pdf",
            "pages": 5,
            "creator": "test_user",
        }

        mock_pdf_service.get_pdf_metadata.return_value = expected_metadata

        # Act
        response = await api_client.get(
            api_client.url_for("get_report_metadata", report_id=report_id)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert data["title"] == "Sample Report"
        assert data["format"] == "pdf"
        assert data["pages"] == 5
        mock_pdf_service.get_pdf_metadata.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_large_report_generation(
        self, api_client, async_session, mock_pdf_service, performance_test_data
    ):
        """Тест производительности генерации больших отчетов."""
        # Arrange
        perf_data = performance_test_data
        surveys = perf_data["surveys"]

        large_pdf = b"LARGE_PDF_CONTENT" * 1000  # Имитация большого PDF
        mock_pdf_service.generate_survey_report.return_value = large_pdf

        # Act
        start_time = datetime.utcnow()
        response = await api_client.post(
            api_client.url_for("generate_survey_report"),
            json={
                "survey_id": surveys[0].id,
                "format": "pdf",
                "options": {"include_all_responses": True},
            },
        )
        end_time = datetime.utcnow()

        # Assert
        assert response.status_code == 200
        assert len(response.content) > 1000

        # Проверяем время выполнения (не должно превышать 30 секунд)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 30

        mock_pdf_service.generate_survey_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_report_generation(
        self, api_client, async_session, mock_pdf_service, sample_survey_data
    ):
        """Тест параллельной генерации отчетов."""
        # Arrange
        survey = sample_survey_data

        mock_pdf_service.generate_survey_report.return_value = b"CONCURRENT_PDF"

        # Act - создаем несколько параллельных запросов
        import asyncio

        async def generate_report():
            return await api_client.post(
                api_client.url_for("generate_survey_report"),
                json={"survey_id": survey.id, "format": "pdf"},
            )

        # Запускаем 5 параллельных генераций
        tasks = [generate_report() for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # Assert
        for response in responses:
            assert response.status_code == 200
            assert response.content == b"CONCURRENT_PDF"

        # Проверяем, что сервис был вызван для каждого запроса
        assert mock_pdf_service.generate_survey_report.call_count == 5
