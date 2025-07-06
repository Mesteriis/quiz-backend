"""
Фабрики для создания тестовых данных Quiz App.

Этот модуль предоставляет фабрики для всех моделей приложения
с использованием factory_boy и Faker для генерации реалистичных данных.
"""

from .user_factory import UserFactory, AdminUserFactory
from .survey_factory import SurveyFactory, PublicSurveyFactory, PrivateSurveyFactory
from .question_factory import (
    QuestionFactory,
    TextQuestionFactory,
    RatingQuestionFactory,
)
from .response_factory import (
    ResponseFactory,
    TextResponseFactory,
    RatingResponseFactory,
)
from .user_data_factory import UserDataFactory, TelegramUserDataFactory

__all__ = [
    # User factories
    "UserFactory",
    "AdminUserFactory",
    # Survey factories
    "SurveyFactory",
    "PublicSurveyFactory",
    "PrivateSurveyFactory",
    # Question factories
    "QuestionFactory",
    "TextQuestionFactory",
    "RatingQuestionFactory",
    # Response factories
    "ResponseFactory",
    "TextResponseFactory",
    "RatingResponseFactory",
    # User data factories
    "UserDataFactory",
    "TelegramUserDataFactory",
]
