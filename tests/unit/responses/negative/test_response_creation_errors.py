"""
Negative тесты для создания ответов на вопросы опросов.

Тестирует обработку ошибок при создании ответов:
- Валидационные ошибки
- Ошибки прав доступа
- Несуществующие сущности
- Дублирование ответов
- Неправильные форматы данных
- Превышение лимитов
"""

import pytest
from typing import Dict, Any
from unittest.mock import patch


class TestResponseCreationValidationErrors:
    """Тесты валидационных ошибок при создании ответов."""

    async def test_create_response_missing_required_fields(
        self, api_client, sample_question
    ):
        """Тест создания ответа с отсутствующими обязательными полями."""
        url = api_client.url_for("create_response")

        # Отсутствует question_id
        response_data = {
            "user_session_id": "test_session",
            "answer": {"value": "Test response"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "question_id" in data["validation_error"]["missing_fields"]

    async def test_create_response_invalid_question_id(self, api_client):
        """Тест создания ответа с несуществующим question_id."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": "non_existent_id",
            "user_session_id": "test_session",
            "answer": {"value": "Test response"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "question not found" in data["error"].lower()

    async def test_create_response_empty_answer(self, api_client, sample_question):
        """Тест создания ответа с пустым answer."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session",
            "answer": {},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "answer" in data["validation_error"]["field_errors"]

    async def test_create_response_invalid_json_structure(
        self, api_client, sample_question
    ):
        """Тест создания ответа с неправильной JSON структурой."""
        url = api_client.url_for("create_response")

        # Неправильная структура данных
        response_data = "invalid json string"

        response = await api_client.post(url, data=response_data)
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "json" in data["error"].lower()

    async def test_create_response_too_long_session_id(
        self, api_client, sample_question
    ):
        """Тест создания ответа со слишком длинным session_id."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "x" * 1000,  # Слишком длинный session_id
            "answer": {"value": "Test response"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "user_session_id" in data["validation_error"]["field_errors"]


class TestRatingResponseValidationErrors:
    """Тесты валидационных ошибок рейтинговых ответов."""

    async def test_create_rating_response_invalid_rating(
        self, api_client, rating_response
    ):
        """Тест создания рейтингового ответа с неправильным рейтингом."""
        url = api_client.url_for("create_response")

        invalid_ratings = [0, 6, -1, 10, "invalid"]

        for rating in invalid_ratings:
            response_data = {
                "question_id": rating_response.question_id,
                "user_session_id": f"test_session_{rating}",
                "answer": {"rating": rating},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 422

            data = response.json()
            assert "validation_error" in data
            assert "rating" in data["validation_error"]["field_errors"]

    async def test_create_rating_response_missing_rating(
        self, api_client, rating_response
    ):
        """Тест создания рейтингового ответа без рейтинга."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": rating_response.question_id,
            "user_session_id": "test_session",
            "answer": {"comment": "Great service"},  # Нет рейтинга
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "rating" in data["validation_error"]["missing_fields"]

    async def test_create_rating_response_non_numeric_rating(
        self, api_client, rating_response
    ):
        """Тест создания рейтингового ответа с нечисловым рейтингом."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": rating_response.question_id,
            "user_session_id": "test_session",
            "answer": {"rating": "five"},  # Строка вместо числа
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "rating" in data["validation_error"]["field_errors"]


class TestEmailResponseValidationErrors:
    """Тесты валидационных ошибок email ответов."""

    async def test_create_email_response_invalid_email(
        self, api_client, email_response
    ):
        """Тест создания email ответа с неправильным email."""
        url = api_client.url_for("create_response")

        invalid_emails = [
            "invalid-email",
            "missing-at-symbol.com",
            "@missing-local-part.com",
            "missing-domain@.com",
            "spaces in@email.com",
            "toolong" + "x" * 100 + "@example.com",
        ]

        for email in invalid_emails:
            response_data = {
                "question_id": email_response.question_id,
                "user_session_id": f"test_session_{hash(email)}",
                "answer": {"email": email},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 422

            data = response.json()
            assert "validation_error" in data
            assert "email" in data["validation_error"]["field_errors"]

    async def test_create_email_response_missing_email(
        self, api_client, email_response
    ):
        """Тест создания email ответа без email."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": email_response.question_id,
            "user_session_id": "test_session",
            "answer": {},  # Пустой answer
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "email" in data["validation_error"]["missing_fields"]

    async def test_create_email_response_empty_email(self, api_client, email_response):
        """Тест создания email ответа с пустым email."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": email_response.question_id,
            "user_session_id": "test_session",
            "answer": {"email": ""},  # Пустой email
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "email" in data["validation_error"]["field_errors"]


class TestPhoneResponseValidationErrors:
    """Тесты валидационных ошибок телефонных ответов."""

    async def test_create_phone_response_invalid_phone(
        self, api_client, phone_response
    ):
        """Тест создания телефонного ответа с неправильным номером."""
        url = api_client.url_for("create_response")

        invalid_phones = [
            "invalid-phone",
            "123",  # Слишком короткий
            "x" * 50,  # Слишком длинный
            "++1234567890",  # Двойной +
            "1234567890++",  # + в конце
            "phone number",  # Текст
        ]

        for phone in invalid_phones:
            response_data = {
                "question_id": phone_response.question_id,
                "user_session_id": f"test_session_{hash(phone)}",
                "answer": {"phone": phone},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 422

            data = response.json()
            assert "validation_error" in data
            assert "phone" in data["validation_error"]["field_errors"]

    async def test_create_phone_response_missing_phone(
        self, api_client, phone_response
    ):
        """Тест создания телефонного ответа без номера."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": phone_response.question_id,
            "user_session_id": "test_session",
            "answer": {},  # Пустой answer
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "phone" in data["validation_error"]["missing_fields"]


class TestMultipleChoiceValidationErrors:
    """Тесты валидационных ошибок множественного выбора."""

    async def test_create_choice_response_invalid_choice(
        self, api_client, multiple_choice_response
    ):
        """Тест создания ответа с неправильным вариантом выбора."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": multiple_choice_response.question_id,
            "user_session_id": "test_session",
            "answer": {"choices": ["Invalid Option"]},  # Несуществующий вариант
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "choices" in data["validation_error"]["field_errors"]

    async def test_create_choice_response_empty_choices(
        self, api_client, multiple_choice_response
    ):
        """Тест создания ответа с пустым списком выборов."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": multiple_choice_response.question_id,
            "user_session_id": "test_session",
            "answer": {"choices": []},  # Пустой список
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "choices" in data["validation_error"]["field_errors"]

    async def test_create_choice_response_too_many_choices(
        self, api_client, multiple_choice_response
    ):
        """Тест создания ответа с слишком многими вариантами."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": multiple_choice_response.question_id,
            "user_session_id": "test_session",
            "answer": {
                "choices": ["Option 1", "Option 2", "Option 3"] * 10
            },  # Слишком много
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "choices" in data["validation_error"]["field_errors"]


class TestLocationResponseValidationErrors:
    """Тесты валидационных ошибок геолокационных ответов."""

    async def test_create_location_response_invalid_coordinates(
        self, api_client, location_response
    ):
        """Тест создания геолокационного ответа с неправильными координатами."""
        url = api_client.url_for("create_response")

        invalid_coordinates = [
            {"latitude": 91, "longitude": 0},  # Latitude > 90
            {"latitude": -91, "longitude": 0},  # Latitude < -90
            {"latitude": 0, "longitude": 181},  # Longitude > 180
            {"latitude": 0, "longitude": -181},  # Longitude < -180
            {"latitude": "invalid", "longitude": 0},  # Нечисловая широта
            {"latitude": 0, "longitude": "invalid"},  # Нечисловая долгота
        ]

        for coords in invalid_coordinates:
            response_data = {
                "question_id": location_response.question_id,
                "user_session_id": f"test_session_{hash(str(coords))}",
                "answer": coords,
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 422

            data = response.json()
            assert "validation_error" in data

    async def test_create_location_response_missing_coordinates(
        self, api_client, location_response
    ):
        """Тест создания геолокационного ответа без координат."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": location_response.question_id,
            "user_session_id": "test_session",
            "answer": {"address": "Some address"},  # Только адрес, без координат
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "latitude" in data["validation_error"]["missing_fields"]
        assert "longitude" in data["validation_error"]["missing_fields"]


class TestFileUploadValidationErrors:
    """Тесты валидационных ошибок файловых ответов."""

    async def test_create_file_upload_response_invalid_file_type(
        self, api_client, file_upload_response
    ):
        """Тест создания файлового ответа с неправильным типом файла."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": file_upload_response.question_id,
            "user_session_id": "test_session",
            "answer": {
                "file_id": "file_123",
                "filename": "virus.exe",  # Неразрешенный тип файла
                "content_type": "application/executable",
            },
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "content_type" in data["validation_error"]["field_errors"]

    async def test_create_file_upload_response_file_too_large(
        self, api_client, file_upload_response
    ):
        """Тест создания файлового ответа со слишком большим файлом."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": file_upload_response.question_id,
            "user_session_id": "test_session",
            "answer": {
                "file_id": "file_123",
                "filename": "huge_file.pdf",
                "file_size": 100 * 1024 * 1024,  # 100MB
                "content_type": "application/pdf",
            },
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "file_size" in data["validation_error"]["field_errors"]

    async def test_create_file_upload_response_missing_file_id(
        self, api_client, file_upload_response
    ):
        """Тест создания файлового ответа без file_id."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": file_upload_response.question_id,
            "user_session_id": "test_session",
            "answer": {
                "filename": "document.pdf",
                "content_type": "application/pdf",
                # Отсутствует file_id
            },
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "file_id" in data["validation_error"]["missing_fields"]


class TestResponseAccessErrors:
    """Тесты ошибок доступа при создании ответов."""

    async def test_create_response_on_closed_survey(self, api_client, sample_question):
        """Тест создания ответа на закрытый опрос."""
        url = api_client.url_for("create_response")

        # Предполагаем, что опрос закрыт
        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session",
            "answer": {"value": "Response to closed survey"},
        }

        with patch(
            "apps.surveys.services.SurveyService.is_survey_active", return_value=False
        ):
            response = await api_client.post(url, json=response_data)
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert "closed" in data["error"].lower()

    async def test_create_response_on_private_survey_unauthorized(
        self, api_client, sample_question
    ):
        """Тест создания ответа на приватный опрос без авторизации."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session",
            "answer": {"value": "Response to private survey"},
        }

        with patch(
            "apps.surveys.services.SurveyService.is_survey_public", return_value=False
        ):
            response = await api_client.post(url, json=response_data)
            assert response.status_code == 401

            data = response.json()
            assert "error" in data
            assert "unauthorized" in data["error"].lower()

    async def test_create_duplicate_response_same_session(
        self, api_client, sample_question
    ):
        """Тест создания дублирующего ответа в той же сессии."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_duplicate",
            "answer": {"value": "First response"},
        }

        # Создаем первый ответ
        first_response = await api_client.post(url, json=response_data)
        assert first_response.status_code == 201

        # Пытаемся создать второй ответ с тем же session_id
        response_data["answer"]["value"] = "Second response"

        second_response = await api_client.post(url, json=response_data)
        assert second_response.status_code == 409

        data = second_response.json()
        assert "error" in data
        assert "duplicate" in data["error"].lower()

    async def test_create_response_exceeded_rate_limit(
        self, api_client, sample_question
    ):
        """Тест создания ответа при превышении лимита запросов."""
        url = api_client.url_for("create_response")

        # Симулируем превышение лимита
        with patch("core.middleware.rate_limit.check_rate_limit", return_value=False):
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": "test_session",
                "answer": {"value": "Rate limited response"},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 429

            data = response.json()
            assert "error" in data
            assert "rate limit" in data["error"].lower()


class TestResponseDataSizeErrors:
    """Тесты ошибок размера данных при создании ответов."""

    async def test_create_response_too_large_answer(self, api_client, sample_question):
        """Тест создания ответа со слишком большим ответом."""
        url = api_client.url_for("create_response")

        # Создаем очень большой ответ
        large_answer = "x" * 100000  # 100KB текста

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session",
            "answer": {"value": large_answer},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 413

        data = response.json()
        assert "error" in data
        assert "too large" in data["error"].lower()

    async def test_create_response_too_many_metadata_fields(
        self, api_client, sample_question
    ):
        """Тест создания ответа со слишком многими метаданными."""
        url = api_client.url_for("create_response")

        # Создаем слишком много метаданных
        metadata = {f"field_{i}": f"value_{i}" for i in range(1000)}

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session",
            "answer": {"value": "Response with too much metadata"},
            "metadata": metadata,
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "metadata" in data["validation_error"]["field_errors"]
