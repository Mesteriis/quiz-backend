"""
Тесты для Reports API роутера Quiz App.

Этот модуль содержит тесты для генерации PDF отчетов
для опросов и пользователей.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from unittest.mock import AsyncMock

from models import User, Survey, Question, Response, UserData
from factories.survey_factory import SurveyFactory
from factories.user_factory import UserFactory
from factories.question_factory import QuestionFactory
from factories.response_factory import ResponseFactory


class TestSurveyPdfReports:
    """Тесты для генерации PDF отчетов по опросам."""

    @pytest_asyncio.async_test
    async def test_generate_survey_pdf_success(
        self, api_client, admin_headers, db_session, mock_pdf_service
    ):
        """Тест успешной генерации PDF отчета для опроса."""
        # Настраиваем mock для PDF сервиса
        mock_pdf_bytes = b"fake-pdf-content"
        mock_pdf_service.generate_survey_report.return_value = mock_pdf_bytes

        # Создаем опрос с данными
        survey_factory = SurveyFactory(db_session)
        question_factory = QuestionFactory(db_session)
        response_factory = ResponseFactory(db_session)
        user_factory = UserFactory(db_session)

        survey = await survey_factory.create(title="Test Survey")
        question = await question_factory.create(
            survey_id=survey.id, title="Test Question", question_type="text"
        )

        user = await user_factory.create()
        await response_factory.create(
            question_id=question.id,
            user_id=user.id,
            response_data={"answer": "Test Answer"},
        )

        response = await api_client.auth_get(
            f"/api/reports/surveys/{survey.id}/pdf", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert (
            f"survey_{survey.id}_report.pdf" in response.headers["content-disposition"]
        )
        assert response.content == mock_pdf_bytes

        # Проверяем что PDF сервис был вызван
        mock_pdf_service.generate_survey_report.assert_called_once()
        args = mock_pdf_service.generate_survey_report.call_args[0]

        # Проверяем данные опроса
        survey_data = args[0]
        assert survey_data["id"] == survey.id
        assert survey_data["title"] == "Test Survey"

        # Проверяем данные ответов
        responses_data = args[1]
        assert len(responses_data) >= 1
        assert responses_data[0]["question"]["id"] == question.id
        assert responses_data[0]["user"]["id"] == user.id

        # Проверяем аналитику
        analytics_data = args[2]
        assert "unique_respondents" in analytics_data
        assert "total_responses" in analytics_data
        assert "completion_rate" in analytics_data

    @pytest_asyncio.async_test
    async def test_generate_survey_pdf_empty_survey(
        self, api_client, admin_headers, db_session, mock_pdf_service
    ):
        """Тест генерации PDF для опроса без ответов."""
        mock_pdf_bytes = b"empty-survey-pdf"
        mock_pdf_service.generate_survey_report.return_value = mock_pdf_bytes

        # Создаем опрос без ответов
        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create(title="Empty Survey")

        response = await api_client.auth_get(
            f"/api/reports/surveys/{survey.id}/pdf", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.content == mock_pdf_bytes

        # Проверяем что аналитика содержит нули
        args = mock_pdf_service.generate_survey_report.call_args[0]
        analytics_data = args[2]
        assert analytics_data["unique_respondents"] == 0
        assert analytics_data["total_responses"] == 0
        assert analytics_data["completion_rate"] == 0

    @pytest_asyncio.async_test
    async def test_generate_survey_pdf_not_found(self, api_client, admin_headers):
        """Тест генерации PDF для несуществующего опроса."""
        response = await api_client.auth_get(
            "/api/reports/surveys/99999/pdf", headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest_asyncio.async_test
    async def test_generate_survey_pdf_requires_admin(
        self, api_client, auth_headers, regular_user, db_session
    ):
        """Тест что генерация PDF опроса требует админ права."""
        headers = await auth_headers(regular_user)

        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create()

        response = await api_client.auth_get(
            f"/api/reports/surveys/{survey.id}/pdf", headers=headers
        )

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest_asyncio.async_test
    async def test_generate_survey_pdf_requires_auth(self, api_client, db_session):
        """Тест что генерация PDF опроса требует авторизацию."""
        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create()

        response = await api_client.get(f"/api/reports/surveys/{survey.id}/pdf")

        assert response.status_code == 401

    @pytest_asyncio.async_test
    async def test_generate_survey_pdf_service_error(
        self, api_client, admin_headers, db_session, mock_pdf_service
    ):
        """Тест обработки ошибки PDF сервиса."""
        # Настраиваем mock для выброса ошибки
        mock_pdf_service.generate_survey_report.side_effect = Exception(
            "PDF generation failed"
        )

        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create()

        response = await api_client.auth_get(
            f"/api/reports/surveys/{survey.id}/pdf", headers=admin_headers
        )

        assert response.status_code == 500
        assert "failed to generate" in response.json()["detail"].lower()


class TestUserPdfReports:
    """Тесты для генерации PDF отчетов пользователей."""

    @pytest_asyncio.async_test
    async def test_generate_user_pdf_success_own_report(
        self, api_client, auth_headers, db_session, mock_pdf_service
    ):
        """Тест успешной генерации PDF отчета для собственных ответов."""
        mock_pdf_bytes = b"user-pdf-content"
        mock_pdf_service.generate_user_report.return_value = mock_pdf_bytes

        # Создаем пользователя с ответами
        user_factory = UserFactory(db_session)
        survey_factory = SurveyFactory(db_session)
        question_factory = QuestionFactory(db_session)
        response_factory = ResponseFactory(db_session)

        user = await user_factory.create()
        survey = await survey_factory.create()
        question = await question_factory.create(survey_id=survey.id)

        await response_factory.create(
            question_id=question.id,
            user_id=user.id,
            response_data={"answer": "My Answer"},
        )

        headers = await auth_headers(user)

        response = await api_client.auth_get(
            f"/api/reports/users/{user.id}/pdf", headers=headers
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert f"user_{user.id}_report.pdf" in response.headers["content-disposition"]
        assert response.content == mock_pdf_bytes

        # Проверяем что PDF сервис был вызван
        mock_pdf_service.generate_user_report.assert_called_once()

    @pytest_asyncio.async_test
    async def test_generate_user_pdf_admin_access(
        self, api_client, admin_headers, db_session, mock_pdf_service
    ):
        """Тест генерации PDF отчета администратором для любого пользователя."""
        mock_pdf_bytes = b"admin-user-pdf-content"
        mock_pdf_service.generate_user_report.return_value = mock_pdf_bytes

        # Создаем пользователя
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        response = await api_client.auth_get(
            f"/api/reports/users/{user.id}/pdf", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.content == mock_pdf_bytes

    @pytest_asyncio.async_test
    async def test_generate_user_pdf_forbidden_other_user(
        self, api_client, auth_headers, db_session
    ):
        """Тест что пользователь не может генерировать отчет для другого пользователя."""
        user_factory = UserFactory(db_session)
        user1 = await user_factory.create()
        user2 = await user_factory.create()

        headers = await auth_headers(user1)

        response = await api_client.auth_get(
            f"/api/reports/users/{user2.id}/pdf", headers=headers
        )

        assert response.status_code == 403
        assert "own responses" in response.json()["detail"].lower()

    @pytest_asyncio.async_test
    async def test_generate_user_pdf_not_found(self, api_client, admin_headers):
        """Тест генерации PDF для несуществующего пользователя."""
        response = await api_client.auth_get(
            "/api/reports/users/99999/pdf", headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest_asyncio.async_test
    async def test_generate_user_pdf_requires_auth(self, api_client, db_session):
        """Тест что генерация PDF пользователя требует авторизацию."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        response = await api_client.get(f"/api/reports/users/{user.id}/pdf")

        assert response.status_code == 401

    @pytest_asyncio.async_test
    async def test_generate_user_pdf_empty_responses(
        self, api_client, auth_headers, db_session, mock_pdf_service
    ):
        """Тест генерации PDF для пользователя без ответов."""
        mock_pdf_bytes = b"empty-user-pdf"
        mock_pdf_service.generate_user_report.return_value = mock_pdf_bytes

        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        response = await api_client.auth_get(
            f"/api/reports/users/{user.id}/pdf", headers=headers
        )

        assert response.status_code == 200
        assert response.content == mock_pdf_bytes

        # Проверяем что сервис был вызван с пустыми данными
        args = mock_pdf_service.generate_user_report.call_args[0]
        responses_data = args[1]
        assert len(responses_data) == 0


