from datetime import datetime
import os
from typing import Optional
import uuid

import httpx
import pytest


@pytest.fixture
def base_url() -> str:
    """Получение базового URL для тестов."""
    return os.environ.get("API_URL", "http://localhost:8000")


class TestApiClient:
    """Клиент для тестирования API приложения Quiz."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
        self.auth_token: Optional[str] = None
        self.admin_token: Optional[str] = None
        self.test_user_id: Optional[int] = None
        self.test_admin_id: Optional[int] = None
        self.test_survey_id: Optional[int] = None
        self.test_question_ids: list[int] = []
        self.user_session_id: str = str(uuid.uuid4())

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
    """Фикстура для создания тестового API клиента."""
    async with TestApiClient(base_url) as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(api_client):
    """Тест проверки работоспособности API."""
    response = await api_client.client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()


@pytest.mark.asyncio
async def test_user_registration_and_login(api_client):
    """Тест регистрации и входа пользователя."""
    # Регистрация пользователя
    timestamp = datetime.now().strftime("%H%M%S")
    username = f"testuser_{timestamp}"
    email = f"test_{timestamp}@example.com"

    user_data = {
        "username": username,
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "display_name": "Test User",
    }

    response = await api_client.client.post(
        "/api/auth/register", json=user_data, headers=api_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert "user" in result
    assert result["user"]["username"] == username

    api_client.auth_token = result["access_token"]
    api_client.test_user_id = result["user"]["id"]

    # Проверка входа
    login_data = {"identifier": username}
    response = await api_client.client.post(
        "/api/auth/login", json=login_data, headers=api_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["user"]["id"] == api_client.test_user_id


@pytest.mark.asyncio
async def test_telegram_auth(api_client):
    """Тест аутентификации через Telegram."""
    telegram_id = int(datetime.now().strftime("%H%M%S"))
    telegram_data = {
        "telegram_id": telegram_id,
        "telegram_username": f"testuser_tg_{telegram_id}",
        "telegram_first_name": "Telegram",
        "telegram_last_name": "User",
    }

    response = await api_client.client.post(
        "/api/auth/telegram", json=telegram_data, headers=api_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert "user" in result
    assert result["user"]["telegram_id"] == telegram_id


@pytest.mark.asyncio
async def test_user_profile(api_client):
    """Тест получения и обновления профиля пользователя."""
    # Сначала регистрируем пользователя, если нет токена
    if not api_client.auth_token:
        await test_user_registration_and_login(api_client)

    # Получение профиля
    response = await api_client.client.get(
        "/api/auth/me", headers=api_client._headers(api_client.auth_token)
    )

    assert response.status_code == 200
    profile = response.json()
    assert "username" in profile
    assert "email" in profile
    assert profile["id"] == api_client.test_user_id

    # Обновление профиля
    update_data = {"bio": "Test bio for e2e testing", "language": "ru"}

    response = await api_client.client.put(
        "/api/auth/me",
        json=update_data,
        headers=api_client._headers(api_client.auth_token),
    )

    assert response.status_code == 200
    updated_profile = response.json()
    assert updated_profile["bio"] == update_data["bio"]
    assert updated_profile["language"] == update_data["language"]


@pytest.mark.asyncio
async def test_email_validation(api_client):
    """Тест валидации email адреса."""
    email_data = {"email": "test@gmail.com", "check_mx": True, "check_smtp": False}

    response = await api_client.client.post(
        "/api/validation/email", json=email_data, headers=api_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "is_valid" in result
    assert "mx_valid" in result


@pytest.mark.asyncio
async def test_token_verification(api_client):
    """Тест проверки токена."""
    # Сначала регистрируем пользователя, если нет токена
    if not api_client.auth_token:
        await test_user_registration_and_login(api_client)

    verify_data = {"token": api_client.auth_token}

    response = await api_client.client.post(
        "/api/auth/verify-token", json=verify_data, headers=api_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert result["valid"] == True
    assert "user" in result
    assert result["user"]["id"] == api_client.test_user_id


@pytest.mark.asyncio
async def test_active_surveys(api_client):
    """Тест получения активных публичных опросов."""
    response = await api_client.client.get(
        "/api/surveys/active", headers=api_client._headers()
    )

    assert response.status_code == 200
    surveys = response.json()
    assert isinstance(surveys, list)

    # Если есть опросы, сохраняем ID первого для дальнейших тестов
    if surveys:
        api_client.test_survey_id = surveys[0]["id"]


@pytest.mark.asyncio
async def test_get_survey_by_id(api_client):
    """Тест получения опроса по ID."""
    # Сначала получаем список опросов, если ID не сохранен
    if not api_client.test_survey_id:
        await test_active_surveys(api_client)

    # Пропускаем тест, если нет доступных опросов
    if not api_client.test_survey_id:
        pytest.skip("No active surveys available")

    response = await api_client.client.get(
        f"/api/surveys/{api_client.test_survey_id}", headers=api_client._headers()
    )

    assert response.status_code == 200
    survey = response.json()
    assert survey["id"] == api_client.test_survey_id
    assert "title" in survey
    assert "questions" in survey

    # Сохраняем ID вопросов для дальнейших тестов
    if survey["questions"]:
        api_client.test_question_ids = [q["id"] for q in survey["questions"]]


@pytest.mark.asyncio
async def test_get_survey_questions(api_client):
    """Тест получения вопросов опроса."""
    # Сначала получаем опрос, если ID не сохранен
    if not api_client.test_survey_id:
        await test_get_survey_by_id(api_client)

    # Пропускаем тест, если нет доступных опросов
    if not api_client.test_survey_id:
        pytest.skip("No active surveys available")

    response = await api_client.client.get(
        f"/api/surveys/{api_client.test_survey_id}/questions",
        headers=api_client._headers(),
    )

    assert response.status_code == 200
    questions = response.json()
    assert isinstance(questions, list)
    if questions:
        assert "id" in questions[0]
        assert "question_text" in questions[0]
        assert "question_type" in questions[0]


@pytest.mark.asyncio
async def test_create_response(api_client):
    """Тест создания ответа на вопрос."""
    # Пропускаем тест, если нет доступных вопросов
    if not api_client.test_question_ids:
        await test_get_survey_questions(api_client)

    if not api_client.test_question_ids:
        pytest.skip("No questions available")

    question_id = api_client.test_question_ids[0]

    response_data = {
        "question_id": question_id,
        "user_session_id": api_client.user_session_id,
        "answer": {"value": "Тестовый ответ e2e"},
    }

    response = await api_client.client.post(
        "/api/responses/", json=response_data, headers=api_client._headers()
    )

    assert response.status_code in [200, 201, 400]  # 400 если уже есть ответ

    if response.status_code in [200, 201]:
        result = response.json()
        assert result["question_id"] == question_id
        assert result["user_session_id"] == api_client.user_session_id


@pytest.mark.asyncio
async def test_get_survey_progress(api_client):
    """Тест получения прогресса прохождения опроса."""
    # Пропускаем тест, если нет доступных опросов
    if not api_client.test_survey_id:
        await test_get_survey_by_id(api_client)

    if not api_client.test_survey_id:
        pytest.skip("No active surveys available")

    # Предварительно создаем ответ, если не было
    if api_client.test_question_ids and not await _check_response_exists(api_client):
        await test_create_response(api_client)

    response = await api_client.client.get(
        f"/api/responses/survey/{api_client.test_survey_id}/progress/{api_client.user_session_id}",
        headers=api_client._headers(),
    )

    assert response.status_code == 200
    progress = response.json()
    assert "survey_id" in progress
    assert "total_questions" in progress
    assert "answered_questions" in progress
    assert "completion_percentage" in progress
    assert progress["survey_id"] == api_client.test_survey_id


@pytest.mark.asyncio
async def test_user_data_collection(api_client):
    """Тест сбора данных о пользователе."""
    user_data = {
        "session_id": api_client.user_session_id,
        "ip_address": "127.0.0.1",
        "user_agent": "E2E Test Agent",
        "browser_fingerprint": {
            "canvas": "test_canvas_hash",
            "webgl": "test_webgl_hash",
        },
        "device_info": {"screen_width": 1920, "screen_height": 1080, "timezone": "UTC"},
        "location_data": {"latitude": 55.7558, "longitude": 37.6176, "accuracy": 100},
    }

    response = await api_client.client.post(
        "/api/user-data/session", json=user_data, headers=api_client._headers()
    )

    assert response.status_code in [200, 201, 400]  # 400 если сессия уже существует

    if response.status_code in [200, 201]:
        result = response.json()
        assert "id" in result
        assert result["session_id"] == api_client.user_session_id


@pytest.mark.asyncio
async def test_telegram_webhook_health(api_client):
    """Тест проверки работоспособности Telegram webhook."""
    response = await api_client.client.get(
        "/api/telegram/health", headers=api_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "status" in result
    assert result["status"] == "healthy"


@pytest.mark.asyncio
async def test_telegram_bot_status(api_client):
    """Тест получения статуса Telegram бота."""
    response = await api_client.client.get(
        "/api/telegram/status", headers=api_client._headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "status" in result


# Вспомогательные функции
async def _check_response_exists(api_client) -> bool:
    """Проверяет, существует ли уже ответ на вопрос."""
    if not api_client.test_question_ids:
        return False

    question_id = api_client.test_question_ids[0]

    try:
        response = await api_client.client.get(
            f"/api/responses/question/{question_id}", headers=api_client._headers()
        )

        if response.status_code == 200:
            responses = response.json()
            for resp in responses:
                if resp["user_session_id"] == api_client.user_session_id:
                    return True
        return False
    except Exception:
        return False


# Запуск всех тестов
if __name__ == "__main__":
    pytest.main(["--asyncio-mode=auto", "-v"])
