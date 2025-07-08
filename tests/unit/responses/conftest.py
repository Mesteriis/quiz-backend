"""
Конфигурация тестов для домена ответов.

Содержит фикстуры и настройки специфичные для тестирования
системы ответов на опросы, включая создание, валидацию,
получение ответов, анонимные/аутентифицированные пользователи.
"""

import pytest
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock

# Импорт фабрик для responses домена
from tests.factories import (
    # Response фабрики
    ResponseFactory,
    AnonymousResponseFactory,
    AuthenticatedResponseFactory,
    TextResponseFactory,
    YesNoResponseFactory,
    RatingResponseFactory,
    EmailResponseFactory,
    PhoneResponseFactory,
    MultipleChoiceResponseFactory,
    LocationResponseFactory,
    FileUploadResponseFactory,
    ComplexResponseFactory,
    # Survey и Question фабрики (нужны для ответов)
    SurveyFactory,
    PublicSurveyFactory,
    PrivateSurveyFactory,
    SurveyWithQuestionsFactory,
    QuestionFactory,
    TextQuestionFactory,
    RatingQuestionFactory,
    # Respondent фабрики
    RespondentFactory,
    RespondentSurveyFactory,
    StartedSurveyFactory,
    InProgressSurveyFactory,
    CompletedSurveyFactory,
    # User фабрики
    UserFactory,
    RegularUserFactory,
    AnonymousUserFactory,
    # Utility functions
    create_response_batch,
    create_survey_responses,
    create_user_responses,
    create_response_validation_data,
)


@pytest.fixture
async def response_manager(db_session):
    """Менеджер для управления ответами в тестах."""
    from tests.factories.response_factory import ResponseAsyncManager

    return ResponseAsyncManager(db_session)


@pytest.fixture
async def respondent_manager(db_session):
    """Менеджер для управления респондентами в тестах."""
    from tests.factories.respondent_factory import RespondentAsyncManager

    return RespondentAsyncManager(db_session)


@pytest.fixture
async def sample_response(response_manager, sample_question):
    """Базовый ответ для тестов."""
    return await response_manager.create_text_response(
        question_id=sample_question.id,
        user_session_id="test_session_basic",
        answer={"value": "Sample response text"},
    )


@pytest.fixture
async def anonymous_response(response_manager, sample_question):
    """Анонимный ответ для тестов."""
    return await response_manager.create_anonymous_response(
        question_id=sample_question.id,
        user_session_id="anonymous_session_123",
        answer={"value": "Anonymous response"},
    )


@pytest.fixture
async def authenticated_response(response_manager, sample_question, regular_user):
    """Аутентифицированный ответ для тестов."""
    return await response_manager.create_authenticated_response(
        question_id=sample_question.id,
        user_id=regular_user.id,
        user_session_id="auth_session_456",
        answer={"value": "Authenticated response"},
    )


@pytest.fixture
async def rating_response(response_manager, sample_survey):
    """Рейтинговый ответ для тестов."""
    # Создаем рейтинговый вопрос
    rating_question = await response_manager.create_rating_question(
        survey_id=sample_survey.id,
        text="Rate our service",
        min_rating=1,
        max_rating=5,
    )

    return await response_manager.create_rating_response(
        question_id=rating_question.id,
        user_session_id="rating_session",
        rating_value=4,
    )


@pytest.fixture
async def yes_no_response(response_manager, sample_survey):
    """Ответ да/нет для тестов."""
    # Создаем вопрос да/нет
    yes_no_question = await response_manager.create_yes_no_question(
        survey_id=sample_survey.id,
        text="Do you like this service?",
    )

    return await response_manager.create_yes_no_response(
        question_id=yes_no_question.id,
        user_session_id="yesno_session",
        answer_value=True,
    )


@pytest.fixture
async def email_response(response_manager, sample_survey):
    """Email ответ для тестов."""
    # Создаем email вопрос
    email_question = await response_manager.create_email_question(
        survey_id=sample_survey.id,
        text="Enter your email",
    )

    return await response_manager.create_email_response(
        question_id=email_question.id,
        user_session_id="email_session",
        email_value="test@example.com",
    )


@pytest.fixture
async def phone_response(response_manager, sample_survey):
    """Телефонный ответ для тестов."""
    # Создаем телефонный вопрос
    phone_question = await response_manager.create_phone_question(
        survey_id=sample_survey.id,
        text="Enter your phone number",
    )

    return await response_manager.create_phone_response(
        question_id=phone_question.id,
        user_session_id="phone_session",
        phone_value="+1234567890",
    )


