"""
Response factory для тестов Quiz App.

Создает различные типы ответов для тестирования Response модели
с поддержкой новой архитектуры Respondent.
"""

from pathlib import Path
import sys

import factory
from faker import Faker
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from models.response import Response
from .user_factory import UserFactory
from .respondent_factory import RespondentFactory, AnonymousRespondentFactory

fake = Faker(["en_US", "ru_RU"])


class ResponseFactory(factory.Factory):
    """Базовая фабрика для создания ответов."""

    class Meta:
        model = Response

    question_id = factory.Sequence(lambda n: n + 1)
    user_id = None  # Nullable
    user_session_id = factory.LazyAttribute(lambda obj: f"session_{fake.uuid4()}")
    respondent_id = None  # Nullable
    answer = factory.LazyAttribute(lambda obj: {"value": fake.sentence()})
    created_at = factory.LazyFunction(datetime.utcnow)


class AnonymousResponseFactory(ResponseFactory):
    """Фабрика для создания анонимных ответов."""

    user_id = None
    respondent_id = None


class AuthenticatedResponseFactory(ResponseFactory):
    """Фабрика для создания ответов авторизованных пользователей."""

    user_id = factory.Sequence(lambda n: n + 1)
    respondent_id = None
    user_session_id = factory.LazyAttribute(lambda obj: f"auth_session_{fake.uuid4()}")


class TextResponseFactory(ResponseFactory):
    """Фабрика для создания текстовых ответов."""

    answer = factory.LazyAttribute(lambda obj: {"value": fake.text(max_nb_chars=200)})


class YesNoResponseFactory(ResponseFactory):
    """Фабрика для создания ответов да/нет."""

    answer = factory.LazyAttribute(lambda obj: {"value": fake.boolean()})


class RatingResponseFactory(ResponseFactory):
    """Фабрика для создания рейтинговых ответов."""

    answer = factory.LazyAttribute(
        lambda obj: {"value": fake.random_int(min=1, max=10)}
    )


class EmailResponseFactory(ResponseFactory):
    """Фабрика для создания email ответов."""

    answer = factory.LazyAttribute(lambda obj: {"value": fake.email()})


class PhoneResponseFactory(ResponseFactory):
    """Фабрика для создания телефонных ответов."""

    answer = factory.LazyAttribute(lambda obj: {"value": fake.phone_number()})


class MultipleChoiceResponseFactory(ResponseFactory):
    """Фабрика для создания ответов с множественным выбором."""

    answer = factory.LazyAttribute(
        lambda obj: {
            "selected": fake.random_element(elements=["option1", "option2", "option3"]),
            "options": ["option1", "option2", "option3"],
        }
    )


class LocationResponseFactory(ResponseFactory):
    """Фабрика для создания геолокационных ответов."""

    answer = factory.LazyAttribute(
        lambda obj: {
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
            "accuracy": fake.random_int(min=1, max=100),
        }
    )


class FileUploadResponseFactory(ResponseFactory):
    """Фабрика для создания ответов с загрузкой файлов."""

    answer = factory.LazyAttribute(
        lambda obj: {
            "file_url": fake.url(),
            "file_name": fake.file_name(),
            "file_size": fake.random_int(min=1024, max=1024 * 1024),
        }
    )


class ComplexResponseFactory(ResponseFactory):
    """Фабрика для создания сложных ответов с дополнительными данными."""

    answer = factory.LazyAttribute(
        lambda obj: {
            "value": fake.sentence(),
            "confidence": fake.random_int(min=1, max=100),
            "time_spent": fake.random_int(min=5, max=300),
            "metadata": {
                "source": "web",
                "device": fake.random_element(elements=["desktop", "mobile", "tablet"]),
                "user_agent": fake.user_agent(),
            },
        }
    )


# Вспомогательные функции для создания ответов


def create_response_for_question(
    question_id: int, respondent_id: int = None, **kwargs
) -> Response:
    """
    Создает ответ для конкретного вопроса.

    Args:
        question_id: ID вопроса
        respondent_id: ID респондента (если не указан, создается новый)
        **kwargs: Дополнительные параметры ответа

    Returns:
        Response: Созданный ответ
    """
    if respondent_id is None:
        respondent_id = RespondentFactory().id

    return ResponseFactory(
        question_id=question_id, respondent_id=respondent_id, **kwargs
    )


