"""
Conftest для Validation domain тестов.

Фикстуры и фабрики для тестирования validation endpoints:
- Email валидация данные
- Phone валидация данные
- Batch валидация данные
- Domain MX проверка данные
"""

import pytest
from faker import Faker
from polyfactory.factories import BaseFactory
from polyfactory.fields import Use
from polyfactory.pytest_plugin import register_fixture

from src.schemas.validation import (
    EmailValidationRequest,
    PhoneValidationRequest,
    EmailValidationResponse,
    PhoneValidationResponse,
)

# Глобальный faker для консистентности
fake = Faker(["en_US", "ru_RU"])
fake.seed_instance(42)


class EmailValidationRequestFactory(BaseFactory[EmailValidationRequest]):
    """Фабрика для создания запросов валидации email."""

    __model__ = EmailValidationRequest

    @classmethod
    def email(cls) -> str:
        """Генерирует валидный email."""
        return fake.email()

    check_mx = Use(lambda: fake.boolean(chance_of_getting_true=50))
    check_smtp = Use(lambda: fake.boolean(chance_of_getting_true=30))


class PhoneValidationRequestFactory(BaseFactory[PhoneValidationRequest]):
    """Фабрика для создания запросов валидации телефона."""

    __model__ = PhoneValidationRequest

    @classmethod
    def phone(cls) -> str:
        """Генерирует валидный телефон."""
        return fake.phone_number()

    @classmethod
    def country_code(cls) -> str | None:
        """Код страны (опционально)."""
        return fake.random_element(["US", "RU", "GB", "FR", "DE", None])

    normalize = Use(lambda: fake.boolean(chance_of_getting_true=70))


class EmailValidationResponseFactory(BaseFactory[EmailValidationResponse]):
    """Фабрика для создания ответов валидации email."""

    __model__ = EmailValidationResponse

    @classmethod
    def email(cls) -> str:
        """Email из запроса."""
        return fake.email()

    is_valid = Use(lambda: fake.boolean(chance_of_getting_true=70))
    mx_valid = Use(lambda: fake.boolean(chance_of_getting_true=80))
    smtp_valid = Use(lambda: fake.boolean(chance_of_getting_true=60))

    @classmethod
    def error_message(cls) -> str | None:
        """Сообщение об ошибке."""
        return fake.sentence() if fake.boolean(chance_of_getting_true=30) else None

    @classmethod
    def suggestions(cls) -> list[str]:
        """Предложения исправления."""
        if fake.boolean(chance_of_getting_true=40):
            return [fake.email() for _ in range(fake.random_int(min=1, max=3))]
        return []


class PhoneValidationResponseFactory(BaseFactory[PhoneValidationResponse]):
    """Фабрика для создания ответов валидации телефона."""

    __model__ = PhoneValidationResponse

    @classmethod
    def phone(cls) -> str:
        """Телефон из запроса."""
        return fake.phone_number()

    @classmethod
    def normalized_phone(cls) -> str:
        """Нормализованный телефон."""
        return f"+{fake.random_int(min=10000000000, max=99999999999)}"

    is_valid = Use(lambda: fake.boolean(chance_of_getting_true=70))

    @classmethod
    def country_code(cls) -> str | None:
        """Определенный код страны."""
        return fake.random_element(["US", "RU", "GB", "FR", "DE", None])

    @classmethod
    def carrier(cls) -> str | None:
        """Оператор связи."""
        return fake.random_element(["Verizon", "AT&T", "MTS", "Beeline", None])

    @classmethod
    def error_message(cls) -> str | None:
        """Сообщение об ошибке."""
        return fake.sentence() if fake.boolean(chance_of_getting_true=30) else None


# Специализированные фабрики для тестовых данных
class ValidEmailDataFactory(EmailValidationRequestFactory):
    """Фабрика для валидных email данных."""

    @classmethod
    def email(cls) -> str:
        """Гарантированно валидный email."""
        domains = ["gmail.com", "outlook.com", "yahoo.com", "example.com"]
        name = fake.user_name()
        domain = fake.random_element(domains)
        return f"{name}@{domain}"

    check_mx = False
    check_smtp = False


