"""
Конфигурация и фикстуры для тестов домена users.

Этот модуль содержит общие фикстуры для тестирования:
- Профилей пользователей
- Пользовательских данных (fingerprinting, геолокация)
- Различных типов устройств и браузеров
- Telegram интеграции
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import uuid4

from tests.factories import (
    UserFactory,
    ProfileFactory,
    UserDataFactory,
    CompleteProfileFactory,
    MinimalProfileFactory,
    TelegramProfileFactory,
)


@pytest.fixture
async def basic_user(async_session):
    """Базовый пользователь без профиля."""
    user = UserFactory()
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def verified_user(async_session):
    """Верифицированный пользователь."""
    user = UserFactory(is_verified=True, is_active=True)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(async_session):
    """Администратор."""
    user = UserFactory(is_admin=True, is_verified=True, is_active=True)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def user_with_complete_profile(async_session):
    """Пользователь с полным профилем."""
    user = UserFactory()
    profile = CompleteProfileFactory(user=user)

    async_session.add(user)
    async_session.add(profile)
    await async_session.commit()
    await async_session.refresh(user)
    await async_session.refresh(profile)

    return user, profile


@pytest.fixture
async def user_with_minimal_profile(async_session):
    """Пользователь с минимальным профилем."""
    user = UserFactory()
    profile = MinimalProfileFactory(user=user)

    async_session.add(user)
    async_session.add(profile)
    await async_session.commit()
    await async_session.refresh(user)
    await async_session.refresh(profile)

    return user, profile


@pytest.fixture
async def user_with_telegram_profile(async_session):
    """Пользователь с Telegram профилем."""
    user = UserFactory()
    profile = TelegramProfileFactory(user=user)

    async_session.add(user)
    async_session.add(profile)
    await async_session.commit()
    await async_session.refresh(user)
    await async_session.refresh(profile)

    return user, profile


@pytest.fixture
async def user_with_private_profile(async_session):
    """Пользователь с приватным профилем."""
    user = UserFactory()
    profile = ProfileFactory(
        user=user,
        is_public=False,
        show_email=False,
        show_phone=False,
        show_location=False,
        show_birth_date=False,
    )

    async_session.add(user)
    async_session.add(profile)
    await async_session.commit()
    await async_session.refresh(user)
    await async_session.refresh(profile)

    return user, profile


@pytest.fixture
async def multiple_users_with_profiles(async_session):
    """Несколько пользователей с разными профилями."""
    users_and_profiles = []

    for i in range(5):
        user = UserFactory()
        if i % 2 == 0:
            profile = CompleteProfileFactory(user=user)
        else:
            profile = MinimalProfileFactory(user=user)

        users_and_profiles.append((user, profile))
        async_session.add(user)
        async_session.add(profile)

    await async_session.commit()

    for user, profile in users_and_profiles:
        await async_session.refresh(user)
        await async_session.refresh(profile)

    return users_and_profiles


@pytest.fixture
def desktop_user_data() -> Dict[str, Any]:
    """Данные для desktop устройства."""
    return {
        "session_id": f"desktop_{uuid4().hex[:8]}",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "fingerprint": f"desktop_fp_{uuid4().hex[:12]}",
        "geolocation": {
            "latitude": 55.7558,
            "longitude": 37.6173,
            "accuracy": 10.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "device_info": {
            "platform": "desktop",
            "screen_width": 1920,
            "screen_height": 1080,
            "color_depth": 24,
            "pixel_ratio": 1.0,
            "touch_support": False,
            "max_touch_points": 0,
            "orientation": "landscape",
        },
        "browser_info": {
            "language": "en-US",
            "languages": ["en-US", "en"],
            "timezone": "America/New_York",
            "timezone_offset": 300,
            "screen_resolution": "1920x1080",
            "cookie_enabled": True,
            "do_not_track": False,
        },
        "network_info": {
            "connection_type": "ethernet",
            "effective_type": "4g",
            "downlink": 10.0,
            "rtt": 50,
        },
    }


@pytest.fixture
def mobile_user_data() -> Dict[str, Any]:
    """Данные для mobile устройства."""
    return {
        "session_id": f"mobile_{uuid4().hex[:8]}",
        "ip_address": "192.168.1.50",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "fingerprint": f"mobile_fp_{uuid4().hex[:12]}",
        "geolocation": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 5.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "device_info": {
            "platform": "mobile",
            "screen_width": 390,
            "screen_height": 844,
            "color_depth": 24,
            "pixel_ratio": 3.0,
            "touch_support": True,
            "max_touch_points": 5,
            "orientation": "portrait",
        },
        "browser_info": {
            "language": "en-US",
            "timezone": "America/New_York",
            "timezone_offset": 300,
            "screen_resolution": "390x844",
            "cookie_enabled": True,
        },
        "network_info": {
            "connection_type": "cellular",
            "effective_type": "4g",
            "downlink": 2.5,
            "rtt": 100,
        },
    }


@pytest.fixture
def tablet_user_data() -> Dict[str, Any]:
    """Данные для tablet устройства."""
    return {
        "session_id": f"tablet_{uuid4().hex[:8]}",
        "ip_address": "172.16.0.1",
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "fingerprint": f"tablet_fp_{uuid4().hex[:12]}",
        "geolocation": {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "accuracy": 15.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "device_info": {
            "platform": "tablet",
            "screen_width": 1024,
            "screen_height": 768,
            "color_depth": 24,
            "pixel_ratio": 2.0,
            "touch_support": True,
            "max_touch_points": 10,
            "orientation": "landscape",
        },
        "browser_info": {
            "language": "fr-FR",
            "timezone": "Europe/Paris",
            "timezone_offset": -60,
            "screen_resolution": "1024x768",
            "cookie_enabled": True,
        },
        "network_info": {
            "connection_type": "wifi",
            "effective_type": "4g",
            "downlink": 8.0,
            "rtt": 40,
        },
    }


@pytest.fixture
def telegram_user_data() -> Dict[str, Any]:
    """Данные для Telegram пользователя."""
    return {
        "session_id": f"telegram_{uuid4().hex[:8]}",
        "ip_address": "10.0.0.1",
        "user_agent": "TelegramBot/1.0",
        "fingerprint": f"telegram_fp_{uuid4().hex[:12]}",
        "device_info": {"platform": "telegram"},
        "browser_info": {"language": "ru"},
        "tg_id": 123456789,
        "telegram_data": {
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "en",
            "is_bot": False,
            "is_premium": True,
            "added_to_attachment_menu": False,
            "allows_write_to_pm": True,
            "photo_url": "https://t.me/i/userpic/320/test_user.jpg",
        },
    }


@pytest.fixture
async def sample_user_data(async_session, desktop_user_data):
    """Готовая запись пользовательских данных в БД."""
    user_data = UserDataFactory(**desktop_user_data)
    async_session.add(user_data)
    await async_session.commit()
    await async_session.refresh(user_data)
    return user_data


@pytest.fixture
async def multiple_user_data_records(async_session):
    """Несколько записей пользовательских данных."""
    records = []

    for i in range(5):
        data = {
            "session_id": f"session_{i}_{uuid4().hex[:8]}",
            "ip_address": f"192.168.1.{i + 100}",
            "user_agent": f"Test Agent {i}/1.0",
            "fingerprint": f"fp_{i}_{uuid4().hex[:8]}",
            "device_info": {"platform": f"platform_{i}"},
            "browser_info": {"language": "en"},
        }

        if i % 2 == 0:
            data["tg_id"] = 123456789 + i
            data["telegram_data"] = {
                "username": f"user_{i}",
                "first_name": f"User{i}",
                "language_code": "en",
            }

        user_data = UserDataFactory(**data)
        records.append(user_data)
        async_session.add(user_data)

    await async_session.commit()

    for record in records:
        await async_session.refresh(record)

    return records


@pytest.fixture
def profile_update_data() -> Dict[str, Any]:
    """Данные для обновления профиля."""
    return {
        "first_name": "Updated",
        "last_name": "User",
        "bio": "Updated bio with new information",
        "phone": "+9876543210",
        "website": "https://updated-website.com",
        "location": "Updated Location",
        "social_links": {"twitter": "updated_user", "linkedin": "updated-user"},
        "interests": ["updated", "interests"],
        "languages": ["en", "fr"],
        "is_public": True,
    }


@pytest.fixture
def invalid_profile_data() -> Dict[str, Any]:
    """Невалидные данные профиля для негативных тестов."""
    return {
        "first_name": "",  # пустое имя
        "phone": "invalid-phone",  # неправильный формат
        "website": "not-a-url",  # неправильный URL
        "birth_date": "invalid-date",  # неправильная дата
        "social_links": "not-a-dict",  # неправильный тип
        "interests": "not-a-list",  # неправильный тип
        "languages": ["invalid-lang-code-too-long"],  # слишком длинный код языка
    }


@pytest.fixture
def invalid_user_data() -> Dict[str, Any]:
    """Невалидные пользовательские данные для негативных тестов."""
    return {
        "session_id": "",  # пустой session_id
        "ip_address": "invalid-ip",  # неправильный IP
        "user_agent": "",  # пустой user agent
        "fingerprint": "",  # пустой fingerprint
        "geolocation": {"invalid": "data"},  # неправильная структура
        "device_info": "not-a-dict",  # неправильный тип
        "browser_info": "not-a-dict",  # неправильный тип
        "tg_id": "not-a-number",  # неправильный тип
        "telegram_data": "not-a-dict",  # неправильный тип
    }


@pytest.fixture
def large_profile_data() -> Dict[str, Any]:
    """Данные профиля с большими значениями для граничных тестов."""
    return {
        "first_name": "A" * 100,  # максимальная длина имени
        "last_name": "B" * 100,  # максимальная длина фамилии
        "bio": "C" * 1000,  # максимальная длина био
        "phone": "+1234567890123456789",  # длинный номер телефона
        "website": "https://" + "a" * 240 + ".com",  # длинный URL
        "location": "D" * 200,  # максимальная длина локации
        "interests": ["interest" + str(i) for i in range(50)],  # много интересов
        "languages": ["la" + str(i).zfill(2) for i in range(20)],  # много языков
        "social_links": {
            f"platform{i}": f"user{i}" for i in range(20)
        },  # много соцсетей
    }


@pytest.fixture
def auth_headers(verified_user):
    """Заголовки аутентификации для тестов."""
    return {"Authorization": f"Bearer {verified_user.token}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    """Заголовки аутентификации администратора."""
    return {"Authorization": f"Bearer {admin_user.token}"}


@pytest.fixture
async def cleanup_profiles(async_session):
    """Очистка профилей после тестов."""
    yield
    # Логика очистки будет добавлена при необходимости
    pass


@pytest.fixture
async def cleanup_user_data(async_session):
    """Очистка пользовательских данных после тестов."""
    yield
    # Логика очистки будет добавлена при необходимости
    pass
