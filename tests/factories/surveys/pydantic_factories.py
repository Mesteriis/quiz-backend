"""
Pydantic фабрики для API схем опросов.

Генерируют данные для:
- Создания опросов (SurveyCreate)
- Обновления опросов (SurveyUpdate)
- Ответов API (SurveyResponse)

Поддерживают сложные сценарии с различными типами опросов.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.fields import Use, PostGenerated, Require
from polyfactory.pytest_plugin import register_fixture
from faker import Faker

from src.schemas.survey import (
    SurveyCreate,
    SurveyUpdate,
    SurveyResponse,
)

# Глобальный faker
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


class SurveyCreateDataFactory(ModelFactory[SurveyCreate]):
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
    def end_date(cls):
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


class SurveyUpdateDataFactory(ModelFactory[SurveyUpdate]):
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


class SurveyResponseDataFactory(ModelFactory[SurveyResponse]):
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
        """Дата начала опроса."""
        if fake.boolean(chance_of_getting_true=30):
            days_from_now = fake.random_int(min=-30, max=30)
            return datetime.utcnow() + timedelta(days=days_from_now)
        return None

    @classmethod
    def end_date(cls) -> Optional[datetime]:
        """Дата окончания опроса."""
        if fake.boolean(chance_of_getting_true=50):
            days_from_now = fake.random_int(min=7, max=90)
            return datetime.utcnow() + timedelta(days=days_from_now)
        return None


# ============================================================================
# SPECIALIZED FACTORIES
# ============================================================================


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
    def end_date(cls):
        """Дата окончания в будущем."""

        def generate_future_end_date(name: str, values: Dict[str, Any]) -> datetime:
            days_future = fake.random_int(min=7, max=90)
            return datetime.utcnow() + timedelta(days=days_future)

        return PostGenerated(generate_future_end_date)
