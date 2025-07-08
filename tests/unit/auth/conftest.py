"""
Конфигурация тестов для домена аутентификации.

Содержит фикстуры и настройки специфичные для тестирования
системы аутентификации, включая JWT, регистрацию, авторизацию,
Telegram интеграцию и управление профилями пользователей.
"""

import pytest
from typing import Dict, Any, Optional, Callable
from unittest.mock import AsyncMock, MagicMock

# Импорт фабрик для auth домена
from tests.factories import (
    UserFactory,
    AdminUserFactory,
    TelegramUserFactory,
    InactiveUserFactory,
    VerifiedUserFactory,
    UserWithBioFactory,
    ProfileFactory,
    CompleteProfileFactory,
    TelegramProfileFactory,
    UserDataFactory,
    TelegramUserDataFactory,
    create_user_with_responses,
    create_test_users_batch,
    create_profile_for_user,
    create_telegram_synced_profile,
)

# Импорт сервисов для мокирования
from services.jwt_service import jwt_service
from services.user_service import user_service
from services.telegram_service import telegram_service


@pytest.fixture
def auth_user_factory():
    """Фабрика для создания пользователей в auth тестах."""
    return UserFactory


@pytest.fixture
def admin_user_factory():
    """Фабрика для создания админов в auth тестах."""
    return AdminUserFactory


@pytest.fixture
def telegram_user_factory():
    """Фабрика для создания Telegram пользователей в auth тестах."""
    return TelegramUserFactory


@pytest.fixture
def inactive_user_factory():
    """Фабрика для создания неактивных пользователей в auth тестах."""
    return InactiveUserFactory


@pytest.fixture
async def regular_user(auth_user_factory, db_session):
    """Фикстура для создания обычного пользователя."""
    user = await auth_user_factory.create()
    await db_session.commit()
    return user


@pytest.fixture
async def admin_user(admin_user_factory, db_session):
    """Фикстура для создания админа."""
    user = await admin_user_factory.create()
    await db_session.commit()
    return user


@pytest.fixture
async def telegram_user(telegram_user_factory, db_session):
    """Фикстура для создания Telegram пользователя."""
    user = await telegram_user_factory.create()
    await db_session.commit()
    return user


@pytest.fixture
async def inactive_user(inactive_user_factory, db_session):
    """Фикстура для создания неактивного пользователя."""
    user = await inactive_user_factory.create()
    await db_session.commit()
    return user


@pytest.fixture
async def user_with_profile(auth_user_factory, db_session):
    """Фикстура для создания пользователя с профилем."""
    user = await auth_user_factory.create()
    profile = await create_profile_for_user(user)
    await db_session.commit()
    return user, profile


@pytest.fixture
async def telegram_user_with_profile(telegram_user_factory, db_session):
    """Фикстура для создания Telegram пользователя с синхронизированным профилем."""
    user = await telegram_user_factory.create()
    profile = await create_telegram_synced_profile(user)
    await db_session.commit()
    return user, profile


@pytest.fixture
def auth_headers_factory():
    """Фабрика для создания заголовков аутентификации."""

    def _create_auth_headers(user_id: int) -> Dict[str, str]:
        access_token = jwt_service.create_access_token(user_id)
        return {"Authorization": f"Bearer {access_token}"}

    return _create_auth_headers


@pytest.fixture
def invalid_auth_headers():
    """Фикстура для создания невалидных заголовков аутентификации."""
    return {"Authorization": "Bearer invalid_token"}


@pytest.fixture
def expired_auth_headers():
    """Фикстура для создания истекших заголовков аутентификации."""
    # Создаем токен с истекшим временем
    expired_token = jwt_service.create_access_token(999, expires_delta=-3600)
    return {"Authorization": f"Bearer {expired_token}"}


@pytest.fixture
def malformed_auth_headers():
    """Фикстура для создания некорректно сформированных заголовков."""
    return {"Authorization": "InvalidBearerToken"}


@pytest.fixture
def mock_jwt_service():
    """Мок для JWT сервиса."""
    mock = MagicMock()
    mock.create_access_token = MagicMock(return_value="mock_access_token")
    mock.create_refresh_token = MagicMock(return_value="mock_refresh_token")
    mock.decode_token = MagicMock(return_value={"user_id": 1, "exp": 9999999999})
    mock.verify_token = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_user_service():
    """Мок для User сервиса."""
    mock = AsyncMock()
    mock.create_user = AsyncMock()
    mock.get_user_by_id = AsyncMock()
    mock.get_user_by_username = AsyncMock()
    mock.get_user_by_email = AsyncMock()
    mock.get_user_by_telegram_id = AsyncMock()
    mock.update_user = AsyncMock()
    mock.verify_user = AsyncMock()
    mock.get_users_list = AsyncMock()
    return mock


