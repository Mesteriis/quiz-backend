"""
UNIT TESTS CONFTEST.PY - КОНФИГУРАЦИЯ ДЛЯ МОДУЛЬНЫХ ТЕСТОВ
===========================================================

Этот файл содержит fixture специально для unit тестов:
- Интеграция с фабриками из tests/factories
- Моки для изоляции от внешних зависимостей
- Утилиты для быстрого создания тестовых данных
- Context7 для управления состоянием unit тестов

ПРИНЦИПЫ UNIT ТЕСТИРОВАНИЯ:
- Полная изоляция от внешних систем
- Быстрое выполнение (< 100ms на тест)
- Детерминированные результаты
- Фокус на логике бизнес-слоя

SYNC vs ASYNC в Unit тестах:
Unit тесты используют ASYNC подход потому что:
1. Модели и репозитории используют async SQLAlchemy
2. Сервисы имеют async интерфейсы
3. Необходимо тестировать async flows
4. Context7 лучше работает с async
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Type, Union
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем базовые фикстуры из корневого conftest.py
from tests.conftest import (
    TestContext,
    MockRedisService,
    MockTelegramService,
    MockExternalServices,
)

# Импорты фабрик - используем polyfactory
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type, Any, List

# Импортируем все фабрики для удобства
from tests.factories import *


# ============================================================================
# UNIT TEST CONTEXT - Context7 для модульных тестов
# ============================================================================


class UnitTestContext(TestContext):
    """
    Специализированный Context7 для unit тестов.

    Расширяет базовый TestContext дополнительными возможностями:
    - Быстрое создание моков для зависимостей
    - Изоляция тестируемых компонентов
    - Автоматическая очистка состояния
    """

    def __init__(self, test_name: str, component_type: str = "service"):
        super().__init__(test_name)
        self.component_type = component_type
        self.isolated_mocks = {}
        self.factory_manager = None

    async def __aenter__(self):
        """Настройка окружения unit теста."""
        await super().__aenter__()

        # Создаем factory manager для этого теста
        # (session будет подключена позже через dependency injection)

        return self

    def create_mock(
        self, name: str, spec: Optional[Type] = None, **kwargs
    ) -> MagicMock:
        """
        Создание изолированного мока для unit теста.

        Args:
            name: Имя мока (для отладки)
            spec: Спецификация класса/интерфейса
            **kwargs: Дополнительные параметры для MagicMock

        Returns:
            MagicMock: Настроенный мок
        """
        mock = MagicMock(spec=spec, **kwargs)
        mock.name = name
        self.isolated_mocks[name] = mock

        # Регистрируем очистку мока
        self.register_cleanup(lambda: mock.reset_mock())

        return mock

    def create_async_mock(
        self, name: str, spec: Optional[Type] = None, **kwargs
    ) -> AsyncMock:
        """
        Создание асинхронного мока для unit теста.

        Args:
            name: Имя мока
            spec: Спецификация async класса/интерфейса
            **kwargs: Дополнительные параметры

        Returns:
            AsyncMock: Настроенный async мок
        """
        mock = AsyncMock(spec=spec, **kwargs)
        mock.name = name
        self.isolated_mocks[name] = mock

        # Регистрируем очистку мока
        self.register_cleanup(lambda: mock.reset_mock())

        return mock

    def get_mock(self, name: str) -> Union[MagicMock, AsyncMock]:
        """Получение мока по имени."""
        return self.isolated_mocks.get(name)

    def setup_factory_manager(self, session: AsyncSession):
        """Настройка factory manager с сессией БД."""
        self.factory_manager = session
        self.set_temp_data("factory_manager", self.factory_manager)


# ============================================================================
# ФИКСТУРЫ ДЛЯ FACTORY ИНТЕГРАЦИИ
# ============================================================================


@pytest_asyncio.fixture
async def factory_session(async_session: AsyncSession) -> AsyncSession:
    """
    Сессия для работы с polyfactory фабриками.

    Возвращает async сессию для использования в polyfactory.
    """
    return async_session


@pytest.fixture
def unit_test_context(request) -> UnitTestContext:
    """Context7 фикстура специально для unit тестов."""
    return UnitTestContext(request.node.name, "unit")


# ============================================================================
# ПРЕДКОНФИГУРИРОВАННЫЕ ФАБРИКИ ДЛЯ UNIT ТЕСТОВ
# ============================================================================


@pytest_asyncio.fixture
async def test_user(factory_session: AsyncSession):
    """Создание тестового пользователя для unit тестов."""
    from tests.factories.users.model_factories import UserModelFactory

    return await UserModelFactory.create_async(session=factory_session)


@pytest_asyncio.fixture
async def test_admin_user(factory_session: AsyncSession):
    """Создание администратора для unit тестов."""
    from tests.factories.users.model_factories import AdminUserModelFactory

    return await AdminUserModelFactory.create_async(session=factory_session)


@pytest_asyncio.fixture
async def test_telegram_user(factory_session: AsyncSession):
    """Создание Telegram пользователя для unit тестов."""
    from tests.factories.users.model_factories import TelegramUserModelFactory

    return await TelegramUserModelFactory.create_async(session=factory_session)


@pytest_asyncio.fixture
async def predictable_user(factory_session: AsyncSession):
    """Создание пользователя с предсказуемыми данными."""
    from tests.factories.users.model_factories import PredictableUserModelFactory

    return await PredictableUserModelFactory.create_async(session=factory_session)


@pytest_asyncio.fixture
async def test_users_cohort(factory_session: AsyncSession):
    """Создание группы тестовых пользователей."""
    from tests.factories.users.model_factories import UserModelFactory

    return await UserModelFactory.create_batch_async(session=factory_session, size=5)


# ============================================================================
# МОКИ ДЛЯ ИЗОЛЯЦИИ UNIT ТЕСТОВ
# ============================================================================


@pytest.fixture
def mock_user_repository():
    """
    Mock для UserRepository.

    Используется для изоляции сервисов от слоя данных.
    """
    mock = AsyncMock()

    # Настраиваем стандартные методы
    mock.get_by_id = AsyncMock(return_value=None)
    mock.get_by_username = AsyncMock(return_value=None)
    mock.get_by_email = AsyncMock(return_value=None)
    mock.create = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.list = AsyncMock(return_value=[])

    return mock


@pytest.fixture
def mock_survey_repository():
    """Mock для SurveyRepository."""
    mock = AsyncMock()

    mock.get_by_id = AsyncMock(return_value=None)
    mock.get_by_access_token = AsyncMock(return_value=None)
    mock.create = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.list_active = AsyncMock(return_value=[])
    mock.list_by_user = AsyncMock(return_value=[])

    return mock


@pytest.fixture
def mock_response_repository():
    """Mock для ResponseRepository."""
    mock = AsyncMock()

    mock.get_by_id = AsyncMock(return_value=None)
    mock.create = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.get_by_question = AsyncMock(return_value=[])
    mock.get_by_user = AsyncMock(return_value=[])

    return mock


@pytest.fixture
def mock_repositories(
    mock_user_repository,
    mock_survey_repository,
    mock_response_repository,
):
    """Контейнер всех repository моков."""
    return {
        "user": mock_user_repository,
        "survey": mock_survey_repository,
        "response": mock_response_repository,
    }


# ============================================================================
# МОКИ СЕРВИСОВ
# ============================================================================


@pytest.fixture
def mock_auth_service():
    """Mock для AuthService."""
    mock = AsyncMock()

    mock.create_access_token = MagicMock(return_value="test-token")
    mock.verify_token = AsyncMock(return_value={"user_id": 1})
    mock.authenticate_user = AsyncMock(return_value=None)
    mock.register_user = AsyncMock()
    mock.change_password = AsyncMock(return_value=True)

    return mock


@pytest.fixture
def mock_email_service():
    """Mock для EmailService."""
    mock = AsyncMock()

    mock.send_email = AsyncMock(return_value=True)
    mock.send_verification_email = AsyncMock(return_value=True)
    mock.send_password_reset_email = AsyncMock(return_value=True)

    return mock


@pytest.fixture
def mock_notification_service():
    """Mock для NotificationService."""
    mock = AsyncMock()

    mock.send_push_notification = AsyncMock(return_value=True)
    mock.send_telegram_notification = AsyncMock(return_value=True)
    mock.schedule_notification = AsyncMock()

    return mock


# ============================================================================
# УТИЛИТЫ ДЛЯ UNIT ТЕСТИРОВАНИЯ
# ============================================================================


def assert_called_once_with_user(mock_method, user_id: int):
    """
    Проверка, что метод был вызван один раз с указанным user_id.

    Полезно для проверки вызовов repository методов.
    """
    mock_method.assert_called_once()
    args, kwargs = mock_method.call_args

    if args and hasattr(args[0], "id"):
        assert args[0].id == user_id
    elif "user_id" in kwargs:
        assert kwargs["user_id"] == user_id
    elif args:
        assert args[0] == user_id
    else:
        pytest.fail("Could not find user_id in method call")


def assert_mock_called_with_fields(mock_method, **expected_fields):
    """
    Проверка, что mock метод был вызван с объектом,
    содержащим указанные поля.
    """
    mock_method.assert_called_once()
    args, kwargs = mock_method.call_args

    # Получаем первый аргумент (обычно это объект)
    if args:
        obj = args[0]
        for field_name, expected_value in expected_fields.items():
            actual_value = getattr(obj, field_name, None)
            assert actual_value == expected_value, (
                f"Expected {field_name}={expected_value}, "
                f"got {field_name}={actual_value}"
            )


@pytest.fixture
def assert_unit_test():
    """Утилиты для проверок в unit тестах."""
    return {
        "called_once_with_user": assert_called_once_with_user,
        "called_with_fields": assert_mock_called_with_fields,
    }


# ============================================================================
# ПАРАМЕТРИЗАЦИЯ ДЛЯ UNIT ТЕСТОВ
# ============================================================================

# Стандартные наборы данных для параметризованных тестов

VALID_USER_DATA = [
    {"username": "testuser1", "email": "test1@example.com"},
    {"username": "testuser2", "email": "test2@example.com"},
    {"username": "admin_user", "email": "admin@example.com"},
]

INVALID_USER_DATA = [
    {"username": "", "email": "test@example.com"},  # Пустой username
    {"username": "test", "email": "invalid-email"},  # Невалидный email
    {"username": "a", "email": "test@example.com"},  # Слишком короткий username
    {"username": "x" * 101, "email": "test@example.com"},  # Слишком длинный username
]

EDGE_CASE_STRINGS = [
    "",  # Пустая строка
    " ",  # Пробел
    "   ",  # Несколько пробелов
    "\t",  # Табуляция
    "\n",  # Перенос строки
    "a" * 1000,  # Очень длинная строка
    "🚀🎉✨",  # Эмодзи
    "русский текст",  # Кириллица
    "<script>alert('xss')</script>",  # XSS попытка
    "'; DROP TABLE users; --",  # SQL injection попытка
]


@pytest.fixture(params=VALID_USER_DATA)
def valid_user_data(request):
    """Параметризованная фикстура с валидными данными пользователя."""
    return request.param


@pytest.fixture(params=INVALID_USER_DATA)
def invalid_user_data(request):
    """Параметризованная фикстура с невалидными данными пользователя."""
    return request.param


@pytest.fixture(params=EDGE_CASE_STRINGS)
def edge_case_string(request):
    """Параметризованная фикстура с граничными случаями строк."""
    return request.param


# ============================================================================
# HELPER ФИКСТУРЫ ДЛЯ СПЕЦИФИЧЕСКИХ ДОМЕНОВ
# ============================================================================


@pytest.fixture
def auth_test_context(unit_test_context: UnitTestContext):
    """Context для тестирования модуля аутентификации."""
    unit_test_context.component_type = "auth"

    # Создаем специфичные для auth моки
    unit_test_context.create_async_mock("jwt_service")
    unit_test_context.create_async_mock("password_service")
    unit_test_context.create_async_mock("token_service")

    return unit_test_context


@pytest.fixture
def survey_test_context(unit_test_context: UnitTestContext):
    """Context для тестирования модуля опросов."""
    unit_test_context.component_type = "surveys"

    # Создаем специфичные для surveys моки
    unit_test_context.create_async_mock("access_control_service")
    unit_test_context.create_async_mock("analytics_service")

    return unit_test_context


@pytest.fixture
def user_test_context(unit_test_context: UnitTestContext):
    """Context для тестирования модуля пользователей."""
    unit_test_context.component_type = "users"

    # Создаем специфичные для users моки
    unit_test_context.create_async_mock("profile_service")
    unit_test_context.create_async_mock("verification_service")

    return unit_test_context


# ============================================================================
# ВРЕМЯ И ДАТЫ ДЛЯ ТЕСТОВ
# ============================================================================


@pytest.fixture
def fixed_datetime():
    """Фиксированная дата для детерминированных тестов."""
    return datetime(2024, 1, 15, 12, 0, 0)


@pytest.fixture
def time_range():
    """Диапазон времени для тестирования временных интервалов."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    return {
        "start": base_time,
        "middle": base_time + timedelta(days=15),
        "end": base_time + timedelta(days=30),
    }


# ============================================================================
# ЭКСПОРТ ОСНОВНЫХ КОМПОНЕНТОВ ДЛЯ UNIT ТЕСТОВ
# ============================================================================

__all__ = [
    # Context7 для unit тестов
    "UnitTestContext",
    "unit_test_context",
    "auth_test_context",
    "survey_test_context",
    "user_test_context",
    # Factory фикстуры
    "factory_session",
    "test_user",
    "test_admin_user",
    "test_telegram_user",
    "predictable_user",
    "test_users_cohort",
    # Repository моки
    "mock_user_repository",
    "mock_survey_repository",
    "mock_response_repository",
    "mock_repositories",
    # Service моки
    "mock_auth_service",
    "mock_email_service",
    "mock_notification_service",
    # Утилиты тестирования
    "assert_unit_test",
    "assert_called_once_with_user",
    "assert_mock_called_with_fields",
    # Параметризованные данные
    "valid_user_data",
    "invalid_user_data",
    "edge_case_string",
    # Время и даты
    "fixed_datetime",
    "time_range",
]
