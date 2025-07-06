"""
Фабрики для создания тестовых данных пользователей.
"""

from pathlib import Path
import sys

import factory
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.user_data import UserData

fake = Faker(["en_US", "ru_RU"])


class UserDataFactory(factory.Factory):
    class Meta:
        model = UserData

    session_id = factory.Sequence(lambda n: f"session-{n}")
    ip_address = factory.Faker("ipv4")
    user_agent = "Mozilla/5.0 (Test Browser)"
    fingerprint = factory.Sequence(lambda n: f"fingerprint-{n}")
    device_info = {"device_type": "desktop", "os": "Linux"}
    browser_info = {"language": "en-US", "timezone": "UTC"}


class TelegramUserDataFactory(UserDataFactory):
    telegram_user_id = factory.Sequence(lambda n: 1000000 + n)
    telegram_username = factory.Sequence(lambda n: f"tguser{n}")
    telegram_first_name = factory.Faker("first_name")
    telegram_last_name = factory.Faker("last_name")
