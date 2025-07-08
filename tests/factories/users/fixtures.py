"""
Утилиты и фикстуры для создания пользователей в тестах.

Этот модуль предоставляет удобные функции для создания пользователей
с различными профилями прямо в тестах без необходимости создания
фабрик вручную.
"""

import asyncio
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

import pytest
from polyfactory.pytest_plugin import register_fixture

from src.models.user import User
from src.services.jwt_service import jwt_service
from .model_factories import (
    UserModelFactory,
    AdminUserModelFactory,
    TelegramUserModelFactory,
    InactiveUserModelFactory,
    PredictableUserModelFactory,
)
from .pydantic_factories import (
    UserCreateDataFactory,
    UserLoginDataFactory,
    TelegramAuthDataFactory,
    ValidUserCreateDataFactory,
    ValidUserLoginDataFactory,
    ValidTelegramAuthDataFactory,
)


# ============================================================================
# УТИЛИТЫ ДЛЯ СОЗДАНИЯ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================


async def create_user_for_test(
    session: AsyncSession,
    factory_class: type = UserModelFactory,
    commit: bool = True,
    **kwargs,
) -> User:
    """
    Создает пользователя для тестирования.

    Args:
        session: Async сессия БД
        factory_class: Класс фабрики для создания пользователя
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры для фабрики

    Returns:
        User: Созданный пользователь

    Example:
        ```python
        user = await create_user_for_test(session, username="testuser")
        admin = await create_user_for_test(session, AdminUserModelFactory, is_admin=True)
        ```
    """
    # Создаем пользователя через фабрику
    user_data = factory_class.build(**kwargs)

    # Создаем User объект
    user = User(**user_data.__dict__)

    # Сохраняем в БД
    session.add(user)
    if commit:
        await session.commit()
        await session.refresh(user)
    else:
        await session.flush()
        await session.refresh(user)

    return user


async def create_admin_user(
    session: AsyncSession, commit: bool = True, **kwargs
) -> User:
    """
    Создает пользователя-администратора.

    Args:
        session: Async сессия БД
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры

    Returns:
        User: Созданный админ
    """
    return await create_user_for_test(
        session, AdminUserModelFactory, commit=commit, **kwargs
    )


async def create_telegram_user(
    session: AsyncSession, commit: bool = True, **kwargs
) -> User:
    """
    Создает пользователя из Telegram.

    Args:
        session: Async сессия БД
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры

    Returns:
        User: Созданный Telegram пользователь
    """
    return await create_user_for_test(
        session, TelegramUserModelFactory, commit=commit, **kwargs
    )


async def create_inactive_user(
    session: AsyncSession, commit: bool = True, **kwargs
) -> User:
    """
    Создает неактивного пользователя.

    Args:
        session: Async сессия БД
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры

    Returns:
        User: Созданный неактивный пользователь
    """
    return await create_user_for_test(
        session, InactiveUserModelFactory, commit=commit, **kwargs
    )


async def create_users_batch(
    session: AsyncSession,
    count: int,
    factory_class: type = UserModelFactory,
    commit: bool = True,
    **kwargs,
) -> List[User]:
    """
    Создает несколько пользователей одновременно.

    Args:
        session: Async сессия БД
        count: Количество пользователей
        factory_class: Класс фабрики
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры для всех пользователей

    Returns:
        List[User]: Список созданных пользователей
    """
    users = []
    for i in range(count):
        # Добавляем уникальный суффикс для каждого пользователя
        user_kwargs = {**kwargs}
        if "username" in user_kwargs:
            user_kwargs["username"] = f"{user_kwargs['username']}_{i}"
        if "email" in user_kwargs:
            base_email = user_kwargs["email"]
            if "@" in base_email:
                name, domain = base_email.split("@", 1)
                user_kwargs["email"] = f"{name}_{i}@{domain}"

        user = await create_user_for_test(
            session, factory_class, commit=False, **user_kwargs
        )
        users.append(user)

    if commit:
        await session.commit()
        for user in users:
            await session.refresh(user)

    return users


