"""
Pydantic фабрики для API схем пользователей.

Генерируют данные для:
- Регистрации пользователей (UserCreate)
- Обновления профиля (UserUpdate)
- Аутентификации (UserLogin, TelegramAuth)
- API ответов (UserResponse)

Все фабрики используют LazyAttribute для избежания дублирования данных.
"""

import uuid
from typing import Optional, Dict, Any

from polyfactory.factories import BaseFactory
from polyfactory.fields import Use, PostGenerated, Require
from polyfactory.pytest_plugin import register_fixture
from faker import Faker

from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserLogin,
    TelegramAuth,
    UserResponse,
    UserProfile,
)

# Глобальный faker
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


class UserCreateDataFactory(BaseFactory[UserCreate]):
    """
    Фабрика для данных регистрации пользователей.

    Генерирует валидные данные для создания новых пользователей
    через API endpoint регистрации.
    """

    __model__ = UserCreate

    @classmethod
    def username(cls) -> str:
        """Уникальный username для регистрации."""
        return f"new_user_{uuid.uuid4().hex[:8]}_{fake.random_int(min=1000, max=9999)}"

    @classmethod
    def email(cls) -> str:
        """Уникальный email для регистрации."""
        unique_part = uuid.uuid4().hex[:8]
        domain = fake.domain_name()
        return f"newuser_{unique_part}@{domain}"

    @classmethod
    def password(cls) -> str:
        """Сложный пароль для регистрации."""
        # Генерируем пароль, соответствующий требованиям безопасности
        base = fake.password(
            length=12, special_chars=True, digits=True, upper_case=True, lower_case=True
        )
        return f"{base}1!"  # Гарантируем наличие цифры и спецсимвола

    # Персональные данные
    first_name = Use(fake.first_name)
    last_name = Use(fake.last_name)

    @classmethod
    def bio(cls) -> Optional[str]:
        """Bio присутствует у 50% пользователей при регистрации."""
        return (
            fake.text(max_nb_chars=150)
            if fake.boolean(chance_of_getting_true=50)
            else None
        )

    # Опциональные поля
    language = Use(lambda: fake.random_element(["en", "ru", "es", "fr"]))
    timezone = Use(fake.timezone)


@register_fixture(name="user_create_data")
class ValidUserCreateDataFactory(UserCreateDataFactory):
    """Фабрика для валидных данных регистрации."""

    @classmethod
    def password(cls) -> str:
        """Гарантированно валидный пароль."""
        return "ValidPass123!"

    @classmethod
    def email(cls) -> str:
        """Валидный email с проверенным доменом."""
        unique_part = uuid.uuid4().hex[:6]
        return f"valid_{unique_part}@example.com"


class UserUpdateDataFactory(BaseFactory[UserUpdate]):
    """
    Фабрика для данных обновления профиля пользователя.

    Генерирует данные для PATCH/PUT запросов к профилю пользователя.
    Все поля опциональны в соответствии с UserUpdate схемой.
    """

    __model__ = UserUpdate

    # Все поля опциональны для обновления
    @classmethod
    def first_name(cls) -> Optional[str]:
        """Новое имя (50% случаев)."""
        return fake.first_name() if fake.boolean(chance_of_getting_true=50) else None

    @classmethod
    def last_name(cls) -> Optional[str]:
        """Новая фамилия (50% случаев)."""
        return fake.last_name() if fake.boolean(chance_of_getting_true=50) else None

    @classmethod
    def bio(cls) -> Optional[str]:
        """Новое bio (30% случаев)."""
        return (
            fake.text(max_nb_chars=200)
            if fake.boolean(chance_of_getting_true=30)
            else None
        )

    @classmethod
    def language(cls) -> Optional[str]:
        """Новый язык (20% случаев)."""
        return (
            fake.random_element(["en", "ru", "es", "fr", "de"])
            if fake.boolean(chance_of_getting_true=20)
            else None
        )

    @classmethod
    def timezone(cls) -> Optional[str]:
        """Новая временная зона (20% случаев)."""
        return fake.timezone() if fake.boolean(chance_of_getting_true=20) else None


