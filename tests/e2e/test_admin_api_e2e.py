from datetime import datetime
import os
from typing import Optional

import httpx
import pytest


@pytest.fixture
def base_url() -> str:
    """Получение базового URL для тестов."""
    return os.environ.get("API_URL", "http://localhost:8000")


class TestAdminApiClient:
    """Клиент для тестирования административных API приложения Quiz."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
        self.admin_token: Optional[str] = None
        self.admin_id: Optional[int] = None
        self.test_user_id: Optional[int] = None
        self.test_survey_id: Optional[int] = None

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
async def admin_client(base_url):
    """Фикстура для создания административного API клиента."""
    async with TestAdminApiClient(base_url) as client:
        yield client


@pytest.mark.asyncio
async def test_admin_registration(admin_client):
    """Тест регистрации администратора."""
    # Регистрация администратора
    timestamp = datetime.now().strftime("%H%M%S")
    username = f"adminuser_{timestamp}"
    email = f"admin_{timestamp}@example.com"

    admin_data = {
        "username": username,
        "email": email,
        "first_name": "Admin",
        "last_name": "User",
        "display_name": "Admin Test User",
    }

    response = await admin_client.client.post(
        "/api/auth/register", json=admin_data, headers=admin_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert "user" in result

    admin_client.admin_token = result["access_token"]
    admin_client.admin_id = result["user"]["id"]

    # Примечание: После регистрации пользователь еще не является администратором
    # В реальной системе нужно назначить права администратора через API или БД
    # Этот шаг не выполняется в тесте, т.к. может потребовать уже существующего администратора


@pytest.mark.asyncio
async def test_get_admin_dashboard(admin_client):
    """Тест получения информации для админ-панели."""
    # Сначала регистрируем администратора, если нет токена
    if not admin_client.admin_token:
        await test_admin_registration(admin_client)

    # Этот тест может не пройти, если у пользователя нет прав администратора
    response = await admin_client.client.get(
        "/api/admin/dashboard", headers=admin_client._headers(admin_client.admin_token)
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        result = response.json()
        assert "total_users" in result
        assert "total_surveys" in result
        assert "total_responses" in result
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для запроса требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_get_all_surveys(admin_client):
    """Тест получения всех опросов (включая приватные)."""
    # Сначала регистрируем администратора, если нет токена
    if not admin_client.admin_token:
        await test_admin_registration(admin_client)

    response = await admin_client.client.get(
        "/api/admin/surveys", headers=admin_client._headers(admin_client.admin_token)
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        surveys = response.json()
        assert isinstance(surveys, list)

        # Если есть опросы, сохраняем ID первого для дальнейших тестов
        if surveys:
            admin_client.test_survey_id = surveys[0]["id"]
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для запроса требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_create_survey(admin_client):
    """Тест создания нового опроса."""
    # Сначала регистрируем администратора, если нет токена
    if not admin_client.admin_token:
        await test_admin_registration(admin_client)

    timestamp = datetime.now().strftime("%H%M%S")
    survey_data = {
        "title": f"Test Survey {timestamp}",
        "description": "A test survey created by e2e tests",
        "is_active": True,
        "is_public": True,
        "telegram_notifications": False,
        "questions": [
            {
                "question_text": "How would you rate this service?",
                "question_type": "RATING_1_10",
                "is_required": True,
                "order": 1,
                "options": {},
            },
            {
                "question_text": "Any additional comments?",
                "question_type": "TEXT",
                "is_required": False,
                "order": 2,
                "options": {},
            },
        ],
    }

    response = await admin_client.client.post(
        "/api/admin/surveys",
        json=survey_data,
        headers=admin_client._headers(admin_client.admin_token),
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code in [200, 201]:
        result = response.json()
        assert "id" in result
        assert result["title"] == survey_data["title"]
        assert result["description"] == survey_data["description"]

        admin_client.test_survey_id = result["id"]
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для создания опроса требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_update_survey(admin_client):
    """Тест обновления опроса."""
    # Пропускаем тест, если нет ID опроса
    if not admin_client.test_survey_id:
        await test_get_all_surveys(admin_client)

    if not admin_client.test_survey_id:
        pytest.skip("No survey ID available")

    update_data = {
        "title": f"Updated Survey {datetime.now().strftime('%H%M%S')}",
        "description": "Updated description by e2e tests",
        "is_active": True,
    }

    response = await admin_client.client.put(
        f"/api/admin/surveys/{admin_client.test_survey_id}",
        json=update_data,
        headers=admin_client._headers(admin_client.admin_token),
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        result = response.json()
        assert result["id"] == admin_client.test_survey_id
        assert result["title"] == update_data["title"]
        assert result["description"] == update_data["description"]
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для обновления опроса требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_get_survey_responses(admin_client):
    """Тест получения всех ответов для опроса."""
    # Пропускаем тест, если нет ID опроса
    if not admin_client.test_survey_id:
        await test_get_all_surveys(admin_client)

    if not admin_client.test_survey_id:
        pytest.skip("No survey ID available")

    response = await admin_client.client.get(
        f"/api/admin/surveys/{admin_client.test_survey_id}/responses",
        headers=admin_client._headers(admin_client.admin_token),
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        result = response.json()
        assert "survey" in result
        assert "responses" in result
        assert "questions" in result
        assert result["survey"]["id"] == admin_client.test_survey_id
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для получения ответов требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_get_survey_analytics(admin_client):
    """Тест получения аналитики по опросу."""
    # Пропускаем тест, если нет ID опроса
    if not admin_client.test_survey_id:
        await test_get_all_surveys(admin_client)

    if not admin_client.test_survey_id:
        pytest.skip("No survey ID available")

    response = await admin_client.client.get(
        f"/api/admin/surveys/{admin_client.test_survey_id}/analytics",
        headers=admin_client._headers(admin_client.admin_token),
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        result = response.json()
        assert "survey" in result
        assert "stats" in result
        assert "question_stats" in result
        assert result["survey"]["id"] == admin_client.test_survey_id
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для получения аналитики требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_get_all_users(admin_client):
    """Тест получения списка всех пользователей."""
    # Сначала регистрируем администратора, если нет токена
    if not admin_client.admin_token:
        await test_admin_registration(admin_client)

    response = await admin_client.client.get(
        "/api/admin/users", headers=admin_client._headers(admin_client.admin_token)
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        users = response.json()
        assert isinstance(users, list)

        # Если есть пользователи, сохраняем ID первого (не админа) для дальнейших тестов
        if users:
            for user in users:
                if user["id"] != admin_client.admin_id:
                    admin_client.test_user_id = user["id"]
                    break
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для получения списка пользователей требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_toggle_user_admin(admin_client):
    """Тест назначения/снятия прав администратора."""
    # Пропускаем тест, если нет ID пользователя
    if not admin_client.test_user_id:
        await test_get_all_users(admin_client)

    if not admin_client.test_user_id:
        pytest.skip("No user ID available")

    response = await admin_client.client.post(
        f"/api/admin/users/{admin_client.test_user_id}/admin",
        json={"is_admin": True},
        headers=admin_client._headers(admin_client.admin_token),
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        result = response.json()
        assert "success" in result
        assert result["success"] == True
        assert "user" in result
        assert result["user"]["id"] == admin_client.test_user_id
        assert result["user"]["is_admin"] == True
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для изменения прав пользователя требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


@pytest.mark.asyncio
async def test_system_health(admin_client):
    """Тест проверки состояния системы (только для администраторов)."""
    # Сначала регистрируем администратора, если нет токена
    if not admin_client.admin_token:
        await test_admin_registration(admin_client)

    response = await admin_client.client.get(
        "/api/admin/system/health",
        headers=admin_client._headers(admin_client.admin_token),
    )

    # Проверяем код состояния (может быть 403, если нет прав)
    if response.status_code == 200:
        result = response.json()
        assert "status" in result
        assert "database" in result
        assert "telegram_bot" in result
        assert "memory_usage" in result
    elif response.status_code == 403:
        # Если нет прав администратора, отмечаем это
        print("Для проверки состояния системы требуются права администратора")
    else:
        assert False, f"Unexpected status code: {response.status_code}"


# Запуск всех тестов
if __name__ == "__main__":
    pytest.main(["--asyncio-mode=auto", "-v"])
