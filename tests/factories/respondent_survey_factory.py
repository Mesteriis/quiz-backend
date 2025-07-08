"""
Фабрики для создания тестовых участий респондентов в опросах.

Этот модуль содержит фабрики для создания различных типов участий
с использованием factory_boy и Faker.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

import factory
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.respondent_survey import RespondentSurvey
from models.respondent import Respondent
from models.survey import Survey

# Создаем глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])


class RespondentSurveyFactory(factory.Factory):
    """Базовая фабрика для создания участий в опросах."""

    class Meta:
        model = RespondentSurvey

    # Основные поля
    respondent_id = factory.SubFactory(
        "tests.factories.respondent_factory.RespondentFactory"
    )
    survey_id = factory.SubFactory("tests.factories.survey_factory.SurveyFactory")

    # Статус участия
    status = "started"
    progress_percentage = factory.Faker("random_int", min=0, max=100)
    questions_answered = factory.Faker("random_int", min=0, max=20)
    last_question_id = None

    # Завершение
    completion_time = None
    final_score = None
    completion_source = "web"
    abandonment_reason = None

    # Дополнительные данные
    context_data = factory.LazyAttribute(
        lambda obj: {
            "source": obj.completion_source,
            "device": fake.random_element(["desktop", "mobile", "tablet"]),
            "browser": fake.random_element(["chrome", "firefox", "safari", "edge"]),
        }
    )

    # Временные метки
    started_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(hours=fake.random_int(min=1, max=24))
    )
    completed_at = None
    updated_at = factory.LazyAttribute(lambda obj: obj.started_at)


class StartedSurveyFactory(RespondentSurveyFactory):
    """Фабрика для создания начатых опросов."""

    status = "started"
    progress_percentage = factory.Faker("random_int", min=1, max=25)
    questions_answered = factory.Faker("random_int", min=1, max=5)


class InProgressSurveyFactory(RespondentSurveyFactory):
    """Фабрика для создания опросов в процессе."""

    status = "in_progress"
    progress_percentage = factory.Faker("random_int", min=26, max=79)
    questions_answered = factory.Faker("random_int", min=5, max=15)
    last_question_id = factory.Faker("random_int", min=1, max=20)


class AlmostCompletedSurveyFactory(RespondentSurveyFactory):
    """Фабрика для создания почти завершенных опросов."""

    status = "almost_completed"
    progress_percentage = factory.Faker("random_int", min=80, max=99)
    questions_answered = factory.Faker("random_int", min=15, max=19)
    last_question_id = factory.Faker("random_int", min=15, max=20)


class CompletedSurveyFactory(RespondentSurveyFactory):
    """Фабрика для создания завершенных опросов."""

    status = "completed"
    progress_percentage = 100
    questions_answered = factory.Faker("random_int", min=15, max=25)
    completion_time = factory.Faker("random_int", min=300, max=3600)  # 5-60 минут
    final_score = factory.Faker("random_int", min=50, max=100)
    completed_at = factory.LazyAttribute(
        lambda obj: obj.started_at + timedelta(seconds=obj.completion_time)
    )


class AbandonedSurveyFactory(RespondentSurveyFactory):
    """Фабрика для создания заброшенных опросов."""

    status = "abandoned"
    progress_percentage = factory.Faker("random_int", min=10, max=70)
    questions_answered = factory.Faker("random_int", min=2, max=10)
    abandonment_reason = factory.Faker(
        "random_element",
        elements=[
            "too_long",
            "technical_issues",
            "not_interested",
            "privacy_concerns",
            "other",
        ],
    )


class QuickCompletedSurveyFactory(CompletedSurveyFactory):
    """Фабрика для создания быстро завершенных опросов."""

    completion_time = factory.Faker("random_int", min=60, max=300)  # 1-5 минут
    final_score = factory.Faker("random_int", min=70, max=100)


class ThoroughCompletedSurveyFactory(CompletedSurveyFactory):
    """Фабрика для создания тщательно пройденных опросов."""

    completion_time = factory.Faker("random_int", min=1200, max=3600)  # 20-60 минут
    final_score = factory.Faker("random_int", min=85, max=100)
    questions_answered = factory.Faker("random_int", min=20, max=30)


class TelegramSurveyFactory(RespondentSurveyFactory):
    """Фабрика для создания опросов из Telegram."""

    completion_source = "telegram_webapp"
    context_data = factory.LazyAttribute(
        lambda obj: {
            "source": "telegram_webapp",
            "platform": "telegram",
            "webapp_version": "6.9",
        }
    )


class MobileSurveyFactory(RespondentSurveyFactory):
    """Фабрика для создания мобильных опросов."""

    completion_source = "mobile_app"
    context_data = factory.LazyAttribute(
        lambda obj: {
            "source": "mobile_app",
            "device": "mobile",
            "os": fake.random_element(["iOS", "Android"]),
            "app_version": "1.2.3",
        }
    )


def create_survey_participation(
    respondent: Respondent, survey: Survey, status: str = "started", **kwargs
) -> RespondentSurvey:
    """
    Создает участие в опросе для конкретного респондента и опроса.

    Args:
        respondent: Респондент
        survey: Опрос
        status: Статус участия
        **kwargs: Дополнительные параметры

    Returns:
        RespondentSurvey: Созданное участие
    """
    factory_map = {
        "started": StartedSurveyFactory,
        "in_progress": InProgressSurveyFactory,
        "almost_completed": AlmostCompletedSurveyFactory,
        "completed": CompletedSurveyFactory,
        "abandoned": AbandonedSurveyFactory,
    }

    factory_class = factory_map.get(status, RespondentSurveyFactory)
    return factory_class(respondent_id=respondent.id, survey_id=survey.id, **kwargs)


def create_survey_journey(
    respondent: Respondent, survey: Survey, journey_type: str = "completion"
) -> list[RespondentSurvey]:
    """
    Создает путешествие респондента по опросу с несколькими этапами.

    Args:
        respondent: Респондент
        survey: Опрос
        journey_type: Тип путешествия (completion, abandonment, partial)

    Returns:
        list[RespondentSurvey]: Список этапов участия
    """
    journey = []
    base_time = datetime.utcnow() - timedelta(hours=2)

    if journey_type == "completion":
        # Полное прохождение
        stages = [
            ("started", 0, 5),
            ("in_progress", 5, 40),
            ("almost_completed", 40, 85),
            ("completed", 85, 100),
        ]
    elif journey_type == "abandonment":
        # Забрасывание на середине
        stages = [
            ("started", 0, 5),
            ("in_progress", 5, 25),
            ("abandoned", 25, 25),
        ]
    else:  # partial
        # Частичное прохождение
        stages = [
            ("started", 0, 5),
            ("in_progress", 5, 60),
        ]

    for i, (status, prev_progress, progress) in enumerate(stages):
        participation_time = base_time + timedelta(minutes=i * 15)

        participation = create_survey_participation(
            respondent=respondent,
            survey=survey,
            status=status,
            progress_percentage=progress,
            questions_answered=progress // 5,  # Примерно 5% за вопрос
            started_at=participation_time,
        )

        journey.append(participation)

    return journey


def create_participations_batch(
    count: int = 10, participation_type: str = "mixed"
) -> list[RespondentSurvey]:
    """
    Создает батч участий в опросах.

    Args:
        count: Количество участий
        participation_type: Тип участий (mixed, completed, abandoned, in_progress)

    Returns:
        list[RespondentSurvey]: Список созданных участий
    """
    participations = []

    for i in range(count):
        if participation_type == "mixed":
            if i % 5 == 0:
                participation = AbandonedSurveyFactory()
            elif i % 3 == 0:
                participation = CompletedSurveyFactory()
            else:
                participation = InProgressSurveyFactory()
        elif participation_type == "completed":
            participation = CompletedSurveyFactory()
        elif participation_type == "abandoned":
            participation = AbandonedSurveyFactory()
        elif participation_type == "in_progress":
            participation = InProgressSurveyFactory()
        else:
            participation = RespondentSurveyFactory()

        participations.append(participation)

    return participations