class InvalidEmailDataFactory(EmailValidationRequestFactory):
    """Фабрика для невалидных email данных."""

    @classmethod
    def email(cls) -> str:
        """Генерирует невалидный email."""
        invalid_patterns = [
            "plainaddress",
            "@missing-domain.com",
            "missing@.com",
            "missing@domain",
            "spaces in@email.com",
            "email@",
            "email@domain@domain.com",
            "email..email@domain.com",
        ]
        return fake.random_element(invalid_patterns)

    check_mx = False
    check_smtp = False


class ValidPhoneDataFactory(PhoneValidationRequestFactory):
    """Фабрика для валидных телефонных номеров."""

    @classmethod
    def phone(cls) -> str:
        """Гарантированно валидный телефон."""
        valid_phones = [
            "+1234567890",
            "+79161234567",
            "+44 20 7946 0958",
            "+33 1 23 45 67 89",
            "+49 30 12345678",
        ]
        return fake.random_element(valid_phones)

    normalize = True


class InvalidPhoneDataFactory(PhoneValidationRequestFactory):
    """Фабрика для невалидных телефонных номеров."""

    @classmethod
    def phone(cls) -> str:
        """Генерирует невалидный телефон."""
        invalid_patterns = [
            "123",  # Too short
            "abc123def",  # Contains letters
            "12345678901234567890",  # Too long
            "+",  # Just plus sign
            "completely-invalid",  # Completely invalid
            "",  # Empty
        ]
        return fake.random_element(invalid_patterns)

    normalize = True


class BatchEmailDataFactory(BaseFactory[list]):
    """Фабрика для пакетной валидации email."""

    __model__ = list

    @classmethod
    def __create_batch(cls) -> list[str]:
        """Создает пакет email для валидации."""
        count = fake.random_int(min=5, max=15)
        emails = []

        # 70% валидных email
        valid_count = int(count * 0.7)
        for _ in range(valid_count):
            emails.append(ValidEmailDataFactory.build().email)

        # 30% невалидных email
        invalid_count = count - valid_count
        for _ in range(invalid_count):
            emails.append(InvalidEmailDataFactory.build().email)

        fake.shuffle(emails)
        return emails

    @classmethod
    def build(cls) -> list[str]:
        """Создает пакет email."""
        return cls.__create_batch()


class EdgeCaseEmailDataFactory(EmailValidationRequestFactory):
    """Фабрика для граничных случаев email валидации."""

    @classmethod
    def email(cls) -> str:
        """Генерирует граничные случаи email."""
        edge_cases = [
            "a@b.co",  # shortest valid
            "test@localhost",  # localhost domain
            "user+tag@example.com",  # with plus
            "user.name@example.com",  # with dot
            "test123@example.com",  # with numbers
            "UPPERCASE@EXAMPLE.COM",  # uppercase
            "тест@пример.рф",  # cyrillic
            "user@sub.domain.com",  # subdomain
            "very.long.email.address@very.long.domain.name.com",  # long
        ]
        return fake.random_element(edge_cases)


class EdgeCasePhoneDataFactory(PhoneValidationRequestFactory):
    """Фабрика для граничных случаев телефонной валидации."""

    @classmethod
    def phone(cls) -> str:
        """Генерирует граничные случаи телефонов."""
        edge_cases = [
            "+1234567890123456",  # very long
            "+1",  # shortest possible
            "+0000000000",  # all zeros
            "8 (916) 123-45-67",  # Russian format
            "(234) 567-8901",  # US format
            "234-567-8901",  # US format with dashes
            "234.567.8901",  # US format with dots
            "234 567 8901",  # US format with spaces
            "+7-916-123-45-67",  # Russian with dashes
            "+7 916 123 45 67",  # Russian with spaces
        ]
        return fake.random_element(edge_cases)


# Регистрация фикстур
@register_fixture(name="email_validation_request_factory")
def email_validation_request_factory():
    """Фикстура для фабрики запросов валидации email."""
    return EmailValidationRequestFactory