class UserLoginDataFactory(BaseFactory[UserLogin]):
    """
    Фабрика для данных аутентификации пользователей.

    Генерирует данные для POST /auth/login запросов.
    """

    __model__ = UserLogin

    @classmethod
    def username(cls) -> str:
        """Username существующего пользователя."""
        # В реальных тестах это будет заменено на данные созданного пользователя
        return f"existing_user_{fake.random_int(min=1000, max=9999)}"

    @classmethod
    def password(cls) -> str:
        """Пароль для аутентификации."""
        return "TestPassword123!"


@register_fixture(name="user_login_data")
class ValidUserLoginDataFactory(UserLoginDataFactory):
    """Фабрика для валидных данных входа."""

    username = "testuser"
    password = "ValidPass123!"


class TelegramAuthDataFactory(BaseFactory[TelegramAuth]):
    """
    Фабрика для данных Telegram аутентификации.

    Генерирует данные для POST /auth/telegram запросов,
    имитируя данные от Telegram Bot API.
    """

    __model__ = TelegramAuth

    @classmethod
    def telegram_id(cls) -> int:
        """Уникальный Telegram ID."""
        base = fake.random_int(min=100000000, max=999999999)
        return base + int(uuid.uuid4().hex[:6], 16) % 100000000

    @classmethod
    def username(cls) -> Optional[str]:
        """Telegram username (80% пользователей имеют)."""
        if fake.boolean(chance_of_getting_true=80):
            return f"tguser_{uuid.uuid4().hex[:8]}"
        return None

    first_name = Use(fake.first_name)

    @classmethod
    def last_name(cls) -> Optional[str]:
        """Фамилия (70% пользователей имеют)."""
        return fake.last_name() if fake.boolean(chance_of_getting_true=70) else None

    @classmethod
    def photo_url(cls) -> Optional[str]:
        """URL фото профиля (60% пользователей имеют)."""
        if fake.boolean(chance_of_getting_true=60):
            photo_id = uuid.uuid4().hex[:12]
            return f"https://t.me/i/userpic/320/{photo_id}.jpg"
        return None

    @classmethod
    def auth_date(cls) -> int:
        """Timestamp аутентификации."""
        return int(fake.unix_time())

    @classmethod
    def hash(cls) -> str:
        """Telegram auth hash."""
        return uuid.uuid4().hex


@register_fixture(name="telegram_auth_data")
class ValidTelegramAuthDataFactory(TelegramAuthDataFactory):
    """Фабрика для валидных Telegram данных."""

    telegram_id = 123456789
    username = "test_telegram_user"
    first_name = "Test"
    last_name = "User"


class UserResponseDataFactory(BaseFactory[UserResponse]):
    """
    Фабрика для данных ответов API пользователей.

    Генерирует данные для проверки структуры ответов
    от endpoints, возвращающих информацию о пользователе.
    """

    __model__ = UserResponse

    @classmethod
    def id(cls) -> int:
        """ID пользователя."""
        return fake.random_int(min=1, max=999999)

    @classmethod
    def username(cls) -> Optional[str]:
        """Username пользователя."""
        return (
            f"user_{uuid.uuid4().hex[:8]}"
            if fake.boolean(chance_of_getting_true=70)
            else None
        )

    @classmethod
    def email(cls) -> Optional[str]:
        """Email пользователя."""
        if fake.boolean(chance_of_getting_true=70):
            unique_part = uuid.uuid4().hex[:6]
            return f"user_{unique_part}@example.com"
        return None

    first_name = Use(fake.first_name)
    last_name = Use(fake.last_name)

    @classmethod
    def display_name(cls) -> PostGenerated[str]:
        """Display name на основе имени и фамилии."""

        def generate_display_name(name: str, values: Dict[str, Any]) -> str:
            first = values.get("first_name", "User")
            last = values.get("last_name", "")
            return f"{first} {last}".strip()

        return PostGenerated(generate_display_name)

    is_active = Use(lambda: fake.boolean(chance_of_getting_true=85))
    is_verified = Use(lambda: fake.boolean(chance_of_getting_true=60))
    is_admin = Use(lambda: fake.boolean(chance_of_getting_true=5))

    # Опциональные поля
    @classmethod
    def bio(cls) -> Optional[str]:
        """Bio пользователя."""
        return (
            fake.text(max_nb_chars=200)
            if fake.boolean(chance_of_getting_true=40)
            else None
        )

    @classmethod
    def telegram_id(cls) -> Optional[int]:
        """Telegram ID если есть."""
        if fake.boolean(chance_of_getting_true=60):
            return fake.random_int(min=100000000, max=999999999)
        return None

    @classmethod
    def telegram_username(cls) -> Optional[str]:
        """Telegram username если есть."""
        return (
            f"tg_{uuid.uuid4().hex[:6]}"
            if fake.boolean(chance_of_getting_true=50)
            else None
        )

    language = Use(lambda: fake.random_element(["en", "ru", "es", "fr"]))
    timezone = Use(fake.timezone)

    # Временные поля
    created_at = Use(fake.date_time)
    updated_at = Use(fake.date_time)
    last_login = Use(
        lambda: fake.date_time() if fake.boolean(chance_of_getting_true=80) else None
    )


