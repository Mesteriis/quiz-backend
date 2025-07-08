"""
Позитивные тесты для создания пользовательских данных.

Этот модуль содержит все успешные сценарии создания user data:
- Создание с полными данными fingerprinting
- Создание с геолокацией
- Создание с Telegram данными
- Создание с browser/device информацией
- Обновление существующих данных
"""

import pytest
from httpx import AsyncClient
from datetime import datetime

from tests.factories import UserDataFactory


class TestUserDataCreationPositive:
    """Позитивные тесты создания пользовательских данных."""

    async def test_create_user_data_full(self, api_client: AsyncClient, async_session):
        """Тест создания полных пользовательских данных."""
        # Arrange
        user_data = {
            "session_id": "session_12345678",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "fingerprint": "fp_abc123def456ghi789",
            "geolocation": {
                "latitude": 55.7558,
                "longitude": 37.6173,
                "accuracy": 10.0,
                "altitude": 150.0,
                "altitude_accuracy": 5.0,
                "heading": 90.0,
                "speed": 0.0,
                "timestamp": "2024-01-15T12:30:00Z",
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
                "languages": ["en-US", "en", "ru"],
                "timezone": "Europe/Moscow",
                "timezone_offset": -180,
                "screen_resolution": "1920x1080",
                "available_resolution": "1920x1040",
                "cookie_enabled": True,
                "do_not_track": False,
                "java_enabled": False,
                "webgl_vendor": "Google Inc.",
                "webgl_renderer": "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
            },
            "network_info": {
                "connection_type": "wifi",
                "effective_type": "4g",
                "downlink": 10.0,
                "rtt": 50,
            },
            "tg_id": 123456789,
            "telegram_data": {
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "language_code": "en",
                "is_bot": False,
                "is_premium": True,
                "added_to_attachment_menu": False,
                "allows_write_to_pm": True,
                "photo_url": "https://t.me/i/userpic/320/testuser.jpg",
            },
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == user_data["session_id"]
        assert data["ip_address"] == user_data["ip_address"]
        assert data["user_agent"] == user_data["user_agent"]
        assert data["fingerprint"] == user_data["fingerprint"]
        assert data["geolocation"] == user_data["geolocation"]
        assert data["device_info"] == user_data["device_info"]
        assert data["browser_info"] == user_data["browser_info"]
        assert data["network_info"] == user_data["network_info"]
        assert data["tg_id"] == user_data["tg_id"]
        assert data["telegram_data"] == user_data["telegram_data"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_user_data_minimal(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания минимальных пользовательских данных."""
        # Arrange
        user_data = {
            "session_id": "minimal_session",
            "ip_address": "127.0.0.1",
            "user_agent": "Test Agent/1.0",
            "fingerprint": "minimal_fp",
            "device_info": {"platform": "test"},
            "browser_info": {"language": "en"},
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == user_data["session_id"]
        assert data["ip_address"] == user_data["ip_address"]
        assert data["user_agent"] == user_data["user_agent"]
        assert data["fingerprint"] == user_data["fingerprint"]
        assert data["device_info"] == user_data["device_info"]
        assert data["browser_info"] == user_data["browser_info"]
        # Опциональные поля должны быть None
        assert data["geolocation"] is None
        assert data["network_info"] is None
        assert data["tg_id"] is None
        assert data["telegram_data"] is None

    async def test_create_user_data_mobile_device(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания данных для мобильного устройства."""
        # Arrange
        user_data = {
            "session_id": "mobile_session",
            "ip_address": "192.168.1.50",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "fingerprint": "mobile_fp_xyz789",
            "geolocation": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "accuracy": 5.0,
                "timestamp": "2024-01-15T12:30:00Z",
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
                "do_not_track": False,
            },
            "network_info": {
                "connection_type": "cellular",
                "effective_type": "4g",
                "downlink": 2.5,
                "rtt": 100,
            },
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["device_info"]["platform"] == "mobile"
        assert data["device_info"]["touch_support"] is True
        assert data["device_info"]["max_touch_points"] == 5
        assert data["device_info"]["pixel_ratio"] == 3.0
        assert data["network_info"]["connection_type"] == "cellular"
        assert data["geolocation"]["latitude"] == 40.7128
        assert data["geolocation"]["longitude"] == -74.0060

    async def test_create_user_data_with_telegram(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания данных с Telegram информацией."""
        # Arrange
        user_data = {
            "session_id": "telegram_session",
            "ip_address": "10.0.0.1",
            "user_agent": "TelegramBot/1.0",
            "fingerprint": "telegram_fp",
            "device_info": {"platform": "telegram"},
            "browser_info": {"language": "ru"},
            "tg_id": 987654321,
            "telegram_data": {
                "username": "telegram_user",
                "first_name": "Telegram",
                "last_name": "User",
                "language_code": "ru",
                "is_bot": False,
                "is_premium": False,
                "added_to_attachment_menu": True,
                "allows_write_to_pm": True,
                "photo_url": None,
            },
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["tg_id"] == 987654321
        telegram_data = data["telegram_data"]
        assert telegram_data["username"] == "telegram_user"
        assert telegram_data["first_name"] == "Telegram"
        assert telegram_data["last_name"] == "User"
        assert telegram_data["language_code"] == "ru"
        assert telegram_data["is_bot"] is False
        assert telegram_data["is_premium"] is False
        assert telegram_data["added_to_attachment_menu"] is True
        assert telegram_data["allows_write_to_pm"] is True

    async def test_create_user_data_high_accuracy_geolocation(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания данных с высокоточной геолокацией."""
        # Arrange
        user_data = {
            "session_id": "gps_session",
            "ip_address": "203.0.113.1",
            "user_agent": "GPS Navigator/2.0",
            "fingerprint": "gps_fp",
            "geolocation": {
                "latitude": 51.5074,
                "longitude": -0.1278,
                "accuracy": 1.0,
                "altitude": 35.0,
                "altitude_accuracy": 1.0,
                "heading": 270.5,
                "speed": 15.5,
                "timestamp": "2024-01-15T14:25:30Z",
            },
            "device_info": {"platform": "gps"},
            "browser_info": {"language": "en-GB"},
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        geolocation = data["geolocation"]
        assert geolocation["latitude"] == 51.5074
        assert geolocation["longitude"] == -0.1278
        assert geolocation["accuracy"] == 1.0
        assert geolocation["altitude"] == 35.0
        assert geolocation["altitude_accuracy"] == 1.0
        assert geolocation["heading"] == 270.5
        assert geolocation["speed"] == 15.5
        assert geolocation["timestamp"] == "2024-01-15T14:25:30Z"

    async def test_create_user_data_advanced_browser_fingerprint(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания данных с расширенным browser fingerprinting."""
        # Arrange
        user_data = {
            "session_id": "advanced_session",
            "ip_address": "198.51.100.1",
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "fingerprint": "advanced_fp_complex",
            "device_info": {
                "platform": "linux",
                "screen_width": 2560,
                "screen_height": 1440,
                "color_depth": 24,
                "pixel_ratio": 1.0,
                "touch_support": False,
                "max_touch_points": 0,
                "orientation": "landscape",
            },
            "browser_info": {
                "language": "en-US",
                "languages": ["en-US", "en", "de", "fr"],
                "timezone": "Europe/Berlin",
                "timezone_offset": -60,
                "screen_resolution": "2560x1440",
                "available_resolution": "2560x1400",
                "cookie_enabled": True,
                "do_not_track": True,
                "java_enabled": False,
                "webgl_vendor": "NVIDIA Corporation",
                "webgl_renderer": "NVIDIA GeForce GTX 1080/PCIe/SSE2",
                "canvas_fingerprint": "canvas_hash_123456",
                "audio_fingerprint": "audio_hash_789012",
                "fonts": ["Arial", "Times", "Helvetica", "Georgia", "Verdana"],
                "plugins": ["PDF Viewer", "Chrome PDF Viewer"],
                "local_storage": True,
                "session_storage": True,
                "indexed_db": True,
                "web_rtc": True,
            },
            "network_info": {
                "connection_type": "ethernet",
                "effective_type": "4g",
                "downlink": 50.0,
                "rtt": 20,
            },
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        browser_info = data["browser_info"]
        assert browser_info["canvas_fingerprint"] == "canvas_hash_123456"
        assert browser_info["audio_fingerprint"] == "audio_hash_789012"
        assert browser_info["fonts"] == [
            "Arial",
            "Times",
            "Helvetica",
            "Georgia",
            "Verdana",
        ]
        assert browser_info["plugins"] == ["PDF Viewer", "Chrome PDF Viewer"]
        assert browser_info["local_storage"] is True
        assert browser_info["session_storage"] is True
        assert browser_info["indexed_db"] is True
        assert browser_info["web_rtc"] is True
        assert browser_info["do_not_track"] is True

    async def test_update_existing_user_data(
        self, api_client: AsyncClient, async_session
    ):
        """Тест обновления существующих пользовательских данных."""
        # Arrange - создаем первоначальные данные
        initial_data = {
            "session_id": "update_session",
            "ip_address": "127.0.0.1",
            "user_agent": "Old User Agent",
            "fingerprint": "old_fingerprint",
            "device_info": {"platform": "old"},
            "browser_info": {"language": "en"},
        }

        # Создаем первую запись
        response1 = await api_client.post("/api/user-data/", json=initial_data)
        assert response1.status_code == 200
        original_id = response1.json()["id"]

        # Обновляем данные
        updated_data = {
            "session_id": "update_session",  # тот же session_id
            "ip_address": "192.168.1.1",
            "user_agent": "New User Agent",
            "fingerprint": "new_fingerprint",
            "geolocation": {
                "latitude": 55.7558,
                "longitude": 37.6173,
                "accuracy": 10.0,
                "timestamp": "2024-01-15T15:00:00Z",
            },
            "device_info": {"platform": "updated"},
            "browser_info": {"language": "ru"},
            "tg_id": 123456789,
            "telegram_data": {
                "username": "updated_user",
                "first_name": "Updated",
                "last_name": "User",
            },
        }

        # Act
        response2 = await api_client.post("/api/user-data/", json=updated_data)

        # Assert
        assert response2.status_code == 200
        data = response2.json()

        assert data["id"] == original_id  # тот же ID
        assert data["session_id"] == "update_session"
        assert data["ip_address"] == "192.168.1.1"
        assert data["user_agent"] == "New User Agent"
        assert data["fingerprint"] == "new_fingerprint"
        assert data["geolocation"] is not None
        assert data["geolocation"]["latitude"] == 55.7558
        assert data["device_info"]["platform"] == "updated"
        assert data["browser_info"]["language"] == "ru"
        assert data["tg_id"] == 123456789
        assert data["telegram_data"]["username"] == "updated_user"

    async def test_create_user_data_tablet_device(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания данных для планшетного устройства."""
        # Arrange
        user_data = {
            "session_id": "tablet_session",
            "ip_address": "172.16.0.1",
            "user_agent": "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "fingerprint": "tablet_fp_unique",
            "geolocation": {
                "latitude": 48.8566,
                "longitude": 2.3522,
                "accuracy": 15.0,
                "timestamp": "2024-01-15T16:45:00Z",
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

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["device_info"]["platform"] == "tablet"
        assert data["device_info"]["touch_support"] is True
        assert data["device_info"]["max_touch_points"] == 10
        assert data["device_info"]["pixel_ratio"] == 2.0
        assert data["browser_info"]["language"] == "fr-FR"
        assert data["browser_info"]["timezone"] == "Europe/Paris"

    async def test_create_user_data_unicode_content(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания данных с Unicode контентом."""
        # Arrange
        user_data = {
            "session_id": "unicode_session_测试",
            "ip_address": "203.0.113.50",
            "user_agent": "Mozilla/5.0 (compatible; Unicode Test/1.0; 中文支持)",
            "fingerprint": "unicode_fp_αβγδε",
            "device_info": {"platform": "测试平台"},
            "browser_info": {
                "language": "zh-CN",
                "languages": ["zh-CN", "zh", "en-US", "ja"],
                "timezone": "Asia/Shanghai",
            },
            "tg_id": 111222333,
            "telegram_data": {
                "username": "用户名",
                "first_name": "张",
                "last_name": "三",
                "language_code": "zh-hans",
                "is_bot": False,
            },
        }

        # Act
        response = await api_client.post("/api/user-data/", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == "unicode_session_测试"
        assert "中文支持" in data["user_agent"]
        assert data["fingerprint"] == "unicode_fp_αβγδε"
        assert data["device_info"]["platform"] == "测试平台"
        assert data["browser_info"]["language"] == "zh-CN"
        assert data["telegram_data"]["username"] == "用户名"
        assert data["telegram_data"]["first_name"] == "张"
        assert data["telegram_data"]["last_name"] == "三"
