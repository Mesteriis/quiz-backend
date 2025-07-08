"""
Фабрики для создания тестовых респондентов.

Этот модуль содержит фабрики для создания различных типов респондентов
с использованием factory_boy и Faker.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import hashlib
import uuid

import factory
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.respondent import Respondent
from models.user import User

# Создаем глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])


class RespondentFactory(factory.Factory):
    """Базовая фабрика для создания респондентов."""

    class Meta:
        model = Respondent

    # Основные поля
    user_id = None  # По умолчанию анонимный
    session_id = factory.LazyFunction(
        lambda: hashlib.sha256(f"{uuid.uuid4()}".encode()).hexdigest()[:32]
    )
    browser_fingerprint = factory.LazyFunction(
        lambda: hashlib.md5(f"{fake.user_agent()}|{fake.ipv4()}".encode()).hexdigest()
    )
    is_anonymous = True

    # Технические данные
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    browser_info = factory.LazyAttribute(
        lambda obj: {
            "user_agent": obj.user_agent,
            "language": fake.locale(),
            "encoding": "gzip, deflate",
        }
    )
    device_info = factory.LazyAttribute(
        lambda obj: {
            "type": fake.random_element(["desktop", "mobile", "tablet"]),
            "user_agent": obj.user_agent,
        }
    )
    geo_info = factory.LazyAttribute(
        lambda obj: {
            "ip": obj.ip_address,
            "country": fake.country_code(),
            "city": fake.city(),
        }
    )

    # Дополнительные данные
    referrer_info = factory.LazyAttribute(
        lambda obj: {
            "url": fake.url(),
            "source": "referrer",
        }
    )
    entry_point = "web"

    # Telegram данные (None для обычных респондентов)
    telegram_data = None

    # Анонимные данные
    anonymous_name = factory.Faker("name")
    anonymous_email = factory.Faker("email")

    # Временные метки
    first_seen_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=7))
    )
    created_at = factory.LazyAttribute(lambda obj: obj.first_seen_at)
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
    last_activity_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(minutes=fake.random_int(min=1, max=60))
    )


class AuthenticatedRespondentFactory(RespondentFactory):
    """Фабрика для создания авторизованных респондентов."""

    user_id = factory.SubFactory("tests.factories.user_factory.UserFactory")
    is_anonymous = False
    anonymous_name = None
    anonymous_email = None


class AnonymousRespondentFactory(RespondentFactory):
    """Фабрика для создания анонимных респондентов."""

    user_id = None
    is_anonymous = True
    anonymous_name = factory.Faker("name")
    anonymous_email = factory.Faker("email")


class TelegramRespondentFactory(RespondentFactory):
    """Фабрика для создания респондентов из Telegram."""

    entry_point = "telegram_webapp"
    telegram_data = factory.LazyAttribute(
        lambda obj: {
            "id": fake.random_int(min=100000000, max=999999999),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "username": fake.user_name(),
            "language_code": "ru",
        }
    )


class TelegramAuthenticatedRespondentFactory(AuthenticatedRespondentFactory):
    """Фабрика для создания авторизованных респондентов из Telegram."""

    entry_point = "telegram_webapp"
    telegram_data = factory.LazyAttribute(
        lambda obj: {
            "id": fake.random_int(min=100000000, max=999999999),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "username": fake.user_name(),
            "language_code": "ru",
        }
    )


class TelegramAnonymousRespondentFactory(AnonymousRespondentFactory):
    """Фабрика для создания анонимных респондентов из Telegram."""

    entry_point = "telegram_webapp"
    telegram_data = factory.LazyAttribute(
        lambda obj: {
            "id": fake.random_int(min=100000000, max=999999999),
            "first_name": fake.first_name(),
            "username": fake.user_name(),
            "language_code": "ru",
        }
    )


class MobileRespondentFactory(RespondentFactory):
    """Фабрика для создания мобильных респондентов."""

    device_info = factory.LazyAttribute(
        lambda obj: {
            "type": "mobile",
            "user_agent": obj.user_agent,
            "os": fake.random_element(["iOS", "Android"]),
        }
    )
    user_agent = factory.Faker("user_agent", platforms=["mobile"])


class LocationEnabledRespondentFactory(RespondentFactory):
    """Фабрика для создания респондентов с данными о местоположении."""

    geo_info = factory.LazyAttribute(
        lambda obj: {
            "ip": obj.ip_address,
            "country": fake.country_code(),
            "city": fake.city(),
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
        }
    )
    precise_location = factory.LazyAttribute(
        lambda obj: {
            "latitude": obj.geo_info["latitude"],
            "longitude": obj.geo_info["longitude"],
            "accuracy": fake.random_int(min=5, max=100),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


class ActiveRespondentFactory(RespondentFactory):
    """Фабрика для создания активных респондентов."""

    last_activity_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(minutes=fake.random_int(min=1, max=30))
    )


class InactiveRespondentFactory(RespondentFactory):
    """Фабрика для создания неактивных респондентов."""

    last_activity_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=7, max=30))
    )


def create_respondent_for_user(user: User, **kwargs) -> Respondent:
    """
    Создает респондента для конкретного пользователя.

    Args:
        user: Пользователь для которого создается респондент
        **kwargs: Дополнительные параметры респондента

    Returns:
        Respondent: Созданный респондент
    """
    return AuthenticatedRespondentFactory(user_id=user.id, **kwargs)


def create_anonymous_respondent_with_fingerprint(
    browser_fingerprint: str, **kwargs
) -> Respondent:
    """
    Создает анонимного респондента с конкретным отпечатком браузера.

    Args:
        browser_fingerprint: Отпечаток браузера
        **kwargs: Дополнительные параметры

    Returns:
        Respondent: Созданный анонимный респондент
    """
    return AnonymousRespondentFactory(browser_fingerprint=browser_fingerprint, **kwargs)


def create_telegram_respondent(
    telegram_id: int, user: User = None, **kwargs
) -> Respondent:
    """
    Создает респондента из Telegram.

    Args:
        telegram_id: ID пользователя в Telegram
        user: Пользователь (если авторизован)
        **kwargs: Дополнительные параметры

    Returns:
        Respondent: Созданный Telegram респондент
    """
    telegram_data = {
        "id": telegram_id,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "username": fake.user_name(),
        "language_code": "ru",
    }

    if user:
        return TelegramAuthenticatedRespondentFactory(
            user_id=user.id, telegram_data=telegram_data, **kwargs
        )
    else:
        return TelegramAnonymousRespondentFactory(telegram_data=telegram_data, **kwargs)


def create_respondents_batch(
    count: int = 10, respondent_type: str = "mixed"
) -> list[Respondent]:
    """
    Создает батч респондентов.

    Args:
        count: Количество респондентов
        respondent_type: Тип респондентов (mixed, anonymous, authenticated, telegram)

    Returns:
        list[Respondent]: Список созданных респондентов
    """
    respondents = []

    for i in range(count):
        if respondent_type == "mixed":
            if i % 4 == 0:
                respondent = TelegramRespondentFactory()
            elif i % 3 == 0:
                respondent = AuthenticatedRespondentFactory()
            else:
                respondent = AnonymousRespondentFactory()
        elif respondent_type == "anonymous":
            respondent = AnonymousRespondentFactory()
        elif respondent_type == "authenticated":
            respondent = AuthenticatedRespondentFactory()
        elif respondent_type == "telegram":
            respondent = TelegramRespondentFactory()
        else:
            respondent = RespondentFactory()

        respondents.append(respondent)

    return respondents
