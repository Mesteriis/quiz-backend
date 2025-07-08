"""
Фабрики для создания тестовых профилей пользователей.

Этот модуль содержит фабрики для создания различных типов профилей
с использованием factory_boy и Faker.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

import factory
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.profile import Profile
from models.user import User

# Создаем глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])


class ProfileFactory(factory.Factory):
    """Базовая фабрика для создания профилей пользователей."""

    class Meta:
        model = Profile

    # Основные поля
    user_id = factory.SubFactory("tests.factories.user_factory.UserFactory")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    bio = factory.Faker("text", max_nb_chars=250)
    profile_picture_url = factory.LazyAttribute(
        lambda obj: f"https://example.com/avatars/{fake.uuid4()}.jpg"
    )
    phone = factory.Faker("phone_number")

    # Временные метки
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=30))
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class CompleteProfileFactory(ProfileFactory):
    """Фабрика для создания полных профилей со всеми данными."""

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    bio = factory.Faker("paragraph", nb_sentences=2)
    profile_picture_url = factory.LazyAttribute(
        lambda obj: f"https://example.com/avatars/complete_{fake.uuid4()}.jpg"
    )
    phone = factory.Faker("phone_number")


class MinimalProfileFactory(ProfileFactory):
    """Фабрика для создания минимальных профилей."""

    first_name = factory.Faker("first_name")
    last_name = None
    bio = None
    profile_picture_url = None
    phone = None


class TelegramProfileFactory(ProfileFactory):
    """Фабрика для создания профилей синхронизированных с Telegram."""

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    bio = factory.Faker("sentence", nb_words=10)
    profile_picture_url = factory.LazyAttribute(
        lambda obj: f"https://t.me/i/userpic/320/{fake.uuid4()}.jpg"
    )
    phone = None  # Telegram не всегда предоставляет телефон


class BusinessProfileFactory(ProfileFactory):
    """Фабрика для создания бизнес-профилей."""

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    bio = factory.LazyAttribute(
        lambda obj: f"{fake.job()} at {fake.company()}. {fake.catch_phrase()}"
    )
    profile_picture_url = factory.LazyAttribute(
        lambda obj: f"https://example.com/business/{fake.uuid4()}.jpg"
    )
    phone = factory.Faker("phone_number")


class InternationalProfileFactory(ProfileFactory):
    """Фабрика для создания международных профилей."""

    first_name = factory.Faker("first_name", locale="en_US")
    last_name = factory.Faker("last_name", locale="en_US")
    bio = factory.Faker("text", max_nb_chars=200, locale="en_US")
    profile_picture_url = factory.LazyAttribute(
        lambda obj: f"https://example.com/international/{fake.uuid4()}.jpg"
    )
    phone = factory.Faker("phone_number", locale="en_US")


class ProfileWithoutPictureFactory(ProfileFactory):
    """Фабрика для создания профилей без фотографии."""

    profile_picture_url = None


def create_profile_for_user(user: User, **kwargs) -> Profile:
    """
    Создает профиль для конкретного пользователя.

    Args:
        user: Пользователь для которого создается профиль
        **kwargs: Дополнительные параметры профиля

    Returns:
        Profile: Созданный профиль
    """
    return ProfileFactory(user_id=user.id, **kwargs)


def create_telegram_synced_profile(user: User, telegram_data: dict) -> Profile:
    """
    Создает профиль синхронизированный с данными Telegram.

    Args:
        user: Пользователь
        telegram_data: Данные из Telegram

    Returns:
        Profile: Профиль с данными из Telegram
    """
    return ProfileFactory(
        user_id=user.id,
        first_name=telegram_data.get("first_name"),
        last_name=telegram_data.get("last_name"),
        profile_picture_url=telegram_data.get("photo_url"),
    )


def create_profiles_batch(
    users: list[User], profile_type: str = "complete"
) -> list[Profile]:
    """
    Создает профили для списка пользователей.

    Args:
        users: Список пользователей
        profile_type: Тип профилей (complete, minimal, telegram, business)

    Returns:
        list[Profile]: Список созданных профилей
    """
    factory_map = {
        "complete": CompleteProfileFactory,
        "minimal": MinimalProfileFactory,
        "telegram": TelegramProfileFactory,
        "business": BusinessProfileFactory,
    }

    factory_class = factory_map.get(profile_type, CompleteProfileFactory)
    profiles = []

    for user in users:
        profile = factory_class(user_id=user.id)
        profiles.append(profile)

    return profiles