class UserProfileDataFactory(BaseFactory[UserProfile]):
    """
    Фабрика для расширенных данных профиля пользователя.

    Используется для тестирования endpoints профиля
    с дополнительной информацией.
    """

    __model__ = UserProfile

    @classmethod
    def id(cls) -> int:
        """ID пользователя."""
        return fake.random_int(min=1, max=999999)

    @classmethod
    def username(cls) -> Optional[str]:
        """Username пользователя."""
        return f"profile_user_{uuid.uuid4().hex[:6]}"

    first_name = Use(fake.first_name)
    last_name = Use(fake.last_name)

    @classmethod
    def bio(cls) -> Optional[str]:
        """Развернутое bio для профиля."""
        return (
            fake.paragraph(nb_sentences=3)
            if fake.boolean(chance_of_getting_true=70)
            else None
        )

    # Статистика профиля
    @classmethod
    def surveys_created(cls) -> int:
        """Количество созданных опросов."""
        return fake.random_int(min=0, max=50)

    @classmethod
    def surveys_completed(cls) -> int:
        """Количество пройденных опросов."""
        return fake.random_int(min=0, max=200)

    @classmethod
    def total_responses(cls) -> int:
        """Общее количество ответов."""
        return fake.random_int(min=0, max=1000)

    # Дополнительные поля
    language = Use(lambda: fake.random_element(["en", "ru", "es", "fr"]))
    timezone = Use(fake.timezone)
    is_verified = Use(lambda: fake.boolean(chance_of_getting_true=75))

    created_at = Use(fake.date_time)
    last_login = Use(fake.date_time)


# Специализированные фабрики для различных сценариев тестирования


class PartialUserUpdateDataFactory(UserUpdateDataFactory):
    """Фабрика для частичного обновления профиля."""

    # Обновляем только имя и bio
    first_name = Use(fake.first_name)
    bio = Use(lambda: fake.text(max_nb_chars=100))

    # Остальные поля остаются None
    last_name = None
    language = None
    timezone = None


class AdminUserResponseDataFactory(UserResponseDataFactory):
    """Фабрика для ответов с данными админа."""

    # Админы всегда активны и верифицированы
    is_admin = True
    is_active = True
    is_verified = True

    @classmethod
    def username(cls) -> str:
        """Админский username."""
        return f"admin_{uuid.uuid4().hex[:6]}"

    @classmethod
    def email(cls) -> str:
        """Админский email."""
        unique_part = uuid.uuid4().hex[:6]
        return f"admin_{unique_part}@admin.example.com"


class TelegramUserResponseDataFactory(UserResponseDataFactory):
    """Фабрика для ответов с Telegram пользователями."""

    # Telegram пользователи могут не иметь username/email
    username = None
    email = None

    # Но всегда имеют Telegram данные
    @classmethod
    def telegram_id(cls) -> int:
        """Telegram ID обязателен."""
        return fake.random_int(min=100000000, max=999999999)

    @classmethod
    def telegram_username(cls) -> str:
        """Telegram username обязателен."""
        return f"tguser_{uuid.uuid4().hex[:8]}"