def create_response_for_respondent(
    respondent_id: int, question_id: int = None, **kwargs
) -> Response:
    """
    Создает ответ для конкретного респондента.

    Args:
        respondent_id: ID респондента
        question_id: ID вопроса (если не указан, создается случайный)
        **kwargs: Дополнительные параметры ответа

    Returns:
        Response: Созданный ответ
    """
    if question_id is None:
        question_id = fake.random_int(min=1, max=100)

    return ResponseFactory(
        question_id=question_id, respondent_id=respondent_id, **kwargs
    )


def create_survey_responses(
    survey_id: int,
    question_ids: list[int],
    respondent_id: int = None,
    response_type: str = "text",
) -> list[Response]:
    """
    Создает набор ответов для опроса.

    Args:
        survey_id: ID опроса
        question_ids: Список ID вопросов
        respondent_id: ID респондента (если не указан, создается новый)
        response_type: Тип ответов (text, yesno, rating, email, phone)

    Returns:
        list[Response]: Список созданных ответов
    """
    if respondent_id is None:
        respondent_id = RespondentFactory().id

    responses = []

    for question_id in question_ids:
        if response_type == "text":
            response = TextResponseFactory(
                question_id=question_id, respondent_id=respondent_id
            )
        elif response_type == "yesno":
            response = YesNoResponseFactory(
                question_id=question_id, respondent_id=respondent_id
            )
        elif response_type == "rating":
            response = RatingResponseFactory(
                question_id=question_id, respondent_id=respondent_id
            )
        elif response_type == "email":
            response = EmailResponseFactory(
                question_id=question_id, respondent_id=respondent_id
            )
        elif response_type == "phone":
            response = PhoneResponseFactory(
                question_id=question_id, respondent_id=respondent_id
            )
        else:
            response = ResponseFactory(
                question_id=question_id, respondent_id=respondent_id
            )

        responses.append(response)

    return responses


def create_responses_batch(
    count: int = 10, respondent_type: str = "mixed", response_type: str = "mixed"
) -> list[Response]:
    """
    Создает батч ответов различных типов.

    Args:
        count: Количество ответов
        respondent_type: Тип респондентов (mixed, anonymous, authenticated)
        response_type: Тип ответов (mixed, text, yesno, rating)

    Returns:
        list[Response]: Список созданных ответов
    """
    responses = []

    for i in range(count):
        # Определяем тип респондента
        if respondent_type == "mixed":
            if i % 2 == 0:
                factory_class = AnonymousResponseFactory
            else:
                factory_class = AuthenticatedResponseFactory
        elif respondent_type == "anonymous":
            factory_class = AnonymousResponseFactory
        elif respondent_type == "authenticated":
            factory_class = AuthenticatedResponseFactory
        else:
            factory_class = ResponseFactory

        # Определяем тип ответа
        if response_type == "mixed":
            response_factories = [
                TextResponseFactory,
                YesNoResponseFactory,
                RatingResponseFactory,
                EmailResponseFactory,
            ]
            response_factory = fake.random_element(elements=response_factories)
        elif response_type == "text":
            response_factory = TextResponseFactory
        elif response_type == "yesno":
            response_factory = YesNoResponseFactory
        elif response_type == "rating":
            response_factory = RatingResponseFactory
        elif response_type == "email":
            response_factory = EmailResponseFactory
        else:
            response_factory = factory_class

        # Создаем ответ, комбинируя типы
        if response_type == "mixed":
            response = response_factory()
        else:
            response = factory_class()

        responses.append(response)

    return responses


def create_partial_survey_responses(
    survey_id: int,
    question_ids: list[int],
    completion_percentage: float = 0.5,
    respondent_id: int = None,
) -> list[Response]:
    """
    Создает частично заполненные ответы для опроса.

    Args:
        survey_id: ID опроса
        question_ids: Список ID вопросов
        completion_percentage: Процент заполнения (0.0-1.0)
        respondent_id: ID респондента

    Returns:
        list[Response]: Список созданных ответов
    """
    if respondent_id is None:
        respondent_id = RespondentFactory().id

    questions_to_answer = int(len(question_ids) * completion_percentage)
    selected_questions = fake.random_elements(
        elements=question_ids, length=questions_to_answer, unique=True
    )

    return create_survey_responses(
        survey_id=survey_id,
        question_ids=selected_questions,
        respondent_id=respondent_id,
    )
