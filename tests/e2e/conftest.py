"""
E2E TESTS CONFTEST.PY - КОНФИГУРАЦИЯ ДЛЯ END-TO-END ТЕСТОВ
===========================================================

Этот файл содержит fixture для e2e тестов:
- Полная интеграция всех компонентов системы
- Реальная БД, но изолированная от production
- Минимальные моки (только критически важные внешние API)
- Тестирование полных пользовательских сценариев

ПРИНЦИПЫ E2E ТЕСТИРОВАНИЯ:
- Тестируют систему целиком от UI до БД
- Имитируют реальное поведение пользователей
- Самые медленные но наиболее ценные тесты (< 10s на тест)
- Высокая стоимость поддержки, поэтому фокус на критичных flows

SYNC vs ASYNC в E2E тестах:
E2E тесты используют ASYNC потому что:
1. Тестируют полные async request-response cycles
2. Включают реальные HTTP calls и database operations
3. Могут включать параллельные операции (multiple users)
4. Context7 идеально подходит для complex e2e scenarios
"""

import asyncio
import os
from typing import Optional

import httpx
import pytest


@pytest.fixture
def base_url() -> str:
    """Получение базового URL для тестов."""
    return os.environ.get("API_URL", "http://localhost:8000")


@pytest.fixture
def telegram_token() -> str:
    """Получение тестового токена Telegram бота."""
    return os.environ.get("TEST_TELEGRAM_TOKEN", "test_token")


@pytest.fixture(scope="session")
def event_loop():
    """Создание глобального event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class BaseApiClient:
    """Базовый API клиент для тестирования."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _headers(self, token: Optional[str] = None) -> dict[str, str]:
        """Получение заголовков с опциональной аутентификацией."""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers


@pytest.fixture
async def api_client(base_url):
    """Фикстура для создания базового API клиента."""
    async with BaseApiClient(base_url) as client:
        yield client


@pytest.fixture
def api_token() -> Optional[str]:
    """Получение токена API для авторизованных запросов."""
    return os.environ.get("API_TOKEN")


@pytest.fixture
def admin_token() -> Optional[str]:
    """Получение админского токена API для авторизованных запросов."""
    return os.environ.get("ADMIN_API_TOKEN")