@pytest.fixture
def mock_telegram_service():
    """Мок для Telegram сервиса."""
    mock = AsyncMock()
    mock.verify_telegram_data = AsyncMock(return_value=True)
    mock.get_user_info = AsyncMock()
    mock.send_message = AsyncMock()
    mock.create_webhook = AsyncMock()
    return mock


# Фикстуры для positive тестов
@pytest.fixture
def valid_registration_data():
    """Валидные данные для регистрации."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "language": "en",
        "timezone": "UTC",
    }


@pytest.fixture
def valid_login_data():
    """Валидные данные для входа."""
    return {"identifier": "testuser"}


@pytest.fixture
def valid_telegram_auth_data():
    """Валидные данные для Telegram аутентификации."""
    return {
        "telegram_id": 123456789,
        "telegram_username": "testuser",
        "telegram_first_name": "Test",
        "telegram_last_name": "User",
        "auth_date": 1234567890,
        "hash": "valid_hash",
    }


@pytest.fixture
def valid_profile_update_data():
    """Валидные данные для обновления профиля."""
    return {
        "first_name": "Updated",
        "last_name": "Name",
        "bio": "Updated bio",
        "location": "Updated location",
        "language": "ru",
        "timezone": "Europe/Moscow",
    }


# Фикстуры для negative тестов
@pytest.fixture
def invalid_registration_data():
    """Невалидные данные для регистрации."""
    return {
        "username": "",  # Пустой username
        "email": "invalid-email",  # Невалидный email
        "first_name": "",
        "last_name": "",
    }


@pytest.fixture
def invalid_login_data():
    """Невалидные данные для входа."""
    return {"identifier": ""}


@pytest.fixture
def invalid_telegram_auth_data():
    """Невалидные данные для Telegram аутентификации."""
    return {
        "telegram_id": "invalid_id",  # Невалидный ID
        "auth_date": "invalid_date",  # Невалидная дата
        "hash": "invalid_hash",
    }


# Фикстуры для edge cases
@pytest.fixture
def edge_case_registration_data():
    """Граничные случаи для регистрации."""
    return {
        "username": "a" * 150,  # Очень длинный username
        "email": "a" * 100 + "@example.com",  # Длинный email
        "first_name": "Имя",  # Unicode символы
        "last_name": "Фамилия",
        "language": "zh-CN",  # Необычный язык
        "timezone": "Pacific/Kiritimati",  # Экзотическая временная зона
    }


@pytest.fixture
def edge_case_telegram_data():
    """Граничные случаи для Telegram."""
    return {
        "telegram_id": 2**31 - 1,  # Максимальный возможный ID
        "telegram_username": "a" * 32,  # Максимальная длина username
        "telegram_first_name": "🙂" * 20,  # Эмодзи в имени
        "telegram_last_name": None,  # Отсутствующая фамилия
        "photo_url": "https://example.com/very/long/photo/url/" + "a" * 200,
    }


@pytest.fixture
async def users_batch(db_session):
    """Фикстура для создания пакета пользователей для тестов пагинации."""
    users = await create_test_users_batch(count=25)
    await db_session.commit()
    return users


@pytest.fixture
def concurrent_requests_data():
    """Данные для тестов конкурентных запросов."""
    return [
        {
            "username": f"user_{i}",
            "email": f"user_{i}@example.com",
            "first_name": f"User{i}",
            "last_name": "Test",
        }
        for i in range(10)
    ]


# Параметризованные фикстуры
@pytest.fixture(params=["username", "email", "telegram_id"])
def login_identifier_type(request):
    """Параметризованная фикстура для типов идентификаторов при входе."""
    return request.param


@pytest.fixture(
    params=[
        {"language": "en", "timezone": "UTC"},
        {"language": "ru", "timezone": "Europe/Moscow"},
        {"language": "zh-CN", "timezone": "Asia/Shanghai"},
    ]
)
def localization_params(request):
    """Параметризованная фикстура для тестов локализации."""
    return request.param


@pytest.fixture(params=["regular_user", "admin_user", "telegram_user", "inactive_user"])
def user_type(request):
    """Параметризованная фикстура для разных типов пользователей."""
    return request.param
