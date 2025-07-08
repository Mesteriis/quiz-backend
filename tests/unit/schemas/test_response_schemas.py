"""
Comprehensive тесты для Response Schemas.

Покрывает все схемы ответов:
- Создание и валидация ответов
- Различные типы ответов (текст, выбор, шкала)
- Валидация данных ответов
- Обработка ошибок валидации
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas.response import (
    ResponseCreate,
    ResponseRead,
    ResponseValidate,
)
from tests.factories.surveys.model_factories import (
    ResponseModelFactory,
    QuestionModelFactory,
)


class TestResponseCreateSchema:
    """Тесты схемы создания ответов."""

    def test_response_create_text_answer(self):
        """Тест создания ответа с текстовым ответом."""
        # Arrange
        response_data = {
            "question_id": 1,
            "answer": {"text": "This is my detailed answer"},
            "user_session_id": "session_123",
            "user_id": 42,
            "respondent_id": 1,
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == 1
        assert response.answer["text"] == "This is my detailed answer"
        assert response.user_session_id == "session_123"
        assert response.user_id == 42
        assert response.respondent_id == 1

    def test_response_create_single_choice_answer(self):
        """Тест создания ответа с одиночным выбором."""
        # Arrange
        response_data = {
            "question_id": 2,
            "answer": {"selected_option": "Option A"},
            "user_session_id": "session_456",
            "user_id": None,  # Anonymous user
            "respondent_id": None,
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == 2
        assert response.answer["selected_option"] == "Option A"
        assert response.user_session_id == "session_456"
        assert response.user_id is None
        assert response.respondent_id is None

    def test_response_create_multiple_choice_answer(self):
        """Тест создания ответа с множественным выбором."""
        # Arrange
        response_data = {
            "question_id": 3,
            "answer": {"selected_options": ["Option 1", "Option 3", "Option 5"]},
            "user_session_id": "session_789",
            "user_id": 15,
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == 3
        assert len(response.answer["selected_options"]) == 3
        assert "Option 1" in response.answer["selected_options"]
        assert "Option 3" in response.answer["selected_options"]
        assert "Option 5" in response.answer["selected_options"]

    def test_response_create_scale_answer(self):
        """Тест создания ответа со шкалой."""
        # Arrange
        response_data = {
            "question_id": 4,
            "answer": {"scale_value": 7, "scale_label": "Agree"},
            "user_session_id": "session_scale",
            "user_id": 20,
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == 4
        assert response.answer["scale_value"] == 7
        assert response.answer["scale_label"] == "Agree"

    def test_response_create_rating_answer(self):
        """Тест создания ответа с рейтингом."""
        # Arrange
        response_data = {
            "question_id": 5,
            "answer": {
                "rating": 4.5,
                "max_rating": 5.0,
                "comment": "Very good service",
            },
            "user_session_id": "session_rating",
            "user_id": 30,
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == 5
        assert response.answer["rating"] == 4.5
        assert response.answer["max_rating"] == 5.0
        assert response.answer["comment"] == "Very good service"

    def test_response_create_complex_answer(self):
        """Тест создания ответа со сложной структурой."""
        # Arrange
        response_data = {
            "question_id": 6,
            "answer": {
                "type": "matrix",
                "responses": {
                    "Quality": "Excellent",
                    "Price": "Good",
                    "Service": "Average",
                },
                "additional_comments": "Overall satisfied with the experience",
                "metadata": {"completion_time": 45, "changed_answers": 2},
            },
            "user_session_id": "session_complex",
            "user_id": 50,
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == 6
        assert response.answer["type"] == "matrix"
        assert response.answer["responses"]["Quality"] == "Excellent"
        assert (
            response.answer["additional_comments"]
            == "Overall satisfied with the experience"
        )
        assert response.answer["metadata"]["completion_time"] == 45

    def test_response_create_missing_required_fields(self):
        """Тест создания ответа без обязательных полей."""
        # Arrange
        response_data = {
            "answer": {"text": "Answer without question_id"},
            "user_session_id": "session_incomplete",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ResponseCreate(**response_data)

        assert "question_id" in str(exc_info.value)

    def test_response_create_invalid_question_id(self):
        """Тест создания ответа с невалидным question_id."""
        # Arrange
        response_data = {
            "question_id": "not_a_number",  # Should be integer
            "answer": {"text": "Test answer"},
            "user_session_id": "session_invalid",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ResponseCreate(**response_data)

        assert "question_id" in str(exc_info.value)

    def test_response_create_empty_answer(self):
        """Тест создания ответа с пустым ответом."""
        # Arrange
        response_data = {
            "question_id": 1,
            "answer": {},  # Empty answer
            "user_session_id": "session_empty",
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == 1
        assert response.answer == {}
        assert response.user_session_id == "session_empty"

    def test_response_create_empty_session_id(self):
        """Тест создания ответа с пустым session_id."""
        # Arrange
        response_data = {
            "question_id": 1,
            "answer": {"text": "Test answer"},
            "user_session_id": "",  # Empty session ID
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ResponseCreate(**response_data)

        assert "user_session_id" in str(exc_info.value)

    def test_response_create_negative_user_id(self):
        """Тест создания ответа с отрицательным user_id."""
        # Arrange
        response_data = {
            "question_id": 1,
            "answer": {"text": "Test answer"},
            "user_session_id": "session_negative",
            "user_id": -1,  # Negative user ID
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ResponseCreate(**response_data)

        assert "user_id" in str(exc_info.value)

    def test_response_create_with_factory_data(self):
        """Тест создания ответа с данными из фабрики."""
        # Arrange
        model_response = ResponseModelFactory.build()

        response_data = {
            "question_id": model_response.question_id,
            "answer": model_response.answer,
            "user_session_id": model_response.user_session_id,
            "user_id": model_response.user_id,
            "respondent_id": model_response.respondent_id,
        }

        # Act
        response = ResponseCreate(**response_data)

        # Assert
        assert response.question_id == model_response.question_id
        assert response.answer == model_response.answer
        assert response.user_session_id == model_response.user_session_id


class TestResponseReadSchema:
    """Тесты схемы чтения ответов."""

    def test_response_read_complete_data(self):
        """Тест чтения полного ответа."""
        # Arrange
        response_data = {
            "id": 123,
            "question_id": 45,
            "answer": {"text": "Complete response data"},
            "user_session_id": "session_read_test",
            "user_id": 67,
            "respondent_id": 89,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # Act
        response = ResponseRead(**response_data)

        # Assert
        assert response.id == 123
        assert response.question_id == 45
        assert response.answer["text"] == "Complete response data"
        assert response.user_session_id == "session_read_test"
        assert response.user_id == 67
        assert response.respondent_id == 89
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)

    def test_response_read_minimal_data(self):
        """Тест чтения минимального ответа."""
        # Arrange
        response_data = {
            "id": 456,
            "question_id": 78,
            "answer": {"selected_option": "Yes"},
            "user_session_id": "minimal_session",
            "created_at": datetime.now(),
        }

        # Act
        response = ResponseRead(**response_data)

        # Assert
        assert response.id == 456
        assert response.question_id == 78
        assert response.answer["selected_option"] == "Yes"
        assert response.user_session_id == "minimal_session"
        assert response.user_id is None
        assert response.respondent_id is None
        assert response.updated_at is None

    def test_response_read_with_complex_answer(self):
        """Тест чтения ответа со сложной структурой."""
        # Arrange
        complex_answer = {
            "type": "survey_matrix",
            "questions": {
                "q1": {"rating": 5, "comment": "Excellent"},
                "q2": {"rating": 4, "comment": "Good"},
                "q3": {"rating": 3, "comment": "Average"},
            },
            "overall_satisfaction": 4.2,
            "would_recommend": True,
            "feedback": "Great experience overall!",
        }

        response_data = {
            "id": 789,
            "question_id": 10,
            "answer": complex_answer,
            "user_session_id": "complex_session",
            "user_id": 100,
            "created_at": datetime.now(),
        }

        # Act
        response = ResponseRead(**response_data)

        # Assert
        assert response.id == 789
        assert response.answer["type"] == "survey_matrix"
        assert response.answer["questions"]["q1"]["rating"] == 5
        assert response.answer["overall_satisfaction"] == 4.2
        assert response.answer["would_recommend"] is True

    def test_response_read_missing_id(self):
        """Тест чтения ответа без ID."""
        # Arrange
        response_data = {
            "question_id": 1,
            "answer": {"text": "No ID response"},
            "user_session_id": "no_id_session",
            "created_at": datetime.now(),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ResponseRead(**response_data)

        assert "id" in str(exc_info.value)

    def test_response_read_invalid_datetime(self):
        """Тест чтения ответа с невалидной датой."""
        # Arrange
        response_data = {
            "id": 999,
            "question_id": 1,
            "answer": {"text": "Invalid date response"},
            "user_session_id": "invalid_date_session",
            "created_at": "not_a_datetime",  # Invalid datetime
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ResponseRead(**response_data)

        assert "created_at" in str(exc_info.value)


class TestResponseValidateSchema:
    """Тесты схемы валидации ответов."""

    def test_response_validate_basic(self):
        """Тест базовой валидации ответа."""
        # Arrange
        validate_data = {
            "question_id": 1,
            "answer": {"text": "Text to validate"},
            "user_session_id": "validate_session",
        }

        # Act
        validation = ResponseValidate(**validate_data)

        # Assert
        assert validation.question_id == 1
        assert validation.answer["text"] == "Text to validate"
        assert validation.user_session_id == "validate_session"

    def test_response_validate_with_metadata(self):
        """Тест валидации ответа с метаданными."""
        # Arrange
        validate_data = {
            "question_id": 2,
            "answer": {"selected_option": "Option B"},
            "user_session_id": "validate_meta_session",
            "validation_rules": {"required": True, "min_length": 1, "max_length": 100},
            "context": {
                "previous_answers": ["Option A"],
                "question_type": "single_choice",
                "attempt_number": 1,
            },
        }

        # Act
        validation = ResponseValidate(**validate_data)

        # Assert
        assert validation.question_id == 2
        assert validation.answer["selected_option"] == "Option B"
        assert validation.validation_rules["required"] is True
        assert validation.context["question_type"] == "single_choice"

    def test_response_validate_empty_context(self):
        """Тест валидации ответа с пустым контекстом."""
        # Arrange
        validate_data = {
            "question_id": 3,
            "answer": {"scale_value": 5},
            "user_session_id": "empty_context_session",
            "validation_rules": {},
            "context": {},
        }

        # Act
        validation = ResponseValidate(**validate_data)

        # Assert
        assert validation.question_id == 3
        assert validation.answer["scale_value"] == 5
        assert validation.validation_rules == {}
        assert validation.context == {}

    def test_response_validate_without_optional_fields(self):
        """Тест валидации ответа без опциональных полей."""
        # Arrange
        validate_data = {
            "question_id": 4,
            "answer": {"rating": 3.5},
            "user_session_id": "no_optional_session",
        }

        # Act
        validation = ResponseValidate(**validate_data)

        # Assert
        assert validation.question_id == 4
        assert validation.answer["rating"] == 3.5
        assert validation.user_session_id == "no_optional_session"
        assert validation.validation_rules is None
        assert validation.context is None

    def test_response_validate_complex_rules(self):
        """Тест валидации ответа со сложными правилами."""
        # Arrange
        complex_rules = {
            "required": True,
            "data_type": "string",
            "pattern": r"^[A-Za-z\s]+$",
            "min_length": 5,
            "max_length": 200,
            "forbidden_words": ["spam", "test"],
            "custom_validators": [
                {"name": "profanity_check", "enabled": True},
                {"name": "sentiment_analysis", "enabled": False},
            ],
        }

        validate_data = {
            "question_id": 5,
            "answer": {"text": "This is a proper response"},
            "user_session_id": "complex_rules_session",
            "validation_rules": complex_rules,
        }

        # Act
        validation = ResponseValidate(**validate_data)

        # Assert
        assert validation.question_id == 5
        assert validation.validation_rules["required"] is True
        assert validation.validation_rules["pattern"] == r"^[A-Za-z\s]+$"
        assert len(validation.validation_rules["forbidden_words"]) == 2
        assert len(validation.validation_rules["custom_validators"]) == 2

    def test_response_validate_missing_required_field(self):
        """Тест валидации ответа без обязательного поля."""
        # Arrange
        validate_data = {
            "answer": {"text": "Missing question_id"},
            "user_session_id": "missing_field_session",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ResponseValidate(**validate_data)

        assert "question_id" in str(exc_info.value)


class TestResponseSchemasIntegration:
    """Интеграционные тесты схем ответов."""

    def test_response_create_to_read_conversion(self):
        """Тест конвертации схемы создания в схему чтения."""
        # Arrange
        create_data = {
            "question_id": 100,
            "answer": {"text": "Integration test response"},
            "user_session_id": "integration_session",
            "user_id": 200,
            "respondent_id": 300,
        }

        # Act
        create_response = ResponseCreate(**create_data)

        # Simulate database save and add ID + timestamps
        read_data = {
            "id": 1001,
            "question_id": create_response.question_id,
            "answer": create_response.answer,
            "user_session_id": create_response.user_session_id,
            "user_id": create_response.user_id,
            "respondent_id": create_response.respondent_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        read_response = ResponseRead(**read_data)

        # Assert
        assert read_response.question_id == create_response.question_id
        assert read_response.answer == create_response.answer
        assert read_response.user_session_id == create_response.user_session_id
        assert read_response.user_id == create_response.user_id
        assert read_response.respondent_id == create_response.respondent_id
        assert read_response.id == 1001
        assert isinstance(read_response.created_at, datetime)

    def test_response_validate_to_create_flow(self):
        """Тест потока валидации к созданию ответа."""
        # Arrange
        validate_data = {
            "question_id": 500,
            "answer": {"selected_options": ["A", "C", "E"]},
            "user_session_id": "validate_to_create_session",
            "validation_rules": {
                "required": True,
                "min_selections": 1,
                "max_selections": 5,
            },
        }

        # Act
        # Step 1: Validate
        validation = ResponseValidate(**validate_data)

        # Step 2: If validation passes, create response
        create_data = {
            "question_id": validation.question_id,
            "answer": validation.answer,
            "user_session_id": validation.user_session_id,
            "user_id": 600,
        }

        create_response = ResponseCreate(**create_data)

        # Assert
        assert create_response.question_id == validation.question_id
        assert create_response.answer == validation.answer
        assert create_response.user_session_id == validation.user_session_id
        assert len(create_response.answer["selected_options"]) == 3

    def test_response_schemas_with_all_question_types(self):
        """Тест схем ответов со всеми типами вопросов."""
        # Arrange & Act
        question_types = [
            # Text question
            {"question_id": 1, "answer": {"text": "Text response"}, "type": "text"},
            # Single choice
            {
                "question_id": 2,
                "answer": {"selected_option": "Option A"},
                "type": "single_choice",
            },
            # Multiple choice
            {
                "question_id": 3,
                "answer": {"selected_options": ["A", "B"]},
                "type": "multiple_choice",
            },
            # Scale
            {
                "question_id": 4,
                "answer": {"scale_value": 7, "scale_max": 10},
                "type": "scale",
            },
            # Rating
            {
                "question_id": 5,
                "answer": {"rating": 4.5, "max_rating": 5},
                "type": "rating",
            },
            # Boolean
            {"question_id": 6, "answer": {"boolean_value": True}, "type": "boolean"},
            # Date
            {"question_id": 7, "answer": {"date_value": "2024-01-20"}, "type": "date"},
            # Number
            {"question_id": 8, "answer": {"number_value": 42.7}, "type": "number"},
        ]

        responses = []
        for q_data in question_types:
            response_data = {
                "question_id": q_data["question_id"],
                "answer": q_data["answer"],
                "user_session_id": f"session_{q_data['type']}",
            }
            responses.append(ResponseCreate(**response_data))

        # Assert
        assert len(responses) == 8

        # Check specific answer types
        text_response = responses[0]
        assert "text" in text_response.answer

        choice_response = responses[1]
        assert "selected_option" in choice_response.answer

        multi_choice_response = responses[2]
        assert "selected_options" in multi_choice_response.answer
        assert len(multi_choice_response.answer["selected_options"]) == 2

        scale_response = responses[3]
        assert scale_response.answer["scale_value"] == 7

        rating_response = responses[4]
        assert rating_response.answer["rating"] == 4.5

    def test_response_schemas_validation_edge_cases(self):
        """Тест граничных случаев валидации схем."""
        # Test 1: Very long text response
        long_text = "A" * 10000  # Very long text
        long_response = ResponseCreate(
            question_id=1,
            answer={"text": long_text},
            user_session_id="long_text_session",
        )
        assert len(long_response.answer["text"]) == 10000

        # Test 2: Empty string in answer
        empty_response = ResponseCreate(
            question_id=2, answer={"text": ""}, user_session_id="empty_text_session"
        )
        assert empty_response.answer["text"] == ""

        # Test 3: Special characters in answer
        special_chars_response = ResponseCreate(
            question_id=3,
            answer={"text": "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"},
            user_session_id="special_chars_session",
        )
        assert "!@#$%^&*" in special_chars_response.answer["text"]

        # Test 4: Unicode characters in answer
        unicode_response = ResponseCreate(
            question_id=4,
            answer={"text": "Unicode: 🌟 ñáéíóú αβγδε 中文"},
            user_session_id="unicode_session",
        )
        assert "🌟" in unicode_response.answer["text"]
        assert "中文" in unicode_response.answer["text"]

        # Test 5: Very large numbers
        large_number_response = ResponseCreate(
            question_id=5,
            answer={"number_value": 1e15},
            user_session_id="large_number_session",
        )
        assert large_number_response.answer["number_value"] == 1e15

        # Test 6: Very small numbers
        small_number_response = ResponseCreate(
            question_id=6,
            answer={"number_value": 1e-15},
            user_session_id="small_number_session",
        )
        assert small_number_response.answer["number_value"] == 1e-15

    def test_response_schemas_with_model_factory(self):
        """Тест схем ответов с использованием модельных фабрик."""
        # Arrange
        question = QuestionModelFactory.build(id=1000, question_type="TEXT")
        model_response = ResponseModelFactory.build(
            question_id=question.id, answer={"text": "Factory generated response"}
        )

        # Act
        # Create schema from model
        create_data = {
            "question_id": model_response.question_id,
            "answer": model_response.answer,
            "user_session_id": model_response.user_session_id,
            "user_id": model_response.user_id,
            "respondent_id": model_response.respondent_id,
        }
        create_response = ResponseCreate(**create_data)

        # Create read schema
        read_data = {
            "id": model_response.id,
            "question_id": model_response.question_id,
            "answer": model_response.answer,
            "user_session_id": model_response.user_session_id,
            "user_id": model_response.user_id,
            "respondent_id": model_response.respondent_id,
            "created_at": model_response.created_at,
            "updated_at": model_response.updated_at,
        }
        read_response = ResponseRead(**read_data)

        # Assert
        assert create_response.question_id == question.id
        assert create_response.answer == model_response.answer
        assert read_response.id == model_response.id
        assert read_response.question_id == create_response.question_id
        assert read_response.answer == create_response.answer