@pytest.fixture
async def multiple_choice_response(response_manager, sample_survey):
    """Ответ множественного выбора для тестов."""
    # Создаем вопрос множественного выбора
    choice_question = await response_manager.create_choice_question(
        survey_id=sample_survey.id,
        text="Select your preferences",
        options=["Option 1", "Option 2", "Option 3"],
        allow_multiple=True,
    )

    return await response_manager.create_multiple_choice_response(
        question_id=choice_question.id,
        user_session_id="choice_session",
        selected_options=["Option 1", "Option 3"],
    )


@pytest.fixture
async def file_upload_response(response_manager, sample_survey):
    """Ответ с файлом для тестов."""
    # Создаем вопрос для загрузки файла
    file_question = await response_manager.create_file_question(
        survey_id=sample_survey.id,
        text="Upload your document",
        allowed_types=["pdf", "doc", "txt"],
    )

    return await response_manager.create_file_upload_response(
        question_id=file_question.id,
        user_session_id="file_session",
        file_data={
            "filename": "document.pdf",
            "content_type": "application/pdf",
            "size": 1024,
            "url": "https://storage.example.com/document.pdf",
        },
    )


@pytest.fixture
async def location_response(response_manager, sample_survey):
    """Географический ответ для тестов."""
    # Создаем вопрос о местоположении
    location_question = await response_manager.create_location_question(
        survey_id=sample_survey.id,
        text="Where are you located?",
    )

    return await response_manager.create_location_response(
        question_id=location_question.id,
        user_session_id="location_session",
        location_data={
            "latitude": 55.7558,
            "longitude": 37.6176,
            "address": "Moscow, Russia",
        },
    )


@pytest.fixture
async def responses_batch(response_manager, sample_survey):
    """Batch ответов для тестов списков и аналитики."""
    return await response_manager.create_responses_batch(
        survey_id=sample_survey.id,
        count=25,
        mix_types=True,  # Смесь разных типов ответов
        mix_users=True,  # Анонимные и аутентифицированные
    )


@pytest.fixture
async def user_responses(response_manager, regular_user, survey_with_questions):
    """Ответы конкретного пользователя для тестов."""
    return await response_manager.create_user_responses(
        user_id=regular_user.id,
        survey_id=survey_with_questions.id,
        completion_rate=0.8,  # 80% завершения
    )


@pytest.fixture
async def completed_survey_responses(
    response_manager, regular_user, survey_with_questions
):
    """Полностью завершенные ответы пользователя."""
    return await response_manager.create_complete_survey_responses(
        user_id=regular_user.id,
        survey_id=survey_with_questions.id,
    )


@pytest.fixture
async def partial_survey_responses(
    response_manager, regular_user, survey_with_questions
):
    """Частично завершенные ответы пользователя."""
    return await response_manager.create_partial_survey_responses(
        user_id=regular_user.id,
        survey_id=survey_with_questions.id,
        completion_rate=0.4,  # 40% завершения
    )


@pytest.fixture
async def anonymous_survey_responses(response_manager, survey_with_questions):
    """Анонимные ответы на опрос."""
    return await response_manager.create_anonymous_survey_responses(
        survey_id=survey_with_questions.id,
        sessions_count=10,
    )


@pytest.fixture
async def survey_progress_data(response_manager, regular_user, survey_with_questions):
    """Данные прогресса прохождения опроса."""
    return await response_manager.create_survey_progress(
        user_id=regular_user.id,
        survey_id=survey_with_questions.id,
        answered_count=3,
        total_count=5,
    )


# Фикстуры для валидных данных
@pytest.fixture
def valid_text_response_data():
    """Валидные данные для текстового ответа."""
    return {
        "user_session_id": "test_session_text",
        "answer": {"value": "This is a valid text response"},
        "is_anonymous": True,
    }


@pytest.fixture
def valid_rating_response_data():
    """Валидные данные для рейтингового ответа."""
    return {
        "user_session_id": "test_session_rating",
        "answer": {"value": 4},
        "is_anonymous": True,
    }


@pytest.fixture
def valid_yes_no_response_data():
    """Валидные данные для ответа да/нет."""
    return {
        "user_session_id": "test_session_yesno",
        "answer": {"value": True},
        "is_anonymous": True,
    }


@pytest.fixture
def valid_email_response_data():
    """Валидные данные для email ответа."""
    return {
        "user_session_id": "test_session_email",
        "answer": {"value": "user@example.com"},
        "is_anonymous": False,
    }