@register_fixture(name="phone_validation_request_factory")
def phone_validation_request_factory():
    """Фикстура для фабрики запросов валидации телефона."""
    return PhoneValidationRequestFactory


@register_fixture(name="valid_email_data_factory")
def valid_email_data_factory():
    """Фикстура для валидных email данных."""
    return ValidEmailDataFactory


@register_fixture(name="invalid_email_data_factory")
def invalid_email_data_factory():
    """Фикстура для невалидных email данных."""
    return InvalidEmailDataFactory


@register_fixture(name="valid_phone_data_factory")
def valid_phone_data_factory():
    """Фикстура для валидных телефонных данных."""
    return ValidPhoneDataFactory


@register_fixture(name="invalid_phone_data_factory")
def invalid_phone_data_factory():
    """Фикстура для невалидных телефонных данных."""
    return InvalidPhoneDataFactory


@register_fixture(name="batch_email_data_factory")
def batch_email_data_factory():
    """Фикстура для пакетных email данных."""
    return BatchEmailDataFactory


@register_fixture(name="edge_case_email_factory")
def edge_case_email_factory():
    """Фикстура для граничных случаев email."""
    return EdgeCaseEmailDataFactory


@register_fixture(name="edge_case_phone_factory")
def edge_case_phone_factory():
    """Фикстура для граничных случаев телефона."""
    return EdgeCasePhoneDataFactory


# Готовые данные для тестов
@pytest.fixture
def valid_email_request(valid_email_data_factory):
    """Готовый валидный запрос валидации email."""
    return valid_email_data_factory.build()


@pytest.fixture
def invalid_email_request(invalid_email_data_factory):
    """Готовый невалидный запрос валидации email."""
    return invalid_email_data_factory.build()


@pytest.fixture
def valid_phone_request(valid_phone_data_factory):
    """Готовый валидный запрос валидации телефона."""
    return valid_phone_data_factory.build()


@pytest.fixture
def invalid_phone_request(invalid_phone_data_factory):
    """Готовый невалидный запрос валидации телефона."""
    return invalid_phone_data_factory.build()


@pytest.fixture
def batch_email_data(batch_email_data_factory):
    """Готовые данные для пакетной валидации."""
    return batch_email_data_factory.build()


@pytest.fixture
def common_domains():
    """Популярные домены для тестирования."""
    return [
        "gmail.com",
        "outlook.com",
        "yahoo.com",
        "hotmail.com",
        "mail.ru",
        "yandex.ru",
        "example.com",
        "test.com",
    ]


@pytest.fixture
def international_phones():
    """Международные телефонные номера для тестирования."""
    return [
        "+1234567890",  # US
        "+79161234567",  # Russia
        "+44 20 7946 0958",  # UK
        "+33 1 23 45 67 89",  # France
        "+49 30 12345678",  # Germany
        "+86 138 0013 8000",  # China
        "+81 3 1234 5678",  # Japan
        "+39 06 1234 5678",  # Italy
        "+34 91 123 45 67",  # Spain
        "+61 2 1234 5678",  # Australia
    ]


@pytest.fixture
def email_typos():
    """Распространенные опечатки в email."""
    return [
        "user@gmai.com",  # missing 'l'
        "user@gmial.com",  # 'l' and 'i' swapped
        "user@gmail.co",  # missing 'm'
        "user@yahooo.com",  # extra 'o'
        "user@hotmai.com",  # missing 'l'
        "user@outlok.com",  # missing 'o'
        "user@yandx.ru",  # missing 'e'
        "user@mai.ru",  # missing 'l'
    ]


@pytest.fixture
def domain_validation_data():
    """Данные для валидации доменов."""
    return {
        "valid_domains": [
            "gmail.com",
            "outlook.com",
            "yahoo.com",
            "example.com",
        ],
        "invalid_domains": [
            "invalid-domain-that-does-not-exist.com",
            "test.invalid",
            "localhost",
            "fake.domain",
        ],
        "suspicious_domains": [
            "tempmail.com",
            "10minutemail.com",
            "guerrillamail.com",
            "disposable.com",
        ],
    }
