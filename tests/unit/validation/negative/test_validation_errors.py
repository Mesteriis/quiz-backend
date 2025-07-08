"""
Негативные тесты для Validation endpoints.

Тестирует сценарии с ошибками валидации:
- Невалидные email форматы
- Невалидные телефонные номера
- Ошибки сервисов (MX, SMTP)
- Превышение лимитов
- Некорректные данные
- Внутренние ошибки сервиса
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException


class TestEmailValidationErrors:
    """Тесты ошибок валидации email адресов."""

    async def test_validate_email_invalid_format(
        self, api_client, invalid_email_data_factory
    ):
        """Тест валидации email с невалидным форматом."""
        # Arrange
        invalid_email_request = invalid_email_data_factory.build()

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=invalid_email_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200  # Сервис возвращает 200 даже для невалидных
        data = response.json()

        assert data["email"] == invalid_email_request.email
        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert isinstance(data["error_message"], str)

    async def test_validate_email_empty_string(self, api_client):
        """Тест валидации пустого email."""
        # Arrange
        email_data = {
            "email": "",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == ""
        assert data["is_valid"] is False
        assert data["error_message"] is not None

    async def test_validate_email_none_value(self, api_client):
        """Тест валидации email с None значением."""
        # Arrange
        email_data = {
            "email": None,
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    async def test_validate_email_missing_at_symbol(self, api_client):
        """Тест валидации email без символа @."""
        # Arrange
        email_data = {
            "email": "plainaddress",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert "@" in data["error_message"] or "format" in data["error_message"].lower()

    async def test_validate_email_missing_domain(self, api_client):
        """Тест валидации email без домена."""
        # Arrange
        email_data = {
            "email": "user@",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert "domain" in data["error_message"].lower()

    async def test_validate_email_missing_local_part(self, api_client):
        """Тест валидации email без локальной части."""
        # Arrange
        email_data = {
            "email": "@example.com",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None

    async def test_validate_email_multiple_at_symbols(self, api_client):
        """Тест валидации email с несколькими символами @."""
        # Arrange
        email_data = {
            "email": "user@domain@example.com",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None

    async def test_validate_email_consecutive_dots(self, api_client):
        """Тест валидации email с подряд идущими точками."""
        # Arrange
        email_data = {
            "email": "user..name@example.com",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None

    async def test_validate_email_spaces_in_address(self, api_client):
        """Тест валидации email с пробелами."""
        # Arrange
        invalid_emails = [
            "user name@example.com",
            "user@exam ple.com",
            " user@example.com",
            "user@example.com ",
            "user @example.com",
            "user@ example.com",
        ]

        # Act & Assert
        for email in invalid_emails:
            email_data = {
                "email": email,
                "check_mx": False,
                "check_smtp": False,
            }

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"), json=email_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["is_valid"] is False
            assert data["error_message"] is not None

    async def test_validate_email_too_long(self, api_client):
        """Тест валидации слишком длинного email."""
        # Arrange - максимальная длина email 254 символа
        long_local = "a" * 65  # Превышает максимум локальной части (64)
        long_domain = "b" * 190 + ".com"  # Очень длинный домен

        email_data = {
            "email": f"{long_local}@{long_domain}",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert (
            "length" in data["error_message"].lower()
            or "long" in data["error_message"].lower()
        )

    async def test_validate_email_mx_check_failure(self, api_client):
        """Тест валидации email с ошибкой MX проверки."""
        # Arrange
        email_data = {
            "email": "user@nonexistent-domain-12345.com",
            "check_mx": True,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email_data["email"]
        assert data["mx_valid"] is False
        # Email может быть формально валидным, но MX проверка неудачная

    async def test_validate_email_smtp_check_failure(self, api_client):
        """Тест валидации email с ошибкой SMTP проверки."""
        # Arrange
        email_data = {
            "email": "nonexistent@gmail.com",
            "check_mx": True,
            "check_smtp": True,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"), json=email_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email_data["email"]
        # SMTP проверка может быть неудачной даже для валидного домена
        assert "smtp_valid" in data
        assert isinstance(data["smtp_valid"], (bool, type(None)))

    async def test_validate_email_service_internal_error(self, api_client):
        """Тест внутренней ошибки сервиса валидации email."""
        # Arrange
        email_data = {
            "email": "test@example.com",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        with patch(
            "services.email_validation.email_validator.validate_email_comprehensive"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Internal validation error")

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"), json=email_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Email validation failed" in data["detail"]

    async def test_validate_email_malformed_json(self, api_client):
        """Тест валидации с некорректным JSON."""
        # Arrange - некорректный JSON
        malformed_data = '{"email": "test@example.com", "check_mx": invalid_bool}'

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            content=malformed_data,
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestEmailBatchValidationErrors:
    """Тесты ошибок пакетной валидации email."""

    async def test_validate_emails_batch_too_many_emails(self, api_client):
        """Тест пакетной валидации с превышением лимита."""
        # Arrange - создаем более 100 email для превышения лимита
        emails = [f"user{i}@example.com" for i in range(101)]

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
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Maximum 100 emails" in data["detail"]

    async def test_validate_emails_batch_empty_emails(self, api_client):
        """Тест пакетной валидации с пустыми email."""
        # Arrange
        emails = ["", "   ", "test@example.com", "", "user@test.com"]

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
        assert data["invalid_count"] > 0  # Пустые email должны быть невалидными

    async def test_validate_emails_batch_all_invalid(self, api_client):
        """Тест пакетной валидации только невалидных email."""
        # Arrange
        invalid_emails = [
            "plainaddress",
            "@missing-domain.com",
            "missing@.com",
            "missing@domain",
            "spaces in@email.com",
        ]

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": invalid_emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == len(invalid_emails)
        assert data["invalid_count"] == len(invalid_emails)
        assert data["valid_count"] == 0

    async def test_validate_emails_batch_service_error(self, api_client):
        """Тест пакетной валидации с ошибкой сервиса."""
        # Arrange
        emails = ["test@example.com", "user@test.com"]

        # Act
        with patch(
            "services.email_validation.email_validator.validate_email_batch"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Batch validation error")

            response = await api_client.post(
                api_client.url_for("validate_emails_batch"),
                json={
                    "emails": emails,
                    "check_mx": False,
                    "check_smtp": False,
                },
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Batch email validation failed" in data["detail"]

    async def test_validate_emails_batch_invalid_parameters(self, api_client):
        """Тест пакетной валидации с некорректными параметрами."""
        # Arrange
        invalid_requests = [
            {
                "emails": "not-a-list",  # Не список
                "check_mx": False,
                "check_smtp": False,
            },
            {
                "emails": ["test@example.com"],
                "check_mx": "invalid-bool",  # Не boolean
                "check_smtp": False,
            },
            {
                "emails": ["test@example.com"],
                "check_mx": False,
                "check_smtp": "invalid-bool",  # Не boolean
            },
        ]

        # Act & Assert
        for request_data in invalid_requests:
            response = await api_client.post(
                api_client.url_for("validate_emails_batch"), json=request_data
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data


class TestPhoneValidationErrors:
    """Тесты ошибок валидации телефонных номеров."""

    async def test_validate_phone_invalid_format(
        self, api_client, invalid_phone_data_factory
    ):
        """Тест валидации телефона с невалидным форматом."""
        # Arrange
        invalid_phone_request = invalid_phone_data_factory.build()

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=invalid_phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == invalid_phone_request.phone
        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert isinstance(data["error_message"], str)

    async def test_validate_phone_too_short(self, api_client):
        """Тест валидации слишком короткого телефона."""
        # Arrange
        phone_data = {
            "phone": "123",
            "normalize": True,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"), json=phone_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert "short" in data["error_message"].lower()

    async def test_validate_phone_too_long(self, api_client):
        """Тест валидации слишком длинного телефона."""
        # Arrange
        phone_data = {
            "phone": "12345678901234567890",  # 20 цифр
            "normalize": True,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"), json=phone_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert "long" in data["error_message"].lower()

    async def test_validate_phone_empty_string(self, api_client):
        """Тест валидации пустого телефона."""
        # Arrange
        phone_data = {
            "phone": "",
            "normalize": True,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"), json=phone_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["error_message"] is not None

    async def test_validate_phone_only_special_characters(self, api_client):
        """Тест валидации телефона только из спецсимволов."""
        # Arrange
        special_phones = [
            "++++++",
            "------",
            "()()()",
            "...",
            "   ",
            "######",
        ]

        # Act & Assert
        for phone in special_phones:
            phone_data = {
                "phone": phone,
                "normalize": True,
            }

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"), json=phone_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["is_valid"] is False
            assert data["error_message"] is not None

    async def test_validate_phone_only_letters(self, api_client):
        """Тест валидации телефона только из букв."""
        # Arrange
        letter_phones = [
            "abcdefghij",
            "completely-invalid",
            "ABCDEFGHIJ",
            "hello-world",
            "тест-телефон",
        ]

        # Act & Assert
        for phone in letter_phones:
            phone_data = {
                "phone": phone,
                "normalize": True,
            }

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"), json=phone_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["is_valid"] is False
            assert data["error_message"] is not None

    async def test_validate_phone_mixed_invalid_characters(self, api_client):
        """Тест валидации телефона со смешанными невалидными символами."""
        # Arrange
        mixed_phones = [
            "123abc456",
            "+7abc123def",
            "8-916-abc-def",
            "123@456#789",
            "123!@#$%^&*()",
        ]

        # Act & Assert
        for phone in mixed_phones:
            phone_data = {
                "phone": phone,
                "normalize": True,
            }

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"), json=phone_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["is_valid"] is False
            assert data["error_message"] is not None

    async def test_validate_phone_none_value(self, api_client):
        """Тест валидации телефона с None значением."""
        # Arrange
        phone_data = {
            "phone": None,
            "normalize": True,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"), json=phone_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_validate_phone_invalid_country_code(self, api_client):
        """Тест валидации телефона с невалидным кодом страны."""
        # Arrange
        phone_data = {
            "phone": "1234567890",
            "country_code": "INVALID",
            "normalize": True,
        }

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"), json=phone_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Невалидный код страны не должен вызывать ошибку,
        # но может влиять на валидность номера
        assert "is_valid" in data
        assert "country_code" in data

    async def test_validate_phone_service_internal_error(self, api_client):
        """Тест внутренней ошибки сервиса валидации телефона."""
        # Arrange
        phone_data = {
            "phone": "+1234567890",
            "normalize": True,
        }

        # Act
        with patch("src.routers.validation.re.sub") as mock_re:
            mock_re.side_effect = Exception("Internal phone validation error")

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"), json=phone_data
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Phone validation failed" in data["detail"]

    async def test_validate_phone_malformed_json(self, api_client):
        """Тест валидации телефона с некорректным JSON."""
        # Arrange
        malformed_data = '{"phone": "+1234567890", "normalize": invalid_bool}'

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            content=malformed_data,
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestDomainValidationErrors:
    """Тесты ошибок валидации доменов."""

    async def test_check_domain_mx_invalid_domain(self, api_client):
        """Тест проверки MX записей для невалидного домена."""
        # Arrange
        invalid_domain = "invalid-domain-that-does-not-exist.com"

        # Act
        response = await api_client.get(
            api_client.url_for("check_domain_mx_records", domain=invalid_domain)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["domain"] == invalid_domain
        assert data["mx_valid"] is False
        assert data["error_message"] is not None

    async def test_check_domain_mx_empty_domain(self, api_client):
        """Тест проверки MX записей для пустого домена."""
        # Arrange
        empty_domain = ""

        # Act
        response = await api_client.get(
            api_client.url_for("check_domain_mx_records", domain=empty_domain)
        )

        # Assert
        # URL может быть некорректным или возвращать ошибку
        assert response.status_code in [400, 404, 422]

    async def test_check_domain_mx_special_characters(self, api_client):
        """Тест проверки MX записей для домена со спецсимволами."""
        # Arrange
        special_domains = [
            "test@domain.com",  # @ не должен быть в домене
            "domain space.com",  # пробел
            "domain#.com",  # #
            "domain$.com",  # $
            "domain%.com",  # %
        ]

        # Act & Assert
        for domain in special_domains:
            response = await api_client.get(
                api_client.url_for("check_domain_mx_records", domain=domain)
            )

            assert response.status_code == 200
            data = response.json()

            assert data["domain"] == domain
            assert data["mx_valid"] is False
            assert data["error_message"] is not None

    async def test_check_domain_mx_service_error(self, api_client):
        """Тест ошибки сервиса при проверке MX записей."""
        # Arrange
        domain = "example.com"

        # Act
        with patch(
            "services.email_validation.EmailValidationService._validate_mx_records"
        ) as mock_mx:
            mock_mx.side_effect = Exception("MX check service error")

            response = await api_client.get(
                api_client.url_for("check_domain_mx_records", domain=domain)
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "MX record check failed" in data["detail"]

    async def test_check_domain_mx_very_long_domain(self, api_client):
        """Тест проверки MX записей для очень длинного домена."""
        # Arrange
        long_domain = "a" * 253 + ".com"  # Превышает максимальную длину домена

        # Act
        response = await api_client.get(
            api_client.url_for("check_domain_mx_records", domain=long_domain)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["domain"] == long_domain
        assert data["mx_valid"] is False
        assert data["error_message"] is not None


class TestEmailSuggestionsErrors:
    """Тесты ошибок предложений email."""

    async def test_get_email_suggestions_invalid_email(self, api_client):
        """Тест получения предложений для сильно невалидного email."""
        # Arrange
        invalid_emails = [
            "completely-wrong-format",
            "123456789",
            "!@#$%^&*()",
            "тест без домена",
        ]

        # Act & Assert
        for email in invalid_emails:
            response = await api_client.post(
                api_client.url_for("get_email_suggestions"), json={"email": email}
            )

            assert response.status_code == 200
            data = response.json()

            assert "suggestions" in data
            # Для сильно невалидных email может не быть предложений
            assert isinstance(data["suggestions"], list)

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
        assert isinstance(data["suggestions"], list)

    async def test_get_email_suggestions_none_email(self, api_client):
        """Тест получения предложений для None email."""
        # Act
        response = await api_client.post(
            api_client.url_for("get_email_suggestions"), json={"email": None}
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_get_email_suggestions_malformed_request(self, api_client):
        """Тест получения предложений с некорректным запросом."""
        # Arrange
        malformed_requests = [
            {},  # Отсутствует поле email
            {"not_email": "test@example.com"},  # Неправильное поле
            {"email": 123},  # Не строка
            {"email": True},  # Не строка
        ]

        # Act & Assert
        for request_data in malformed_requests:
            response = await api_client.post(
                api_client.url_for("get_email_suggestions"), json=request_data
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data


class TestSMTPValidationErrors:
    """Тесты ошибок SMTP валидации."""

    async def test_test_email_smtp_invalid_email(self, api_client):
        """Тест SMTP проверки для невалидного email."""
        # Arrange
        invalid_email = "invalid-email"

        # Act
        response = await api_client.get(
            api_client.url_for("test_email_smtp", email=invalid_email)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "smtp_valid" in data
        assert data["smtp_valid"] is False
        assert "smtp_response" in data

    async def test_test_email_smtp_nonexistent_domain(self, api_client):
        """Тест SMTP проверки для несуществующего домена."""
        # Arrange
        email = "test@nonexistent-domain-12345.com"

        # Act
        response = await api_client.get(
            api_client.url_for("test_email_smtp", email=email)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "smtp_valid" in data
        assert data["smtp_valid"] is False
        assert "smtp_response" in data

    async def test_test_email_smtp_empty_email(self, api_client):
        """Тест SMTP проверки для пустого email."""
        # Arrange
        email = ""

        # Act
        response = await api_client.get(
            api_client.url_for("test_email_smtp", email=email)
        )

        # Assert
        # URL может быть некорректным
        assert response.status_code in [400, 404, 422]

    async def test_test_email_smtp_service_error(self, api_client):
        """Тест ошибки сервиса SMTP проверки."""
        # Arrange
        email = "test@example.com"

        # Act
        with patch("services.email_validation.EmailValidationService") as mock_service:
            mock_service.side_effect = Exception("SMTP service error")

            response = await api_client.get(
                api_client.url_for("test_email_smtp", email=email)
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestValidationHealthCheckErrors:
    """Тесты ошибок проверки здоровья."""

    async def test_validation_health_check_service_error(self, api_client):
        """Тест ошибки сервиса проверки здоровья."""
        # Act
        with patch("src.routers.validation.datetime") as mock_datetime:
            mock_datetime.side_effect = Exception("Health check error")

            response = await api_client.get(
                api_client.url_for("validation_health_check")
            )

        # Assert
        # Зависит от реализации - может возвращать ошибку или справляться с ней
        assert response.status_code in [200, 500]


class TestValidationMissingEndpoints:
    """Тесты обращения к несуществующим endpoints."""

    async def test_validation_nonexistent_endpoint(self, api_client):
        """Тест обращения к несуществующему validation endpoint."""
        # Act
        response = await api_client.get("/api/validation/nonexistent")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_validation_wrong_http_method(self, api_client):
        """Тест использования неправильного HTTP метода."""
        # Arrange
        email_data = {
            "email": "test@example.com",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act - используем GET вместо POST
        response = await api_client.get(
            api_client.url_for("validate_email_endpoint"), params=email_data
        )

        # Assert
        assert response.status_code == 405  # Method Not Allowed
        data = response.json()
        assert "detail" in data

    async def test_validation_missing_content_type(self, api_client):
        """Тест отсутствия Content-Type header."""
        # Arrange
        email_data = (
            '{"email": "test@example.com", "check_mx": false, "check_smtp": false}'
        )

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            content=email_data,
            # Не указываем Content-Type
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