@pytest.fixture
def valid_phone_response_data():
    """Валидные данные для телефонного ответа."""
    return {
        "user_session_id": "test_session_phone",
        "answer": {"value": "+1-555-123-4567"},
        "is_anonymous": False,
    }


@pytest.fixture
def valid_choice_response_data():
    """Валидные данные для ответа с выбором."""
    return {
        "user_session_id": "test_session_choice",
        "answer": {"value": ["Option 1", "Option 2"]},
        "is_anonymous": True,
    }


@pytest.fixture
def valid_location_response_data():
    """Валидные данные для географического ответа."""
    return {
        "user_session_id": "test_session_location",
        "answer": {
            "value": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "New York, NY, USA",
            }
        },
        "is_anonymous": True,
    }


# Фикстуры для невалидных данных
@pytest.fixture
def invalid_response_data():
    """Невалидные данные для тестов ошибок."""
    return {
        "user_session_id": "",  # Пустой session ID
        "answer": None,  # Null answer
        "question_id": -1,  # Невалидный question_id
    }


@pytest.fixture
def invalid_rating_response_data():
    """Невалидные данные для рейтингового ответа."""
    return {
        "user_session_id": "test_session_invalid_rating",
        "answer": {"value": 15},  # За пределами диапазона 1-10
        "is_anonymous": True,
    }


@pytest.fixture
def invalid_email_response_data():
    """Невалидные данные для email ответа."""
    return {
        "user_session_id": "test_session_invalid_email",
        "answer": {"value": "not_an_email"},
        "is_anonymous": False,
    }


@pytest.fixture
def invalid_phone_response_data():
    """Невалидные данные для телефонного ответа."""
    return {
        "user_session_id": "test_session_invalid_phone",
        "answer": {"value": "not_a_phone"},
        "is_anonymous": False,
    }


# Фикстуры для edge cases
@pytest.fixture
def edge_case_response_data():
    """Данные с граничными значениями."""
    return {
        "user_session_id": "edge_session_" + "x" * 200,  # Длинный session ID
        "answer": {"value": "A" * 5000},  # Очень длинный ответ
        "is_anonymous": True,
        "metadata": {"key": "value" * 100},  # Большие метаданные
    }


@pytest.fixture
def unicode_response_data():
    """Данные с Unicode символами."""
    return {
        "user_session_id": "unicode_session_🎉",
        "answer": {"value": "Ответ на русском 🇷🇺 with emoji 😊 and Japanese テスト"},
        "is_anonymous": True,
    }


@pytest.fixture
def boundary_rating_response_data():
    """Граничные значения для рейтинговых ответов."""
    return [
        {
            "user_session_id": "boundary_min",
            "answer": {"value": 1},  # Минимум
            "is_anonymous": True,
        },
        {
            "user_session_id": "boundary_max",
            "answer": {"value": 10},  # Максимум
            "is_anonymous": True,
        },
    ]


# Фикстуры для конкурентности
@pytest.fixture
def concurrent_response_data():
    """Данные для тестов конкурентности."""
    return [
        {
            "user_session_id": f"concurrent_session_{i}",
            "answer": {"value": f"Concurrent response {i}"},
            "is_anonymous": True,
        }
        for i in range(20)
    ]


# Моки для внешних сервисов
@pytest.fixture
def mock_response_notifications(mock_external_services):
    """Мок для уведомлений о ответах."""
    return mock_external_services.notification_service


@pytest.fixture
def mock_response_analytics(mock_external_services):
    """Мок для аналитики ответов."""
    return mock_external_services.analytics_service


@pytest.fixture
def mock_file_storage(mock_external_services):
    """Мок для хранения файлов."""
    return mock_external_services.file_storage_service


@pytest.fixture
def mock_geolocation_service(mock_external_services):
    """Мок для геолокационного сервиса."""
    return mock_external_services.geolocation_service


