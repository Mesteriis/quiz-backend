"""
Negative тесты для вопросов опросов - обработка ошибок.

Содержит тесты для различных ошибочных сценариев при работе с вопросами:
- Невалидные данные вопросов
- Отсутствие авторизации
- Неправильные права доступа
- Несуществующие ресурсы
- Нарушения бизнес-логики
"""

import pytest


class TestQuestionCreationErrors:
    """Negative тесты создания вопросов."""

    @pytest.mark.asyncio
    async def test_add_question_unauthorized(
        self, api_client, db_session, sample_survey, valid_question_data
    ):
        """Тест добавления вопроса без авторизации."""
        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions", json=valid_question_data
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_forbidden_user(
        self,
        api_client,
        db_session,
        sample_survey,
        regular_user,
        auth_headers_factory,
        valid_question_data,
    ):
        """Тест добавления вопроса к чужому опросу."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=valid_question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert (
            "permission" in data["detail"].lower()
            or "forbidden" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_add_question_to_nonexistent_survey(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_question_data,
    ):
        """Тест добавления вопроса к несуществующему опросу."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            "/api/surveys/99999/questions", json=valid_question_data, headers=headers
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_empty_text(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с пустым текстом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "",
            "question_type": "text",
            "is_required": True,
            "order": 1,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("text" in str(error).lower() for error in data["detail"])

    @pytest.mark.asyncio
    async def test_add_question_invalid_type(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с невалидным типом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Valid question text",
            "question_type": "invalid_type",
            "is_required": True,
            "order": 1,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_negative_order(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с отрицательным порядком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Valid question text",
            "question_type": "text",
            "is_required": True,
            "order": -1,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_missing_required_fields(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса без обязательных полей."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            # Отсутствуют text, question_type, order
            "is_required": True,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_invalid_data_types(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с неправильными типами данных."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Valid question text",
            "question_type": "text",
            "is_required": "not_a_boolean",  # Должно быть boolean
            "order": "not_a_number",  # Должно быть число
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_rating_question_invalid_range(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления рейтингового вопроса с невалидным диапазоном."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Rate this",
            "question_type": "rating",
            "is_required": True,
            "order": 1,
            "min_rating": 5,  # min больше max
            "max_rating": 1,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_choice_question_without_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с выбором без вариантов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Choose option",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            # Отсутствуют options
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_choice_question_empty_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с выбором с пустыми вариантами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Choose option",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": [],  # Пустой список
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_choice_question_too_many_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с выбором со слишком большим количеством вариантов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Choose option",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": [f"Option {i}" for i in range(101)],  # Слишком много вариантов
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_to_inactive_survey(
        self,
        api_client,
        db_session,
        sample_inactive_survey,
        regular_user,
        auth_headers_factory,
        valid_question_data,
    ):
        """Тест добавления вопроса к неактивному опросу."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_inactive_survey.id}/questions",
            json=valid_question_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "inactive" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_add_question_duplicate_order(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с дублирующимся порядком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        question_data = {
            "text": "First question",
            "question_type": "text",
            "is_required": True,
            "order": 1,
        }

        # Создаем первый вопрос
        response1 = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question_data,
            headers=headers,
        )
        assert response1.status_code == 201

        # Act - создаем второй вопрос с тем же порядком
        question_data["text"] = "Second question"
        response2 = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question_data,
            headers=headers,
        )

        # Assert
        assert response2.status_code == 422
        data = response2.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_too_long_text(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса со слишком длинным текстом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "Q" * 2000,  # Слишком длинный текст
            "question_type": "text",
            "is_required": True,
            "order": 1,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=invalid_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_question_malformed_json(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест добавления вопроса с некорректным JSON."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        headers["Content-Type"] = "application/json"

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            data="invalid json",
            headers=headers,
        )

        # Assert
        assert response.status_code == 422


class TestQuestionAccessErrors:
    """Negative тесты доступа к вопросам."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_question(self, api_client, db_session):
        """Тест получения несуществующего вопроса."""
        # Act
        response = await api_client.get("/api/questions/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_question_invalid_id_format(self, api_client, db_session):
        """Тест получения вопроса с невалидным форматом ID."""
        # Act
        response = await api_client.get("/api/questions/not_a_number")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_questions_from_nonexistent_survey(self, api_client, db_session):
        """Тест получения вопросов из несуществующего опроса."""
        # Act
        response = await api_client.get("/api/surveys/99999/questions")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_questions_from_private_survey_without_access(
        self, api_client, db_session, sample_private_survey
    ):
        """Тест получения вопросов из приватного опроса без доступа."""
        # Act
        response = await api_client.get(
            f"/api/surveys/{sample_private_survey.id}/questions"
        )

        # Assert
        assert response.status_code in [403, 404]
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_question_from_inactive_survey(
        self, api_client, db_session, sample_inactive_survey
    ):
        """Тест получения вопроса из неактивного опроса."""
        # Act
        response = await api_client.get(
            f"/api/surveys/{sample_inactive_survey.id}/questions"
        )

        # Assert
        assert response.status_code in [403, 404]
        data = response.json()
        assert "detail" in data


class TestQuestionUpdateErrors:
    """Negative тесты обновления вопросов."""

    @pytest.mark.asyncio
    async def test_update_question_unauthorized(
        self, api_client, db_session, sample_question
    ):
        """Тест обновления вопроса без авторизации."""
        # Arrange
        update_data = {
            "text": "Updated question text",
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_question_forbidden_user(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест обновления чужого вопроса."""
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
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_nonexistent_question(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест обновления несуществующего вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "text": "Updated question text",
        }

        # Act
        response = await api_client.put(
            "/api/questions/99999", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_question_invalid_data(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест обновления вопроса с невалидными данными."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "text": "",  # Пустой текст
            "order": -1,  # Отрицательный порядок
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_question_change_type_with_responses(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест изменения типа вопроса при наличии ответов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "question_type": "rating",  # Изменяем тип с text на rating
        }

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "type" in data["detail"].lower() or "responses" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_question_invalid_rating_range(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления рейтингового вопроса с невалидным диапазоном."""
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
        invalid_update_data = {
            "min_rating": 10,  # min больше max
            "max_rating": 1,
        }
        response = await api_client.put(
            f"/api/questions/{question_id}", json=invalid_update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_question_remove_required_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест удаления обязательных вариантов из вопроса с выбором."""
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
        invalid_update_data = {
            "options": [],  # Удаляем все варианты
        }
        response = await api_client.put(
            f"/api/questions/{question_id}", json=invalid_update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_question_conflicting_order(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления вопроса с конфликтующим порядком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем два вопроса
        question1_data = {
            "text": "Question 1",
            "question_type": "text",
            "is_required": True,
            "order": 1,
        }
        question2_data = {
            "text": "Question 2",
            "question_type": "text",
            "is_required": True,
            "order": 2,
        }

        response1 = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question1_data,
            headers=headers,
        )
        assert response1.status_code == 201

        response2 = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question2_data,
            headers=headers,
        )
        assert response2.status_code == 201
        question2_id = response2.json()["id"]

        # Act - пытаемся изменить порядок второго вопроса на 1 (конфликт)
        update_data = {"order": 1}
        response = await api_client.put(
            f"/api/questions/{question2_id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_question_malformed_json(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест обновления вопроса с некорректным JSON."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        headers["Content-Type"] = "application/json"

        # Act
        response = await api_client.put(
            f"/api/questions/{sample_question.id}", data="invalid json", headers=headers
        )

        # Assert
        assert response.status_code == 422


class TestQuestionDeletionErrors:
    """Negative тесты удаления вопросов."""

    @pytest.mark.asyncio
    async def test_delete_question_unauthorized(
        self, api_client, db_session, sample_question
    ):
        """Тест удаления вопроса без авторизации."""
        # Act
        response = await api_client.delete(f"/api/questions/{sample_question.id}")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_question_forbidden_user(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления чужого вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete(
            f"/api/questions/{sample_question.id}", headers=headers
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_nonexistent_question(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест удаления несуществующего вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete("/api/questions/99999", headers=headers)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_question_with_responses(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления вопроса с ответами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete(
            f"/api/questions/{sample_question.id}", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert (
            "responses" in data["detail"].lower()
            or "cannot delete" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_delete_last_required_question(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест удаления последнего обязательного вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем единственный обязательный вопрос
        question_data = {
            "text": "Required question",
            "question_type": "text",
            "is_required": True,
            "order": 1,
        }

        create_response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question_data,
            headers=headers,
        )
        assert create_response.status_code == 201
        question_id = create_response.json()["id"]

        # Act
        response = await api_client.delete(
            f"/api/questions/{question_id}", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "required" in data["detail"].lower() or "last" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_double_delete_question(
        self,
        api_client,
        db_session,
        sample_question,
        regular_user,
        auth_headers_factory,
    ):
        """Тест повторного удаления вопроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        question_id = sample_question.id

        # Первое удаление
        first_response = await api_client.delete(
            f"/api/questions/{question_id}", headers=headers
        )
        assert first_response.status_code == 204

        # Act - второе удаление
        response = await api_client.delete(
            f"/api/questions/{question_id}", headers=headers
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_question_invalid_id_format(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест удаления вопроса с невалидным форматом ID."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete(
            "/api/questions/not_a_number", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_question_from_published_survey(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест удаления вопроса из опубликованного опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем вопрос
        question_data = {
            "text": "Question to delete",
            "question_type": "text",
            "is_required": True,
            "order": 1,
        }

        create_response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question_data,
            headers=headers,
        )
        assert create_response.status_code == 201
        question_id = create_response.json()["id"]

        # Публикуем опрос (устанавливаем is_published=True)
        publish_response = await api_client.put(
            f"/api/surveys/{sample_survey.id}",
            json={"is_published": True},
            headers=headers,
        )
        assert publish_response.status_code == 200

        # Act
        response = await api_client.delete(
            f"/api/questions/{question_id}", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "published" in data["detail"].lower()


class TestQuestionBusinessLogicErrors:
    """Negative тесты бизнес-логики вопросов."""

    @pytest.mark.asyncio
    async def test_exceed_questions_limit_per_survey(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест превышения лимита вопросов на опрос."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем много вопросов (предполагаем лимит 50)
        for i in range(51):
            question_data = {
                "text": f"Question {i}",
                "question_type": "text",
                "is_required": True,
                "order": i + 1,
            }

            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )

            if i < 50:
                # Первые 50 должны создаться успешно
                assert response.status_code == 201
            else:
                # 51-й должен вернуть ошибку
                assert response.status_code == 422
                data = response.json()
                assert "detail" in data
                assert "limit" in data["detail"].lower()
                break

    @pytest.mark.asyncio
    async def test_reorder_questions_invalid_sequence(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест переупорядочивания вопросов с невалидной последовательностью."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем вопросы
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

        # Act - невалидная последовательность (пропущен порядок 2)
        invalid_order = [
            {"id": created_questions[0]["id"], "order": 1},
            {"id": created_questions[1]["id"], "order": 3},  # Пропускаем 2
            {"id": created_questions[2]["id"], "order": 4},
        ]

        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}/questions/reorder",
            json={"questions": invalid_order},
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_dependent_questions_circular_reference(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания зависимых вопросов с циклической ссылкой."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем первый вопрос
        question1_data = {
            "text": "Question 1",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": ["Yes", "No"],
        }

        response1 = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question1_data,
            headers=headers,
        )
        assert response1.status_code == 201
        question1_id = response1.json()["id"]

        # Создаем второй вопрос, зависящий от первого
        question2_data = {
            "text": "Question 2",
            "question_type": "text",
            "is_required": True,
            "order": 2,
            "depends_on": question1_id,
        }

        response2 = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=question2_data,
            headers=headers,
        )
        assert response2.status_code == 201
        question2_id = response2.json()["id"]

        # Act - пытаемся сделать первый вопрос зависимым от второго (циклическая ссылка)
        update_data = {"depends_on": question2_id}
        response = await api_client.put(
            f"/api/questions/{question1_id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert (
            "circular" in data["detail"].lower()
            or "dependency" in data["detail"].lower()
        )
