"""
КОРНЕВОЙ CONFTEST.PY - СИСТЕМНАЯ ИНФРАСТРУКТУРА ТЕСТИРОВАНИЯ
============================================================

Этот файл содержит ТОЛЬКО инфраструктурные компоненты:
- Системные моки (Redis, Telegram, внешние API)
- Базовые настройки тестирования
- Глобальные fixture для всех типов тестов
- Настройки pytest и async окружения

ВАЖНО: Доменные fixture находятся в соответствующих conftest.py файлах
по доменам (auth, surveys, users и т.д.)

Использует Context7 для управления состоянием тестов.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Отключаем шумные логгеры для чистого вывода тестов
NOISY_LOGGERS = [
    "testcontainers",
    "sqlalchemy",
    "asyncpg",
    "uvloop",
    "asyncio",
    "docker",
    "urllib3",
    "requests",
    "aiosqlite",
    "faker",
]

for logger_name in NOISY_LOGGERS:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

# Добавляем корневую директорию проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Конфигурация pytest-asyncio для Context7
pytest_plugins = ["pytest_asyncio"]


# ============================================================================
# СИСТЕМНЫЕ МОКИ - БЛОКИРУЕМ ВНЕШНИЕ ЗАВИСИМОСТИ
# ============================================================================


class MockRedisService:
    """
    Полнофункциональный in-memory mock для Redis.

    Поддерживает:
    - Базовые операции (get, set, delete)
    - TTL и expire
    - Pub/Sub (для уведомлений)
    - Health checks
    - Async context manager
    """

    def __init__(self):
        self.storage: Dict[str, Any] = {}
        self.expires: Dict[str, datetime] = {}
        self.connected = False
        self.subscribers: Dict[str, list] = {}
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def initialize(self):
        """Инициализация mock Redis сервиса."""
        logger.info("Initializing Mock Redis Service")
        self.connected = True
        return True

    async def disconnect(self):
        """Отключение mock Redis сервиса."""
        logger.info("Disconnecting Mock Redis Service")
        self.connected = False
        self.storage.clear()
        self.expires.clear()
        self.subscribers.clear()

    async def _check_expired(self, key: str) -> bool:
        """Проверка на истечение TTL."""
        if key in self.expires:
            if datetime.utcnow() > self.expires[key]:
                await self.delete(key)
                return True
        return False

    async def get(self, key: str) -> Optional[Any]:
        """Получить значение по ключу."""
        if await self._check_expired(key):
            return None
        return self.storage.get(key)

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Установить значение по ключу."""
        if nx and key in self.storage:
            return False

        async with self._lock:
            self.storage[key] = value
            if ttl:
                self.expires[key] = datetime.utcnow() + timedelta(seconds=ttl)
            elif key in self.expires:
                del self.expires[key]

        return True

    async def delete(self, *keys: str) -> int:
        """Удалить ключи."""
        count = 0
        async with self._lock:
            for key in keys:
                if key in self.storage:
                    del self.storage[key]
                    count += 1
                if key in self.expires:
                    del self.expires[key]
        return count

    async def publish(self, channel: str, message: Any) -> int:
        """Публикация сообщения в канал."""
        subscribers = self.subscribers.get(channel, [])
        for subscriber in subscribers:
            await subscriber(message)
        return len(subscribers)

    async def subscribe(self, channel: str, callback):
        """Подписка на канал."""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)

    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса."""
        return {
            "status": "healthy",
            "message": "Mock Redis is operational",
            "response_time_ms": 0.5,
            "keys_count": len(self.storage),
            "connected": self.connected,
        }


class MockTelegramService:
    """
    Полнофункциональный mock для Telegram Bot API.

    Поддерживает:
    - Отправку сообщений
    - Webhook уведомления
    - Файловые операции
    - Управление ботом
    """

    def __init__(self):
        self.bot_token = "test-bot-token"
        self.sent_messages = []
        self.webhook_url = None
        self.polling_active = False
        self.bot_info = {
            "id": 123456789,
            "is_bot": True,
            "first_name": "Test Bot",
            "username": "test_bot",
            "can_join_groups": True,
            "can_read_all_group_messages": False,
            "supports_inline_queries": False,
        }

    async def initialize(self):
        """Инициализация mock Telegram сервиса."""
        logger.info("Initializing Mock Telegram Service")
        return True

    async def send_message(self, chat_id: int, text: str, **kwargs) -> Dict[str, Any]:
        """Отправка сообщения."""
        message = {
            "message_id": len(self.sent_messages) + 1,
            "from": self.bot_info,
            "chat": {"id": chat_id, "type": "private"},
            "date": int(datetime.utcnow().timestamp()),
            "text": text,
            **kwargs,
        }
        self.sent_messages.append(message)
        return message

    async def set_webhook(self, url: str) -> bool:
        """Установка webhook."""
        self.webhook_url = url
        return True

    async def start_polling(self):
        """Запуск polling."""
        self.polling_active = True
        logger.info("Mock Telegram polling started")

    async def stop_polling(self):
        """Остановка polling."""
        self.polling_active = False
        logger.info("Mock Telegram polling stopped")

    async def get_me(self) -> Dict[str, Any]:
        """Получение информации о боте."""
        return self.bot_info

    def get_sent_messages(self) -> list:
        """Получение всех отправленных сообщений."""
        return self.sent_messages.copy()

    def clear_sent_messages(self):
        """Очистка истории сообщений."""
        self.sent_messages.clear()


class MockExternalServices:
    """
    Centralized container для всех внешних сервисов.

    Управляет жизненным циклом всех mock сервисов
    и предоставляет единый интерфейс для тестов.
    """

    def __init__(self):
        self.redis = MockRedisService()
        self.telegram = MockTelegramService()
        self.initialized = False

    async def initialize(self):
        """Инициализация всех mock сервисов."""
        if not self.initialized:
            await self.redis.initialize()
            await self.telegram.initialize()
            self.initialized = True
            logger.info("All mock services initialized")

    async def cleanup(self):
        """Очистка всех mock сервисов."""
        if self.initialized:
            await self.redis.disconnect()
            await self.telegram.stop_polling()
            self.initialized = False
            logger.info("All mock services cleaned up")

    async def reset(self):
        """Сброс состояния всех сервисов."""
        await self.cleanup()
        await self.initialize()


# Создаем глобальный контейнер mock сервисов
_mock_services = MockExternalServices()


# ============================================================================
# ПАТЧИНГ ВНЕШНИХ МОДУЛЕЙ
# ============================================================================


def setup_module_mocks():
    """
    Настройка всех системных моков.

    ВАЖНО: Этот код выполняется на уровне модуля,
    до импорта основного приложения.
    """
    logger.info("Setting up module mocks")

    # Мокируем Redis
    sys.modules["services.redis_service"] = MagicMock()
    sys.modules["services.redis_service"].get_redis_service = AsyncMock(
        return_value=_mock_services.redis
    )
    sys.modules["services.redis_service"].RedisService = MockRedisService

    # Мокируем Telegram
    sys.modules["aiogram"] = MagicMock()
    sys.modules["aiogram.Bot"] = MagicMock()
    sys.modules["aiogram.Dispatcher"] = MagicMock()
    sys.modules["aiogram.types"] = MagicMock()
    sys.modules["services.telegram_service"] = MagicMock()
    sys.modules["services.telegram_service"].get_telegram_service = AsyncMock(
        return_value=_mock_services.telegram
    )

    # Мокируем другие внешние сервисы
    external_services = [
        "services.pdf_service",
        "services.push_notification_service",
        "services.realtime_notifications",
        "services.monitoring_service",
        "weasyprint",
        "psutil",
    ]

    for service in external_services:
        sys.modules[service] = MagicMock()

    logger.info("Module mocks setup complete")


# Выполняем мокирование перед импортом приложения
setup_module_mocks()

# Импорты после мокирования
from config import Settings
from database import Base, get_async_session
from main import app


# ============================================================================
# БАЗОВЫЕ ФИКСТУРЫ ТЕСТИРОВАНИЯ
# ============================================================================


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Политика event loop для тестирования.

    Использует asyncio.WindowsSelectorEventLoopPolicy() на Windows
    для совместимости с pytest-asyncio.
    """
    if sys.platform == "win32":
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="session")
def test_settings():
    """
    Настройки приложения для тестирования.

    Переопределяет основные настройки для изоляции тестов:
    - Использует in-memory SQLite
    - Отключает внешние сервисы
    - Устанавливает тестовые токены
    """
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",  # In-memory для быстроты
        secret_key="test-secret-key-for-testing-only-not-for-production",
        algorithm="HS256",
        access_token_expire_minutes=1440,  # 24 часа для тестов
        telegram_bot_token="123456789:test-token-for-testing-only",
        telegram_webhook_url="https://example.com/webhook",
        log_level="WARNING",  # Уменьшаем шум в тестах
        environment="testing",
        debug=False,
    )


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings):
    """
    Создание async движка SQLAlchemy для тестов.

    Использует in-memory SQLite с поддержкой async операций.
    Создает все таблицы при запуске и очищает при завершении.
    """
    logger.info("Creating test database engine")

    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,  # Отключаем SQL логи в тестах
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
        },
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Очищаем после тестов
    await engine.dispose()
    logger.info("Test database engine disposed")


