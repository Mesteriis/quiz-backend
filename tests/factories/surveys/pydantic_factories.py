"""
Pydantic фабрики для API схем опросов.

Генерируют данные для:
- Создания опросов (SurveyCreate)
- Обновления опросов (SurveyUpdate)
- Создания вопросов (QuestionCreate)
- Ответов API (SurveyResponse)

Поддерживают сложные сценарии с различными типами вопросов.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from polyfactory.factories import BaseFactory
from polyfactory.fields import Use, PostGenerated, Require
from polyfactory.pytest_plugin import register_fixture
from faker import Faker

from src.schemas.survey import (
    SurveyCreate,
    SurveyUpdate,
    SurveyResponse,
    SurveyListResponse,
)
from src.schemas.question import QuestionCreate, QuestionResponse
from src.schemas.response import ResponseCreate, ResponseData

# Глобальный faker
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


class SurveyCreateDataFactory(BaseFactory[SurveyCreate]):
    """
    Фабрика для данных создания опросов.

    Генерирует валидные данные для POST /surveys запросов.
    """

    __model__ = SurveyCreate

    @classmethod
    def title(cls) -> str:
        """Уникальный заголовок опроса."""
        unique_part = uuid.uuid4().hex[:6]
        return f"{fake.catch_phrase()} - {unique_part}"

    @classmethod
    def description(cls) -> str:
        """Описание опроса."""
        return fake.paragraph(nb_sentences=2)

    # Настройки по умолчанию
    is_public = Use(lambda: fake.boolean(chance_of_getting_true=70))
    telegram_notifications = Use(lambda: fake.boolean(chance_of_getting_true=60))
    allow_anonymous = Use(lambda: fake.boolean(chance_of_getting_true=40))
    show_results = Use(lambda: fake.boolean(chance_of_getting_true=85))

    @classmethod
    def max_responses(cls) -> Optional[int]:
        """Максимальное количество ответов."""
        if fake.boolean(chance_of_getting_true=50):
            return fake.random_int(min=10, max=1000)
        return None

    @classmethod
    def start_date(cls) -> Optional[datetime]:
        """Дата начала опроса."""
        if fake.boolean(chance_of_getting_true=30):
            days_from_now = fake.random_int(min=0, max=30)
            return datetime.utcnow() + timedelta(days=days_from_now)
        return None

    @classmethod
    def end_date(cls) -> PostGenerated[Optional[datetime]]:
        """Дата окончания после start_date."""

        def generate_end_date(name: str, values: Dict[str, Any]) -> Optional[datetime]:
            start_date = values.get("start_date")
            if start_date and fake.boolean(chance_of_getting_true=60):
                days_duration = fake.random_int(min=7, max=90)
                return start_date + timedelta(days=days_duration)
            elif fake.boolean(chance_of_getting_true=20):
                # Дата окончания без даты начала
                days_from_now = fake.random_int(min=7, max=90)
                return datetime.utcnow() + timedelta(days=days_from_now)
            return None

        return PostGenerated(generate_end_date)


@register_fixture(name="survey_create_data")
class ValidSurveyCreateDataFactory(SurveyCreateDataFactory):
    """Фабрика для валидных данных создания опроса."""

    @classmethod
    def title(cls) -> str:
        """Валидный заголовок."""
        unique_part = uuid.uuid4().hex[:6]
        return f"Valid Test Survey - {unique_part}"

    @classmethod
    def description(cls) -> str:
        """Валидное описание."""
        return "This is a valid test survey for automated testing purposes."

    # Стандартные настройки для тестов
    is_public = True
    allow_anonymous = True
    telegram_notifications = False
    show_results = True
    max_responses = None


class SurveyUpdateDataFactory(BaseFactory[SurveyUpdate]):
    """
    Фабрика для данных обновления опросов.

    Генерирует данные для PATCH/PUT /surveys/{id} запросов.
    """

    __model__ = SurveyUpdate

    # Все поля опциональны для обновления
    @classmethod
    def title(cls) -> Optional[str]:
        """Новый заголовок (60% случаев)."""
        if fake.boolean(chance_of_getting_true=60):
            unique_part = uuid.uuid4().hex[:4]
            return f"Updated: {fake.catch_phrase()} - {unique_part}"
        return None

    @classmethod
    def description(cls) -> Optional[str]:
        """Новое описание (50% случаев)."""
        return (
            fake.paragraph(nb_sentences=2)
            if fake.boolean(chance_of_getting_true=50)
            else None
        )

    @classmethod
    def is_public(cls) -> Optional[bool]:
        """Изменение публичности (30% случаев)."""
        return fake.boolean() if fake.boolean(chance_of_getting_true=30) else None

    @classmethod
    def telegram_notifications(cls) -> Optional[bool]:
        """Изменение Telegram уведомлений (25% случаев)."""
        return fake.boolean() if fake.boolean(chance_of_getting_true=25) else None

    @classmethod
    def allow_anonymous(cls) -> Optional[bool]:
        """Изменение разрешения анонимных ответов (20% случаев)."""
        return fake.boolean() if fake.boolean(chance_of_getting_true=20) else None


class QuestionCreateDataFactory(BaseFactory[QuestionCreate]):
    """
    Фабрика для данных создания вопросов.

    Генерирует данные для POST /surveys/{id}/questions запросов.
    """

    __model__ = QuestionCreate

    @classmethod
    def title(cls) -> str:
        """Заголовок вопроса."""
        return fake.sentence(nb_words=6).rstrip(".") + "?"

    @classmethod
    def description(cls) -> Optional[str]:
        """Описание вопроса (70% случаев)."""
        return (
            fake.paragraph(nb_sentences=1)
            if fake.boolean(chance_of_getting_true=70)
            else None
        )

    @classmethod
    def question_type(cls) -> str:
        """Тип вопроса."""
        return fake.random_element(
            [
                "TEXT",
                "NUMBER",
                "EMAIL",
                "BOOLEAN",
                "SINGLE_CHOICE",
                "MULTIPLE_CHOICE",
                "SCALE",
            ]
        )

    is_required = Use(lambda: fake.boolean(chance_of_getting_true=75))
    order = Use(lambda: fake.random_int(min=1, max=20))

    @classmethod
    def question_data(cls) -> PostGenerated[Optional[Dict[str, Any]]]:
        """Данные вопроса в зависимости от типа."""

        def generate_question_data(
            name: str, values: Dict[str, Any]
        ) -> Optional[Dict[str, Any]]:
            question_type = values.get("question_type", "TEXT")

            if question_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
                options = [
                    fake.word().title() for _ in range(fake.random_int(min=2, max=5))
                ]
                return {
                    "options": options,
                    "allow_other": fake.boolean(chance_of_getting_true=30),
                }
            elif question_type == "SCALE":
                return {
                    "min_value": 1,
                    "max_value": fake.random_int(min=5, max=10),
                    "step": 1,
                    "min_label": fake.word(),
                    "max_label": fake.word(),
                }

            return None

        return PostGenerated(generate_question_data)


@register_fixture(name="question_create_data")
class TextQuestionCreateDataFactory(QuestionCreateDataFactory):
    """Фабрика для создания текстовых вопросов."""

    question_type = "TEXT"
    question_data = None

    @classmethod
    def title(cls) -> str:
        """Текстовый вопрос."""
        return f"What is your opinion about {fake.word().lower()}?"


class ChoiceQuestionCreateDataFactory(QuestionCreateDataFactory):
    """Фабрика для создания вопросов с выбором."""

    @classmethod
    def question_type(cls) -> str:
        """Тип выбора."""
        return fake.random_element(["SINGLE_CHOICE", "MULTIPLE_CHOICE"])

    @classmethod
    def question_data(cls) -> Dict[str, Any]:
        """Данные для выбора."""
        options = ["Отлично", "Хорошо", "Удовлетворительно", "Плохо"]
        return {"options": options, "allow_other": True}


class ResponseCreateDataFactory(BaseFactory[ResponseCreate]):
    """
    Фабрика для данных создания ответов.

    Генерирует данные для POST /responses запросов.
    """

    __model__ = ResponseCreate

    @classmethod
    def user_session_id(cls) -> str:
        """Уникальный ID сессии."""
        return f"session_{uuid.uuid4().hex[:16]}"

    @classmethod
    def answer(cls) -> Dict[str, Any]:
        """Базовый ответ."""
        return {"text": fake.sentence(), "timestamp": datetime.utcnow().isoformat()}

    # question_id будет передан при создании


@register_fixture(name="response_create_data")
class TextResponseCreateDataFactory(ResponseCreateDataFactory):
    """Фабрика для текстовых ответов."""

    @classmethod
    def answer(cls) -> Dict[str, Any]:
        """Текстовый ответ."""
        return {"text": fake.paragraph(nb_sentences=2)}


class ChoiceResponseCreateDataFactory(ResponseCreateDataFactory):
    """Фабрика для ответов с выбором."""

    @classmethod
    def answer(cls) -> Dict[str, Any]:
        """Ответ с выбором."""
        return {
            "selected_options": [0, 2],
            "other_text": fake.sentence()
            if fake.boolean(chance_of_getting_true=30)
            else None,
        }


class SurveyResponseDataFactory(BaseFactory[SurveyResponse]):
    """
    Фабрика для данных ответов API опросов.

    Генерирует данные для проверки структуры ответов
    от endpoints, возвращающих информацию об опросах.
    """

    __model__ = SurveyResponse

    @classmethod
    def id(cls) -> int:
        """ID опроса."""
        return fake.random_int(min=1, max=999999)

    @classmethod
    def title(cls) -> str:
        """Заголовок опроса."""
        unique_part = uuid.uuid4().hex[:6]
        return f"{fake.catch_phrase()} - {unique_part}"

    description = Use(fake.paragraph)
    is_active = Use(lambda: fake.boolean(chance_of_getting_true=80))
    is_public = Use(lambda: fake.boolean(chance_of_getting_true=70))
    telegram_notifications = Use(lambda: fake.boolean(chance_of_getting_true=60))
    allow_anonymous = Use(lambda: fake.boolean(chance_of_getting_true=40))
    show_results = Use(lambda: fake.boolean(chance_of_getting_true=85))

    @classmethod
    def max_responses(cls) -> Optional[int]:
        """Максимальное количество ответов."""
        if fake.boolean(chance_of_getting_true=50):
            return fake.random_int(min=10, max=1000)
        return None

    @classmethod
    def response_count(cls) -> int:
        """Количество ответов."""
        return fake.random_int(min=0, max=500)

    @classmethod
    def question_count(cls) -> int:
        """Количество вопросов."""
        return fake.random_int(min=1, max=20)

    # Информация о создателе
    @classmethod
    def created_by(cls) -> int:
        """ID создателя."""
        return fake.random_int(min=1, max=1000)

    @classmethod
    def creator_username(cls) -> Optional[str]:
        """Username создателя."""
        return (
            f"user_{uuid.uuid4().hex[:8]}"
            if fake.boolean(chance_of_getting_true=70)
            else None
        )

    # Временные поля
    created_at = Use(fake.date_time)
    updated_at = Use(fake.date_time)

    @classmethod
    def start_date(cls) -> Optional[datetime]:
        """Дата начала."""
        return fake.date_time() if fake.boolean(chance_of_getting_true=30) else None

    @classmethod
    def end_date(cls) -> Optional[datetime]:
        """Дата окончания."""
        return fake.date_time() if fake.boolean(chance_of_getting_true=30) else None


class SurveyListResponseDataFactory(BaseFactory[SurveyListResponse]):
    """
    Фабрика для данных списка опросов.

    Генерирует данные для GET /surveys запросов.
    """

    __model__ = SurveyListResponse

    @classmethod
    def surveys(cls) -> List[Dict[str, Any]]:
        """Список опросов."""
        count = fake.random_int(min=1, max=10)
        return [SurveyResponseDataFactory.build().__dict__ for _ in range(count)]

    @classmethod
    def total(cls) -> PostGenerated[int]:
        """Общее количество опросов."""

        def generate_total(name: str, values: Dict[str, Any]) -> int:
            surveys = values.get("surveys", [])
            base_count = len(surveys)
            return base_count + fake.random_int(min=0, max=50)

        return PostGenerated(generate_total)

    @classmethod
    def page(cls) -> int:
        """Номер страницы."""
        return fake.random_int(min=1, max=10)

    @classmethod
    def page_size(cls) -> int:
        """Размер страницы."""
        return fake.random_element([10, 20, 50])

    @classmethod
    def has_next(cls) -> PostGenerated[bool]:
        """Есть ли следующая страница."""

        def generate_has_next(name: str, values: Dict[str, Any]) -> bool:
            page = values.get("page", 1)
            page_size = values.get("page_size", 10)
            total = values.get("total", 0)
            return (page * page_size) < total

        return PostGenerated(generate_has_next)


# Специализированные фабрики для различных сценариев


class PublicSurveyCreateDataFactory(SurveyCreateDataFactory):
    """Фабрика для создания публичных опросов."""

    is_public = True
    allow_anonymous = True
    telegram_notifications = True

    @classmethod
    def title(cls) -> str:
        """Заголовок публичного опроса."""
        unique_part = uuid.uuid4().hex[:6]
        return f"Public Survey: {fake.catch_phrase()} - {unique_part}"


class PrivateSurveyCreateDataFactory(SurveyCreateDataFactory):
    """Фабрика для создания приватных опросов."""

    is_public = False
    allow_anonymous = False
    telegram_notifications = False

    @classmethod
    def title(cls) -> str:
        """Заголовок приватного опроса."""
        unique_part = uuid.uuid4().hex[:6]
        return f"Private Survey: {fake.catch_phrase()} - {unique_part}"


class ActiveSurveyResponseDataFactory(SurveyResponseDataFactory):
    """Фабрика для активных опросов в ответах API."""

    is_active = True

    @classmethod
    def start_date(cls) -> datetime:
        """Дата начала в прошлом."""
        days_ago = fake.random_int(min=1, max=30)
        return datetime.utcnow() - timedelta(days=days_ago)

    @classmethod
    def end_date(cls) -> PostGenerated[datetime]:
        """Дата окончания в будущем."""

        def generate_future_end_date(name: str, values: Dict[str, Any]) -> datetime:
            start_date = values.get("start_date", datetime.utcnow())
            days_duration = fake.random_int(min=30, max=90)
            return start_date + timedelta(days=days_duration)

        return PostGenerated(generate_future_end_date)
