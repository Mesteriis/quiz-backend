"""
Фабрики для создания тестовых данных Quiz App.

Этот модуль предоставляет фабрики для всех моделей приложения
с использованием factory_boy и Faker для генерации реалистичных данных.
"""

from .question_factory import (
    QuestionFactory,
    RatingQuestionFactory,
    TextQuestionFactory,
)
from .response_factory import (
    RatingResponseFactory,
    ResponseFactory,
    TextResponseFactory,
)
from .survey_factory import PrivateSurveyFactory, PublicSurveyFactory, SurveyFactory
from .user_data_factory import TelegramUserDataFactory, UserDataFactory
from .user_factory import AdminUserFactory, UserFactory

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
