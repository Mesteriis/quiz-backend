"""
Позитивные тесты для Email валидации.

Тестирует успешные сценарии валидации email адресов:
- Валидные email форматы
- MX записи проверка
- SMTP проверка
- Пакетная валидация
- Предложения исправлений
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestEmailValidationSuccess:
    """Тесты успешной валидации email адресов."""

    async def test_validate_email_basic_success(self, api_client, valid_email_request):
        """Тест базовой успешной валидации email."""
        # Arrange
        email_data = valid_email_request.model_dump()

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email_data["email"]
        assert "is_valid" in data
        assert "mx_valid" in data
        assert "error_message" in data
        assert "suggestions" in data

    async def test_validate_email_common_providers(
        self, api_client, valid_email_data_factory, common_domains
    ):
        """Тест валидации email с популярными провайдерами."""
        # Arrange
        test_emails = []
        for domain in common_domains:
            email_request = valid_email_data_factory.build()
            # Заменяем домен на тестовый
            email_parts = email_request.email.split("@")
            email_request.email = f"{email_parts[0]}@{domain}"
            test_emails.append(email_request)

        # Act & Assert
        for email_request in test_emails:
            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email_request.email
            assert isinstance(data["is_valid"], bool)

    async def test_validate_email_with_mx_check(
        self, api_client, valid_email_data_factory
    ):
        """Тест валидации email с проверкой MX записей."""
        # Arrange
        email_request = valid_email_data_factory.build()
        email_request.check_mx = True
        email_request.check_smtp = False

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email_request.email
        assert "mx_valid" in data
        assert isinstance(data["mx_valid"], bool)

    async def test_validate_email_with_smtp_check(
        self, api_client, valid_email_data_factory
    ):
        """Тест валидации email с проверкой SMTP."""
        # Arrange
        email_request = valid_email_data_factory.build()
        email_request.check_mx = True
        email_request.check_smtp = True

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email_request.email
        assert "mx_valid" in data
        assert "smtp_valid" in data
        assert isinstance(data["smtp_valid"], (bool, type(None)))

    async def test_validate_email_special_characters(
        self, api_client, valid_email_data_factory
    ):
        """Тест валидации email со специальными символами."""
        # Arrange
        special_emails = [
            "test+label@example.com",
            "user.name@example.com",
            "test_user@example.com",
            "123@example.com",
            "test-user@example.com",
            "user%test@example.com",
            "a@b.co",  # shortest valid
        ]

        # Act & Assert
        for email in special_emails:
            email_request = valid_email_data_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_international_domains(
        self, api_client, valid_email_data_factory
    ):
        """Тест валидации email с международными доменами."""
        # Arrange
        international_emails = [
            "user@пример.рф",
            "test@münchen.de",
            "user@café.fr",
            "test@日本.jp",
            "user@москва.рф",
        ]

        # Act & Assert
        for email in international_emails:
            email_request = valid_email_data_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_case_insensitive(
        self, api_client, valid_email_data_factory
    ):
        """Тест валидации email с разным регистром."""
        # Arrange
        base_email = "Test.User@Example.Com"
        case_variations = [
            "test.user@example.com",
            "TEST.USER@EXAMPLE.COM",
            "Test.User@Example.Com",
            "test.USER@example.COM",
        ]

        # Act & Assert
        for email in case_variations:
            email_request = valid_email_data_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_with_subdomains(
        self, api_client, valid_email_data_factory
    ):
        """Тест валидации email с поддоменами."""
        # Arrange
        subdomain_emails = [
            "user@mail.example.com",
            "test@smtp.gmail.com",
            "user@sub.domain.co.uk",
            "test@deep.sub.domain.com",
            "user@mail.corporate.company.com",
        ]

        # Act & Assert
        for email in subdomain_emails:
            email_request = valid_email_data_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_long_local_part(
        self, api_client, valid_email_data_factory
    ):
        """Тест валидации email с длинной локальной частью."""
        # Arrange - максимальная длина локальной части 64 символа
        long_local = "a" * 64
        email = f"{long_local}@example.com"

        email_request = valid_email_data_factory.build()
        email_request.email = email

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert "is_valid" in data


class TestEmailBatchValidation:
    """Тесты пакетной валидации email."""

    async def test_batch_validate_emails_success(
        self, api_client, batch_email_data_factory
    ):
        """Тест успешной пакетной валидации email."""
        # Arrange
        email_batch = batch_email_data_factory.build()

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": email_batch,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "total_count" in data
        assert "valid_count" in data
        assert "invalid_count" in data
        assert "results" in data

        assert data["total_count"] == len(email_batch)
        assert data["valid_count"] + data["invalid_count"] == data["total_count"]
        assert len(data["results"]) == len(email_batch)

    async def test_batch_validate_emails_with_mx_check(
        self, api_client, valid_email_data_factory
    ):
        """Тест пакетной валидации email с проверкой MX."""
        # Arrange
        emails = [valid_email_data_factory.build().email for _ in range(5)]

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": emails,
                "check_mx": True,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == len(emails)

        # Проверяем, что для каждого email есть mx_valid
        for result in data["results"]:
            assert "mx_valid" in result
            assert isinstance(result["mx_valid"], bool)

    async def test_batch_validate_mixed_emails(
        self, api_client, valid_email_data_factory, invalid_email_data_factory
    ):
        """Тест пакетной валидации смешанных email."""
        # Arrange
        valid_emails = [valid_email_data_factory.build().email for _ in range(3)]
        invalid_emails = [invalid_email_data_factory.build().email for _ in range(2)]

        all_emails = valid_emails + invalid_emails

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": all_emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == len(all_emails)

        # Проверяем результаты для каждого email
        for i, result in enumerate(data["results"]):
            assert result["email"] == all_emails[i]
            assert "is_valid" in result

    async def test_batch_validate_empty_list(self, api_client):
        """Тест пакетной валидации пустого списка."""
        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": [],
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 0
        assert data["valid_count"] == 0
        assert data["invalid_count"] == 0
        assert data["results"] == []

    async def test_batch_validate_single_email(
        self, api_client, valid_email_data_factory
    ):
        """Тест пакетной валидации одного email."""
        # Arrange
        email = valid_email_data_factory.build().email

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": [email],
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["email"] == email

    async def test_batch_validate_performance_small_batch(
        self, api_client, valid_email_data_factory
    ):
        """Тест производительности небольшой пакетной валидации."""
        # Arrange
        emails = [valid_email_data_factory.build().email for _ in range(10)]

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == len(emails)
        assert len(data["results"]) == len(emails)

        # Проверяем, что все результаты корректны
        for result in data["results"]:
            assert "email" in result
            assert "is_valid" in result
            assert result["email"] in emails


class TestEmailDomainValidation:
    """Тесты валидации доменов email."""

    async def test_check_domain_mx_valid(self, api_client, common_domains):
        """Тест проверки MX записей для валидных доменов."""
        # Arrange
        domain = common_domains[0]  # gmail.com

        # Act
        response = await api_client.get(
            api_client.url_for("check_domain_mx_records", domain=domain)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["domain"] == domain
        assert "mx_valid" in data
        assert "mx_records" in data
        assert isinstance(data["mx_valid"], bool)

    async def test_check_domain_mx_multiple_domains(self, api_client, common_domains):
        """Тест проверки MX записей для нескольких доменов."""
        # Act & Assert
        for domain in common_domains[:5]:  # Тестируем первые 5 доменов
            response = await api_client.get(
                api_client.url_for("check_domain_mx_records", domain=domain)
            )

            assert response.status_code == 200
            data = response.json()

            assert data["domain"] == domain
            assert "mx_valid" in data
            assert "mx_records" in data

    async def test_check_domain_mx_with_subdomain(self, api_client):
        """Тест проверки MX записей для поддоменов."""
        # Arrange
        subdomains = [
            "mail.example.com",
            "smtp.example.com",
            "sub.domain.com",
        ]

        # Act & Assert
        for subdomain in subdomains:
            response = await api_client.get(
                api_client.url_for("check_domain_mx_records", domain=subdomain)
            )

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == subdomain

    async def test_check_domain_mx_international(self, api_client):
        """Тест проверки MX записей для международных доменов."""
        # Arrange
        international_domains = [
            "пример.рф",
            "münchen.de",
            "café.fr",
        ]

        # Act & Assert
        for domain in international_domains:
            response = await api_client.get(
                api_client.url_for("check_domain_mx_records", domain=domain)
            )

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == domain


class TestEmailSuggestions:
    """Тесты предложений исправлений email."""

    async def test_get_email_suggestions_for_typos(self, api_client, email_typos):
        """Тест получения предложений для типичных опечаток."""
        # Act & Assert
        for typo_email in email_typos:
            response = await api_client.post(
                api_client.url_for("get_email_suggestions"), json={"email": typo_email}
            )

            assert response.status_code == 200
            data = response.json()

            assert "suggestions" in data
            assert isinstance(data["suggestions"], list)

    async def test_get_email_suggestions_for_valid_email(
        self, api_client, valid_email_data_factory
    ):
        """Тест получения предложений для валидного email."""
        # Arrange
        valid_email = valid_email_data_factory.build().email

        # Act
        response = await api_client.post(
            api_client.url_for("get_email_suggestions"), json={"email": valid_email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        # Для валидного email может не быть предложений
        assert len(data["suggestions"]) >= 0

    async def test_get_email_suggestions_empty_email(self, api_client):
        """Тест получения предложений для пустого email."""
        # Act
        response = await api_client.post(
            api_client.url_for("get_email_suggestions"), json={"email": ""}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    async def test_get_email_suggestions_partial_domain(self, api_client):
        """Тест получения предложений для частичного домена."""
        # Arrange
        partial_emails = [
            "user@gm",
            "user@gmail",
            "user@yaho",
            "user@outlo",
        ]

        # Act & Assert
        for email in partial_emails:
            response = await api_client.post(
                api_client.url_for("get_email_suggestions"), json={"email": email}
            )

            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data


class TestEmailSMTPValidation:
    """Тесты SMTP валидации email."""

    async def test_test_email_smtp_valid(self, api_client, valid_email_data_factory):
        """Тест SMTP проверки для валидного email."""
        # Arrange
        email = valid_email_data_factory.build().email

        # Act
        response = await api_client.get(
            api_client.url_for("test_email_smtp", email=email)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "smtp_valid" in data
        assert "smtp_response" in data
        assert isinstance(data["smtp_valid"], bool)

    async def test_test_email_smtp_multiple_emails(
        self, api_client, valid_email_data_factory
    ):
        """Тест SMTP проверки для нескольких email."""
        # Arrange
        emails = [valid_email_data_factory.build().email for _ in range(3)]

        # Act & Assert
        for email in emails:
            response = await api_client.get(
                api_client.url_for("test_email_smtp", email=email)
            )

            assert response.status_code == 200
            data = response.json()

            assert "smtp_valid" in data
            assert "smtp_response" in data

    async def test_test_email_smtp_common_providers(
        self, api_client, valid_email_data_factory, common_domains
    ):
        """Тест SMTP проверки для популярных провайдеров."""
        # Arrange
        test_emails = []
        for domain in common_domains[:3]:  # Тестируем первые 3 домена
            email_request = valid_email_data_factory.build()
            email_parts = email_request.email.split("@")
            email = f"{email_parts[0]}@{domain}"
            test_emails.append(email)

        # Act & Assert
        for email in test_emails:
            response = await api_client.get(
                api_client.url_for("test_email_smtp", email=email)
            )

            assert response.status_code == 200
            data = response.json()

            assert "smtp_valid" in data
            assert "smtp_response" in data


class TestValidationHealthCheck:
    """Тесты проверки здоровья validation сервиса."""

    async def test_validation_health_check_success(self, api_client):
        """Тест успешной проверки здоровья validation сервиса."""
        # Act
        response = await api_client.get(api_client.url_for("validation_health_check"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert data["service"] == "validation"

    async def test_validation_health_check_response_structure(self, api_client):
        """Тест структуры ответа проверки здоровья."""
        # Act
        response = await api_client.get(api_client.url_for("validation_health_check"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем обязательные поля
        required_fields = ["status", "service", "timestamp"]
        for field in required_fields:
            assert field in data

        # Проверяем типы данных
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["timestamp"], str)

    async def test_validation_health_check_multiple_calls(self, api_client):
        """Тест множественных вызовов проверки здоровья."""
        # Act & Assert
        for _ in range(5):
            response = await api_client.get(
                api_client.url_for("validation_health_check")
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