def create_auth_headers(user: User) -> Dict[str, str]:
    """
    Создает заголовки аутентификации для пользователя.

    Args:
        user: Пользователь для создания токена

    Returns:
        Dict[str, str]: Заголовки с токеном
    """
    access_token = jwt_service.create_access_token(
        user_id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        is_admin=user.is_admin,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ============================================================================
# ГОТОВЫЕ ФИКСТУРЫ ДЛЯ ТЕСТОВ
# ============================================================================


@pytest.fixture
async def regular_user(async_session: AsyncSession) -> User:
    """Фикстура для обычного пользователя."""
    return await create_user_for_test(async_session)


@pytest.fixture
async def admin_user(async_session: AsyncSession) -> User:
    """Фикстура для пользователя-администратора."""
    return await create_admin_user(async_session)


@pytest.fixture
async def telegram_user(async_session: AsyncSession) -> User:
    """Фикстура для Telegram пользователя."""
    return await create_telegram_user(async_session)


@pytest.fixture
async def inactive_user(async_session: AsyncSession) -> User:
    """Фикстура для неактивного пользователя."""
    return await create_inactive_user(async_session)


@pytest.fixture
async def predictable_user(async_session: AsyncSession) -> User:
    """Фикстура для пользователя с предсказуемыми данными."""
    return await create_user_for_test(async_session, PredictableUserModelFactory)


@pytest.fixture
def user_auth_headers(regular_user: User) -> Dict[str, str]:
    """Фикстура для заголовков аутентификации обычного пользователя."""
    return create_auth_headers(regular_user)


@pytest.fixture
def admin_auth_headers(admin_user: User) -> Dict[str, str]:
    """Фикстура для заголовков аутентификации администратора."""
    return create_auth_headers(admin_user)


@pytest.fixture
def telegram_auth_headers(telegram_user: User) -> Dict[str, str]:
    """Фикстура для заголовков аутентификации Telegram пользователя."""
    return create_auth_headers(telegram_user)


# ============================================================================
# ФИКСТУРЫ ДЛЯ PYDANTIC ДАННЫХ
# ============================================================================


@pytest.fixture
def user_create_data():
    """Фикстура для данных создания пользователя."""
    return UserCreateDataFactory.build()


@pytest.fixture
def valid_user_create_data():
    """Фикстура для валидных данных создания пользователя."""
    return ValidUserCreateDataFactory.build()


@pytest.fixture
def user_login_data():
    """Фикстура для данных входа пользователя."""
    return UserLoginDataFactory.build()


@pytest.fixture
def valid_user_login_data():
    """Фикстура для валидных данных входа пользователя."""
    return ValidUserLoginDataFactory.build()


@pytest.fixture
def telegram_auth_data():
    """Фикстура для данных Telegram аутентификации."""
    return TelegramAuthDataFactory.build()


@pytest.fixture
def valid_telegram_auth_data():
    """Фикстура для валидных данных Telegram аутентификации."""
    return ValidTelegramAuthDataFactory.build()


# ============================================================================
# ПАКЕТНЫЕ ФИКСТУРЫ
# ============================================================================


@pytest.fixture
async def multiple_users(async_session: AsyncSession) -> List[User]:
    """Фикстура для создания нескольких пользователей."""
    return await create_users_batch(async_session, count=5)


@pytest.fixture
async def user_types_sample(async_session: AsyncSession) -> Dict[str, User]:
    """Фикстура для создания различных типов пользователей."""
    return {
        "regular": await create_user_for_test(async_session, UserModelFactory),
        "admin": await create_admin_user(async_session),
        "telegram": await create_telegram_user(async_session),
        "inactive": await create_inactive_user(async_session),
        "predictable": await create_user_for_test(
            async_session, PredictableUserModelFactory
        ),
    }


# ============================================================================
# КОНТЕКСТНЫЕ МЕНЕДЖЕРЫ
# ============================================================================


class UserTestContext:
    """
    Контекстный менеджер для создания пользователей в тестах.

    Автоматически создает пользователя и очищает данные после теста.
    """

    def __init__(
        self, session: AsyncSession, factory_class: type = UserModelFactory, **kwargs
    ):
        self.session = session
        self.factory_class = factory_class
        self.kwargs = kwargs
        self.user: Optional[User] = None
        self.auth_headers: Optional[Dict[str, str]] = None

    async def __aenter__(self) -> "UserTestContext":
        """Создает пользователя при входе в контекст."""
        self.user = await create_user_for_test(
            self.session, self.factory_class, **self.kwargs
        )
        self.auth_headers = create_auth_headers(self.user)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Очищает данные при выходе из контекста."""
        if self.user:
            await self.session.delete(self.user)
            await self.session.commit()


# ============================================================================
# ПОЛЕЗНЫЕ УТИЛИТЫ
# ============================================================================


def get_user_factory_by_type(user_type: str) -> type:
    """
    Получает фабрику по типу пользователя.

    Args:
        user_type: Тип пользователя ("regular", "admin", "telegram", "inactive", "predictable")

    Returns:
        type: Класс фабрики
    """
    factories = {
        "regular": UserModelFactory,
        "admin": AdminUserModelFactory,
        "telegram": TelegramUserModelFactory,
        "inactive": InactiveUserModelFactory,
        "predictable": PredictableUserModelFactory,
    }

    return factories.get(user_type, UserModelFactory)


async def create_user_with_auth(
    session: AsyncSession, user_type: str = "regular", **kwargs
) -> tuple[User, Dict[str, str]]:
    """
    Создает пользователя и возвращает его вместе с заголовками аутентификации.

    Args:
        session: Async сессия БД
        user_type: Тип пользователя
        **kwargs: Дополнительные параметры

    Returns:
        tuple[User, Dict[str, str]]: Пользователь и заголовки аутентификации
    """
    factory_class = get_user_factory_by_type(user_type)
    user = await create_user_for_test(session, factory_class, **kwargs)
    auth_headers = create_auth_headers(user)
    return user, auth_headers


def create_test_scenario_users(session: AsyncSession, scenario: str) -> List[User]:
    """
    Создает пользователей для конкретного сценария тестирования.

    Args:
        session: Async сессия БД
        scenario: Название сценария

    Returns:
        List[User]: Список пользователей для сценария
    """
    scenarios = {
        "auth_flow": [
            ("regular", {"username": "auth_user", "email": "auth@test.com"}),
            ("inactive", {"username": "inactive_auth", "email": "inactive@test.com"}),
        ],
        "admin_actions": [
            ("admin", {"username": "test_admin", "email": "admin@test.com"}),
            ("regular", {"username": "target_user", "email": "target@test.com"}),
        ],
        "telegram_integration": [
            (
                "telegram",
                {"telegram_id": 123456789, "telegram_username": "test_tg_user"},
            ),
            ("regular", {"username": "non_tg_user", "email": "regular@test.com"}),
        ],
    }

    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario}")

    users = []
    for user_type, user_kwargs in scenarios[scenario]:
        factory_class = get_user_factory_by_type(user_type)
        user = asyncio.run(create_user_for_test(session, factory_class, **user_kwargs))
        users.append(user)

    return users