class TestMyResponsesPdfReports:
    """Тесты для генерации PDF отчетов собственных ответов."""

    @pytest_asyncio.async_test
    async def test_generate_my_responses_pdf_success(
        self, api_client, auth_headers, db_session, mock_pdf_service
    ):
        """Тест успешной генерации PDF отчета собственных ответов."""
        mock_pdf_bytes = b"my-responses-pdf-content"
        mock_pdf_service.generate_user_report.return_value = mock_pdf_bytes

        # Создаем пользователя с ответами
        user_factory = UserFactory(db_session)
        survey_factory = SurveyFactory(db_session)
        question_factory = QuestionFactory(db_session)
        response_factory = ResponseFactory(db_session)

        user = await user_factory.create()
        survey = await survey_factory.create()
        question = await question_factory.create(survey_id=survey.id)

        await response_factory.create(
            question_id=question.id,
            user_id=user.id,
            response_data={"answer": "My Answer"},
        )

        headers = await auth_headers(user)

        response = await api_client.auth_get(
            "/api/reports/my-responses/pdf", headers=headers
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert f"my_responses_report.pdf" in response.headers["content-disposition"]
        assert response.content == mock_pdf_bytes

        # Проверяем что PDF сервис был вызван
        mock_pdf_service.generate_user_report.assert_called_once()
        args = mock_pdf_service.generate_user_report.call_args[0]

        # Проверяем данные пользователя
        user_data = args[0]
        assert user_data["id"] == user.id

        # Проверяем данные ответов
        responses_data = args[1]
        assert len(responses_data) >= 1
        assert responses_data[0]["user"]["id"] == user.id

    @pytest_asyncio.async_test
    async def test_generate_my_responses_pdf_empty(
        self, api_client, auth_headers, db_session, mock_pdf_service
    ):
        """Тест генерации PDF отчета без ответов."""
        mock_pdf_bytes = b"empty-my-responses-pdf"
        mock_pdf_service.generate_user_report.return_value = mock_pdf_bytes

        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        response = await api_client.auth_get(
            "/api/reports/my-responses/pdf", headers=headers
        )

        assert response.status_code == 200
        assert response.content == mock_pdf_bytes

        # Проверяем что сервис был вызван с пустыми ответами
        args = mock_pdf_service.generate_user_report.call_args[0]
        responses_data = args[1]
        assert len(responses_data) == 0

    @pytest_asyncio.async_test
    async def test_generate_my_responses_pdf_requires_auth(self, api_client):
        """Тест что генерация PDF собственных ответов требует авторизацию."""
        response = await api_client.get("/api/reports/my-responses/pdf")

        assert response.status_code == 401

    @pytest_asyncio.async_test
    async def test_generate_my_responses_pdf_service_error(
        self, api_client, auth_headers, db_session, mock_pdf_service
    ):
        """Тест обработки ошибки PDF сервиса."""
        # Настраиваем mock для выброса ошибки
        mock_pdf_service.generate_user_report.side_effect = Exception(
            "PDF generation failed"
        )

        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        headers = await auth_headers(user)

        response = await api_client.auth_get(
            "/api/reports/my-responses/pdf", headers=headers
        )

        assert response.status_code == 500
        assert "failed to generate" in response.json()["detail"].lower()


class TestReportsIntegration:
    """Интеграционные тесты для отчетов."""

    @pytest_asyncio.async_test
    async def test_complete_survey_report_flow(
        self, api_client, admin_headers, db_session, mock_pdf_service
    ):
        """Тест полного цикла создания отчета по опросу."""
        mock_pdf_bytes = b"complete-survey-report"
        mock_pdf_service.generate_survey_report.return_value = mock_pdf_bytes

        # Создаем полный опрос с несколькими вопросами и ответами
        survey_factory = SurveyFactory(db_session)
        question_factory = QuestionFactory(db_session)
        response_factory = ResponseFactory(db_session)
        user_factory = UserFactory(db_session)

        survey = await survey_factory.create(title="Complete Survey")

        # Создаем разные типы вопросов
        question1 = await question_factory.create(
            survey_id=survey.id, title="Text Question", question_type="text"
        )
        question2 = await question_factory.create(
            survey_id=survey.id, title="Rating Question", question_type="rating"
        )
        question3 = await question_factory.create(
            survey_id=survey.id, title="Yes/No Question", question_type="yes_no"
        )

        # Создаем несколько пользователей с ответами
        user1 = await user_factory.create()
        user2 = await user_factory.create()
        user3 = await user_factory.create()

        # Пользователь 1 - полные ответы
        await response_factory.create(
            question_id=question1.id,
            user_id=user1.id,
            response_data={"answer": "Complete answer"},
        )
        await response_factory.create(
            question_id=question2.id, user_id=user1.id, response_data={"rating": 5}
        )
        await response_factory.create(
            question_id=question3.id, user_id=user1.id, response_data={"answer": "yes"}
        )

        # Пользователь 2 - частичные ответы
        await response_factory.create(
            question_id=question1.id,
            user_id=user2.id,
            response_data={"answer": "Partial answer"},
        )
        await response_factory.create(
            question_id=question2.id, user_id=user2.id, response_data={"rating": 3}
        )

        # Пользователь 3 - один ответ
        await response_factory.create(
            question_id=question1.id,
            user_id=user3.id,
            response_data={"answer": "Single answer"},
        )

        # Генерируем отчет
        response = await api_client.auth_get(
            f"/api/reports/surveys/{survey.id}/pdf", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.content == mock_pdf_bytes

        # Проверяем переданные данные
        args = mock_pdf_service.generate_survey_report.call_args[0]

        # Данные опроса
        survey_data = args[0]
        assert survey_data["title"] == "Complete Survey"

        # Данные ответов
        responses_data = args[1]
        assert len(responses_data) == 6  # 3+2+1 ответов

        # Аналитика
        analytics_data = args[2]
        assert analytics_data["unique_respondents"] == 3
        assert analytics_data["total_responses"] == 6
        assert analytics_data["total_questions"] == 3
        assert analytics_data["completion_rate"] == 33.33  # 1 из 3 завершил полностью

    @pytest_asyncio.async_test
    async def test_complete_user_report_flow(
        self, api_client, auth_headers, db_session, mock_pdf_service
    ):
        """Тест полного цикла создания отчета пользователя."""
        mock_pdf_bytes = b"complete-user-report"
        mock_pdf_service.generate_user_report.return_value = mock_pdf_bytes

        # Создаем пользователя с ответами на несколько опросов
        user_factory = UserFactory(db_session)
        survey_factory = SurveyFactory(db_session)
        question_factory = QuestionFactory(db_session)
        response_factory = ResponseFactory(db_session)

        user = await user_factory.create()

        # Создаем несколько опросов
        survey1 = await survey_factory.create(title="Survey 1")
        survey2 = await survey_factory.create(title="Survey 2")

        # Создаем вопросы
        question1 = await question_factory.create(
            survey_id=survey1.id, title="Question 1"
        )
        question2 = await question_factory.create(
            survey_id=survey1.id, title="Question 2"
        )
        question3 = await question_factory.create(
            survey_id=survey2.id, title="Question 3"
        )

        # Создаем ответы пользователя
        await response_factory.create(
            question_id=question1.id,
            user_id=user.id,
            response_data={"answer": "Answer 1"},
        )
        await response_factory.create(
            question_id=question2.id,
            user_id=user.id,
            response_data={"answer": "Answer 2"},
        )
        await response_factory.create(
            question_id=question3.id,
            user_id=user.id,
            response_data={"answer": "Answer 3"},
        )

        headers = await auth_headers(user)

        # Генерируем отчет
        response = await api_client.auth_get(
            f"/api/reports/users/{user.id}/pdf", headers=headers
        )

        assert response.status_code == 200
        assert response.content == mock_pdf_bytes

        # Проверяем переданные данные
        args = mock_pdf_service.generate_user_report.call_args[0]

        # Данные пользователя
        user_data = args[0]
        assert user_data["id"] == user.id

        # Данные ответов
        responses_data = args[1]
        assert len(responses_data) == 3

        # Проверяем что все ответы принадлежат пользователю
        for resp in responses_data:
            assert resp["user"]["id"] == user.id
