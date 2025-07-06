"""
Фабрики для создания тестовых пользователей.

Этот модуль содержит фабрики для создания различных типов пользователей
с использованием factory_boy и Faker.
"""

from datetime import datetime, timedelta
from pathlib import Path

# Локальные импорты
import sys

import factory
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.user import User

# Создаем глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])


class UserFactory(factory.Factory):
    """Базовая фабрика для создания пользователей."""

    class Meta:
        model = User

    # Основные поля
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")

    # Telegram данные
    telegram_id = factory.Sequence(lambda n: 1000000 + n)
    telegram_username = factory.LazyAttribute(lambda obj: f"tg_{obj.username}")
    telegram_first_name = factory.Faker("first_name")
    telegram_last_name = factory.Faker("last_name")
    telegram_photo_url = factory.LazyAttribute(
        lambda obj: f"https://t.me/i/userpic/320/{obj.telegram_username}.jpg"
    )

    # Персональные данные
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    display_name = factory.LazyAttribute(
        lambda obj: f"{obj.first_name} {obj.last_name}"
    )
    bio = factory.Faker("text", max_nb_chars=200)

    # Статус
    is_active = True
    is_admin = False
    is_verified = factory.Faker("boolean", chance_of_getting_true=60)

    # Временные метки
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=365))
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
    last_login = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=fake.random_int(min=0, max=30))
    )

    # Настройки
    language = factory.Faker("random_element", elements=("en", "ru", "es", "fr"))
    timezone = factory.Faker("timezone")


class AdminUserFactory(UserFactory):
    """Фабрика для создания пользователей-администраторов."""

    username = factory.Sequence(lambda n: f"admin{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@admin.com")

    is_admin = True
    is_active = True
    is_verified = True

    # Админы обычно создаются раньше
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=30, max=365))
    )

    # Более частые логины для админов
    last_login = factory.LazyAttribute(
        lambda obj: datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=7))
    )


class TelegramUserFactory(UserFactory):
    """Фабрика для создания пользователей из Telegram."""

    # Нет username и email - только Telegram данные
    username = None
    email = None

    # Обязательные Telegram поля
    telegram_id = factory.Sequence(lambda n: 500000000 + n)
    telegram_username = factory.Sequence(lambda n: f"tguser{n}")
    telegram_first_name = factory.Faker("first_name")
    telegram_last_name = factory.Faker("last_name")
    telegram_photo_url = factory.LazyAttribute(
        lambda obj: f"https://t.me/i/userpic/320/{obj.telegram_username}.jpg"
    )

    # Используем Telegram данные для display_name
    display_name = factory.LazyAttribute(
        lambda obj: f"{obj.telegram_first_name} {obj.telegram_last_name}"
    )

    # Telegram пользователи часто менее верифицированы
    is_verified = factory.Faker("boolean", chance_of_getting_true=30)


class InactiveUserFactory(UserFactory):
    """Фабрика для создания неактивных пользователей."""

    is_active = False
    is_verified = False

    # Неактивные пользователи давно не логинились
    last_login = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=fake.random_int(min=1, max=5))
    )


class VerifiedUserFactory(UserFactory):
    """Фабрика для создания верифицированных пользователей."""

    is_verified = True
    is_active = True

    # Верифицированные пользователи более активны
    last_login = factory.LazyAttribute(
        lambda obj: datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=7))
    )


class UserWithBioFactory(UserFactory):
    """Фабрика для создания пользователей с подробной биографией."""

    bio = factory.Faker("paragraph", nb_sentences=3)

    # Больше персональных данных
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    display_name = factory.LazyAttribute(
        lambda obj: f"{obj.first_name} {obj.last_name}"
    )

    # Обычно верифицированы
    is_verified = True


def create_user_with_responses(db_session, response_count: int = 5) -> User:
    """
    Создает пользователя с указанным количеством ответов.

    Args:
        db_session: Сессия базы данных
        response_count: Количество ответов для создания

    Returns:
        User: Созданный пользователь
    """
    user = UserFactory()

    # Здесь можно добавить создание ответов
    # Будет реализовано после создания ResponseFactory

    return user


def create_test_users_batch(db_session, count: int = 10) -> list[User]:
    """
    Создает батч тестовых пользователей.

    Args:
        db_session: Сессия базы данных
        count: Количество пользователей для создания

    Returns:
        list[User]: Список созданных пользователей
    """
    users = []

    for i in range(count):
        if i == 0:
            # Первый пользователь - админ
            user = AdminUserFactory()
        elif i % 5 == 0:
            # Каждый 5-й пользователь - Telegram
            user = TelegramUserFactory()
        elif i % 7 == 0:
            # Каждый 7-й пользователь - неактивен
            user = InactiveUserFactory()
        else:
            # Остальные - обычные пользователи
            user = UserFactory()

        users.append(user)

    return users
