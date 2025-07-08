"""
Comprehensive тесты для Responses Router.

Покрывает все эндпоинты управления ответами:
- Создание ответов с немедленным сохранением
- Получение ответов по вопросам и пользователям
- Валидация ответов
- Прогресс опросов
- Обработка ошибок
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from datetime import datetime

from models.response import ResponseCreate, ResponseRead, ResponseValidate
from models.question import Question
from models.survey import Survey
from models.respondent import Respondent, RespondentCreate
from tests.factories.surveys.model_factories import (
    SurveyModelFactory,
    QuestionModelFactory,
    ResponseModelFactory,
)
from tests.factories.users.model_factories import UserModelFactory
from tests.factories.surveys.pydantic_factories import (
    SurveyCreateDataFactory,
    ValidSurveyCreateDataFactory,
)


class TestResponsesRouterCreation:
    """Тесты создания ответов."""

    @pytest.mark.asyncio
    async def test_create_response_success(self, api_client, async_session):
        """Тест успешного создания ответа."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1, question_type="TEXT", is_required=True
        )
        survey = SurveyModelFactory.build(id=1, is_active=True, is_public=True)

        response_data = {
            "question_id": question.id,
            "answer": {"text": "Test answer"},
            "user_session_id": "test_session_123",
            "user_id": 1,
            "respondent_id": None,
        }

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
            patch(
                "src.routers.responses.get_respondent_repository"
            ) as mock_respondent_repo,
        ):
            # Mock repositories
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                None
            )
            mock_response_repo.return_value.create.return_value = (
                ResponseModelFactory.build(
                    id=1,
                    question_id=question.id,
                    answer=response_data["answer"],
                    user_session_id=response_data["user_session_id"],
                )
            )

            # Mock respondent creation
            mock_respondent_repo.return_value.create.return_value = MagicMock(id=1)

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["question_id"] == question.id
            assert data["answer"] == response_data["answer"]
            assert data["user_session_id"] == response_data["user_session_id"]

            # Verify repositories were called correctly
            mock_question_repo.return_value.get.assert_called_once_with(question.id)
            mock_response_repo.return_value.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_response_question_not_found(self, api_client, async_session):
        """Тест создания ответа с несуществующим вопросом."""
        # Arrange
        response_data = {
            "question_id": 999,
            "answer": {"text": "Test answer"},
            "user_session_id": "test_session_123",
            "user_id": 1,
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = None

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 404
            assert "Question not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_response_inactive_survey(self, api_client, async_session):
        """Тест создания ответа для неактивного опроса."""
        # Arrange
        question = QuestionModelFactory.build(id=1, question_type="TEXT")
        survey = SurveyModelFactory.build(id=1, is_active=False)

        response_data = {
            "question_id": question.id,
            "answer": {"text": "Test answer"},
            "user_session_id": "test_session_123",
            "user_id": 1,
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 400
            assert "Survey is not active" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_response_duplicate_response(self, api_client, async_session):
        """Тест создания дублирующего ответа."""
        # Arrange
        question = QuestionModelFactory.build(id=1, question_type="TEXT")
        survey = SurveyModelFactory.build(id=1, is_active=True)
        existing_response = ResponseModelFactory.build(
            question_id=question.id, user_session_id="test_session_123"
        )

        response_data = {
            "question_id": question.id,
            "answer": {"text": "Test answer"},
            "user_session_id": "test_session_123",
            "user_id": 1,
        }

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
        ):
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                existing_response
            )

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 400
            assert "Response already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_response_invalid_answer_data(self, api_client, async_session):
        """Тест создания ответа с невалидными данными."""
        # Arrange
        question = QuestionModelFactory.build(id=1, question_type="SINGLE_CHOICE")
        survey = SurveyModelFactory.build(id=1, is_active=True)

        response_data = {
            "question_id": question.id,
            "answer": {
                "invalid_format": "wrong"
            },  # Неправильный формат для SINGLE_CHOICE
            "user_session_id": "test_session_123",
            "user_id": 1,
        }

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
            patch("src.routers.responses._validate_response_data") as mock_validate,
        ):
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                None
            )
            mock_validate.return_value = False

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 400
            assert "Invalid response data" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_response_without_respondent_id(
        self, api_client, async_session
    ):
        """Тест создания ответа без ID респондента (создание анонимного)."""
        # Arrange
        question = QuestionModelFactory.build(id=1, question_type="TEXT")
        survey = SurveyModelFactory.build(id=1, is_active=True)

        response_data = {
            "question_id": question.id,
            "answer": {"text": "Test answer"},
            "user_session_id": "test_session_123",
            "user_id": None,  # Анонимный пользователь
            "respondent_id": None,
        }

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
            patch(
                "src.routers.responses.get_respondent_repository"
            ) as mock_respondent_repo,
        ):
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                None
            )

            # Mock anonymous respondent creation
            mock_respondent = MagicMock(id=1)
            mock_respondent_repo.return_value.create.return_value = mock_respondent

            mock_response_repo.return_value.create.return_value = (
                ResponseModelFactory.build(
                    id=1, question_id=question.id, respondent_id=mock_respondent.id
                )
            )

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 200
            mock_respondent_repo.return_value.create.assert_called_once()

            # Verify anonymous respondent was created
            create_call = mock_respondent_repo.return_value.create.call_args
            respondent_data = create_call[1]["obj_in"]
            assert respondent_data.is_anonymous is True

    @pytest.mark.asyncio
    async def test_create_response_with_multiple_choice_answer(
        self, api_client, async_session
    ):
        """Тест создания ответа с множественным выбором."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1,
            question_type="MULTIPLE_CHOICE",
            question_data={"options": ["Option 1", "Option 2", "Option 3"]},
        )
        survey = SurveyModelFactory.build(id=1, is_active=True)

        response_data = {
            "question_id": question.id,
            "answer": {"selected_options": ["Option 1", "Option 3"]},
            "user_session_id": "test_session_123",
            "user_id": 1,
        }

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
            patch(
                "src.routers.responses.get_respondent_repository"
            ) as mock_respondent_repo,
        ):
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                None
            )

            mock_respondent_repo.return_value.create.return_value = MagicMock(id=1)
            mock_response_repo.return_value.create.return_value = (
                ResponseModelFactory.build(
                    id=1, question_id=question.id, answer=response_data["answer"]
                )
            )

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["answer"]["selected_options"] == ["Option 1", "Option 3"]

    @pytest.mark.asyncio
    async def test_create_response_server_error(self, api_client, async_session):
        """Тест обработки серверной ошибки при создании ответа."""
        # Arrange
        response_data = {
            "question_id": 1,
            "answer": {"text": "Test answer"},
            "user_session_id": "test_session_123",
            "user_id": 1,
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.side_effect = Exception(
                "Database error"
            )

            # Act
            response = await api_client.post("/responses/", json=response_data)

            # Assert
            assert response.status_code == 500
            assert "Failed to create response" in response.json()["detail"]


class TestResponsesRouterRetrieval:
    """Тесты получения ответов."""

    @pytest.mark.asyncio
    async def test_get_responses_by_question_success(self, api_client, async_session):
        """Тест успешного получения ответов по вопросу."""
        # Arrange
        question_id = 1
        question = QuestionModelFactory.build(id=question_id, question_type="TEXT")
        survey = SurveyModelFactory.build(id=1, is_public=True)

        responses = [
            ResponseModelFactory.build(id=1, question_id=question_id),
            ResponseModelFactory.build(id=2, question_id=question_id),
        ]

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
        ):
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_id.return_value = responses

            # Act
            response = await api_client.get(f"/responses/question/{question_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all(item["question_id"] == question_id for item in data)

    @pytest.mark.asyncio
    async def test_get_responses_by_question_not_found(self, api_client, async_session):
        """Тест получения ответов для несуществующего вопроса."""
        # Arrange
        question_id = 999

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = None

            # Act
            response = await api_client.get(f"/responses/question/{question_id}")

            # Assert
            assert response.status_code == 404
            assert "Question not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_responses_by_question_private_survey(
        self, api_client, async_session
    ):
        """Тест получения ответов для приватного опроса."""
        # Arrange
        question_id = 1
        question = QuestionModelFactory.build(id=question_id)
        survey = SurveyModelFactory.build(id=1, is_public=False)

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )

            # Act
            response = await api_client.get(f"/responses/question/{question_id}")

            # Assert
            assert response.status_code == 403
            assert (
                "Cannot access responses for private survey"
                in response.json()["detail"]
            )

    @pytest.mark.asyncio
    async def test_get_responses_by_user_success(self, api_client, async_session):
        """Тест успешного получения ответов пользователя."""
        # Arrange
        user_session_id = "test_session_123"
        responses = [
            ResponseModelFactory.build(id=1, user_session_id=user_session_id),
            ResponseModelFactory.build(id=2, user_session_id=user_session_id),
        ]

        with patch(
            "src.routers.responses.get_response_repository"
        ) as mock_response_repo:
            mock_response_repo.return_value.get_by_user_session_public_only.return_value = responses

            # Act
            response = await api_client.get(f"/responses/user/{user_session_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all(item["user_session_id"] == user_session_id for item in data)

    @pytest.mark.asyncio
    async def test_get_responses_by_user_empty_result(self, api_client, async_session):
        """Тест получения ответов пользователя с пустым результатом."""
        # Arrange
        user_session_id = "nonexistent_session"

        with patch(
            "src.routers.responses.get_response_repository"
        ) as mock_response_repo:
            mock_response_repo.return_value.get_by_user_session_public_only.return_value = []

            # Act
            response = await api_client.get(f"/responses/user/{user_session_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_responses_by_user_server_error(self, api_client, async_session):
        """Тест обработки серверной ошибки при получении ответов пользователя."""
        # Arrange
        user_session_id = "test_session_123"

        with patch(
            "src.routers.responses.get_response_repository"
        ) as mock_response_repo:
            mock_response_repo.return_value.get_by_user_session_public_only.side_effect = Exception(
                "Database error"
            )

            # Act
            response = await api_client.get(f"/responses/user/{user_session_id}")

            # Assert
            assert response.status_code == 500
            assert "Failed to fetch user responses" in response.json()["detail"]


class TestResponsesRouterSurveyProgress:
    """Тесты прогресса опроса."""

    @pytest.mark.asyncio
    async def test_get_survey_progress_success(self, api_client, async_session):
        """Тест успешного получения прогресса опроса."""
        # Arrange
        survey_id = 1
        user_session_id = "test_session_123"

        survey = SurveyModelFactory.build(id=survey_id, is_active=True)
        questions = [
            QuestionModelFactory.build(id=1, survey_id=survey_id),
            QuestionModelFactory.build(id=2, survey_id=survey_id),
            QuestionModelFactory.build(id=3, survey_id=survey_id),
        ]
        responses = [
            ResponseModelFactory.build(
                id=1, question_id=1, user_session_id=user_session_id
            ),
            ResponseModelFactory.build(
                id=2, question_id=2, user_session_id=user_session_id
            ),
        ]

        with (
            patch("src.routers.responses.get_survey_repository") as mock_survey_repo,
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
        ):
            mock_survey_repo.return_value.get.return_value = survey
            mock_question_repo.return_value.get_by_survey_id.return_value = questions
            mock_response_repo.return_value.get_by_survey_and_session.return_value = (
                responses
            )

            # Act
            response = await api_client.get(
                f"/responses/survey/{survey_id}/progress/{user_session_id}"
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["survey_id"] == survey_id
            assert data["user_session_id"] == user_session_id
            assert data["total_questions"] == 3
            assert data["answered_questions"] == 2
            assert data["progress_percentage"] == 66.67

    @pytest.mark.asyncio
    async def test_get_survey_progress_survey_not_found(
        self, api_client, async_session
    ):
        """Тест получения прогресса для несуществующего опроса."""
        # Arrange
        survey_id = 999
        user_session_id = "test_session_123"

        with patch("src.routers.responses.get_survey_repository") as mock_survey_repo:
            mock_survey_repo.return_value.get.return_value = None

            # Act
            response = await api_client.get(
                f"/responses/survey/{survey_id}/progress/{user_session_id}"
            )

            # Assert
            assert response.status_code == 404
            assert "Survey not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_survey_progress_inactive_survey(self, api_client, async_session):
        """Тест получения прогресса для неактивного опроса."""
        # Arrange
        survey_id = 1
        user_session_id = "test_session_123"
        survey = SurveyModelFactory.build(id=survey_id, is_active=False)

        with patch("src.routers.responses.get_survey_repository") as mock_survey_repo:
            mock_survey_repo.return_value.get.return_value = survey

            # Act
            response = await api_client.get(
                f"/responses/survey/{survey_id}/progress/{user_session_id}"
            )

            # Assert
            assert response.status_code == 400
            assert "Survey is not active" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_survey_progress_no_questions(self, api_client, async_session):
        """Тест получения прогресса для опроса без вопросов."""
        # Arrange
        survey_id = 1
        user_session_id = "test_session_123"
        survey = SurveyModelFactory.build(id=survey_id, is_active=True)

        with (
            patch("src.routers.responses.get_survey_repository") as mock_survey_repo,
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
        ):
            mock_survey_repo.return_value.get.return_value = survey
            mock_question_repo.return_value.get_by_survey_id.return_value = []
            mock_response_repo.return_value.get_by_survey_and_session.return_value = []

            # Act
            response = await api_client.get(
                f"/responses/survey/{survey_id}/progress/{user_session_id}"
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["total_questions"] == 0
            assert data["answered_questions"] == 0
            assert data["progress_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_get_survey_progress_completed(self, api_client, async_session):
        """Тест получения прогресса для полностью завершенного опроса."""
        # Arrange
        survey_id = 1
        user_session_id = "test_session_123"

        survey = SurveyModelFactory.build(id=survey_id, is_active=True)
        questions = [
            QuestionModelFactory.build(id=1, survey_id=survey_id),
            QuestionModelFactory.build(id=2, survey_id=survey_id),
        ]
        responses = [
            ResponseModelFactory.build(
                id=1, question_id=1, user_session_id=user_session_id
            ),
            ResponseModelFactory.build(
                id=2, question_id=2, user_session_id=user_session_id
            ),
        ]

        with (
            patch("src.routers.responses.get_survey_repository") as mock_survey_repo,
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
        ):
            mock_survey_repo.return_value.get.return_value = survey
            mock_question_repo.return_value.get_by_survey_id.return_value = questions
            mock_response_repo.return_value.get_by_survey_and_session.return_value = (
                responses
            )

            # Act
            response = await api_client.get(
                f"/responses/survey/{survey_id}/progress/{user_session_id}"
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["progress_percentage"] == 100.0
            assert data["is_completed"] is True


class TestResponsesRouterValidation:
    """Тесты валидации ответов."""

    @pytest.mark.asyncio
    async def test_validate_response_before_save_success(
        self, api_client, async_session
    ):
        """Тест успешной валидации ответа перед сохранением."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1, question_type="TEXT", is_required=True
        )

        validation_data = {
            "question_id": question.id,
            "answer": {"text": "Valid answer"},
            "user_session_id": "test_session_123",
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question

            # Act
            response = await api_client.post(
                "/responses/validate-before-save", json=validation_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["question_id"] == question.id

    @pytest.mark.asyncio
    async def test_validate_response_before_save_invalid(
        self, api_client, async_session
    ):
        """Тест валидации невалидного ответа."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1, question_type="TEXT", is_required=True
        )

        validation_data = {
            "question_id": question.id,
            "answer": {"text": ""},  # Пустой ответ для обязательного вопроса
            "user_session_id": "test_session_123",
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question

            # Act
            response = await api_client.post(
                "/responses/validate-before-save", json=validation_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert "validation_message" in data

    @pytest.mark.asyncio
    async def test_validate_response_before_save_question_not_found(
        self, api_client, async_session
    ):
        """Тест валидации ответа для несуществующего вопроса."""
        # Arrange
        validation_data = {
            "question_id": 999,
            "answer": {"text": "Test answer"},
            "user_session_id": "test_session_123",
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = None

            # Act
            response = await api_client.post(
                "/responses/validate-before-save", json=validation_data
            )

            # Assert
            assert response.status_code == 404
            assert "Question not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_response_before_save_single_choice(
        self, api_client, async_session
    ):
        """Тест валидации ответа с одиночным выбором."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1,
            question_type="SINGLE_CHOICE",
            question_data={"options": ["Option 1", "Option 2", "Option 3"]},
        )

        validation_data = {
            "question_id": question.id,
            "answer": {"selected_option": "Option 1"},
            "user_session_id": "test_session_123",
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question

            # Act
            response = await api_client.post(
                "/responses/validate-before-save", json=validation_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_response_before_save_multiple_choice(
        self, api_client, async_session
    ):
        """Тест валидации ответа с множественным выбором."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1,
            question_type="MULTIPLE_CHOICE",
            question_data={"options": ["Option 1", "Option 2", "Option 3"]},
        )

        validation_data = {
            "question_id": question.id,
            "answer": {"selected_options": ["Option 1", "Option 3"]},
            "user_session_id": "test_session_123",
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question

            # Act
            response = await api_client.post(
                "/responses/validate-before-save", json=validation_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_response_before_save_scale_question(
        self, api_client, async_session
    ):
        """Тест валидации ответа для шкалы."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1, question_type="SCALE", question_data={"min_value": 1, "max_value": 5}
        )

        validation_data = {
            "question_id": question.id,
            "answer": {"scale_value": 3},
            "user_session_id": "test_session_123",
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question

            # Act
            response = await api_client.post(
                "/responses/validate-before-save", json=validation_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_response_before_save_scale_out_of_range(
        self, api_client, async_session
    ):
        """Тест валидации ответа для шкалы вне диапазона."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1, question_type="SCALE", question_data={"min_value": 1, "max_value": 5}
        )

        validation_data = {
            "question_id": question.id,
            "answer": {"scale_value": 10},  # Вне диапазона
            "user_session_id": "test_session_123",
        }

        with patch(
            "src.routers.responses.get_question_repository"
        ) as mock_question_repo:
            mock_question_repo.return_value.get.return_value = question

            # Act
            response = await api_client.post(
                "/responses/validate-before-save", json=validation_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert "validation_message" in data


class TestResponsesRouterValidationHelpers:
    """Тесты вспомогательных функций валидации."""

    def test_validate_response_data_text_question(self):
        """Тест валидации текстового вопроса."""
        # Arrange
        from src.routers.responses import _validate_response_data

        question_type = "TEXT"
        answer = {"text": "Valid text answer"}

        # Act
        result = _validate_response_data(question_type, answer)

        # Assert
        assert result is True

    def test_validate_response_data_text_question_empty(self):
        """Тест валидации пустого текстового ответа."""
        # Arrange
        from src.routers.responses import _validate_response_data

        question_type = "TEXT"
        answer = {"text": ""}

        # Act
        result = _validate_response_data(question_type, answer)

        # Assert
        assert result is False

    def test_validate_response_data_single_choice(self):
        """Тест валидации одиночного выбора."""
        # Arrange
        from src.routers.responses import _validate_response_data

        question_type = "SINGLE_CHOICE"
        answer = {"selected_option": "Option 1"}

        # Act
        result = _validate_response_data(question_type, answer)

        # Assert
        assert result is True

    def test_validate_response_data_multiple_choice(self):
        """Тест валидации множественного выбора."""
        # Arrange
        from src.routers.responses import _validate_response_data

        question_type = "MULTIPLE_CHOICE"
        answer = {"selected_options": ["Option 1", "Option 2"]}

        # Act
        result = _validate_response_data(question_type, answer)

        # Assert
        assert result is True

    def test_validate_response_data_scale(self):
        """Тест валидации шкалы."""
        # Arrange
        from src.routers.responses import _validate_response_data

        question_type = "SCALE"
        answer = {"scale_value": 3}

        # Act
        result = _validate_response_data(question_type, answer)

        # Assert
        assert result is True

    def test_validate_response_data_invalid_format(self):
        """Тест валидации с неправильным форматом."""
        # Arrange
        from src.routers.responses import _validate_response_data

        question_type = "TEXT"
        answer = {"wrong_key": "value"}

        # Act
        result = _validate_response_data(question_type, answer)

        # Assert
        assert result is False

    def test_get_validation_message_text_question(self):
        """Тест получения сообщения валидации для текстового вопроса."""
        # Arrange
        from src.routers.responses import _get_validation_message

        question = QuestionModelFactory.build(
            question_type="TEXT", title="Test Question", is_required=True
        )
        answer = {"text": ""}

        # Act
        result = _get_validation_message(question, answer)

        # Assert
        assert "required" in result.lower()

    def test_get_validation_message_single_choice(self):
        """Тест получения сообщения валидации для одиночного выбора."""
        # Arrange
        from src.routers.responses import _get_validation_message

        question = QuestionModelFactory.build(
            question_type="SINGLE_CHOICE", title="Choose one option", is_required=True
        )
        answer = {}

        # Act
        result = _get_validation_message(question, answer)

        # Assert
        assert "select" in result.lower()


class TestResponsesRouterIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    async def test_full_response_workflow(self, api_client, async_session):
        """Тест полного workflow создания и получения ответа."""
        # Arrange
        question = QuestionModelFactory.build(
            id=1, question_type="TEXT", is_required=True
        )
        survey = SurveyModelFactory.build(id=1, is_active=True, is_public=True)

        response_data = {
            "question_id": question.id,
            "answer": {"text": "Integration test answer"},
            "user_session_id": "integration_test_session",
            "user_id": 1,
        }

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
            patch(
                "src.routers.responses.get_respondent_repository"
            ) as mock_respondent_repo,
        ):
            # Setup mocks
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                None
            )
            mock_respondent_repo.return_value.create.return_value = MagicMock(id=1)

            created_response = ResponseModelFactory.build(
                id=1,
                question_id=question.id,
                answer=response_data["answer"],
                user_session_id=response_data["user_session_id"],
            )
            mock_response_repo.return_value.create.return_value = created_response

            # For retrieval
            mock_response_repo.return_value.get_by_question_id.return_value = [
                created_response
            ]

            # Act & Assert
            # 1. Create response
            create_response = await api_client.post("/responses/", json=response_data)
            assert create_response.status_code == 200

            # 2. Get responses by question
            get_response = await api_client.get(f"/responses/question/{question.id}")
            assert get_response.status_code == 200
            data = get_response.json()
            assert len(data) == 1
            assert data[0]["answer"]["text"] == "Integration test answer"

    @pytest.mark.asyncio
    async def test_response_creation_with_progress_tracking(
        self, api_client, async_session
    ):
        """Тест создания ответа с отслеживанием прогресса."""
        # Arrange
        survey_id = 1
        user_session_id = "progress_test_session"

        survey = SurveyModelFactory.build(id=survey_id, is_active=True)
        questions = [
            QuestionModelFactory.build(id=1, survey_id=survey_id, question_type="TEXT"),
            QuestionModelFactory.build(id=2, survey_id=survey_id, question_type="TEXT"),
        ]

        response_data = {
            "question_id": questions[0].id,
            "answer": {"text": "First answer"},
            "user_session_id": user_session_id,
            "user_id": 1,
        }

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
            patch(
                "src.routers.responses.get_respondent_repository"
            ) as mock_respondent_repo,
            patch("src.routers.responses.get_survey_repository") as mock_survey_repo,
        ):
            # Setup mocks for creation
            mock_question_repo.return_value.get.return_value = questions[0]
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                None
            )
            mock_respondent_repo.return_value.create.return_value = MagicMock(id=1)

            created_response = ResponseModelFactory.build(
                id=1, question_id=questions[0].id, user_session_id=user_session_id
            )
            mock_response_repo.return_value.create.return_value = created_response

            # Setup mocks for progress
            mock_survey_repo.return_value.get.return_value = survey
            mock_question_repo.return_value.get_by_survey_id.return_value = questions
            mock_response_repo.return_value.get_by_survey_and_session.return_value = [
                created_response
            ]

            # Act & Assert
            # 1. Create response
            create_response = await api_client.post("/responses/", json=response_data)
            assert create_response.status_code == 200

            # 2. Check progress
            progress_response = await api_client.get(
                f"/responses/survey/{survey_id}/progress/{user_session_id}"
            )
            assert progress_response.status_code == 200
            progress_data = progress_response.json()
            assert progress_data["answered_questions"] == 1
            assert progress_data["total_questions"] == 2
            assert progress_data["progress_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_concurrent_response_creation(self, api_client, async_session):
        """Тест параллельного создания ответов."""
        # Arrange
        import asyncio

        question = QuestionModelFactory.build(id=1, question_type="TEXT")
        survey = SurveyModelFactory.build(id=1, is_active=True)

        async def create_response(session_id):
            response_data = {
                "question_id": question.id,
                "answer": {"text": f"Answer from {session_id}"},
                "user_session_id": session_id,
                "user_id": 1,
            }
            return await api_client.post("/responses/", json=response_data)

        with (
            patch(
                "src.routers.responses.get_question_repository"
            ) as mock_question_repo,
            patch(
                "src.routers.responses.get_response_repository"
            ) as mock_response_repo,
            patch(
                "src.routers.responses.get_respondent_repository"
            ) as mock_respondent_repo,
        ):
            mock_question_repo.return_value.get.return_value = question
            mock_question_repo.return_value.get_survey_by_question_id.return_value = (
                survey
            )
            mock_response_repo.return_value.get_by_question_and_session.return_value = (
                None
            )
            mock_respondent_repo.return_value.create.return_value = MagicMock(id=1)
            mock_response_repo.return_value.create.return_value = (
                ResponseModelFactory.build(id=1, question_id=question.id)
            )

            # Act
            tasks = [create_response(f"session_{i}") for i in range(5)]
            responses = await asyncio.gather(*tasks)

            # Assert
            for response in responses:
                assert response.status_code == 200
