"""
Positive тесты для работы с вопросами опросов.

Содержит тесты успешных сценариев добавления, обновления,
удаления и получения вопросов в опросах.
"""

import pytest


class TestQuestionCreationPositive:
    """Positive тесты создания вопросов."""

    @pytest.mark.asyncio
    async def test_add_text_question_to_survey(
        self,
        api_client,
        db_session,
        sample_survey,
        regular_user,
        auth_headers_factory,
        valid_question_data,
    ):
        """Тест добавления текстового вопроса в опрос."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=valid_question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["text"] == valid_question_data["text"]
        assert data["question_type"] == valid_question_data["question_type"]
        assert data["is_required"] == valid_question_data["is_required"]
        assert data["order"] == valid_question_data["order"]
        assert data["survey_id"] == sample_survey.id

    @pytest.mark.asyncio
    async def test_add_rating_question_to_survey(
        self,
        api_client,
        db_session,
        sample_survey,
        regular_user,
        auth_headers_factory,
        valid_rating_question_data,
    ):
        """Тест добавления рейтингового вопроса в опрос."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=valid_rating_question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["question_type"] == "rating"
        assert data["min_rating"] == valid_rating_question_data["min_rating"]
        assert data["max_rating"] == valid_rating_question_data["max_rating"]
        assert data["survey_id"] == sample_survey.id

    @pytest.mark.asyncio
    async def test_add_choice_question_to_survey(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с выбором в опрос."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        choice_question_data = {
            "text": "Choose your favorite color",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": ["Red", "Blue", "Green", "Yellow"],
            "allow_multiple": False,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=choice_question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["question_type"] == "choice"
        assert data["options"] == choice_question_data["options"]
        assert data["allow_multiple"] is False

    @pytest.mark.asyncio
    async def test_add_multiple_choice_question(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с множественным выбором."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        multiple_choice_data = {
            "text": "Select all that apply",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": ["Option 1", "Option 2", "Option 3"],
            "allow_multiple": True,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=multiple_choice_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["allow_multiple"] is True
        assert len(data["options"]) == 3

    @pytest.mark.asyncio
    async def test_add_optional_question(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления необязательного вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        optional_question_data = {
            "text": "Optional feedback",
            "question_type": "text",
            "is_required": False,
            "order": 1,
            "help_text": "This question is optional",
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=optional_question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["is_required"] is False
        assert data["help_text"] == "This question is optional"

    @pytest.mark.asyncio
    async def test_add_questions_with_order(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопросов с правильным порядком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        questions_data = [
            {
                "text": "First question",
                "question_type": "text",
                "is_required": True,
                "order": 1,
            },
            {
                "text": "Second question",
                "question_type": "text",
                "is_required": True,
                "order": 2,
            },
            {
                "text": "Third question",
                "question_type": "text",
                "is_required": True,
                "order": 3,
            },
        ]

        # Act & Assert
        for question_data in questions_data:
            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["order"] == question_data["order"]

    @pytest.mark.asyncio
    async def test_add_question_with_validation(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с валидацией."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        question_data = {
            "text": "Enter your age",
            "question_type": "number",
            "is_required": True,
            "order": 1,
            "min_value": 0,
            "max_value": 150,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["question_type"] == "number"
        assert data["min_value"] == 0
        assert data["max_value"] == 150

    @pytest.mark.asyncio
    async def test_add_question_with_unicode_text(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с Unicode текстом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        unicode_question_data = {
            "text": "Какой ваш любимый цвет? 🎨 テスト 测试",
            "question_type": "text",
            "is_required": True,
            "order": 1,
            "help_text": "Ответьте на русском языке 🇷🇺",
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=unicode_question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["text"] == unicode_question_data["text"]
        assert data["help_text"] == unicode_question_data["help_text"]


class TestQuestionRetrievalPositive:
    """Positive тесты получения вопросов."""

    @pytest.mark.asyncio
    async def test_get_survey_questions(
        self, api_client, db_session, survey_with_questions
    ):
        """Тест получения всех вопросов опроса."""
        # Act
        response = await api_client.get(
            f"/api/surveys/{survey_with_questions.id}/questions"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Проверяем структуру вопросов
        for question in data:
            assert "id" in question
            assert "text" in question
            assert "question_type" in question
            assert "order" in question
            assert "is_required" in question
            assert "survey_id" in question

    @pytest.mark.asyncio
    async def test_get_single_question(self, api_client, db_session, sample_question):
        """Тест получения одного вопроса."""
        # Act
        response = await api_client.get(f"/api/questions/{sample_question.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_question.id
        assert data["text"] == sample_question.text
        assert data["question_type"] == sample_question.question_type

    @pytest.mark.asyncio
    async def test_get_questions_ordered(
        self, api_client, db_session, survey_with_questions
    ):
        """Тест получения вопросов в правильном порядке."""
        # Act
        response = await api_client.get(
            f"/api/surveys/{survey_with_questions.id}/questions"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем что вопросы отсортированы по order
        if len(data) > 1:
            orders = [q["order"] for q in data]
            assert orders == sorted(orders)

    @pytest.mark.asyncio
    async def test_get_questions_with_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест получения вопросов с вариантами ответов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        choice_question_data = {
            "text": "Choose color",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": ["Red", "Blue", "Green"],
        }

        # Создаем вопрос с вариантами
        create_response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=choice_question_data,
            headers=headers,
        )
        assert create_response.status_code == 201

        # Act
        response = await api_client.get(f"/api/surveys/{sample_survey.id}/questions")

        # Assert
        assert response.status_code == 200
        data = response.json()

        choice_question = next(
            (q for q in data if q["question_type"] == "choice"), None
        )
        assert choice_question is not None
        assert choice_question["options"] == ["Red", "Blue", "Green"]

    @pytest.mark.asyncio
    async def test_get_questions_different_types(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест получения вопросов разных типов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        questions_data = [
            {
                "text": "Text question",
                "question_type": "text",
                "is_required": True,
                "order": 1,
            },
            {
                "text": "Rating question",
                "question_type": "rating",
                "is_required": True,
                "order": 2,
                "min_rating": 1,
                "max_rating": 5,
            },
            {
                "text": "Choice question",
                "question_type": "choice",
                "is_required": True,
                "order": 3,
                "options": ["Yes", "No"],
            },
        ]

        # Создаем вопросы
        for question_data in questions_data:
            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )
            assert response.status_code == 201

        # Act
        response = await api_client.get(f"/api/surveys/{sample_survey.id}/questions")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3
        question_types = [q["question_type"] for q in data]
        assert "text" in question_types
        assert "rating" in question_types
        assert "choice" in question_types


class TestQuestionUpdatePositive:
    """Positive тесты обновления вопросов."""

    @pytest.mark.asyncio
    async def test_update_question_text(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест обновления текста вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "text": "Updated question text",
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["text"] == "Updated question text"
        assert data["id"] == sample_question.id

    @pytest.mark.asyncio
    async def test_update_question_requirement(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест изменения обязательности вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "is_required": False,
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_required"] is False

    @pytest.mark.asyncio
    async def test_update_question_order(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест изменения порядка вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "order": 5,
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["order"] == 5

    @pytest.mark.asyncio
    async def test_update_question_help_text(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест обновления подсказки вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "help_text": "This is helpful text for the question",
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["help_text"] == "This is helpful text for the question"

    @pytest.mark.asyncio
    async def test_update_rating_question_range(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления диапазона рейтингового вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем рейтинговый вопрос
        rating_question_data = {
            "text": "Rate this",
            "question_type": "rating",
            "is_required": True,
            "order": 1,
            "min_rating": 1,
            "max_rating": 5,
        }

        create_response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=rating_question_data,
            headers=headers,
        )
        assert create_response.status_code == 201
        question_id = create_response.json()["id"]

        # Act
        update_data = {
            "min_rating": 1,
            "max_rating": 10,
        }
        response = await api_client.put(
            f"/api/questions/{question_id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["min_rating"] == 1
        assert data["max_rating"] == 10

    @pytest.mark.asyncio
    async def test_update_choice_question_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления вариантов ответов для вопроса с выбором."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем вопрос с выбором
        choice_question_data = {
            "text": "Choose option",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": ["Option 1", "Option 2"],
        }

        create_response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=choice_question_data,
            headers=headers,
        )
        assert create_response.status_code == 201
        question_id = create_response.json()["id"]

        # Act
        update_data = {
            "options": ["New Option 1", "New Option 2", "New Option 3"],
        }
        response = await api_client.put(
            f"/api/questions/{question_id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["options"] == ["New Option 1", "New Option 2", "New Option 3"]

    @pytest.mark.asyncio
    async def test_update_question_partial(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест частичного обновления вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        original_text = sample_question.text
        update_data = {
            "is_required": False,
            # text не обновляем
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_required"] is False
        assert data["text"] == original_text  # Не изменился


class TestQuestionDeletionPositive:
    """Positive тесты удаления вопросов."""

    @pytest.mark.asyncio
    async def test_delete_question_from_survey(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления вопроса из опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        question_id = sample_question.id

        # Act
        response = await api_client.delete(
            f"/api/questions/{question_id}", headers=headers
        )

        # Assert
        assert response.status_code == 204

        # Проверяем что вопрос удален
        get_response = await api_client.get(f"/api/questions/{question_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_question_reorders_remaining(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест что удаление вопроса переупорядочивает оставшиеся."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем несколько вопросов
        questions_data = [
            {
                "text": "Question 1",
                "question_type": "text",
                "is_required": True,
                "order": 1,
            },
            {
                "text": "Question 2",
                "question_type": "text",
                "is_required": True,
                "order": 2,
            },
            {
                "text": "Question 3",
                "question_type": "text",
                "is_required": True,
                "order": 3,
            },
        ]

        created_questions = []
        for question_data in questions_data:
            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )
            assert response.status_code == 201
            created_questions.append(response.json())

        # Act - удаляем средний вопрос
        middle_question_id = created_questions[1]["id"]
        response = await api_client.delete(
            f"/api/questions/{middle_question_id}", headers=headers
        )

        # Assert
        assert response.status_code == 204

        # Проверяем что остальные вопросы остались
        get_response = await api_client.get(
            f"/api/surveys/{sample_survey.id}/questions"
        )
        assert get_response.status_code == 200
        remaining_questions = get_response.json()

        assert len(remaining_questions) == 2
        assert remaining_questions[0]["text"] == "Question 1"
        assert remaining_questions[1]["text"] == "Question 3"

    @pytest.mark.asyncio
    async def test_delete_all_questions_from_survey(
        self,
        api_client,
        db_session,
        survey_with_questions,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления всех вопросов из опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Получаем все вопросы
        get_response = await api_client.get(
            f"/api/surveys/{survey_with_questions.id}/questions"
        )
        assert get_response.status_code == 200
        questions = get_response.json()

        # Act - удаляем все вопросы
        for question in questions:
            response = await api_client.delete(
                f"/api/questions/{question['id']}", headers=headers
            )
            assert response.status_code == 204

        # Assert
        get_response = await api_client.get(
            f"/api/surveys/{survey_with_questions.id}/questions"
        )
        assert get_response.status_code == 200
        remaining_questions = get_response.json()

        assert len(remaining_questions) == 0

    @pytest.mark.asyncio
    async def test_delete_question_admin_permissions(
        self, api_client, db_session, sample_question, admin_user, auth_headers_factory
    ):
        """Тест удаления вопроса администратором."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)
        question_id = sample_question.id

        # Act
        response = await api_client.delete(
            f"/api/questions/{question_id}", headers=headers
        )

        # Assert
        assert response.status_code == 204

        # Проверяем что вопрос удален
        get_response = await api_client.get(f"/api/questions/{question_id}")
        assert get_response.status_code == 404


class TestQuestionReorderingPositive:
    """Positive тесты переупорядочивания вопросов."""

    @pytest.mark.asyncio
    async def test_reorder_questions_in_survey(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест переупорядочивания вопросов в опросе."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем вопросы
        questions_data = [
            {
                "text": "Question A",
                "question_type": "text",
                "is_required": True,
                "order": 1,
            },
            {
                "text": "Question B",
                "question_type": "text",
                "is_required": True,
                "order": 2,
            },
            {
                "text": "Question C",
                "question_type": "text",
                "is_required": True,
                "order": 3,
            },
        ]

        created_questions = []
        for question_data in questions_data:
            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )
            assert response.status_code == 201
            created_questions.append(response.json())

        # Act - переупорядочиваем вопросы
        new_order = [
            {"id": created_questions[2]["id"], "order": 1},  # C -> 1
            {"id": created_questions[0]["id"], "order": 2},  # A -> 2
            {"id": created_questions[1]["id"], "order": 3},  # B -> 3
        ]

        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}/questions/reorder",
            json={"questions": new_order},
            headers=headers,
        )

        # Assert
        assert response.status_code == 200

        # Проверяем новый порядок
        get_response = await api_client.get(
            f"/api/surveys/{sample_survey.id}/questions"
        )
        assert get_response.status_code == 200
        questions = get_response.json()

        assert len(questions) == 3
        assert questions[0]["text"] == "Question C"
        assert questions[1]["text"] == "Question A"
        assert questions[2]["text"] == "Question B"

    @pytest.mark.asyncio
    async def test_move_question_to_different_position(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест перемещения вопроса на другую позицию."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act - перемещаем вопрос на позицию 10
        update_data = {"order": 10}
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["order"] == 10
