"""
SQLAlchemy фабрики для моделей пользователей.

Использует Polyfactory для создания моделей User с различными профилями:
- Обычные пользователи
- Администраторы
- Telegram пользователи
- Неактивные пользователи

Все фабрики используют LazyAttribute для избежания коллизий ID.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from polyfactory.fields import Use, PostGenerated, Ignore
from polyfactory.pytest_plugin import register_fixture
from faker import Faker

from models.user import User

# Глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)  # Для предсказуемости в тестах


class UserModelFactory(SQLAlchemyFactory[User]):
    """
    Фабрика для создания базовых пользователей.

    Использует LazyAttribute и PostGenerated для избежания коллизий.
    Все ID и уникальные поля генерируются динамически.
    """

    __model__ = User
    __async_persistence__ = "commit"  # Автоматическая персистентность через commit

    # Уникальные поля с LazyAttribute для избежания коллизий
    @classmethod
    def username(cls) -> str:
        """Генерирует уникальный username."""
        return f"user_{uuid.uuid4().hex[:8]}_{fake.random_int(min=1000, max=9999)}"

    @classmethod
    def email(cls) -> str:
        """Генерирует уникальный email."""
        unique_part = uuid.uuid4().hex[:8]
        return f"user_{unique_part}@{fake.domain_name()}"

    @classmethod
    def telegram_id(cls) -> int:
        """Генерирует уникальный telegram_id."""
        # Используем большой диапазон для избежания коллизий
        base = fake.random_int(min=100000000, max=900000000)
        return base + int(uuid.uuid4().hex[:8], 16) % 1000000

    # Персональные данные
    first_name = Use(fake.first_name)
    last_name = Use(fake.last_name)

    @classmethod
    def display_name(cls) -> str:
        """Генерирует display_name на основе имени и фамилии."""
        return f"{fake.first_name()} {fake.last_name()}"

    # Telegram данные
    @classmethod
    def telegram_username(cls) -> str:
        """Генерирует уникальный telegram username."""
        return f"tg_{uuid.uuid4().hex[:6]}_{fake.random_int(min=100, max=999)}"

    telegram_first_name = Use(fake.first_name)
    telegram_last_name = Use(fake.last_name)

    @classmethod
    def telegram_photo_url(cls) -> str:
        """Генерирует URL фото профиля Telegram."""
        photo_id = uuid.uuid4().hex[:12]
        return f"https://t.me/i/userpic/320/{photo_id}.jpg"

    # Статусы с вероятностным распределением
    @classmethod
    def is_active(cls) -> bool:
        """85% пользователей активны."""
        return fake.boolean(chance_of_getting_true=85)

    @classmethod
    def is_admin(cls) -> bool:
        """5% пользователей - админы."""
        return fake.boolean(chance_of_getting_true=5)

    @classmethod
    def is_verified(cls) -> bool:
        """60% пользователей верифицированы."""
        return fake.boolean(chance_of_getting_true=60)

    # Дополнительные поля
    bio = Use(
        lambda: fake.text(max_nb_chars=200)
        if fake.boolean(chance_of_getting_true=30)
        else None
    )
    language = Use(lambda: fake.random_element(["en", "ru", "es", "fr", "de"]))
    timezone = Use(fake.timezone)

    # Временные метки с реалистичными значениями
    @classmethod
    def created_at(cls) -> datetime:
        """Дата создания в прошлом (до 365 дней)."""
        days_ago = fake.random_int(min=0, max=365)
        return datetime.utcnow() - timedelta(days=days_ago)

    # PostGenerated поля, зависящие от других
    @classmethod
    def updated_at(cls) -> PostGenerated:
        """updated_at после created_at."""

        def generate_updated_at(name: str, values: dict[str, Any]) -> datetime:
            created = values.get("created_at", datetime.utcnow())
            # updated_at между created_at и сейчас
            max_days = (datetime.utcnow() - created).days
            if max_days > 0:
                days_after = fake.random_int(min=0, max=max_days)
                return created + timedelta(days=days_after)
            return created

        return PostGenerated(generate_updated_at)

    @classmethod
    def last_login(cls) -> PostGenerated:
        """last_login после created_at."""

        def generate_last_login(name: str, values: dict[str, Any]) -> datetime:
            created = values.get("created_at", datetime.utcnow())
            # Последний логин в пределах 30 дней от создания
            max_days = min(30, (datetime.utcnow() - created).days)
            if max_days > 0:
                days_after = fake.random_int(min=0, max=max_days)
                return created + timedelta(days=days_after)
            return created

        return PostGenerated(generate_last_login)


@register_fixture(name="user_model")
class AdminUserModelFactory(UserModelFactory):
    """
    Фабрика для создания пользователей-администраторов.

    Наследует от UserModelFactory и переопределяет специфичные поля.
    """

    @classmethod
    def username(cls) -> str:
        """Админский username."""
        return f"admin_{uuid.uuid4().hex[:8]}_{fake.random_int(min=1000, max=9999)}"

    @classmethod
    def email(cls) -> str:
        """Админский email."""
        unique_part = uuid.uuid4().hex[:8]
        return f"admin_{unique_part}@admin.{fake.domain_name()}"

    # Админы всегда активны и верифицированы
    is_admin = True
    is_active = True
    is_verified = True

    # Админы создаются раньше
    @classmethod
    def created_at(cls) -> datetime:
        """Админы создаются 30-365 дней назад."""
        days_ago = fake.random_int(min=30, max=365)
        return datetime.utcnow() - timedelta(days=days_ago)

    # Админы логинятся чаще
    @classmethod
    def last_login(cls) -> PostGenerated:
        """Админы логинятся в последние 7 дней."""

        def generate_admin_last_login(name: str, values: dict[str, Any]) -> datetime:
            # Админы логинились в последние 7 дней
            days_ago = fake.random_int(min=0, max=7)
            return datetime.utcnow() - timedelta(days=days_ago)

        return PostGenerated(generate_admin_last_login)


@register_fixture(name="telegram_user_model")
class TelegramUserModelFactory(UserModelFactory):
    """
    Фабрика для создания пользователей из Telegram.

    Особенности:
    - Нет обычного username/email
    - Обязательные Telegram поля
    - Часто не верифицированы
    """

    # Нет стандартных полей авторизации
    username = None
    email = None

    # Обязательные Telegram поля
    @classmethod
    def telegram_id(cls) -> int:
        """Telegram ID в специальном диапазоне."""
        base = fake.random_int(min=500000000, max=999999999)
        return base + int(uuid.uuid4().hex[:6], 16) % 1000000

    @classmethod
    def telegram_username(cls) -> str:
        """Уникальный Telegram username."""
        return f"tguser_{uuid.uuid4().hex[:8]}"

    # Используем Telegram данные для display_name
    @classmethod
    def display_name(cls) -> PostGenerated:
        """display_name на основе Telegram имени."""

        def generate_display_name(name: str, values: dict[str, Any]) -> str:
            tg_first = values.get("telegram_first_name", "User")
            tg_last = values.get("telegram_last_name", "")
            return f"{tg_first} {tg_last}".strip()

        return PostGenerated(generate_display_name)

    # Telegram пользователи менее верифицированы
    @classmethod
    def is_verified(cls) -> bool:
        """Только 30% Telegram пользователей верифицированы."""
        return fake.boolean(chance_of_getting_true=30)


@register_fixture(name="inactive_user_model")
class InactiveUserModelFactory(UserModelFactory):
    """
    Фабрика для создания неактивных пользователей.

    Используется для тестирования функционала с заблокированными пользователями.
    """

    # Неактивные пользователи
    is_active = False
    is_verified = False
    is_admin = False

    # Давно не логинились
    @classmethod
    def last_login(cls) -> PostGenerated:
        """Неактивные пользователи давно не логинились."""

        def generate_inactive_last_login(name: str, values: dict[str, Any]) -> datetime:
            created = values.get("created_at", datetime.utcnow())
            # Логинились только в первые 5 дней после создания
            days_after = fake.random_int(min=1, max=5)
            return created + timedelta(days=days_after)

        return PostGenerated(generate_inactive_last_login)


class PredictableUserModelFactory(UserModelFactory):
    """
    Фабрика для создания пользователей с предсказуемыми данными.

    Полезна для тестов, требующих детерминированных результатов.
    """

    @classmethod
    def username(cls) -> str:
        """Предсказуемый username с последовательным номером."""
        # Используем счетчик для предсказуемости
        counter = getattr(cls, "_counter", 0)
        cls._counter = counter + 1
        return f"predictable_user_{counter:04d}"

    @classmethod
    def email(cls) -> str:
        """Email на основе username."""
        username = cls.username()
        return f"{username}@predictable.test"

    @classmethod
    def telegram_id(cls) -> int:
        """Детерминированный telegram_id."""
        username = cls.username()
        # Используем hash для детерминированного ID
        return abs(hash(username)) % 1000000000 + 100000000

    # Предсказуемые статусы на основе номера пользователя
    @classmethod
    def is_verified(cls) -> PostGenerated:
        """Четные пользователи верифицированы."""

        def generate_verified_status(name: str, values: dict[str, Any]) -> bool:
            username = values.get("username", "user_0000")
            user_num = int(username.split("_")[-1])
            return user_num % 2 == 0

        return PostGenerated(generate_verified_status)

    @classmethod
    def is_admin(cls) -> PostGenerated:
        """Каждый 10-й пользователь - админ."""

        def generate_admin_status(name: str, values: dict[str, Any]) -> bool:
            username = values.get("username", "user_0000")
            user_num = int(username.split("_")[-1])
            return user_num % 10 == 0

        return PostGenerated(generate_admin_status)

    # Фиксированные значения для предсказуемости
    is_active = True
    language = "en"
    timezone = "UTC"
