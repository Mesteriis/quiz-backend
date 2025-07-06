"""
Тесты для Responses Router.

Этот модуль содержит тесты для всех endpoints responses router,
включая создание ответов, получение ответов и валидацию данных.
"""

import asyncio
from pathlib import Path

# Локальные импорты
import sys

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.question import Question, QuestionType
from models.response import Response
from models.survey import Survey


class TestCreateResponse:
    """Тесты создания ответов."""

    @pytest.mark.asyncio
    async def test_create_response_success(
        self, api_client, db_session, sample_question
    ):
        """Тест успешного создания ответа."""
        # Arrange
        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_123",
            "answer": {"value": "Test answer"},
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["question_id"] == sample_question.id
        assert data["user_session_id"] == "test_session_123"
        assert data["answer"] == {"value": "Test answer"}
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_response_rating_question(
        self, api_client, db_session, sample_survey
    ):
        """Тест создания ответа для рейтингового вопроса."""
        # Arrange - создаем рейтинговый вопрос
        rating_question = Question(
            survey_id=sample_survey.id,
            title="Rate this service",
            question_type=QuestionType.RATING_1_10,
            is_required=True,
            order=1,
        )
        db_session.add(rating_question)
        await db_session.commit()
        await db_session.refresh(rating_question)

        response_data = {
            "question_id": rating_question.id,
            "user_session_id": "test_session_rating",
            "answer": {"value": 8},
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["answer"]["value"] == 8

    @pytest.mark.asyncio
    async def test_create_response_yes_no_question(
        self, api_client, db_session, sample_survey
    ):
        """Тест создания ответа для вопроса да/нет."""
        # Arrange - создаем вопрос да/нет
        yes_no_question = Question(
            survey_id=sample_survey.id,
            title="Do you like this app?",
            question_type=QuestionType.YES_NO,
            is_required=True,
            order=1,
        )
        db_session.add(yes_no_question)
        await db_session.commit()
        await db_session.refresh(yes_no_question)

        response_data = {
            "question_id": yes_no_question.id,
            "user_session_id": "test_session_yesno",
            "answer": {"value": True},
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["answer"]["value"] is True

    @pytest.mark.asyncio
    async def test_create_response_question_not_found(self, api_client, db_session):
        """Тест ошибки при несуществующем вопросе."""
        # Arrange
        response_data = {
            "question_id": 99999,
            "user_session_id": "test_session_123",
            "answer": {"value": "Test answer"},
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Question not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_response_inactive_survey(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки при неактивном опросе."""
        # Arrange - деактивируем опрос
        sample_survey.is_active = False
        await db_session.commit()

        question = Question(
            survey_id=sample_survey.id,
            title="Test question",
            question_type=QuestionType.TEXT,
            is_required=True,
            order=1,
        )
        db_session.add(question)
        await db_session.commit()
        await db_session.refresh(question)

        response_data = {
            "question_id": question.id,
            "user_session_id": "test_session_123",
            "answer": {"value": "Test answer"},
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Survey is not active" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_response_duplicate_response(
        self, api_client, db_session, sample_question
    ):
        """Тест ошибки при дублировании ответа."""
        # Arrange - создаем первый ответ
        first_response = Response(
            question_id=sample_question.id,
            user_session_id="test_session_123",
            answer={"value": "First answer"},
        )
        db_session.add(first_response)
        await db_session.commit()

        # Пытаемся создать второй ответ
        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_123",
            "answer": {"value": "Second answer"},
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Response already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_response_invalid_rating(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки при невалидном рейтинге."""
        # Arrange - создаем рейтинговый вопрос
        rating_question = Question(
            survey_id=sample_survey.id,
            title="Rate this service",
            question_type=QuestionType.RATING_1_10,
            is_required=True,
            order=1,
        )
        db_session.add(rating_question)
        await db_session.commit()
        await db_session.refresh(rating_question)

        response_data = {
            "question_id": rating_question.id,
            "user_session_id": "test_session_rating",
            "answer": {"value": 15},  # Невалидный рейтинг (больше 10)
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid response data" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_response_missing_required_answer(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки при отсутствии обязательного ответа."""
        # Arrange - создаем обязательный вопрос
        required_question = Question(
            survey_id=sample_survey.id,
            title="Required question",
            question_type=QuestionType.TEXT,
            is_required=True,
            order=1,
        )
        db_session.add(required_question)
        await db_session.commit()
        await db_session.refresh(required_question)

        response_data = {
            "question_id": required_question.id,
            "user_session_id": "test_session_required",
            "answer": {"value": ""},  # Пустой ответ
        }

        # Act
        response = await api_client.post("/api/responses/", json=response_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid response data" in data["detail"]


class TestGetResponsesByQuestion:
    """Тесты получения ответов по вопросу."""

    @pytest.mark.asyncio
    async def test_get_responses_by_question_success(
        self, api_client, db_session, sample_question
    ):
        """Тест успешного получения ответов по вопросу."""
        # Arrange - создаем несколько ответов
        responses = [
            Response(
                question_id=sample_question.id,
                user_session_id=f"session_{i}",
                answer={"value": f"Answer {i}"},
            )
            for i in range(3)
        ]

        for resp in responses:
            db_session.add(resp)
        await db_session.commit()

        # Act
        response = await api_client.get(f"/api/responses/question/{sample_question.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("answer" in resp for resp in data)
        assert all("created_at" in resp for resp in data)

    @pytest.mark.asyncio
    async def test_get_responses_by_question_not_found(self, api_client, db_session):
        """Тест ошибки при несуществующем вопросе."""
        # Act
        response = await api_client.get("/api/responses/question/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Question not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_responses_by_question_private_survey(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки при приватном опросе."""
        # Arrange - делаем опрос приватным
        sample_survey.is_public = False
        await db_session.commit()

        question = Question(
            survey_id=sample_survey.id,
            title="Private question",
            question_type=QuestionType.TEXT,
            is_required=True,
            order=1,
        )
        db_session.add(question)
        await db_session.commit()
        await db_session.refresh(question)

        # Act
        response = await api_client.get(f"/api/responses/question/{question.id}")

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "private survey" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_responses_by_question_empty_results(
        self, api_client, db_session, sample_question
    ):
        """Тест получения пустого списка ответов."""
        # Act
        response = await api_client.get(f"/api/responses/question/{sample_question.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestGetResponsesByUser:
    """Тесты получения ответов по пользователю."""

    @pytest.mark.asyncio
    async def test_get_responses_by_user_success(
        self, api_client, db_session, sample_question
    ):
        """Тест успешного получения ответов пользователя."""
        # Arrange - создаем ответы для пользователя
        user_session_id = "test_user_session"
        responses = [
            Response(
                question_id=sample_question.id,
                user_session_id=user_session_id,
                answer={"value": f"User answer {i}"},
            )
            for i in range(2)
        ]

        for resp in responses:
            db_session.add(resp)
        await db_session.commit()

        # Act
        response = await api_client.get(f"/api/responses/user/{user_session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(resp["user_session_id"] == user_session_id for resp in data)

    @pytest.mark.asyncio
    async def test_get_responses_by_user_only_public_surveys(
        self, api_client, db_session, sample_survey
    ):
        """Тест получения только ответов из публичных опросов."""
        # Arrange - создаем публичный и приватный опросы
        private_survey = Survey(
            title="Private Survey",
            description="Private survey description",
            is_public=False,
            is_active=True,
        )
        db_session.add(private_survey)
        await db_session.commit()
        await db_session.refresh(private_survey)

        # Создаем вопросы
        public_question = Question(
            survey_id=sample_survey.id,
            title="Public question",
            question_type=QuestionType.TEXT,
            order=1,
        )
        private_question = Question(
            survey_id=private_survey.id,
            title="Private question",
            question_type=QuestionType.TEXT,
            order=1,
        )
        db_session.add(public_question)
        db_session.add(private_question)
        await db_session.commit()

        # Создаем ответы для обоих вопросов
        user_session_id = "test_user_session"
        public_response = Response(
            question_id=public_question.id,
            user_session_id=user_session_id,
            answer={"value": "Public answer"},
        )
        private_response = Response(
            question_id=private_question.id,
            user_session_id=user_session_id,
            answer={"value": "Private answer"},
        )
        db_session.add(public_response)
        db_session.add(private_response)
        await db_session.commit()

        # Act
        response = await api_client.get(f"/api/responses/user/{user_session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Только публичный ответ
        assert data[0]["answer"]["value"] == "Public answer"

    @pytest.mark.asyncio
    async def test_get_responses_by_user_empty_results(self, api_client, db_session):
        """Тест получения пустого списка ответов пользователя."""
        # Act
        response = await api_client.get("/api/responses/user/nonexistent_user")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestGetSurveyProgress:
    """Тесты получения прогресса по опросу."""

    @pytest.mark.asyncio
    async def test_get_survey_progress_success(
        self, api_client, db_session, sample_survey
    ):
        """Тест успешного получения прогресса по опросу."""
        # Arrange - создаем вопросы
        questions = [
            Question(
                survey_id=sample_survey.id,
                title=f"Question {i}",
                question_type=QuestionType.TEXT,
                order=i,
            )
            for i in range(1, 4)
        ]

        for q in questions:
            db_session.add(q)
        await db_session.commit()

        # Создаем ответы на первые 2 вопроса
        user_session_id = "progress_user_session"
        responses = [
            Response(
                question_id=questions[0].id,
                user_session_id=user_session_id,
                answer={"value": "Answer 1"},
            ),
            Response(
                question_id=questions[1].id,
                user_session_id=user_session_id,
                answer={"value": "Answer 2"},
            ),
        ]

        for resp in responses:
            db_session.add(resp)
        await db_session.commit()

        # Act
        response = await api_client.get(
            f"/api/responses/survey/{sample_survey.id}/progress/{user_session_id}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_questions"] == 3
        assert data["answered_questions"] == 2
        assert data["completion_percentage"] == 66.67
        assert data["is_completed"] is False
        assert data["next_question_id"] == questions[2].id

    @pytest.mark.asyncio
    async def test_get_survey_progress_completed(
        self, api_client, db_session, sample_survey
    ):
        """Тест прогресса для завершенного опроса."""
        # Arrange - создаем вопросы
        questions = [
            Question(
                survey_id=sample_survey.id,
                title=f"Question {i}",
                question_type=QuestionType.TEXT,
                order=i,
            )
            for i in range(1, 3)
        ]

        for q in questions:
            db_session.add(q)
        await db_session.commit()

        # Создаем ответы на все вопросы
        user_session_id = "completed_user_session"
        responses = [
            Response(
                question_id=q.id,
                user_session_id=user_session_id,
                answer={"value": f"Answer {i}"},
            )
            for i, q in enumerate(questions, 1)
        ]

        for resp in responses:
            db_session.add(resp)
        await db_session.commit()

        # Act
        response = await api_client.get(
            f"/api/responses/survey/{sample_survey.id}/progress/{user_session_id}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_questions"] == 2
        assert data["answered_questions"] == 2
        assert data["completion_percentage"] == 100.0
        assert data["is_completed"] is True
        assert data["next_question_id"] is None

    @pytest.mark.asyncio
    async def test_get_survey_progress_survey_not_found(self, api_client, db_session):
        """Тест ошибки при несуществующем опросе."""
        # Act
        response = await api_client.get(
            "/api/responses/survey/99999/progress/user_session"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Survey not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_survey_progress_private_survey(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки при приватном опросе."""
        # Arrange - делаем опрос приватным
        sample_survey.is_public = False
        await db_session.commit()

        # Act
        response = await api_client.get(
            f"/api/responses/survey/{sample_survey.id}/progress/user_session"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Survey not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_survey_progress_inactive_survey(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки при неактивном опросе."""
        # Arrange - деактивируем опрос
        sample_survey.is_active = False
        await db_session.commit()

        # Act
        response = await api_client.get(
            f"/api/responses/survey/{sample_survey.id}/progress/user_session"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Survey not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_survey_progress_no_responses(
        self, api_client, db_session, sample_survey
    ):
        """Тест прогресса без ответов."""
        # Arrange - создаем вопросы
        questions = [
            Question(
                survey_id=sample_survey.id,
                title=f"Question {i}",
                question_type=QuestionType.TEXT,
                order=i,
            )
            for i in range(1, 3)
        ]

        for q in questions:
            db_session.add(q)
        await db_session.commit()

        # Act
        response = await api_client.get(
            f"/api/responses/survey/{sample_survey.id}/progress/new_user_session"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_questions"] == 2
        assert data["answered_questions"] == 0
        assert data["completion_percentage"] == 0.0
        assert data["is_completed"] is False
        assert data["next_question_id"] == questions[0].id


class TestValidateResponseBeforeSave:
    """Тесты валидации ответов перед сохранением."""

    @pytest.mark.asyncio
    async def test_validate_response_text_question_valid(
        self, api_client, db_session, sample_question
    ):
        """Тест валидации текстового вопроса - валидный ответ."""
        # Arrange
        validation_data = {
            "question_id": sample_question.id,
            "answer": {"value": "Valid text answer"},
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["question_id"] == sample_question.id
        assert data["question_type"] == sample_question.question_type
        assert data["validation_message"] is None

    @pytest.mark.asyncio
    async def test_validate_response_text_question_invalid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации текстового вопроса - невалидный ответ."""
        # Arrange - создаем обязательный текстовый вопрос
        required_question = Question(
            survey_id=sample_survey.id,
            title="Required text question",
            question_type=QuestionType.TEXT,
            is_required=True,
            order=1,
        )
        db_session.add(required_question)
        await db_session.commit()
        await db_session.refresh(required_question)

        validation_data = {
            "question_id": required_question.id,
            "answer": {"value": ""},  # Пустой ответ
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["validation_message"] is not None

    @pytest.mark.asyncio
    async def test_validate_response_rating_question_valid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации рейтингового вопроса - валидный ответ."""
        # Arrange - создаем рейтинговый вопрос
        rating_question = Question(
            survey_id=sample_survey.id,
            title="Rating question",
            question_type=QuestionType.RATING_1_10,
            is_required=True,
            order=1,
        )
        db_session.add(rating_question)
        await db_session.commit()
        await db_session.refresh(rating_question)

        validation_data = {"question_id": rating_question.id, "answer": {"value": 7}}

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["question_type"] == QuestionType.RATING_1_10

    @pytest.mark.asyncio
    async def test_validate_response_rating_question_invalid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации рейтингового вопроса - невалидный ответ."""
        # Arrange - создаем рейтинговый вопрос
        rating_question = Question(
            survey_id=sample_survey.id,
            title="Rating question",
            question_type=QuestionType.RATING_1_10,
            is_required=True,
            order=1,
        )
        db_session.add(rating_question)
        await db_session.commit()
        await db_session.refresh(rating_question)

        validation_data = {
            "question_id": rating_question.id,
            "answer": {"value": 15},  # Больше 10
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["validation_message"] is not None

    @pytest.mark.asyncio
    async def test_validate_response_yes_no_question_valid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации вопроса да/нет - валидный ответ."""
        # Arrange - создаем вопрос да/нет
        yes_no_question = Question(
            survey_id=sample_survey.id,
            title="Yes/No question",
            question_type=QuestionType.YES_NO,
            is_required=True,
            order=1,
        )
        db_session.add(yes_no_question)
        await db_session.commit()
        await db_session.refresh(yes_no_question)

        validation_data = {
            "question_id": yes_no_question.id,
            "answer": {"value": "yes"},
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_response_email_question_valid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации email вопроса - валидный ответ."""
        # Arrange - создаем email вопрос
        email_question = Question(
            survey_id=sample_survey.id,
            title="Email question",
            question_type=QuestionType.EMAIL,
            is_required=True,
            order=1,
        )
        db_session.add(email_question)
        await db_session.commit()
        await db_session.refresh(email_question)

        validation_data = {
            "question_id": email_question.id,
            "answer": {"value": "test@example.com"},
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_response_email_question_invalid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации email вопроса - невалидный ответ."""
        # Arrange - создаем email вопрос
        email_question = Question(
            survey_id=sample_survey.id,
            title="Email question",
            question_type=QuestionType.EMAIL,
            is_required=True,
            order=1,
        )
        db_session.add(email_question)
        await db_session.commit()
        await db_session.refresh(email_question)

        validation_data = {
            "question_id": email_question.id,
            "answer": {"value": "invalid-email"},
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["validation_message"] is not None

    @pytest.mark.asyncio
    async def test_validate_response_phone_question_valid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации телефонного вопроса - валидный ответ."""
        # Arrange - создаем телефонный вопрос
        phone_question = Question(
            survey_id=sample_survey.id,
            title="Phone question",
            question_type=QuestionType.PHONE,
            is_required=True,
            order=1,
        )
        db_session.add(phone_question)
        await db_session.commit()
        await db_session.refresh(phone_question)

        validation_data = {
            "question_id": phone_question.id,
            "answer": {"value": "+1234567890"},
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_response_phone_question_invalid(
        self, api_client, db_session, sample_survey
    ):
        """Тест валидации телефонного вопроса - невалидный ответ."""
        # Arrange - создаем телефонный вопрос
        phone_question = Question(
            survey_id=sample_survey.id,
            title="Phone question",
            question_type=QuestionType.PHONE,
            is_required=True,
            order=1,
        )
        db_session.add(phone_question)
        await db_session.commit()
        await db_session.refresh(phone_question)

        validation_data = {
            "question_id": phone_question.id,
            "answer": {"value": "123"},  # Слишком короткий
        }

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["validation_message"] is not None

    @pytest.mark.asyncio
    async def test_validate_response_question_not_found(self, api_client, db_session):
        """Тест валидации при несуществующем вопросе."""
        # Arrange
        validation_data = {"question_id": 99999, "answer": {"value": "Test answer"}}

        # Act
        response = await api_client.post(
            "/api/responses/validate-before-save", json=validation_data
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Question not found" in data["detail"]


class TestResponsesIntegration:
    """Интеграционные тесты для responses router."""

    @pytest.mark.asyncio
    async def test_full_response_flow(self, api_client, db_session, sample_survey):
        """Тест полного потока создания и получения ответов."""
        # Arrange - создаем несколько вопросов
        questions = [
            Question(
                survey_id=sample_survey.id,
                title="Text question",
                question_type=QuestionType.TEXT,
                is_required=True,
                order=1,
            ),
            Question(
                survey_id=sample_survey.id,
                title="Rating question",
                question_type=QuestionType.RATING_1_10,
                is_required=True,
                order=2,
            ),
            Question(
                survey_id=sample_survey.id,
                title="Yes/No question",
                question_type=QuestionType.YES_NO,
                is_required=False,
                order=3,
            ),
        ]

        for q in questions:
            db_session.add(q)
        await db_session.commit()

        user_session_id = "integration_test_session"

        # Act & Assert - создаем ответы на все вопросы
        responses_data = [
            {
                "question_id": questions[0].id,
                "user_session_id": user_session_id,
                "answer": {"value": "Text answer"},
            },
            {
                "question_id": questions[1].id,
                "user_session_id": user_session_id,
                "answer": {"value": 8},
            },
            {
                "question_id": questions[2].id,
                "user_session_id": user_session_id,
                "answer": {"value": True},
            },
        ]

        created_responses = []
        for response_data in responses_data:
            response = await api_client.post("/api/responses/", json=response_data)
            assert response.status_code == 200
            created_responses.append(response.json())

        # Проверяем прогресс
        progress_response = await api_client.get(
            f"/api/responses/survey/{sample_survey.id}/progress/{user_session_id}"
        )
        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        assert progress_data["is_completed"] is True
        assert progress_data["completion_percentage"] == 100.0

        # Проверяем получение ответов пользователя
        user_responses = await api_client.get(f"/api/responses/user/{user_session_id}")
        assert user_responses.status_code == 200
        user_data = user_responses.json()
        assert len(user_data) == 3

        # Проверяем получение ответов по каждому вопросу
        for question in questions:
            question_responses = await api_client.get(
                f"/api/responses/question/{question.id}"
            )
            assert question_responses.status_code == 200
            question_data = question_responses.json()
            assert len(question_data) == 1

    @pytest.mark.asyncio
    async def test_response_validation_flow(
        self, api_client, db_session, sample_survey
    ):
        """Тест потока валидации ответов."""
        # Arrange - создаем вопросы разных типов
        questions = [
            Question(
                survey_id=sample_survey.id,
                title="Text question",
                question_type=QuestionType.TEXT,
                is_required=True,
                order=1,
            ),
            Question(
                survey_id=sample_survey.id,
                title="Rating question",
                question_type=QuestionType.RATING_1_10,
                is_required=True,
                order=2,
            ),
        ]

        for q in questions:
            db_session.add(q)
        await db_session.commit()

        # Act & Assert - валидируем ответы перед сохранением
        valid_text_validation = await api_client.post(
            "/api/responses/validate-before-save",
            json={"question_id": questions[0].id, "answer": {"value": "Valid text"}},
        )
        assert valid_text_validation.status_code == 200
        assert valid_text_validation.json()["is_valid"] is True

        invalid_rating_validation = await api_client.post(
            "/api/responses/validate-before-save",
            json={
                "question_id": questions[1].id,
                "answer": {"value": 15},  # Невалидный рейтинг
            },
        )
        assert invalid_rating_validation.status_code == 200
        assert invalid_rating_validation.json()["is_valid"] is False

        # Пытаемся сохранить валидный ответ
        valid_response = await api_client.post(
            "/api/responses/",
            json={
                "question_id": questions[0].id,
                "user_session_id": "validation_test_session",
                "answer": {"value": "Valid text"},
            },
        )
        assert valid_response.status_code == 200

        # Пытаемся сохранить невалидный ответ
        invalid_response = await api_client.post(
            "/api/responses/",
            json={
                "question_id": questions[1].id,
                "user_session_id": "validation_test_session",
                "answer": {"value": 15},
            },
        )
        assert invalid_response.status_code == 400
        assert "Invalid response data" in invalid_response.json()["detail"]

    @pytest.mark.asyncio
    async def test_response_ordering_by_creation_time(
        self, api_client, db_session, sample_question
    ):
        """Тест упорядочивания ответов по времени создания."""
        # Arrange - создаем ответы с интервалом
        user_sessions = [f"session_{i}" for i in range(3)]

        for i, session_id in enumerate(user_sessions):
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": session_id,
                "answer": {"value": f"Answer {i}"},
            }
            response = await api_client.post("/api/responses/", json=response_data)
            assert response.status_code == 200

            # Небольшая задержка для разных created_at
            await asyncio.sleep(0.01)

        # Act - получаем ответы по вопросу
        responses = await api_client.get(
            f"/api/responses/question/{sample_question.id}"
        )

        # Assert - проверяем упорядочивание по убыванию времени создания
        assert responses.status_code == 200
        data = responses.json()
        assert len(data) == 3

        # Проверяем, что ответы упорядочены по убыванию времени создания
        created_times = [resp["created_at"] for resp in data]
        assert created_times == sorted(created_times, reverse=True)
