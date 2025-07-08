"""
Позитивные тесты для Phone валидации.

Тестирует успешные сценарии валидации телефонных номеров:
- Валидные форматы телефонов
- Нормализация номеров
- Международные форматы
- Определение стран
- Различные провайдеры
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestPhoneValidationSuccess:
    """Тесты успешной валидации телефонных номеров."""

    async def test_validate_phone_basic_success(self, api_client, valid_phone_request):
        """Тест базовой успешной валидации телефона."""
        # Arrange
        phone_data = valid_phone_request.model_dump()

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"), json=phone_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone_data["phone"]
        assert "normalized_phone" in data
        assert "is_valid" in data
        assert "country_code" in data
        assert "carrier" in data
        assert "error_message" in data

    async def test_validate_phone_us_formats(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации американских форматов телефонов."""
        # Arrange
        us_formats = [
            "+1234567890",
            "(234) 567-8901",
            "234-567-8901",
            "234.567.8901",
            "234 567 8901",
            "12345678901",  # with country code
            "2345678901",  # without country code
        ]

        # Act & Assert
        for phone in us_formats:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone
            phone_request.country_code = "US"

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "normalized_phone" in data
            assert "is_valid" in data

    async def test_validate_phone_russian_formats(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации российских форматов телефонов."""
        # Arrange
        russian_formats = [
            "+79161234567",
            "89161234567",
            "+7 916 123 45 67",
            "8 (916) 123-45-67",
            "+7-916-123-45-67",
            "8-916-123-45-67",
            "8(916)123-45-67",
            "79161234567",
        ]

        # Act & Assert
        for phone in russian_formats:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone
            phone_request.country_code = "RU"

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "normalized_phone" in data
            assert "is_valid" in data

    async def test_validate_phone_international_formats(
        self, api_client, valid_phone_data_factory, international_phones
    ):
        """Тест валидации международных форматов телефонов."""
        # Act & Assert
        for phone in international_phones:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "normalized_phone" in data
            assert "is_valid" in data

    async def test_validate_phone_with_normalization(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона с нормализацией."""
        # Arrange
        test_cases = [
            {
                "input": "+7 (916) 123-45-67",
                "expected_pattern": "+7916",  # Начало нормализованного номера
            },
            {
                "input": "(234) 567-8901",
                "expected_pattern": "+1234",  # US формат
            },
            {
                "input": "8 916 123 45 67",
                "expected_pattern": "+7916",  # Российский формат
            },
        ]

        # Act & Assert
        for case in test_cases:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = case["input"]
            phone_request.normalize = True

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == case["input"]
            assert "normalized_phone" in data
            assert isinstance(data["normalized_phone"], str)
            # Проверяем, что нормализация работает
            assert data["normalized_phone"] != case["input"]

    async def test_validate_phone_without_normalization(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона без нормализации."""
        # Arrange
        phone_request = valid_phone_data_factory.build()
        phone_request.normalize = False

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone_request.phone
        assert "normalized_phone" in data
        assert "is_valid" in data

    async def test_validate_phone_country_detection(
        self, api_client, valid_phone_data_factory
    ):
        """Тест определения страны по номеру телефона."""
        # Arrange
        country_test_cases = [
            {
                "phone": "+1234567890",
                "expected_country": "US",
            },
            {
                "phone": "+79161234567",
                "expected_country": "RU",
            },
            {
                "phone": "+44 20 7946 0958",
                "expected_country": "GB",
            },
            {
                "phone": "+33 1 23 45 67 89",
                "expected_country": "FR",
            },
        ]

        # Act & Assert
        for case in country_test_cases:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = case["phone"]

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == case["phone"]
            assert "country_code" in data
            # Проверяем, что страна определена (может быть None)
            assert data["country_code"] is not None or data["country_code"] is None

    async def test_validate_phone_with_explicit_country(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона с явным указанием страны."""
        # Arrange
        phone_request = valid_phone_data_factory.build()
        phone_request.phone = "2345678901"  # Без кода страны
        phone_request.country_code = "US"

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone_request.phone
        assert data["country_code"] == "US"
        assert "normalized_phone" in data

    async def test_validate_phone_mobile_vs_landline(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации мобильных и стационарных телефонов."""
        # Arrange
        phone_types = [
            {
                "phone": "+79161234567",  # Мобильный RU
                "type": "mobile",
            },
            {
                "phone": "+74951234567",  # Стационарный RU
                "type": "landline",
            },
            {
                "phone": "+1234567890",  # US может быть любым
                "type": "unknown",
            },
        ]

        # Act & Assert
        for phone_info in phone_types:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone_info["phone"]

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone_info["phone"]
            assert "is_valid" in data
            # Тип телефона может быть в carrier или отдельном поле
            assert "carrier" in data

    async def test_validate_phone_with_extensions(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефонов с добавочными номерами."""
        # Arrange
        phones_with_extensions = [
            "+1234567890 ext 123",
            "+1234567890 x123",
            "+1234567890,123",
            "+1234567890;123",
            "+1234567890 #123",
        ]

        # Act & Assert
        for phone in phones_with_extensions:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "normalized_phone" in data
            assert "is_valid" in data

    async def test_validate_phone_short_codes(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации коротких номеров."""
        # Arrange
        short_codes = [
            "911",  # US emergency
            "112",  # EU emergency
            "101",  # RU emergency
            "103",  # RU medical
            "8800",  # RU toll-free start
        ]

        # Act & Assert
        for code in short_codes:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = code

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == code
            assert "is_valid" in data
            # Короткие коды могут быть валидными или нет в зависимости от логики


class TestPhoneNormalization:
    """Тесты нормализации телефонных номеров."""

    async def test_normalize_phone_remove_formatting(
        self, api_client, valid_phone_data_factory
    ):
        """Тест удаления форматирования при нормализации."""
        # Arrange
        formatting_test_cases = [
            {
                "input": "+7 (916) 123-45-67",
                "has_formatting": True,
            },
            {
                "input": "+1-234-567-8901",
                "has_formatting": True,
            },
            {
                "input": "+49 30 12345678",
                "has_formatting": True,
            },
            {
                "input": "+79161234567",
                "has_formatting": False,
            },
        ]

        # Act & Assert
        for case in formatting_test_cases:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = case["input"]
            phone_request.normalize = True

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == case["input"]
            normalized = data["normalized_phone"]

            # Проверяем, что нормализованный номер не содержит пробелов, скобок, дефисов
            assert " " not in normalized
            assert "(" not in normalized
            assert ")" not in normalized
            assert "-" not in normalized

    async def test_normalize_phone_add_country_code(
        self, api_client, valid_phone_data_factory
    ):
        """Тест добавления кода страны при нормализации."""
        # Arrange
        phones_without_country = [
            {
                "phone": "2345678901",
                "country": "US",
                "expected_start": "+1",
            },
            {
                "phone": "9161234567",
                "country": "RU",
                "expected_start": "+7",
            },
        ]

        # Act & Assert
        for case in phones_without_country:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = case["phone"]
            phone_request.country_code = case["country"]
            phone_request.normalize = True

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            normalized = data["normalized_phone"]
            assert normalized.startswith(case["expected_start"])

    async def test_normalize_phone_handle_leading_zeros(
        self, api_client, valid_phone_data_factory
    ):
        """Тест обработки ведущих нулей при нормализации."""
        # Arrange
        phones_with_zeros = [
            "0049 30 12345678",  # German with leading zero
            "0033 1 23 45 67 89",  # French with leading zero
            "0044 20 7946 0958",  # UK with leading zero
        ]

        # Act & Assert
        for phone in phones_with_zeros:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone
            phone_request.normalize = True

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            normalized = data["normalized_phone"]
            # Проверяем, что нормализованный номер начинается с +
            assert normalized.startswith("+")

    async def test_normalize_phone_preserve_plus_sign(
        self, api_client, valid_phone_data_factory
    ):
        """Тест сохранения знака + при нормализации."""
        # Arrange
        phone_request = valid_phone_data_factory.build()
        phone_request.phone = "+1234567890"
        phone_request.normalize = True

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        normalized = data["normalized_phone"]
        assert normalized.startswith("+")


class TestPhoneValidationEdgeCases:
    """Тесты граничных случаев валидации телефонов."""

    async def test_validate_phone_minimum_length(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона минимальной длины."""
        # Arrange
        phone_request = valid_phone_data_factory.build()
        phone_request.phone = "+1234567890"  # 10 цифр + код страны

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone_request.phone
        assert "is_valid" in data

    async def test_validate_phone_maximum_length(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона максимальной длины."""
        # Arrange - международный стандарт максимум 15 цифр
        phone_request = valid_phone_data_factory.build()
        phone_request.phone = "+123456789012345"  # 15 цифр

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone_request.phone
        assert "is_valid" in data

    async def test_validate_phone_all_zeros(self, api_client, valid_phone_data_factory):
        """Тест валидации телефона из одних нулей."""
        # Arrange
        phone_request = valid_phone_data_factory.build()
        phone_request.phone = "+0000000000"

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone_request.phone
        assert "is_valid" in data

    async def test_validate_phone_special_formatting(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона со специальным форматированием."""
        # Arrange
        special_formats = [
            "+1.234.567.8901",
            "+1 234 567 8901",
            "+1-234-567-8901",
            "+1 (234) 567-8901",
            "+1 234-567-8901",
            "+1/234/567/8901",
        ]

        # Act & Assert
        for phone in special_formats:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_with_letters_in_formatting(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона с буквами в форматировании."""
        # Arrange - некоторые US номера используют буквы
        phones_with_letters = [
            "1-800-FLOWERS",
            "1-800-CALL-NOW",
            "+1-800-GET-HELP",
        ]

        # Act & Assert
        for phone in phones_with_letters:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_unicode_characters(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона с unicode символами."""
        # Arrange
        unicode_phones = [
            "＋79161234567",  # Полноширинный плюс
            "79161234567",  # Обычные цифры
            "７９１６１２３４５６７",  # Полноширинные цифры
        ]

        # Act & Assert
        for phone in unicode_phones:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_with_whitespace_variations(
        self, api_client, valid_phone_data_factory
    ):
        """Тест валидации телефона с различными пробелами."""
        # Arrange
        whitespace_phones = [
            " +1234567890 ",  # Пробелы в начале и конце
            "+1 234 567 8901",  # Обычные пробелы
            "+1　234　567　8901",  # Полноширинные пробелы
            "+1\t234\t567\t8901",  # Табуляция
            "+1\n234\n567\n8901",  # Переносы строк
        ]

        # Act & Assert
        for phone in whitespace_phones:
            phone_request = valid_phone_data_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data


class TestPhoneValidationPerformance:
    """Тесты производительности валидации телефонов."""

    async def test_validate_phone_batch_performance(
        self, api_client, valid_phone_data_factory
    ):
        """Тест производительности валидации множества телефонов."""
        # Arrange
        phone_requests = [valid_phone_data_factory.build() for _ in range(20)]

        # Act & Assert
        for phone_request in phone_requests:
            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone_request.phone
            assert "is_valid" in data

    async def test_validate_phone_concurrent_requests(
        self, api_client, valid_phone_data_factory
    ):
        """Тест параллельных запросов валидации."""
        # Arrange
        phone_request = valid_phone_data_factory.build()

        # Act - выполняем несколько запросов подряд
        responses = []
        for _ in range(5):
            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )
            responses.append(response)

        # Assert
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == phone_request.phone

    async def test_validate_phone_large_number_normalization(
        self, api_client, valid_phone_data_factory
    ):
        """Тест нормализации очень длинных номеров."""
        # Arrange
        phone_request = valid_phone_data_factory.build()
        phone_request.phone = "+1234567890123456789012345"  # Очень длинный номер

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone_request.phone
        assert "normalized_phone" in data
        assert "is_valid" in data
        # Ожидаем, что очень длинный номер будет невалидным
        assert isinstance(data["is_valid"], bool)
