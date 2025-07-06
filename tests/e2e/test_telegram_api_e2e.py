import os
import pytest
import httpx
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


@pytest.fixture
def base_url() -> str:
    """Получение базового URL для тестов."""
    return os.environ.get("API_URL", "http://localhost:8000")


@pytest.fixture
def telegram_token() -> str:
    """Получение тестового токена Telegram бота."""
    return os.environ.get("TEST_TELEGRAM_TOKEN", "test_token")


class TestTelegramApiClient:
    """Клиент для тестирования Telegram API интеграции."""

    def __init__(self, base_url: str, telegram_token: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
        self.telegram_token = telegram_token
        self.auth_token: Optional[str] = None
        self.webhook_url: Optional[str] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Получение заголовков с опциональной аутентификацией."""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers


@pytest.fixture
async def telegram_client(base_url, telegram_token):
    """Фикстура для создания Telegram API клиента."""
    async with TestTelegramApiClient(base_url, telegram_token) as client:
        yield client


@pytest.mark.asyncio
async def test_telegram_health(telegram_client):
    """Тест проверки работоспособности Telegram интеграции."""
    response = await telegram_client.client.get(
        "/api/telegram/health",
        headers=telegram_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "status" in result
    assert result["status"] == "healthy"
    assert "service" in result


@pytest.mark.asyncio
async def test_telegram_status(telegram_client):
    """Тест получения статуса Telegram бота."""
    response = await telegram_client.client.get(
        "/api/telegram/status",
        headers=telegram_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "status" in result

    # Если бот инициализирован, проверяем дополнительную информацию
    if result["status"] == "active":
        assert "bot_info" in result
        assert "webhook_info" in result


@pytest.mark.asyncio
async def test_get_webhook_info(telegram_client):
    """Тест получения информации о webhook."""
    response = await telegram_client.client.get(
        "/api/telegram/webhook/info",
        headers=telegram_client._headers()
    )

    # Этот запрос может не сработать, если бот не инициализирован
    if response.status_code == 200:
        result = response.json()
        assert "url" in result

        # Сохраняем текущий URL вебхука для дальнейших тестов
        telegram_client.webhook_url = result["url"]
    elif response.status_code == 503:
        # Бот не инициализирован
        print("Telegram бот не инициализирован")
    elif response.status_code == 401:
        # Недостаточно прав или неверный токен
        print("Недостаточно прав для доступа к информации о вебхуке")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_set_webhook(telegram_client):
    """Тест установки webhook для бота."""
    # Генерируем тестовый URL для вебхука
    test_webhook_url = f"https://example.com/test/webhook/{uuid.uuid4()}"

    webhook_data = {"url": test_webhook_url}

    response = await telegram_client.client.post(
        "/api/telegram/webhook/set",
        json=webhook_data,
        headers=telegram_client._headers()
    )

    # Этот запрос может не сработать, если бот не инициализирован
    if response.status_code == 200:
        result = response.json()
        assert "status" in result
        assert result["status"] == "success"

        # Проверяем, действительно ли webhook был установлен
        info_response = await telegram_client.client.get(
            "/api/telegram/webhook/info",
            headers=telegram_client._headers()
        )

        if info_response.status_code == 200:
            info = info_response.json()
            assert info["url"] == test_webhook_url
    elif response.status_code == 503:
        # Бот не инициализирован
        print("Telegram бот не инициализирован")
    elif response.status_code in [401, 403]:
        # Недостаточно прав или неверный токен
        print("Недостаточно прав для установки вебхука")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_delete_webhook(telegram_client):
    """Тест удаления webhook."""
    # Пропускаем этот тест, если мы до этого не устанавливали вебхук
    # или если previous_webhook_url не пустой (не хотим удалять боевой вебхук)
    if hasattr(telegram_client, "previous_webhook_url") and telegram_client.previous_webhook_url:
        pytest.skip("Skipping to avoid deleting production webhook")

    response = await telegram_client.client.post(
        "/api/telegram/webhook/delete",
        headers=telegram_client._headers()
    )

    # Этот запрос может не сработать, если бот не инициализирован
    if response.status_code == 200:
        result = response.json()
        assert "status" in result
        assert result["status"] == "success"

        # Проверяем, действительно ли webhook был удален
        info_response = await telegram_client.client.get(
            "/api/telegram/webhook/info",
            headers=telegram_client._headers()
        )

        if info_response.status_code == 200:
            info = info_response.json()
            assert info["url"] == "" or not info["url"]
    elif response.status_code == 503:
        # Бот не инициализирован
        print("Telegram бот не инициализирован")
    elif response.status_code in [401, 403]:
        # Недостаточно прав или неверный токен
        print("Недостаточно прав для удаления вебхука")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_telegram_security_stats(telegram_client):
    """Тест получения статистики безопасности Telegram вебхука."""
    response = await telegram_client.client.get(
        "/api/telegram/security/stats",
        headers=telegram_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "middleware_status" in result
    assert "rate_limiting" in result
    assert "ip_whitelisting" in result


@pytest.mark.asyncio
async def test_send_admin_notification(telegram_client):
    """Тест отправки уведомления администратору."""
    notification_data = {
        "message": f"Test admin notification from e2e tests at {datetime.now().isoformat()}"
    }

    response = await telegram_client.client.post(
        "/api/telegram/send-admin-notification",
        json=notification_data,
        headers=telegram_client._headers()
    )

    # Этот запрос может не сработать, если бот не инициализирован
    # или нет настроенного ID админского чата
    if response.status_code == 200:
        result = response.json()
        assert "status" in result
        assert result["status"] == "success"
    elif response.status_code == 503:
        # Бот не инициализирован
        print("Telegram бот не инициализирован")
    elif response.status_code == 500:
        # Возможно, не настроен ID админского чата
        print("Не удалось отправить уведомление администратору")
    elif response.status_code in [401, 403]:
        # Недостаточно прав или неверный токен
        print("Недостаточно прав для отправки уведомления")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_restore_original_webhook(telegram_client):
    """Тест восстановления исходного webhook после тестов."""
    # Пропускаем, если у нас нет сохраненного исходного URL
    if not telegram_client.webhook_url:
        pytest.skip("No original webhook URL to restore")

    webhook_data = {"url": telegram_client.webhook_url}

    response = await telegram_client.client.post(
        "/api/telegram/webhook/set",
        json=webhook_data,
        headers=telegram_client._headers()
    )

    # Этот запрос может не сработать, если бот не инициализирован
    if response.status_code == 200:
        result = response.json()
        assert "status" in result
        assert result["status"] == "success"

        print(f"Восстановлен исходный webhook URL: {telegram_client.webhook_url}")
    elif response.status_code == 503:
        # Бот не инициализирован
        print("Telegram бот не инициализирован")
    elif response.status_code in [401, 403]:
        # Недостаточно прав или неверный токен
        print("Недостаточно прав для установки вебхука")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


# Запуск всех тестов
if __name__ == "__main__":
    pytest.main(["--asyncio-mode=auto", "-v"])
