"""
Фабрики для создания тестовых опросов.

Этот модуль содержит фабрики для создания различных типов опросов
с использованием factory_boy и Faker.
"""

import factory
import uuid
from faker import Faker
from datetime import datetime, timedelta

# Локальные импорты
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.survey import Survey

# Создаем глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])


class SurveyFactory(factory.Factory):
    """Базовая фабрика для создания опросов."""

    class Meta:
        model = Survey

    # Основные поля
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=500)

    # Статус
    is_active = True
    is_public = True
    telegram_notifications = True

    # Уникальный токен доступа
    access_token = factory.LazyFunction(lambda: str(uuid.uuid4()))

    # Временные метки
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=90))
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class PublicSurveyFactory(SurveyFactory):
    """Фабрика для создания публичных опросов."""

    is_public = True
    is_active = True

    # Публичные опросы обычно имеют более привлекательные названия
    title = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph", nb_sentences=2)


class PrivateSurveyFactory(SurveyFactory):
    """Фабрика для создания приватных опросов."""

    is_public = False
    is_active = True

    # Приватные опросы имеют более формальные названия
    title = factory.LazyAttribute(
        lambda obj: f"Private Survey: {fake.company()} Research"
    )
    description = factory.Faker("paragraph", nb_sentences=3)


class InactiveSurveyFactory(SurveyFactory):
    """Фабрика для создания неактивных опросов."""

    is_active = False

    # Неактивные опросы созданы давно
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=180, max=365))
    )


class SurveyWithQuestionsFactory(SurveyFactory):
    """Фабрика для создания опросов с вопросами."""

    # Эта фабрика будет расширена после создания QuestionFactory
    pass


class ShortSurveyFactory(SurveyFactory):
    """Фабрика для создания коротких опросов."""

    title = factory.Faker("sentence", nb_words=2)
    description = factory.Faker("sentence", nb_words=8)

    # Короткие опросы обычно более активны
    is_active = True
    is_public = True


class LongSurveyFactory(SurveyFactory):
    """Фабрика для создания подробных опросов."""

    title = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("text", max_nb_chars=1000)

    # Подробные опросы чаще приватные
    is_public = factory.Faker("boolean", chance_of_getting_true=30)


class RecentSurveyFactory(SurveyFactory):
    """Фабрика для создания недавно созданных опросов."""

    # Созданы недавно
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=7))
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)

    # Недавние опросы обычно активны
    is_active = True


class PopularSurveyFactory(SurveyFactory):
    """Фабрика для создания популярных опросов."""

    # Популярные опросы имеют привлекательные названия
    title = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph", nb_sentences=2)

    # Публичные и активные
    is_public = True
    is_active = True
    telegram_notifications = True

    # Созданы некоторое время назад, чтобы набрать популярность
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=7, max=30))
    )


class ResearchSurveyFactory(SurveyFactory):
    """Фабрика для создания исследовательских опросов."""

    title = factory.LazyAttribute(lambda obj: f"Research Study: {fake.bs().title()}")
    description = factory.Faker("paragraph", nb_sentences=4)

    # Исследовательские опросы часто приватные
    is_public = False
    is_active = True
    telegram_notifications = False


class FeedbackSurveyFactory(SurveyFactory):
    """Фабрика для создания опросов обратной связи."""

    title = factory.LazyAttribute(lambda obj: f"Feedback: {fake.company()} Service")
    description = factory.Faker("paragraph", nb_sentences=2)

    # Обратная связь обычно публична
    is_public = True
    is_active = True
    telegram_notifications = True


def create_survey_with_questions(db_session, question_count: int = 5) -> Survey:
    """
    Создает опрос с указанным количеством вопросов.

    Args:
        db_session: Сессия базы данных
        question_count: Количество вопросов для создания

    Returns:
        Survey: Созданный опрос
    """
    survey = SurveyFactory()

    # Здесь можно добавить создание вопросов
    # Будет реализовано после создания QuestionFactory

    return survey


def create_test_surveys_batch(db_session, count: int = 10) -> list[Survey]:
    """
    Создает батч тестовых опросов.

    Args:
        db_session: Сессия базы данных
        count: Количество опросов для создания

    Returns:
        list[Survey]: Список созданных опросов
    """
    surveys = []

    for i in range(count):
        if i % 5 == 0:
            # Каждый 5-й опрос - приватный
            survey = PrivateSurveyFactory()
        elif i % 7 == 0:
            # Каждый 7-й опрос - неактивный
            survey = InactiveSurveyFactory()
        elif i % 3 == 0:
            # Каждый 3-й опрос - популярный
            survey = PopularSurveyFactory()
        else:
            # Остальные - обычные публичные
            survey = PublicSurveyFactory()

        surveys.append(survey)

    return surveys


def create_survey_scenarios():
    """
    Создает различные сценарии опросов для тестирования.

    Returns:
        dict: Словарь с различными типами опросов
    """
    return {
        "public_active": PublicSurveyFactory(),
        "private_active": PrivateSurveyFactory(),
        "public_inactive": InactiveSurveyFactory(is_public=True),
        "private_inactive": InactiveSurveyFactory(is_public=False),
        "recent": RecentSurveyFactory(),
        "popular": PopularSurveyFactory(),
        "research": ResearchSurveyFactory(),
        "feedback": FeedbackSurveyFactory(),
        "short": ShortSurveyFactory(),
        "long": LongSurveyFactory(),
    }
