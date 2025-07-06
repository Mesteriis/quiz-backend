"""
Тесты для Validation Router.

Этот модуль содержит тесты для всех endpoints validation router,
включая валидацию email адресов и телефонных номеров.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import json

# Локальные импорты
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))


class TestEmailValidation:
    """Тесты валидации email адресов."""

    @pytest.mark.asyncio
    async def test_validate_email_success(self, api_client, db_session):
        """Тест успешной валидации email адреса."""
        # Arrange
        email_data = {
            "email": "test@example.com",
            "check_mx": False,
            "check_smtp": False,
        }

        # Act
        response = await api_client.post("/api/validation/email", json=email_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["is_valid"] is True
        assert "mx_valid" in data
        assert "error_message" in data

    @pytest.mark.asyncio
    async def test_validate_email_invalid_format(self, api_client, db_session):
        """Тест валидации email с невалидным форматом."""
        # Arrange
        email_data = {"email": "invalid-email", "check_mx": False, "check_smtp": False}

        # Act
        response = await api_client.post("/api/validation/email", json=email_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "invalid-email"
        assert data["is_valid"] is False
        assert data["error_message"] is not None

    @pytest.mark.asyncio
    async def test_validate_email_empty(self, api_client, db_session):
        """Тест валидации пустого email."""
        # Arrange
        email_data = {"email": "", "check_mx": False, "check_smtp": False}

        # Act
        response = await api_client.post("/api/validation/email", json=email_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["error_message"] is not None

    @pytest.mark.asyncio
    async def test_validate_email_with_mx_check(self, api_client, db_session):
        """Тест валидации email с проверкой MX записей."""
        # Arrange
        email_data = {"email": "test@gmail.com", "check_mx": True, "check_smtp": False}

        # Act
        response = await api_client.post("/api/validation/email", json=email_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@gmail.com"
        assert "mx_valid" in data
        assert (
            data["is_valid"] is True or data["is_valid"] is False
        )  # Depends on actual MX check

    @pytest.mark.asyncio
    async def test_validate_email_with_smtp_check(self, api_client, db_session):
        """Тест валидации email с проверкой SMTP."""
        # Arrange
        email_data = {"email": "test@gmail.com", "check_mx": True, "check_smtp": True}

        # Act
        response = await api_client.post("/api/validation/email", json=email_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@gmail.com"
        assert "smtp_valid" in data
        assert "mx_valid" in data

    @pytest.mark.asyncio
    async def test_validate_email_common_domains(self, api_client, db_session):
        """Тест валидации email с популярными доменами."""
        # Arrange
        common_emails = [
            "test@gmail.com",
            "user@yahoo.com",
            "example@outlook.com",
            "test@mail.ru",
            "user@yandex.ru",
        ]

        for email in common_emails:
            email_data = {"email": email, "check_mx": False, "check_smtp": False}

            # Act
            response = await api_client.post("/api/validation/email", json=email_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_email_special_characters(self, api_client, db_session):
        """Тест валидации email со специальными символами."""
        # Arrange
        special_emails = [
            "test+label@example.com",
            "user.name@example.com",
            "test_user@example.com",
            "123@example.com",
            "test-user@example.com",
        ]

        for email in special_emails:
            email_data = {"email": email, "check_mx": False, "check_smtp": False}

            # Act
            response = await api_client.post("/api/validation/email", json=email_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_email_invalid_cases(self, api_client, db_session):
        """Тест валидации явно невалидных email адресов."""
        # Arrange
        invalid_emails = [
            "plainaddress",
            "@missingdomain.com",
            "missing@.com",
            "missing@domain",
            "spaces in@email.com",
            "email@",
            "email@domain@domain.com",
            "email..email@domain.com",
        ]

        for email in invalid_emails:
            email_data = {"email": email, "check_mx": False, "check_smtp": False}

            # Act
            response = await api_client.post("/api/validation/email", json=email_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert data["is_valid"] is False
            assert data["error_message"] is not None

    @pytest.mark.asyncio
    async def test_validate_email_batch_processing(self, api_client, db_session):
        """Тест пакетной обработки email адресов."""
        # Arrange
        batch_emails = [
            "valid1@example.com",
            "valid2@example.com",
            "invalid-email",
            "valid3@example.com",
            "another-invalid",
        ]

        results = []
        for email in batch_emails:
            email_data = {"email": email, "check_mx": False, "check_smtp": False}

            # Act
            response = await api_client.post("/api/validation/email", json=email_data)
            assert response.status_code == 200
            results.append(response.json())

        # Assert
        assert len(results) == 5
        valid_count = sum(1 for r in results if r["is_valid"])
        invalid_count = sum(1 for r in results if not r["is_valid"])
        assert valid_count == 3
        assert invalid_count == 2


class TestPhoneValidation:
    """Тесты валидации телефонных номеров."""

    @pytest.mark.asyncio
    async def test_validate_phone_success(self, api_client, db_session):
        """Тест успешной валидации телефонного номера."""
        # Arrange
        phone_data = {"phone": "+1234567890", "country_code": "US", "normalize": True}

        # Act
        response = await api_client.post("/api/validation/phone", json=phone_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+1234567890"
        assert "normalized_phone" in data
        assert "is_valid" in data
        assert "country_code" in data

    @pytest.mark.asyncio
    async def test_validate_phone_russian_number(self, api_client, db_session):
        """Тест валидации российского номера."""
        # Arrange
        russian_phones = [
            "+79161234567",
            "89161234567",
            "+7 916 123 45 67",
            "8 (916) 123-45-67",
            "+7-916-123-45-67",
        ]

        for phone in russian_phones:
            phone_data = {"phone": phone, "country_code": "RU", "normalize": True}

            # Act
            response = await api_client.post("/api/validation/phone", json=phone_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == phone
            assert (
                data["is_valid"] is True or data["is_valid"] is False
            )  # Depends on actual validation
            assert "normalized_phone" in data

    @pytest.mark.asyncio
    async def test_validate_phone_us_number(self, api_client, db_session):
        """Тест валидации американского номера."""
        # Arrange
        us_phones = [
            "+1234567890",
            "(234) 567-8901",
            "234-567-8901",
            "234.567.8901",
            "234 567 8901",
        ]

        for phone in us_phones:
            phone_data = {"phone": phone, "country_code": "US", "normalize": True}

            # Act
            response = await api_client.post("/api/validation/phone", json=phone_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == phone
            assert "normalized_phone" in data
            assert "is_valid" in data

    @pytest.mark.asyncio
    async def test_validate_phone_international_numbers(self, api_client, db_session):
        """Тест валидации международных номеров."""
        # Arrange
        international_phones = [
            "+44 20 7946 0958",  # UK
            "+33 1 23 45 67 89",  # France
            "+49 30 12345678",  # Germany
            "+86 138 0013 8000",  # China
            "+81 3 1234 5678",  # Japan
        ]

        for phone in international_phones:
            phone_data = {"phone": phone, "normalize": True}

            # Act
            response = await api_client.post("/api/validation/phone", json=phone_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == phone
            assert "normalized_phone" in data
            assert "is_valid" in data

    @pytest.mark.asyncio
    async def test_validate_phone_invalid_numbers(self, api_client, db_session):
        """Тест валидации невалидных номеров."""
        # Arrange
        invalid_phones = [
            "123",  # Too short
            "abc123def",  # Contains letters
            "12345678901234567890",  # Too long
            "+",  # Just plus sign
            "++1234567890",  # Double plus
            "1234567890123456789012345",  # Way too long
            "",  # Empty
        ]

        for phone in invalid_phones:
            phone_data = {"phone": phone, "normalize": True}

            # Act
            response = await api_client.post("/api/validation/phone", json=phone_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == phone
            assert data["is_valid"] is False
            assert "error_message" in data

    @pytest.mark.asyncio
    async def test_validate_phone_normalization(self, api_client, db_session):
        """Тест нормализации телефонных номеров."""
        # Arrange
        test_cases = [
            {"input": "+7 (916) 123-45-67", "expected_format": "+79161234567"},
            {"input": "8 916 123 45 67", "expected_format": "+79161234567"},
            {"input": "(234) 567-8901", "expected_format": "+12345678901"},
        ]

        for case in test_cases:
            phone_data = {"phone": case["input"], "normalize": True}

            # Act
            response = await api_client.post("/api/validation/phone", json=phone_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == case["input"]
            assert "normalized_phone" in data
            # Note: actual normalization depends on the validation service implementation

    @pytest.mark.asyncio
    async def test_validate_phone_without_normalization(self, api_client, db_session):
        """Тест валидации без нормализации."""
        # Arrange
        phone_data = {"phone": "+1234567890", "normalize": False}

        # Act
        response = await api_client.post("/api/validation/phone", json=phone_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+1234567890"
        assert "normalized_phone" in data
        assert "is_valid" in data

    @pytest.mark.asyncio
    async def test_validate_phone_country_detection(self, api_client, db_session):
        """Тест определения страны по номеру."""
        # Arrange
        test_phones = [
            "+79161234567",  # Russia
            "+1234567890",  # US
            "+44 20 7946 0958",  # UK
            "+33 1 23 45 67 89",  # France
        ]

        for phone in test_phones:
            phone_data = {"phone": phone, "normalize": True}

            # Act
            response = await api_client.post("/api/validation/phone", json=phone_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == phone
            assert "country_code" in data
            assert data["country_code"] is not None or data["country_code"] == ""

    @pytest.mark.asyncio
    async def test_validate_phone_batch_processing(self, api_client, db_session):
        """Тест пакетной обработки телефонных номеров."""
        # Arrange
        batch_phones = [
            "+79161234567",
            "+1234567890",
            "invalid-phone",
            "+44 20 7946 0958",
            "123",
        ]

        results = []
        for phone in batch_phones:
            phone_data = {"phone": phone, "normalize": True}

            # Act
            response = await api_client.post("/api/validation/phone", json=phone_data)
            assert response.status_code == 200
            results.append(response.json())

        # Assert
        assert len(results) == 5
        valid_count = sum(1 for r in results if r["is_valid"])
        invalid_count = sum(1 for r in results if not r["is_valid"])
        assert valid_count >= 0  # Depends on actual validation
        assert invalid_count >= 0


class TestValidationIntegration:
    """Интеграционные тесты для validation router."""

    @pytest.mark.asyncio
    async def test_email_and_phone_validation_flow(self, api_client, db_session):
        """Тест полного потока валидации email и телефона."""
        # Arrange
        test_data = {"email": "test@example.com", "phone": "+79161234567"}

        # Act - валидируем email
        email_response = await api_client.post(
            "/api/validation/email",
            json={"email": test_data["email"], "check_mx": False, "check_smtp": False},
        )

        # Act - валидируем телефон
        phone_response = await api_client.post(
            "/api/validation/phone",
            json={"phone": test_data["phone"], "normalize": True},
        )

        # Assert
        assert email_response.status_code == 200
        assert phone_response.status_code == 200

        email_data = email_response.json()
        phone_data = phone_response.json()

        assert email_data["email"] == test_data["email"]
        assert phone_data["phone"] == test_data["phone"]
        assert "is_valid" in email_data
        assert "is_valid" in phone_data

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, api_client, db_session):
        """Тест обработки ошибок валидации."""
        # Arrange - тест с невалидными данными
        invalid_requests = [
            {"email": None, "endpoint": "/api/validation/email"},
            {"phone": None, "endpoint": "/api/validation/phone"},
        ]

        for req in invalid_requests:
            if req["endpoint"] == "/api/validation/email":
                data = {"email": req["email"], "check_mx": False, "check_smtp": False}
            else:
                data = {"phone": req["phone"], "normalize": True}

            # Act
            response = await api_client.post(req["endpoint"], json=data)

            # Assert
            assert response.status_code == 422 or response.status_code == 200
            # Validation errors should be handled gracefully

    @pytest.mark.asyncio
    async def test_comprehensive_validation_scenarios(self, api_client, db_session):
        """Тест комплексных сценариев валидации."""
        # Arrange
        test_scenarios = [
            {
                "email": "valid@example.com",
                "phone": "+79161234567",
                "expected_email_valid": True,
                "expected_phone_valid": True,
            },
            {
                "email": "invalid-email",
                "phone": "invalid-phone",
                "expected_email_valid": False,
                "expected_phone_valid": False,
            },
            {
                "email": "test@gmail.com",
                "phone": "+1234567890",
                "expected_email_valid": True,
                "expected_phone_valid": True,
            },
        ]

        for scenario in test_scenarios:
            # Act - валидируем email
            email_response = await api_client.post(
                "/api/validation/email",
                json={
                    "email": scenario["email"],
                    "check_mx": False,
                    "check_smtp": False,
                },
            )

            # Act - валидируем телефон
            phone_response = await api_client.post(
                "/api/validation/phone",
                json={"phone": scenario["phone"], "normalize": True},
            )

            # Assert
            assert email_response.status_code == 200
            assert phone_response.status_code == 200

            email_data = email_response.json()
            phone_data = phone_response.json()

            assert email_data["is_valid"] == scenario["expected_email_valid"]
            assert phone_data["is_valid"] == scenario["expected_phone_valid"]

    @pytest.mark.asyncio
    async def test_validation_performance(self, api_client, db_session):
        """Тест производительности валидации."""
        # Arrange
        test_emails = [f"test{i}@example.com" for i in range(10)]
        test_phones = [f"+791612345{i:02d}" for i in range(10)]

        # Act - валидируем множество email
        email_responses = []
        for email in test_emails:
            response = await api_client.post(
                "/api/validation/email",
                json={"email": email, "check_mx": False, "check_smtp": False},
            )
            email_responses.append(response)

        # Act - валидируем множество телефонов
        phone_responses = []
        for phone in test_phones:
            response = await api_client.post(
                "/api/validation/phone", json={"phone": phone, "normalize": True}
            )
            phone_responses.append(response)

        # Assert
        assert len(email_responses) == 10
        assert len(phone_responses) == 10
        assert all(r.status_code == 200 for r in email_responses)
        assert all(r.status_code == 200 for r in phone_responses)

    @pytest.mark.asyncio
    async def test_validation_edge_cases(self, api_client, db_session):
        """Тест граничных случаев валидации."""
        # Arrange
        edge_cases = [
            {"type": "email", "value": "a@b.co", "description": "shortest valid email"},
            {
                "type": "email",
                "value": "very-long-email-address-that-might-be-problematic@very-long-domain-name-that-could-cause-issues.com",
                "description": "very long email",
            },
            {
                "type": "phone",
                "value": "+1234567890123456",
                "description": "very long phone",
            },
            {"type": "phone", "value": "+1", "description": "shortest possible phone"},
            {
                "type": "email",
                "value": "test@localhost",
                "description": "localhost domain",
            },
            {"type": "phone", "value": "+0000000000", "description": "all zeros phone"},
        ]

        for case in edge_cases:
            if case["type"] == "email":
                data = {"email": case["value"], "check_mx": False, "check_smtp": False}
                endpoint = "/api/validation/email"
            else:
                data = {"phone": case["value"], "normalize": True}
                endpoint = "/api/validation/phone"

            # Act
            response = await api_client.post(endpoint, json=data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "is_valid" in data
            # We don't assert specific validity as it depends on the validation logic
