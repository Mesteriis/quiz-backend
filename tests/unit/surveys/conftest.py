"""
Конфигурация тестов для домена опросов.

Содержит фикстуры и настройки специфичные для тестирования
системы опросов, включая создание, управление, публикацию,
приватные опросы, вопросы и ответы.
"""

import pytest
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock

# Импорт фабрик для surveys домена
from tests.factories import (
    # Survey фабрики
    SurveyFactory,
    PublicSurveyFactory,
    PrivateSurveyFactory,
    InactiveSurveyFactory,
    SurveyWithQuestionsFactory,
    ShortSurveyFactory,
    LongSurveyFactory,
    RecentSurveyFactory,
    PopularSurveyFactory,
    ResearchSurveyFactory,
    FeedbackSurveyFactory,
    # Question фабрики
    QuestionFactory,
    TextQuestionFactory,
    RatingQuestionFactory,
    # RespondentSurvey фабрики
    RespondentSurveyFactory,
    StartedSurveyFactory,
    InProgressSurveyFactory,
    AlmostCompletedSurveyFactory,
    CompletedSurveyFactory,
    AbandonedSurveyFactory,
    QuickCompletedSurveyFactory,
    ThoroughCompletedSurveyFactory,
    TelegramSurveyFactory,
    MobileSurveyFactory,
    # User фабрики (для владельцев опросов)
    UserFactory,
    AdminUserFactory,
    RegularUserFactory,
    # Utility functions
    create_survey_with_questions,
    create_test_surveys_batch,
    create_survey_lifecycle,
    create_complex_survey_structure,
)


@pytest.fixture
async def survey_manager(db_session):
    """Менеджер для управления опросами в тестах."""
    from tests.factories.survey_factory import SurveyAsyncManager

    return SurveyAsyncManager(db_session)


@pytest.fixture
async def question_manager(db_session):
    """Менеджер для управления вопросами в тестах."""
    from tests.factories.question_factory import QuestionAsyncManager

    return QuestionAsyncManager(db_session)


@pytest.fixture
async def sample_survey(survey_manager):
    """Базовый публичный активный опрос для тестов."""
    return await survey_manager.create_public_survey(
        title="Sample Test Survey",
        description="A sample survey for testing purposes",
    )


@pytest.fixture
async def sample_private_survey(survey_manager):
    """Приватный опрос для тестов."""
    return await survey_manager.create_private_survey(
        title="Private Test Survey",
        description="A private survey for testing purposes",
    )


@pytest.fixture
async def sample_inactive_survey(survey_manager):
    """Неактивный опрос для тестов."""
    return await survey_manager.create_inactive_survey(
        title="Inactive Test Survey",
        description="An inactive survey for testing purposes",
    )


@pytest.fixture
async def sample_question(question_manager, sample_survey):
    """Базовый вопрос для тестов."""
    return await question_manager.create_text_question(
        survey_id=sample_survey.id,
        text="What is your favorite color?",
        order=1,
    )


@pytest.fixture
async def survey_with_questions(survey_manager):
    """Опрос с набором вопросов."""
    return await survey_manager.create_survey_with_questions(
        question_count=5,
        title="Survey with Multiple Questions",
        description="A survey containing multiple questions for testing",
    )


@pytest.fixture
async def long_survey(survey_manager):
    """Длинный опрос для тестов производительности."""
    return await survey_manager.create_long_survey(
        question_count=50,
        title="Long Performance Test Survey",
    )


@pytest.fixture
async def short_survey(survey_manager):
    """Короткий опрос для быстрых тестов."""
    return await survey_manager.create_short_survey(
        question_count=2,
        title="Quick Survey",
    )


@pytest.fixture
async def popular_survey(survey_manager):
    """Популярный опрос с множеством ответов."""
    return await survey_manager.create_popular_survey(
        response_count=100,
        title="Popular Survey with Many Responses",
    )


