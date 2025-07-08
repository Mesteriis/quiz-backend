"""
SQLAlchemy фабрики для моделей опросов.

Использует Polyfactory для создания:
- Survey: основные опросы
- Question: вопросы в опросах
- Response: ответы пользователей

Поддерживает создание сложных сценариев с вложенными вопросами.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional, Dict

from polyfactory.factories import BaseFactory
from polyfactory.fields import Use, PostGenerated, Require
from polyfactory.pytest_plugin import register_fixture
from faker import Faker

from src.models.survey import Survey
from src.models.question import Question
from src.models.response import Response

# Глобальный faker
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


class SurveyModelFactory(BaseFactory[Survey]):
    """
    Фабрика для создания базовых опросов.

    Генерирует опросы с реалистичными данными и уникальными полями.
    """

    __model__ = Survey
    __async_persistence__ = "commit"

    # Уникальные поля
    @classmethod
    def title(cls) -> str:
        """Уникальный заголовок опроса."""
        unique_part = uuid.uuid4().hex[:6]
        return f"{fake.catch_phrase()} - Survey {unique_part}"

    @classmethod
    def description(cls) -> str:
        """Описание опроса."""
        return fake.paragraph(nb_sentences=3)

    # Статусы с вероятностным распределением
    @classmethod
    def is_active(cls) -> bool:
        """80% опросов активны."""
        return fake.boolean(chance_of_getting_true=80)

    @classmethod
    def is_public(cls) -> bool:
        """70% опросов публичны."""
        return fake.boolean(chance_of_getting_true=70)

    @classmethod
    def telegram_notifications(cls) -> bool:
        """60% опросов имеют Telegram уведомления."""
        return fake.boolean(chance_of_getting_true=60)

    # Настройки опроса
    @classmethod
    def max_responses(cls) -> Optional[int]:
        """Ограничение на количество ответов (50% опросов имеют)."""
        if fake.boolean(chance_of_getting_true=50):
            return fake.random_int(min=10, max=1000)
        return None

    @classmethod
    def allow_anonymous(cls) -> bool:
        """40% опросов разрешают анонимные ответы."""
        return fake.boolean(chance_of_getting_true=40)

    @classmethod
    def show_results(cls) -> bool:
        """85% опросов показывают результаты."""
        return fake.boolean(chance_of_getting_true=85)

    # Временные поля
    @classmethod
    def created_at(cls) -> datetime:
        """Дата создания опроса (до 180 дней назад)."""
        days_ago = fake.random_int(min=0, max=180)
        return datetime.utcnow() - timedelta(days=days_ago)

    @classmethod
    def updated_at(cls) -> PostGenerated[datetime]:
        """updated_at после created_at."""

        def generate_updated_at(name: str, values: Dict[str, Any]) -> datetime:
            created = values.get("created_at", datetime.utcnow())
            max_days = (datetime.utcnow() - created).days
            if max_days > 0:
                days_after = fake.random_int(min=0, max=max_days)
                return created + timedelta(days=days_after)
            return created

        return PostGenerated(generate_updated_at)

    # Даты начала и окончания
    @classmethod
    def start_date(cls) -> Optional[datetime]:
        """Дата начала (30% опросов имеют)."""
        if fake.boolean(chance_of_getting_true=30):
            days_from_now = fake.random_int(min=-30, max=30)
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
            return None

        return PostGenerated(generate_end_date)

    # Требуется указать created_by при создании
    created_by = Require()


@register_fixture(name="survey_model")
class PublicSurveyModelFactory(SurveyModelFactory):
    """Фабрика для создания публичных опросов."""

    is_public = True
    is_active = True
    allow_anonymous = True

    @classmethod
    def title(cls) -> str:
        """Заголовок публичного опроса."""
        unique_part = uuid.uuid4().hex[:6]
        return f"Public Survey: {fake.catch_phrase()} - {unique_part}"


@register_fixture(name="private_survey_model")
class PrivateSurveyModelFactory(SurveyModelFactory):
    """Фабрика для создания приватных опросов."""

    is_public = False
    is_active = True
    allow_anonymous = False

    @classmethod
    def title(cls) -> str:
        """Заголовок приватного опроса."""
        unique_part = uuid.uuid4().hex[:6]
        return f"Private Survey: {fake.catch_phrase()} - {unique_part}"


@register_fixture(name="active_survey_model")
class ActiveSurveyModelFactory(SurveyModelFactory):
    """Фабрика для создания активных опросов."""

    is_active = True
    is_public = True

    # Активные опросы имеют даты в будущем
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


class QuestionModelFactory(BaseFactory[Question]):
    """
    Фабрика для создания вопросов в опросах.

    Поддерживает различные типы вопросов с соответствующими данными.
    """

    __model__ = Question
    __async_persistence__ = "commit"

    @classmethod
    def title(cls) -> str:
        """Заголовок вопроса."""
        return fake.sentence(nb_words=6).rstrip(".")

    @classmethod
    def description(cls) -> Optional[str]:
        """Описание вопроса (70% вопросов имеют)."""
        if fake.boolean(chance_of_getting_true=70):
            return fake.paragraph(nb_sentences=2)
        return None

    @classmethod
    def question_type(cls) -> str:
        """Тип вопроса."""
        return fake.random_element(
            [
                "TEXT",
                "NUMBER",
                "EMAIL",
                "PHONE",
                "DATE",
                "SINGLE_CHOICE",
                "MULTIPLE_CHOICE",
                "BOOLEAN",
                "SCALE",
                "MATRIX",
                "FILE_UPLOAD",
            ]
        )

    @classmethod
    def is_required(cls) -> bool:
        """75% вопросов обязательны."""
        return fake.boolean(chance_of_getting_true=75)

    @classmethod
    def order(cls) -> int:
        """Порядок вопроса."""
        return fake.random_int(min=1, max=20)

    # Данные вопроса зависят от типа
    @classmethod
    def question_data(cls) -> PostGenerated[Optional[Dict[str, Any]]]:
        """Данные вопроса в зависимости от типа."""

        def generate_question_data(
            name: str, values: Dict[str, Any]
        ) -> Optional[Dict[str, Any]]:
            question_type = values.get("question_type", "TEXT")

            if question_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
                options = [fake.word() for _ in range(fake.random_int(min=2, max=6))]
                return {
                    "options": options,
                    "allow_other": fake.boolean(chance_of_getting_true=30),
                }
            elif question_type == "SCALE":
                return {
                    "min_value": 1,
                    "max_value": fake.random_int(min=5, max=10),
                    "step": 1,
                    "min_label": "Плохо",
                    "max_label": "Отлично",
                }
            elif question_type == "MATRIX":
                rows = [fake.word() for _ in range(fake.random_int(min=2, max=4))]
                columns = [fake.word() for _ in range(fake.random_int(min=2, max=5))]
                return {"rows": rows, "columns": columns}
            elif question_type == "FILE_UPLOAD":
                return {
                    "allowed_types": ["image/jpeg", "image/png", "application/pdf"],
                    "max_size_mb": fake.random_int(min=1, max=10),
                }

            return None

        return PostGenerated(generate_question_data)

    # Привязка к опросу обязательна
    survey_id = Require()


@register_fixture(name="question_model")
class TextQuestionModelFactory(QuestionModelFactory):
    """Фабрика для текстовых вопросов."""

    question_type = "TEXT"

    @classmethod
    def title(cls) -> str:
        """Заголовок текстового вопроса."""
        return fake.sentence(nb_words=8).rstrip(".") + "?"


class ChoiceQuestionModelFactory(QuestionModelFactory):
    """Фабрика для вопросов с выбором."""

    @classmethod
    def question_type(cls) -> str:
        """Тип выбора."""
        return fake.random_element(["SINGLE_CHOICE", "MULTIPLE_CHOICE"])

    @classmethod
    def question_data(cls) -> Dict[str, Any]:
        """Данные для вопросов с выбором."""
        options = [fake.word() for _ in range(fake.random_int(min=3, max=6))]
        return {
            "options": options,
            "allow_other": fake.boolean(chance_of_getting_true=40),
        }


class ResponseModelFactory(BaseFactory[Response]):
    """
    Фабрика для создания ответов пользователей.

    Генерирует ответы в соответствии с типом вопроса.
    """

    __model__ = Response
    __async_persistence__ = "commit"

    # Идентификаторы сессии
    @classmethod
    def user_session_id(cls) -> str:
        """Уникальный ID сессии пользователя."""
        return f"session_{uuid.uuid4().hex[:16]}"

    # Ответ зависит от типа вопроса
    @classmethod
    def answer(cls) -> Dict[str, Any]:
        """Базовый ответ."""
        return {"text": fake.sentence(), "timestamp": datetime.utcnow().isoformat()}

    # Временные поля
    created_at = Use(
        lambda: datetime.utcnow()
        - timedelta(
            minutes=fake.random_int(min=0, max=1440)  # В последние 24 часа
        )
    )

    # Привязки обязательны
    question_id = Require()
    # user_id опционален (для анонимных ответов)


@register_fixture(name="response_model")
class TextResponseModelFactory(ResponseModelFactory):
    """Фабрика для текстовых ответов."""

    @classmethod
    def answer(cls) -> Dict[str, Any]:
        """Текстовый ответ."""
        return {
            "text": fake.paragraph(nb_sentences=2),
            "word_count": fake.random_int(min=5, max=100),
        }


class ChoiceResponseModelFactory(ResponseModelFactory):
    """Фабрика для ответов с выбором."""

    @classmethod
    def answer(cls) -> Dict[str, Any]:
        """Ответ с выбором опций."""
        return {
            "selected_options": [0, 2],  # Индексы выбранных опций
            "other_text": fake.sentence()
            if fake.boolean(chance_of_getting_true=20)
            else None,
        }


class ScaleResponseModelFactory(ResponseModelFactory):
    """Фабрика для ответов со шкалой."""

    @classmethod
    def answer(cls) -> Dict[str, Any]:
        """Ответ по шкале."""
        return {
            "value": fake.random_int(min=1, max=10),
            "confidence": fake.random_int(min=1, max=5),
        }
