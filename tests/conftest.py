"""
Глобальные фикстуры для тестирования Quiz App API.

Этот модуль предоставляет базовые фикстуры для всех тестов,
включая настройку БД, аутентификацию и создание тестовых данных.
"""

import asyncio
from collections.abc import AsyncGenerator
import logging
import os
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# Настройка логирования для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Добавляем корневую директорию проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Импорты после добавления пути
from config import Settings
from database import get_async_session
from main import app
from models import Question, Response, Survey, User, UserData
from services.jwt_service import jwt_service

# Конфигурация pytest-asyncio
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестирования."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Настройки для тестирования."""
    # Создаем тестовые настройки
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "TELEGRAM_BOT_TOKEN": "test-bot-token",
        "ENVIRONMENT": "test",
    }

    # Устанавливаем переменные окружения
    for key, value in test_env.items():
        os.environ[key] = value

    return Settings()


@pytest.fixture(scope="session")
async def test_engine(test_settings):
    """Создает тестовый движок БД."""
    # Используем in-memory SQLite для тестов
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Очистка после сессии
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для сессии БД с автоматическим откатом."""
    async with AsyncSession(test_engine) as session:
        # Начинаем транзакцию
        await session.begin()

        yield session

        # Откатываем транзакцию после каждого теста
        await session.rollback()


@pytest.fixture
async def client(test_settings, db_session) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для HTTP клиента с переопределенной БД."""

    # Переопределяем зависимость get_async_session для тестов
    async def override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Очищаем переопределения
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(db_session) -> dict[str, str]:
    """Фикстура для создания заголовков авторизации."""

    async def create_auth_headers(user: User) -> dict[str, str]:
        """Создает заголовки авторизации для пользователя."""
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            is_admin=user.is_admin,
        )
        return {"Authorization": f"Bearer {access_token}"}

    return create_auth_headers


@pytest.fixture
async def admin_headers(db_session, auth_headers) -> dict[str, str]:
    """Фикстура для создания заголовков авторизации админа."""
    # Создаем админа
    admin = User(
        username="admin",
        email="admin@test.com",
        is_admin=True,
        is_active=True,
        telegram_id=123456789,
        first_name="Admin",
        last_name="User",
    )

    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    return await auth_headers(admin)