@pytest.fixture
async def research_survey(survey_manager):
    """Исследовательский опрос для академических тестов."""
    return await survey_manager.create_research_survey(
        title="Research Survey",
        categories=["education", "research", "academic"],
    )


@pytest.fixture
async def feedback_survey(survey_manager):
    """Опрос обратной связи."""
    return await survey_manager.create_feedback_survey(
        title="Feedback Survey",
        target_type="service",
    )


@pytest.fixture
async def surveys_batch(survey_manager):
    """Batch опросов для тестов списков и пагинации."""
    return await survey_manager.create_surveys_batch(
        count=20,
        mix_types=True,  # Смесь публичных/приватных/активных/неактивных
    )


@pytest.fixture
async def user_with_surveys(survey_manager, regular_user):
    """Пользователь с несколькими опросами."""
    surveys = []
    for i in range(3):
        survey = await survey_manager.create_survey(
            title=f"User Survey {i + 1}",
            description=f"Survey {i + 1} owned by user",
            creator_id=regular_user.id,
        )
        surveys.append(survey)
    return regular_user, surveys


@pytest.fixture
async def admin_with_surveys(survey_manager, admin_user):
    """Админ с опросами для тестов прав доступа."""
    surveys = []
    for i in range(5):
        survey = await survey_manager.create_survey(
            title=f"Admin Survey {i + 1}",
            description=f"Admin survey {i + 1}",
            creator_id=admin_user.id,
        )
        surveys.append(survey)
    return admin_user, surveys


# Фикстуры для валидных данных
@pytest.fixture
def valid_survey_data():
    """Валидные данные для создания опроса."""
    return {
        "title": "Valid Survey Title",
        "description": "Valid survey description for testing purposes",
        "is_public": True,
        "is_active": True,
        "telegram_notifications": True,
        "allow_anonymous": True,
        "max_responses": 1000,
        "expires_at": None,
    }


@pytest.fixture
def valid_private_survey_data():
    """Валидные данные для создания приватного опроса."""
    return {
        "title": "Private Survey Title",
        "description": "Private survey for testing",
        "is_public": False,
        "is_active": True,
        "telegram_notifications": False,
        "allow_anonymous": False,
        "max_responses": 100,
        "access_password": "test123",
    }


@pytest.fixture
def valid_question_data():
    """Валидные данные для создания вопроса."""
    return {
        "text": "What is your opinion on this topic?",
        "question_type": "text",
        "is_required": True,
        "order": 1,
        "options": None,
    }


@pytest.fixture
def valid_rating_question_data():
    """Валидные данные для создания рейтингового вопроса."""
    return {
        "text": "Rate this from 1 to 5",
        "question_type": "rating",
        "is_required": True,
        "order": 1,
        "min_rating": 1,
        "max_rating": 5,
    }


# Фикстуры для невалидных данных
@pytest.fixture
def invalid_survey_data():
    """Невалидные данные для тестов ошибок."""
    return {
        "title": "",  # Пустой title
        "description": None,  # Null description
        "is_public": "invalid",  # Невалидный boolean
        "max_responses": -1,  # Отрицательное число
    }


@pytest.fixture
def invalid_question_data():
    """Невалидные данные для вопроса."""
    return {
        "text": "",  # Пустой текст
        "question_type": "invalid_type",
        "order": -1,  # Отрицательный порядок
        "is_required": "invalid",  # Невалидный boolean
    }


# Фикстуры для edge cases
@pytest.fixture
def edge_case_survey_data():
    """Данные с граничными значениями."""
    return {
        "title": "A" * 200,  # Максимальная длина
        "description": "D" * 2000,  # Очень длинное описание
        "is_public": True,
        "max_responses": 999999,  # Максимальное количество ответов
        "telegram_notifications": True,
        "allow_anonymous": True,
    }


@pytest.fixture
def edge_case_question_data():
    """Вопрос с граничными значениями."""
    return {
        "text": "Q" * 500,  # Максимальная длина вопроса
        "question_type": "text",
        "is_required": True,
        "order": 999,  # Большой порядок
        "help_text": "H" * 1000,  # Длинный help text
    }


