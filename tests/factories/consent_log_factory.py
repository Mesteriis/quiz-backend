"""
Фабрики для создания тестовых согласий (ConsentLog).

Этот модуль содержит фабрики для создания различных типов согласий
с использованием factory_boy и Faker для GDPR-совместимости.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

import factory
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.consent_log import ConsentLog
from models.respondent import Respondent
from models.survey import Survey

# Создаем глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])


class ConsentLogFactory(factory.Factory):
    """Базовая фабрика для создания согласий."""

    class Meta:
        model = ConsentLog

    # Основные поля
    respondent_id = factory.SubFactory(
        "tests.factories.respondent_factory.RespondentFactory"
    )
    survey_id = factory.SubFactory("tests.factories.survey_factory.SurveyFactory")

    # Тип согласия
    consent_type = factory.Faker(
        "random_element",
        elements=[
            "location",
            "device_info",
            "personal_data",
            "marketing",
            "analytics",
            "cookies",
        ],
    )

    # Статус согласия
    is_granted = True
    is_revoked = False

    # Технические детали
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    consent_source = "web"
    consent_version = "1.0"

    # Дополнительные данные
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": obj.consent_type,
            "source": obj.consent_source,
            "user_agent": obj.user_agent,
            "ip": obj.ip_address,
        }
    )

    # Временные метки
    granted_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(hours=fake.random_int(min=1, max=72))
    )
    revoked_at = None
    created_at = factory.LazyAttribute(lambda obj: obj.granted_at)
    updated_at = factory.LazyAttribute(lambda obj: obj.granted_at)


class LocationConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий на геолокацию."""

    consent_type = "location"
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": "location",
            "precision": "approximate",
            "purpose": "survey_targeting",
            "data_retention": "30_days",
        }
    )


class PreciseLocationConsentFactory(LocationConsentFactory):
    """Фабрика для создания согласий на точную геолокацию."""

    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": "location",
            "precision": "precise",
            "purpose": "detailed_analytics",
            "data_retention": "90_days",
        }
    )


class DeviceInfoConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий на информацию об устройстве."""

    consent_type = "device_info"
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": "device_info",
            "data_types": ["browser", "os", "screen_size", "language"],
            "purpose": "user_experience",
        }
    )


class PersonalDataConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий на персональные данные."""

    consent_type = "personal_data"
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": "personal_data",
            "data_types": ["name", "email", "demographic"],
            "purpose": "survey_completion",
            "data_retention": "2_years",
        }
    )


class MarketingConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий на маркетинг."""

    consent_type = "marketing"
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": "marketing",
            "channels": ["email", "telegram", "push"],
            "frequency": "weekly",
            "purpose": "product_updates",
        }
    )


class AnalyticsConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий на аналитику."""

    consent_type = "analytics"
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": "analytics",
            "tracking_types": ["usage", "performance", "errors"],
            "anonymized": True,
            "purpose": "service_improvement",
        }
    )


class CookiesConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий на cookies."""

    consent_type = "cookies"
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": "cookies",
            "cookie_types": ["essential", "functional", "analytics"],
            "duration": "session",
        }
    )


class TelegramConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий из Telegram."""

    consent_source = "telegram_webapp"
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": obj.consent_type,
            "source": "telegram_webapp",
            "webapp_version": "6.9",
            "telegram_user_id": fake.random_int(min=100000000, max=999999999),
        }
    )


class RevokedConsentFactory(ConsentLogFactory):
    """Фабрика для создания отозванных согласий."""

    is_granted = False
    is_revoked = True
    revoked_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(hours=fake.random_int(min=1, max=24))
    )
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": obj.consent_type,
            "revocation_reason": fake.random_element(
                [
                    "user_request",
                    "privacy_concerns",
                    "account_deletion",
                    "data_breach",
                ]
            ),
            "revoked_via": "user_dashboard",
        }
    )


class ExpiredConsentFactory(ConsentLogFactory):
    """Фабрика для создания истекших согласий."""

    granted_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=fake.random_int(min=365, max=730))
    )
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": obj.consent_type,
            "expiry_policy": "1_year",
            "auto_expired": True,
        }
    )


