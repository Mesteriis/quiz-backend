"""
Positive тесты для создания ответов на вопросы опросов.

Тестирует успешное создание различных типов ответов:
- Текстовые ответы
- Рейтинговые ответы
- Ответы да/нет
- Email ответы
- Телефонные ответы
- Ответы множественного выбора
- Геолокационные ответы
- Файловые ответы
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch


class TestTextResponseCreation:
    """Тесты создания текстовых ответов."""

    async def test_create_text_response_success(
        self, api_client, sample_question, valid_text_response_data, response_test_utils
    ):
        """Тест успешного создания текстового ответа."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_123",
            "answer": {"value": "This is a valid text response"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        await response_test_utils.assert_response_structure(data)
        assert data["question_id"] == sample_question.id
        assert data["answer"]["value"] == "This is a valid text response"

    async def test_create_long_text_response(
        self, api_client, sample_question, response_test_utils
    ):
        """Тест создания длинного текстового ответа."""
        url = api_client.url_for("create_response")

        long_text = "A" * 1000  # 1000 символов
        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_long",
            "answer": {"value": long_text},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["value"] == long_text
        assert len(data["answer"]["value"]) == 1000

    async def test_create_text_response_with_html(
        self, api_client, sample_question, response_test_utils
    ):
        """Тест создания текстового ответа с HTML содержимым."""
        url = api_client.url_for("create_response")

        html_content = "<p>This is <b>bold</b> text with <a href='#'>link</a></p>"
        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_html",
            "answer": {"value": html_content},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["value"] == html_content

    async def test_create_text_response_with_emoji(
        self, api_client, sample_question, unicode_response_data
    ):
        """Тест создания текстового ответа с эмодзи."""
        url = api_client.url_for("create_response")

        emoji_text = "Great service! 😊👍 Very satisfied 🌟"
        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_emoji",
            "answer": {"value": emoji_text},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["value"] == emoji_text


class TestRatingResponseCreation:
    """Тесты создания рейтинговых ответов."""

    async def test_create_rating_response_success(
        self, api_client, rating_response, valid_rating_response_data
    ):
        """Тест успешного создания рейтингового ответа."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": rating_response.question_id,
            "user_session_id": "test_rating_session",
            "answer": {"rating": 5},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["rating"] == 5
        assert 1 <= data["answer"]["rating"] <= 5

    async def test_create_rating_response_all_values(
        self, api_client, rating_response, boundary_rating_response_data
    ):
        """Тест создания рейтинговых ответов для всех допустимых значений."""
        url = api_client.url_for("create_response")

        for rating in [1, 2, 3, 4, 5]:
            response_data = {
                "question_id": rating_response.question_id,
                "user_session_id": f"test_rating_session_{rating}",
                "answer": {"rating": rating},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

            data = response.json()
            assert data["answer"]["rating"] == rating

    async def test_create_rating_response_with_comment(
        self, api_client, rating_response
    ):
        """Тест создания рейтингового ответа с комментарием."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": rating_response.question_id,
            "user_session_id": "test_rating_with_comment",
            "answer": {"rating": 4, "comment": "Good service, but could be better"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["rating"] == 4
        assert data["answer"]["comment"] == "Good service, but could be better"


class TestYesNoResponseCreation:
    """Тесты создания ответов да/нет."""

    async def test_create_yes_no_response_yes(
        self, api_client, yes_no_response, valid_yes_no_response_data
    ):
        """Тест создания ответа 'да'."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": yes_no_response.question_id,
            "user_session_id": "test_yes_session",
            "answer": {"value": True},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["value"] is True

    async def test_create_yes_no_response_no(self, api_client, yes_no_response):
        """Тест создания ответа 'нет'."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": yes_no_response.question_id,
            "user_session_id": "test_no_session",
            "answer": {"value": False},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["value"] is False


class TestEmailResponseCreation:
    """Тесты создания email ответов."""

    async def test_create_email_response_success(
        self, api_client, email_response, valid_email_response_data
    ):
        """Тест успешного создания email ответа."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": email_response.question_id,
            "user_session_id": "test_email_session",
            "answer": {"email": "test@example.com"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["email"] == "test@example.com"

    async def test_create_email_response_various_formats(
        self, api_client, email_response
    ):
        """Тест создания email ответов различных форматов."""
        url = api_client.url_for("create_response")

        valid_emails = [
            "simple@example.com",
            "very.common@example.com",
            "disposable.style.email.with+symbol@example.com",
            "user.name+tag@example.com",
            "x@example.com",
            "example@s.example",
        ]

        for idx, email in enumerate(valid_emails):
            response_data = {
                "question_id": email_response.question_id,
                "user_session_id": f"test_email_session_{idx}",
                "answer": {"email": email},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

            data = response.json()
            assert data["answer"]["email"] == email


class TestPhoneResponseCreation:
    """Тесты создания телефонных ответов."""

    async def test_create_phone_response_success(
        self, api_client, phone_response, valid_phone_response_data
    ):
        """Тест успешного создания телефонного ответа."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": phone_response.question_id,
            "user_session_id": "test_phone_session",
            "answer": {"phone": "+1234567890"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["phone"] == "+1234567890"

    async def test_create_phone_response_various_formats(
        self, api_client, phone_response
    ):
        """Тест создания телефонных ответов различных форматов."""
        url = api_client.url_for("create_response")

        valid_phones = [
            "+1234567890",
            "+1-234-567-890",
            "+1 (234) 567-890",
            "+44 20 7946 0958",
            "+7 (495) 123-45-67",
            "+33 1 42 86 83 26",
        ]

        for idx, phone in enumerate(valid_phones):
            response_data = {
                "question_id": phone_response.question_id,
                "user_session_id": f"test_phone_session_{idx}",
                "answer": {"phone": phone},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

            data = response.json()
            assert data["answer"]["phone"] == phone


class TestMultipleChoiceResponseCreation:
    """Тесты создания ответов множественного выбора."""

    async def test_create_single_choice_response(
        self, api_client, multiple_choice_response, valid_choice_response_data
    ):
        """Тест создания ответа с одним выбором."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": multiple_choice_response.question_id,
            "user_session_id": "test_single_choice_session",
            "answer": {"choices": ["Option 1"]},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["choices"] == ["Option 1"]

    async def test_create_multiple_choice_response(
        self, api_client, multiple_choice_response
    ):
        """Тест создания ответа с множественным выбором."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": multiple_choice_response.question_id,
            "user_session_id": "test_multiple_choice_session",
            "answer": {"choices": ["Option 1", "Option 3"]},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert set(data["answer"]["choices"]) == {"Option 1", "Option 3"}


class TestLocationResponseCreation:
    """Тесты создания геолокационных ответов."""

    async def test_create_location_response_success(
        self, api_client, location_response, valid_location_response_data
    ):
        """Тест успешного создания геолокационного ответа."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": location_response.question_id,
            "user_session_id": "test_location_session",
            "answer": {
                "latitude": 55.7558,
                "longitude": 37.6176,
                "address": "Moscow, Russia",
            },
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["latitude"] == 55.7558
        assert data["answer"]["longitude"] == 37.6176
        assert data["answer"]["address"] == "Moscow, Russia"

    async def test_create_location_response_coordinates_only(
        self, api_client, location_response
    ):
        """Тест создания геолокационного ответа только с координатами."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": location_response.question_id,
            "user_session_id": "test_location_coords_session",
            "answer": {"latitude": 51.5074, "longitude": -0.1278},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["latitude"] == 51.5074
        assert data["answer"]["longitude"] == -0.1278


class TestFileUploadResponseCreation:
    """Тесты создания файловых ответов."""

    @patch("core.storage.file_storage.upload_file")
    async def test_create_file_upload_response_success(
        self, mock_upload_file, api_client, file_upload_response, mock_file_storage
    ):
        """Тест успешного создания файлового ответа."""
        mock_upload_file.return_value = {
            "file_id": "file_123",
            "file_url": "https://storage.example.com/file_123",
            "file_size": 1024,
        }

        url = api_client.url_for("create_response")

        response_data = {
            "question_id": file_upload_response.question_id,
            "user_session_id": "test_file_session",
            "answer": {
                "file_id": "file_123",
                "filename": "document.pdf",
                "file_size": 1024,
                "content_type": "application/pdf",
            },
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["file_id"] == "file_123"
        assert data["answer"]["filename"] == "document.pdf"
        assert data["answer"]["file_size"] == 1024

    @patch("core.storage.file_storage.upload_file")
    async def test_create_multiple_file_upload_response(
        self, mock_upload_file, api_client, file_upload_response
    ):
        """Тест создания ответа с несколькими файлами."""
        mock_upload_file.return_value = {
            "file_id": "file_456",
            "file_url": "https://storage.example.com/file_456",
            "file_size": 2048,
        }

        url = api_client.url_for("create_response")

        response_data = {
            "question_id": file_upload_response.question_id,
            "user_session_id": "test_multi_file_session",
            "answer": {
                "files": [
                    {
                        "file_id": "file_123",
                        "filename": "document1.pdf",
                        "file_size": 1024,
                        "content_type": "application/pdf",
                    },
                    {
                        "file_id": "file_456",
                        "filename": "document2.txt",
                        "file_size": 2048,
                        "content_type": "text/plain",
                    },
                ]
            },
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert len(data["answer"]["files"]) == 2
        assert data["answer"]["files"][0]["filename"] == "document1.pdf"
        assert data["answer"]["files"][1]["filename"] == "document2.txt"


class TestAnonymousResponseCreation:
    """Тесты создания анонимных ответов."""

    async def test_create_anonymous_response_success(
        self, api_client, anonymous_response, response_test_utils
    ):
        """Тест успешного создания анонимного ответа."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": anonymous_response.question_id,
            "user_session_id": "anonymous_session_123",
            "answer": {"value": "Anonymous response"},
            "is_anonymous": True,
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        await response_test_utils.assert_response_structure(data)
        assert data["is_anonymous"] is True
        assert "user_id" not in data or data["user_id"] is None


class TestAuthenticatedResponseCreation:
    """Тесты создания аутентифицированных ответов."""

    async def test_create_authenticated_response_success(
        self, api_client, authenticated_response, regular_user, response_test_utils
    ):
        """Тест успешного создания аутентифицированного ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("create_response")

        response_data = {
            "question_id": authenticated_response.question_id,
            "user_session_id": "auth_session_456",
            "answer": {"value": "Authenticated response"},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        await response_test_utils.assert_response_structure(data)
        assert data["user_id"] == regular_user.id
        assert data["is_anonymous"] is False