@pytest.fixture
def unicode_survey_data():
    """Данные с Unicode символами."""
    return {
        "title": "Опрос с Unicode 🙂 テスト 测试",
        "description": "Описание с эмодзи 🎉 и символами ñáéíóú",
        "is_public": True,
        "is_active": True,
        "telegram_notifications": True,
    }


# Фикстуры для конкурентности
@pytest.fixture
def concurrent_survey_requests():
    """Данные для тестов конкурентности."""
    return [
        {
            "title": f"Concurrent Survey {i}",
            "description": f"Survey {i} for concurrency testing",
            "is_public": True,
            "is_active": True,
        }
        for i in range(10)
    ]


# Моки для внешних сервисов
@pytest.fixture
def mock_survey_notifications(mock_external_services):
    """Мок для уведомлений о опросах."""
    return mock_external_services.notification_service


@pytest.fixture
def mock_survey_analytics(mock_external_services):
    """Мок для аналитики опросов."""
    return mock_external_services.analytics_service


@pytest.fixture
def mock_survey_export(mock_external_services):
    """Мок для экспорта опросов."""
    return mock_external_services.export_service


# Утилиты для тестов
@pytest.fixture
def survey_test_utils():
    """Утилиты для работы с опросами в тестах."""

    class SurveyTestUtils:
        @staticmethod
        async def assert_survey_structure(survey_data: Dict[str, Any]):
            """Проверяет структуру данных опроса."""
            required_fields = [
                "id",
                "title",
                "description",
                "is_public",
                "is_active",
                "created_at",
            ]
            for field in required_fields:
                assert field in survey_data, f"Missing field: {field}"

        @staticmethod
        async def assert_question_structure(question_data: Dict[str, Any]):
            """Проверяет структуру данных вопроса."""
            required_fields = ["id", "text", "question_type", "order", "is_required"]
            for field in required_fields:
                assert field in question_data, f"Missing field: {field}"

        @staticmethod
        async def assert_survey_permissions(survey_data: Dict[str, Any], user_id: int):
            """Проверяет права доступа к опросу."""
            if not survey_data.get("is_public", False):
                assert (
                    "access_token" in survey_data
                    or survey_data.get("creator_id") == user_id
                )

    return SurveyTestUtils()


# Параметризированные фикстуры
@pytest.fixture(params=["public", "private", "inactive"])
async def survey_by_type(request, survey_manager):
    """Параметризированная фикстура для разных типов опросов."""
    if request.param == "public":
        return await survey_manager.create_public_survey()
    elif request.param == "private":
        return await survey_manager.create_private_survey()
    elif request.param == "inactive":
        return await survey_manager.create_inactive_survey()


@pytest.fixture(params=["text", "rating", "choice"])
async def question_by_type(request, question_manager, sample_survey):
    """Параметризированная фикстура для разных типов вопросов."""
    if request.param == "text":
        return await question_manager.create_text_question(survey_id=sample_survey.id)
    elif request.param == "rating":
        return await question_manager.create_rating_question(survey_id=sample_survey.id)
    elif request.param == "choice":
        return await question_manager.create_choice_question(survey_id=sample_survey.id)


@pytest.fixture(params=[1, 5, 10, 25])
async def survey_with_variable_questions(request, survey_manager):
    """Опрос с переменным количеством вопросов."""
    return await survey_manager.create_survey_with_questions(
        question_count=request.param,
        title=f"Survey with {request.param} questions",
    )


# Фикстуры для статистики и метрик
@pytest.fixture
async def survey_with_responses(survey_manager):
    """Опрос с ответами для тестов статистики."""
    return await survey_manager.create_survey_with_responses(
        response_count=50,
        title="Survey with Responses for Statistics",
    )


@pytest.fixture
async def survey_completion_metrics(survey_manager):
    """Метрики завершения опросов."""
    return await survey_manager.create_completion_metrics_data(
        completed=30,
        in_progress=15,
        abandoned=5,
    )