@pytest.fixture
async def regular_user(db_session) -> User:
    """Фикстура для создания обычного пользователя."""
    user = User(
        username="testuser",
        email="test@example.com",
        is_admin=False,
        is_active=True,
        telegram_id=987654321,
        first_name="Test",
        last_name="User",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def admin_user(db_session) -> User:
    """Фикстура для создания пользователя-администратора."""
    admin = User(
        username="admin",
        email="admin@test.com",
        is_admin=True,
        is_active=True,
        telegram_id=123456789,
        first_name="Admin",
        last_name="User",
    )

    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    return admin


@pytest.fixture
async def sample_survey(db_session) -> Survey:
    """Фикстура для создания примера опроса."""
    survey = Survey(
        title="Test Survey",
        description="This is a test survey",
        is_active=True,
        is_public=True,
        telegram_notifications=True,
    )

    db_session.add(survey)
    await db_session.commit()
    await db_session.refresh(survey)

    return survey


@pytest.fixture
async def sample_question(db_session, sample_survey) -> Question:
    """Фикстура для создания примера вопроса."""
    question = Question(
        survey_id=sample_survey.id,
        title="Test Question",
        description="This is a test question",
        question_type="text",
        is_required=True,
        order=1,
    )

    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    return question


@pytest.fixture
async def sample_response(db_session, sample_question, regular_user) -> Response:
    """Фикстура для создания примера ответа."""
    response = Response(
        question_id=sample_question.id,
        user_id=regular_user.id,
        user_session_id="test-session-123",
        answer={"text": "This is a test answer"},
    )

    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    return response


@pytest.fixture
async def sample_user_data(db_session) -> UserData:
    """Фикстура для создания примера данных пользователя."""
    user_data = UserData(
        session_id="test-session-123",
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0 Test Browser",
        fingerprint="test-fingerprint-123",
        device_info={
            "device_type": "desktop",
            "operating_system": "Linux",
            "browser_name": "Firefox",
            "browser_version": "100.0",
        },
        browser_info={
            "language": "en-US",
            "timezone": "UTC",
            "screen_resolution": "1920x1080",
        },
    )

    db_session.add(user_data)
    await db_session.commit()
    await db_session.refresh(user_data)

    return user_data


# Мокирование внешних сервисов


@pytest.fixture
def mock_telegram_service():
    """Мокирует Telegram сервис."""
    mock = MagicMock()
    mock.send_message = AsyncMock(return_value=True)
    mock.get_webhook_info = AsyncMock(
        return_value={
            "url": "https://api.telegram.org/bot/webhook",
            "has_custom_certificate": False,
            "pending_update_count": 0,
        }
    )
    return mock


@pytest.fixture
def mock_email_service():
    """Мокирует email сервис."""
    mock = MagicMock()
    mock.validate_email = AsyncMock(
        return_value={"is_valid": True, "mx_valid": True, "smtp_valid": True}
    )
    return mock


@pytest.fixture
def mock_redis_service():
    """Мокирует Redis сервис."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_pdf_service():
    """Мокирует PDF сервис."""
    mock = MagicMock()
    mock.generate_report = AsyncMock(return_value=b"PDF content")
    return mock


# Утилитарные фикстуры


@pytest.fixture
def api_client(client):
    """Псевдоним для клиента с удобными методами."""

    class ApiClient:
        def __init__(self, client: AsyncClient):
            self.client = client

        async def get(self, url: str, **kwargs):
            return await self.client.get(url, **kwargs)

        async def post(self, url: str, **kwargs):
            return await self.client.post(url, **kwargs)

        async def put(self, url: str, **kwargs):
            return await self.client.put(url, **kwargs)

        async def delete(self, url: str, **kwargs):
            return await self.client.delete(url, **kwargs)

        async def auth_get(self, url: str, headers: dict[str, str], **kwargs):
            """GET запрос с авторизацией."""
            return await self.client.get(url, headers=headers, **kwargs)

        async def auth_post(self, url: str, headers: dict[str, str], **kwargs):
            """POST запрос с авторизацией."""
            return await self.client.post(url, headers=headers, **kwargs)

        async def auth_put(self, url: str, headers: dict[str, str], **kwargs):
            """PUT запрос с авторизацией."""
            return await self.client.put(url, headers=headers, **kwargs)

        async def auth_delete(self, url: str, headers: dict[str, str], **kwargs):
            """DELETE запрос с авторизацией."""
            return await self.client.delete(url, headers=headers, **kwargs)

    return ApiClient(client)


@pytest.fixture
def assert_response():
    """Фикстура для проверки ответов API."""

    def check_response(
        response, expected_status: int = 200, expected_keys: list = None
    ):
        """Проверяет ответ API."""
        assert (
            response.status_code == expected_status
        ), f"Expected {expected_status}, got {response.status_code}: {response.text}"

        if expected_keys:
            data = response.json()
            for key in expected_keys:
                assert key in data, f"Key '{key}' not found in response: {data}"

        return response.json() if response.status_code < 400 else response.text

    return check_response


@pytest.fixture
def create_test_data():
    """Фикстура для создания тестовых данных."""

    async def create_multiple_users(db_session: AsyncSession, count: int = 3):
        """Создает несколько тестовых пользователей."""
        users = []
        for i in range(count):
            user = User(
                username=f"user{i}",
                email=f"user{i}@test.com",
                is_admin=False,
                is_active=True,
                telegram_id=1000000 + i,
                first_name=f"User{i}",
                last_name="Test",
            )
            db_session.add(user)
            users.append(user)

        await db_session.commit()
        for user in users:
            await db_session.refresh(user)

        return users

    async def create_multiple_surveys(db_session: AsyncSession, count: int = 3):
        """Создает несколько тестовых опросов."""
        surveys = []
        for i in range(count):
            survey = Survey(
                title=f"Survey {i}",
                description=f"Description for survey {i}",
                is_active=True,
                is_public=True,
                telegram_notifications=True,
            )
            db_session.add(survey)
            surveys.append(survey)

        await db_session.commit()
        for survey in surveys:
            await db_session.refresh(survey)

        return surveys

    return {"users": create_multiple_users, "surveys": create_multiple_surveys}


# Настройки для pytest


def pytest_configure(config):
    """Конфигурация pytest."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as authentication related")
    config.addinivalue_line("markers", "admin: mark test as admin functionality")


def pytest_collection_modifyitems(config, items):
    """Модифицирует сбор тестов."""
    for item in items:
        # Добавляем маркер async для всех async тестов
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Добавляем маркер slow для тестов с "slow" в названии
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)