@pytest_asyncio.fixture(scope="function")
async def async_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Async сессия для каждого теста.

    Создает новую сессию для каждого теста с автоматическим
    rollback для изоляции тестов.

    ВАЖНО: Используется Context7 паттерн для управления жизненным циклом.
    """
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def test_client(
    test_settings, async_session
) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP клиент для тестирования API.

    Настраивает FastAPI приложение с dependency injection
    для использования тестовой базы данных.
    """

    # Переопределяем dependency для использования тестовой сессии
    async def override_get_async_session():
        yield async_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    try:
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            timeout=30.0,
        ) as client:
            yield client
    finally:
        # Очищаем dependency overrides
        app.dependency_overrides.clear()


# ============================================================================
# УТИЛИТАРНЫЕ КЛАССЫ И ФУНКЦИИ
# ============================================================================


class TestContext:
    """
    Context7 implementation для управления состоянием тестов.

    Предоставляет централизованный способ управления:
    - Mock сервисами
    - Состоянием базы данных
    - Временными данными
    - Логированием тестов
    """

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.utcnow()
        self.temp_data = {}
        self.mocks = {}
        self.cleanups = []

    async def __aenter__(self):
        """Вход в контекст теста."""
        logger.info(f"Starting test context: {self.test_name}")
        await _mock_services.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста теста с очисткой."""
        try:
            # Выполняем все зарегистрированные очистки
            for cleanup in reversed(self.cleanups):
                try:
                    if asyncio.iscoroutinefunction(cleanup):
                        await cleanup()
                    else:
                        cleanup()
                except Exception as e:
                    logger.warning(f"Cleanup error in {self.test_name}: {e}")

            # Сбрасываем состояние mock сервисов
            await _mock_services.reset()

            # Логируем время выполнения теста
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            logger.info(f"Test context completed: {self.test_name} ({duration:.2f}s)")

        except Exception as e:
            logger.error(f"Error during test context cleanup: {e}")
            raise

    def register_cleanup(self, cleanup_func):
        """Регистрация функции очистки."""
        self.cleanups.append(cleanup_func)

    def set_temp_data(self, key: str, value: Any):
        """Сохранение временных данных теста."""
        self.temp_data[key] = value

    def get_temp_data(self, key: str, default=None):
        """Получение временных данных теста."""
        return self.temp_data.get(key, default)


class TestApiClient:
    """
    Обертка для AsyncClient с дополнительными возможностями.

    Предоставляет:
    - Упрощенные методы для API вызовов
    - Автоматическую проверку ответов
    - Логирование запросов
    - Управление аутентификацией
    """

    def __init__(self, client: AsyncClient):
        self.client = client
        self.auth_headers = {}
        self.base_headers = {"Content-Type": "application/json"}

    def set_auth_headers(self, headers: Dict[str, str]):
        """Установка заголовков аутентификации."""
        self.auth_headers = headers

    def clear_auth_headers(self):
        """Очистка заголовков аутентификации."""
        self.auth_headers = {}

    def _merge_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Объединение заголовков."""
        merged = {**self.base_headers, **self.auth_headers}
        if headers:
            merged.update(headers)
        return merged

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs):
        """GET запрос."""
        return await self.client.get(
            url, headers=self._merge_headers(headers), **kwargs
        )

    async def post(
        self,
        url: str,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """POST запрос."""
        return await self.client.post(
            url, json=json, headers=self._merge_headers(headers), **kwargs
        )

    async def put(
        self,
        url: str,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """PUT запрос."""
        return await self.client.put(
            url, json=json, headers=self._merge_headers(headers), **kwargs
        )

    async def patch(
        self,
        url: str,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """PATCH запрос."""
        return await self.client.patch(
            url, json=json, headers=self._merge_headers(headers), **kwargs
        )

    async def delete(
        self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ):
        """DELETE запрос."""
        return await self.client.delete(
            url, headers=self._merge_headers(headers), **kwargs
        )


@pytest.fixture
def api_client(test_client) -> TestApiClient:
    """Улучшенный API клиент для тестирования."""
    return TestApiClient(test_client)


@pytest.fixture
def test_context(request) -> TestContext:
    """Context7 фикстура для управления состоянием теста."""
    return TestContext(request.node.name)


# ============================================================================
# УТИЛИТАРНЫЕ ФУНКЦИИ ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================


def assert_response_structure(
    response, expected_status: int = 200, expected_keys: Optional[list] = None
):
    """
    Проверка структуры HTTP ответа.

    Args:
        response: HTTP ответ
        expected_status: Ожидаемый статус код
        expected_keys: Список ожидаемых ключей в JSON ответе
    """
    assert response.status_code == expected_status, (
        f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"
    )

    if expected_keys:
        try:
            json_data = response.json()
            for key in expected_keys:
                assert key in json_data, (
                    f"Key '{key}' not found in response. Available keys: {list(json_data.keys())}"
                )
        except ValueError:
            pytest.fail(f"Response is not valid JSON: {response.text}")


@pytest.fixture
def assert_response():
    """Фикстура для проверки HTTP ответов."""
    return assert_response_structure


# ============================================================================
# PYTEST HOOKS И КОНФИГУРАЦИЯ
# ============================================================================


def pytest_configure(config):
    """
    Конфигурация pytest для тестирования.

    Добавляет custom маркеры для категоризации тестов.
    """
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "positive: Positive test cases")
    config.addinivalue_line("markers", "negative: Negative test cases")
    config.addinivalue_line("markers", "edge_case: Edge case tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "surveys: Survey domain tests")
    config.addinivalue_line("markers", "users: User domain tests")
    config.addinivalue_line("markers", "telegram: Telegram integration tests")


def pytest_collection_modifyitems(config, items):
    """
    Модификация собранных тестов.

    Автоматически добавляет маркеры на основе:
    - Расположения файлов тестов
    - Имен тестовых функций
    - Patten в названиях
    """
    for item in items:
        # Добавляем маркеры по типу тестов
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

        # Добавляем маркеры по доменам
        test_path = str(item.fspath).lower()
        if "auth" in test_path:
            item.add_marker(pytest.mark.auth)
        elif "survey" in test_path:
            item.add_marker(pytest.mark.surveys)
        elif "user" in test_path:
            item.add_marker(pytest.mark.users)
        elif "telegram" in test_path:
            item.add_marker(pytest.mark.telegram)

        # Добавляем маркеры по типам тестов
        test_name = item.name.lower()
        if "positive" in test_name or "success" in test_name:
            item.add_marker(pytest.mark.positive)
        elif "negative" in test_name or "fail" in test_name or "error" in test_name:
            item.add_marker(pytest.mark.negative)
        elif "edge" in test_name or "boundary" in test_name:
            item.add_marker(pytest.mark.edge_case)


# ============================================================================
# ГЛОБАЛЬНЫЕ MOCK ФИКСТУРЫ
# ============================================================================


@pytest.fixture
def mock_redis_service():
    """Mock Redis сервиса для тестов."""
    return _mock_services.redis


@pytest.fixture
def mock_telegram_service():
    """Mock Telegram сервиса для тестов."""
    return _mock_services.telegram


@pytest.fixture
def mock_external_services():
    """Контейнер всех mock сервисов."""
    return _mock_services


@pytest.fixture(autouse=True)
async def setup_test_environment(mock_external_services):
    """
    Автоматическая настройка окружения для каждого теста.

    Выполняется автоматически перед каждым тестом:
    - Инициализирует mock сервисы
    - Очищает состояние после теста
    - Логирует выполнение тестов
    """
    logger.debug("Setting up test environment")

    # Инициализируем mock сервисы
    await mock_external_services.initialize()

    yield

    # Очищаем после теста
    await mock_external_services.reset()
    logger.debug("Test environment cleaned up")


# ============================================================================
# ЭКСПОРТ ОСНОВНЫХ КОМПОНЕНТОВ
# ============================================================================

__all__ = [
    # Основные фикстуры
    "test_settings",
    "test_engine",
    "async_session",
    "test_client",
    "api_client",
    "test_context",
    # Mock сервисы
    "mock_redis_service",
    "mock_telegram_service",
    "mock_external_services",
    # Утилиты
    "assert_response",
    "TestContext",
    "TestApiClient",
    # Mock классы
    "MockRedisService",
    "MockTelegramService",
    "MockExternalServices",
]