class VersionedConsentFactory(ConsentLogFactory):
    """Фабрика для создания согласий с версионированием."""

    consent_version = factory.Faker(
        "random_element", elements=["1.0", "1.1", "2.0", "2.1", "3.0"]
    )
    details = factory.LazyAttribute(
        lambda obj: {
            "consent_type": obj.consent_type,
            "version": obj.consent_version,
            "policy_changes": fake.random_element(
                [
                    "updated_retention_period",
                    "added_data_types",
                    "new_processing_purposes",
                    "third_party_sharing",
                ]
            ),
        }
    )


def create_consent_for_respondent(
    respondent: Respondent, consent_type: str, survey: Survey = None, **kwargs
) -> ConsentLog:
    """
    Создает согласие для конкретного респондента.

    Args:
        respondent: Респондент
        consent_type: Тип согласия
        survey: Опрос (опционально)
        **kwargs: Дополнительные параметры

    Returns:
        ConsentLog: Созданное согласие
    """
    factory_map = {
        "location": LocationConsentFactory,
        "precise_location": PreciseLocationConsentFactory,
        "device_info": DeviceInfoConsentFactory,
        "personal_data": PersonalDataConsentFactory,
        "marketing": MarketingConsentFactory,
        "analytics": AnalyticsConsentFactory,
        "cookies": CookiesConsentFactory,
    }

    factory_class = factory_map.get(consent_type, ConsentLogFactory)
    return factory_class(
        respondent_id=respondent.id,
        survey_id=survey.id if survey else None,
        consent_type=consent_type,
        **kwargs,
    )


def create_full_consent_set(
    respondent: Respondent, survey: Survey = None
) -> list[ConsentLog]:
    """
    Создает полный набор согласий для респондента.

    Args:
        respondent: Респондент
        survey: Опрос (опционально)

    Returns:
        list[ConsentLog]: Список всех согласий
    """
    consent_types = [
        "location",
        "device_info",
        "personal_data",
        "marketing",
        "analytics",
        "cookies",
    ]

    consents = []
    for consent_type in consent_types:
        consent = create_consent_for_respondent(
            respondent=respondent, consent_type=consent_type, survey=survey
        )
        consents.append(consent)

    return consents


def create_consent_history(
    respondent: Respondent, consent_type: str, survey: Survey = None
) -> list[ConsentLog]:
    """
    Создает историю согласий (предоставление -> отзыв -> новое предоставление).

    Args:
        respondent: Респондент
        consent_type: Тип согласия
        survey: Опрос (опционально)

    Returns:
        list[ConsentLog]: История согласий
    """
    base_time = datetime.utcnow() - timedelta(days=30)

    # Первоначальное согласие
    initial_consent = create_consent_for_respondent(
        respondent=respondent,
        consent_type=consent_type,
        survey=survey,
        granted_at=base_time,
    )

    # Отзыв согласия
    revoked_consent = RevokedConsentFactory(
        respondent_id=respondent.id,
        survey_id=survey.id if survey else None,
        consent_type=consent_type,
        granted_at=base_time + timedelta(days=10),
        revoked_at=base_time + timedelta(days=15),
    )

    # Новое согласие
    new_consent = create_consent_for_respondent(
        respondent=respondent,
        consent_type=consent_type,
        survey=survey,
        granted_at=base_time + timedelta(days=20),
        consent_version="2.0",
    )

    return [initial_consent, revoked_consent, new_consent]


def create_consents_batch(
    count: int = 10, consent_type: str = "mixed"
) -> list[ConsentLog]:
    """
    Создает батч согласий.

    Args:
        count: Количество согласий
        consent_type: Тип согласий (mixed, location, personal_data, etc.)

    Returns:
        list[ConsentLog]: Список созданных согласий
    """
    consents = []

    consent_types = [
        "location",
        "device_info",
        "personal_data",
        "marketing",
        "analytics",
        "cookies",
    ]

    for i in range(count):
        if consent_type == "mixed":
            selected_type = consent_types[i % len(consent_types)]
            if i % 7 == 0:  # Каждое 7-е согласие отозвано
                consent = RevokedConsentFactory(consent_type=selected_type)
            else:
                consent = create_consent_for_respondent(
                    respondent=None,  # Фабрика создаст сама
                    consent_type=selected_type,
                )
        else:
            consent = create_consent_for_respondent(
                respondent=None, consent_type=consent_type
            )

        consents.append(consent)

    return consents
