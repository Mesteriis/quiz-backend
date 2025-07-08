"""
Фабрики для пользователей и аутентификации.

Этот модуль содержит все фабрики, связанные с пользователями:
- Модели пользователей (User)
- Pydantic схемы для API
- Данные для аутентификации
"""

from .model_factories import *
from .pydantic_factories import *
from .fixtures import *

__all__ = [
    # Model factories
    "UserModelFactory",
    "AdminUserModelFactory",
    "TelegramUserModelFactory",
    "InactiveUserModelFactory",
    # Pydantic factories
    "UserCreateDataFactory",
    "UserUpdateDataFactory",
    "UserLoginDataFactory",
    "TelegramAuthDataFactory",
    "UserResponseDataFactory",
    # Utility functions
    "create_user_for_test",
    "create_admin_user",
    "create_telegram_user",
]