# Утилиты для тестов
@pytest.fixture
def response_test_utils():
    """Утилиты для работы с ответами в тестах."""

    class ResponseTestUtils:
        @staticmethod
        async def assert_response_structure(response_data: Dict[str, Any]):
            """Проверяет структуру данных ответа."""
            required_fields = [
                "id",
                "question_id",
                "user_session_id",
                "answer",
                "created_at",
            ]
            for field in required_fields:
                assert field in response_data, f"Missing field: {field}"

        @staticmethod
        async def assert_answer_type(answer_data: Dict[str, Any], expected_type: str):
            """Проверяет тип ответа."""
            assert "value" in answer_data
            value = answer_data["value"]

            if expected_type == "text":
                assert isinstance(value, str)
            elif expected_type == "rating":
                assert isinstance(value, (int, float))
                assert 1 <= value <= 10
            elif expected_type == "yes_no":
                assert isinstance(value, bool)
            elif expected_type == "email":
                assert isinstance(value, str)
                assert "@" in value
            elif expected_type == "choice":
                assert isinstance(value, (str, list))

        @staticmethod
        async def assert_survey_progress(
            progress_data: Dict[str, Any], expected_percentage: float
        ):
            """Проверяет прогресс прохождения опроса."""
            assert "answered_count" in progress_data
            assert "total_count" in progress_data
            assert "percentage" in progress_data

            actual_percentage = progress_data["percentage"]
            assert abs(actual_percentage - expected_percentage) < 0.01

        @staticmethod
        async def assert_response_validation(
            validation_result: Dict[str, Any], is_valid: bool
        ):
            """Проверяет результат валидации ответа."""
            assert "is_valid" in validation_result
            assert validation_result["is_valid"] == is_valid

            if not is_valid:
                assert "errors" in validation_result
                assert len(validation_result["errors"]) > 0

    return ResponseTestUtils()


# Параметризированные фикстуры
@pytest.fixture(params=["text", "rating", "yes_no", "email", "phone", "choice"])
async def response_by_type(request, response_manager, sample_survey):
    """Параметризированная фикстура для разных типов ответов."""
    question_type = request.param

    if question_type == "text":
        question = await response_manager.create_text_question(
            survey_id=sample_survey.id
        )
        return await response_manager.create_text_response(question_id=question.id)
    elif question_type == "rating":
        question = await response_manager.create_rating_question(
            survey_id=sample_survey.id
        )
        return await response_manager.create_rating_response(question_id=question.id)
    elif question_type == "yes_no":
        question = await response_manager.create_yes_no_question(
            survey_id=sample_survey.id
        )
        return await response_manager.create_yes_no_response(question_id=question.id)
    elif question_type == "email":
        question = await response_manager.create_email_question(
            survey_id=sample_survey.id
        )
        return await response_manager.create_email_response(question_id=question.id)
    elif question_type == "phone":
        question = await response_manager.create_phone_question(
            survey_id=sample_survey.id
        )
        return await response_manager.create_phone_response(question_id=question.id)
    elif question_type == "choice":
        question = await response_manager.create_choice_question(
            survey_id=sample_survey.id
        )
        return await response_manager.create_choice_response(question_id=question.id)


@pytest.fixture(params=["anonymous", "authenticated"])
async def response_by_user_type(
    request, response_manager, sample_question, regular_user
):
    """Параметризированная фикстура для анонимных/аутентифицированных ответов."""
    if request.param == "anonymous":
        return await response_manager.create_anonymous_response(
            question_id=sample_question.id
        )
    else:
        return await response_manager.create_authenticated_response(
            question_id=sample_question.id,
            user_id=regular_user.id,
        )


@pytest.fixture(params=[0.2, 0.5, 0.8, 1.0])
async def survey_with_progress(
    request, response_manager, regular_user, survey_with_questions
):
    """Опрос с разным прогрессом завершения."""
    completion_rate = request.param
    return await response_manager.create_survey_with_progress(
        user_id=regular_user.id,
        survey_id=survey_with_questions.id,
        completion_rate=completion_rate,
    )


# Фикстуры для валидации
@pytest.fixture
async def validation_test_data(response_manager, sample_survey):
    """Данные для тестов валидации."""
    return await response_manager.create_validation_test_data(
        survey_id=sample_survey.id,
        include_valid=True,
        include_invalid=True,
        question_types=["text", "rating", "email", "phone", "choice"],
    )


# Фикстуры для производительности
@pytest.fixture
async def large_response_dataset(response_manager, sample_survey):
    """Большой датасет ответов для тестов производительности."""
    return await response_manager.create_large_response_dataset(
        survey_id=sample_survey.id,
        response_count=1000,
        user_count=100,
    )


# Фикстуры для интеграционных тестов
@pytest.fixture
async def survey_flow_data(response_manager, regular_user):
    """Данные для тестирования полного флоу опроса."""
    return await response_manager.create_survey_flow_data(
        user_id=regular_user.id,
        include_survey=True,
        include_questions=True,
        include_responses=True,
        include_completion=True,
    )
