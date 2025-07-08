"""
Positive тесты для управления опросами.

Содержит тесты успешных сценариев создания, получения,
обновления и удаления опросов.
"""

import pytest


class TestSurveyCreationPositive:
    """Positive тесты создания опросов."""

    @pytest.mark.asyncio
    async def test_create_basic_public_survey(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_survey_data,
    ):
        """Тест создания базового публичного опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            "/api/surveys", json=valid_survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == valid_survey_data["title"]
        assert data["description"] == valid_survey_data["description"]
        assert data["is_public"] == valid_survey_data["is_public"]
        assert data["is_active"] == valid_survey_data["is_active"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_create_private_survey(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_private_survey_data,
    ):
        """Тест создания приватного опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            "/api/surveys", json=valid_private_survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == valid_private_survey_data["title"]
        assert data["is_public"] is False
        assert data["is_active"] is True
        assert "access_token" in data
        assert data["telegram_notifications"] is False

    @pytest.mark.asyncio
    async def test_create_survey_with_questions(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_survey_data,
        valid_question_data,
    ):
        """Тест создания опроса с вопросами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_data = {**valid_survey_data, "questions": [valid_question_data]}

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == valid_survey_data["title"]
        assert "questions" in data
        assert len(data["questions"]) == 1
        assert data["questions"][0]["text"] == valid_question_data["text"]

    @pytest.mark.asyncio
    async def test_create_survey_with_multiple_questions(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_survey_data,
    ):
        """Тест создания опроса с несколькими вопросами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        questions = [
            {
                "text": f"Question {i + 1}",
                "question_type": "text",
                "is_required": True,
                "order": i + 1,
            }
            for i in range(5)
        ]
        survey_data = {**valid_survey_data, "questions": questions}

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert len(data["questions"]) == 5
        for i, question in enumerate(data["questions"]):
            assert question["text"] == f"Question {i + 1}"
            assert question["order"] == i + 1

    @pytest.mark.asyncio
    async def test_create_survey_with_rating_questions(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_survey_data,
        valid_rating_question_data,
    ):
        """Тест создания опроса с рейтинговыми вопросами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_data = {**valid_survey_data, "questions": [valid_rating_question_data]}

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        question = data["questions"][0]
        assert question["question_type"] == "rating"
        assert question["min_rating"] == valid_rating_question_data["min_rating"]
        assert question["max_rating"] == valid_rating_question_data["max_rating"]

    @pytest.mark.asyncio
    async def test_create_survey_with_expiration(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_survey_data,
    ):
        """Тест создания опроса с датой истечения."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        from datetime import datetime, timedelta

        expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

        survey_data = {**valid_survey_data, "expires_at": expires_at}

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["expires_at"] is not None
        assert "T" in data["expires_at"]  # ISO format

    @pytest.mark.asyncio
    async def test_create_survey_with_limits(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        valid_survey_data,
    ):
        """Тест создания опроса с ограничениями."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_data = {
            **valid_survey_data,
            "max_responses": 100,
            "allow_anonymous": False,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["max_responses"] == 100
        assert data["allow_anonymous"] is False

    @pytest.mark.asyncio
    async def test_create_survey_admin_permissions(
        self,
        api_client,
        db_session,
        admin_user,
        auth_headers_factory,
        valid_survey_data,
    ):
        """Тест создания опроса администратором."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.post(
            "/api/surveys", json=valid_survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["creator_id"] == admin_user.id
        assert data["title"] == valid_survey_data["title"]

    @pytest.mark.asyncio
    async def test_create_survey_unicode_content(
        self,
        api_client,
        db_session,
        regular_user,
        auth_headers_factory,
        unicode_survey_data,
    ):
        """Тест создания опроса с Unicode контентом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.post(
            "/api/surveys", json=unicode_survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == unicode_survey_data["title"]
        assert data["description"] == unicode_survey_data["description"]

    @pytest.mark.asyncio
    async def test_create_survey_minimal_data(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с минимальными данными."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        minimal_data = {
            "title": "Minimal Survey",
            "description": "Basic description",
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=minimal_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Minimal Survey"
        assert data["is_public"] is True  # Default value
        assert data["is_active"] is True  # Default value


class TestSurveyRetrievalPositive:
    """Positive тесты получения опросов."""

    @pytest.mark.asyncio
    async def test_get_public_survey_by_id(self, api_client, db_session, sample_survey):
        """Тест получения публичного опроса по ID."""
        # Act
        response = await api_client.get(f"/api/surveys/{sample_survey.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_survey.id
        assert data["title"] == sample_survey.title
        assert data["description"] == sample_survey.description
        assert data["is_public"] == sample_survey.is_public
        assert data["is_active"] == sample_survey.is_active

    @pytest.mark.asyncio
    async def test_get_survey_with_questions(
        self, api_client, db_session, survey_with_questions
    ):
        """Тест получения опроса с вопросами."""
        # Act
        response = await api_client.get(f"/api/surveys/{survey_with_questions.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == survey_with_questions.id
        assert "questions" in data
        assert len(data["questions"]) > 0

    @pytest.mark.asyncio
    async def test_get_private_survey_with_token(
        self, api_client, db_session, sample_private_survey
    ):
        """Тест получения приватного опроса с токеном."""
        # Act
        response = await api_client.get(
            f"/api/surveys/{sample_private_survey.id}?token={sample_private_survey.access_token}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_private_survey.id
        assert data["is_public"] is False

    @pytest.mark.asyncio
    async def test_get_survey_by_creator(
        self, api_client, db_session, user_with_surveys, auth_headers_factory
    ):
        """Тест получения опроса его создателем."""
        # Arrange
        user, surveys = user_with_surveys
        headers = auth_headers_factory(user.id)
        survey = surveys[0]

        # Act
        response = await api_client.get(f"/api/surveys/{survey.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == survey.id
        assert data["creator_id"] == user.id

    @pytest.mark.asyncio
    async def test_get_survey_admin_access(
        self, api_client, db_session, admin_user, sample_survey, auth_headers_factory
    ):
        """Тест доступа администратора к любому опросу."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get(
            f"/api/surveys/{sample_survey.id}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_survey.id


class TestSurveyListsPositive:
    """Positive тесты списков опросов."""

    @pytest.mark.asyncio
    async def test_get_active_public_surveys(
        self, api_client, db_session, surveys_batch
    ):
        """Тест получения списка активных публичных опросов."""
        # Act
        response = await api_client.get("/api/surveys/active")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        for survey in data:
            assert survey["is_public"] is True
            assert survey["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_surveys_pagination(self, api_client, db_session, surveys_batch):
        """Тест пагинации списка опросов."""
        # Act
        response = await api_client.get("/api/surveys/active?skip=0&limit=5")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_get_user_surveys(
        self, api_client, db_session, user_with_surveys, auth_headers_factory
    ):
        """Тест получения опросов пользователя."""
        # Arrange
        user, surveys = user_with_surveys
        headers = auth_headers_factory(user.id)

        # Act
        response = await api_client.get("/api/surveys/my", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == len(surveys)
        for survey_data in data:
            assert survey_data["creator_id"] == user.id

    @pytest.mark.asyncio
    async def test_get_surveys_by_status(self, api_client, db_session, surveys_batch):
        """Тест фильтрации опросов по статусу."""
        # Act
        response = await api_client.get("/api/surveys/active?status=active")

        # Assert
        assert response.status_code == 200
        data = response.json()

        for survey in data:
            assert survey["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_surveys_search(self, api_client, db_session, surveys_batch):
        """Тест поиска опросов."""
        # Act
        response = await api_client.get("/api/surveys/active?search=test")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Результаты должны содержать "test" в title или description

    @pytest.mark.asyncio
    async def test_get_surveys_sorting(self, api_client, db_session, surveys_batch):
        """Тест сортировки списка опросов."""
        # Act
        response = await api_client.get(
            "/api/surveys/active?sort=created_at&order=desc"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 1:
            # Проверяем что отсортировано по убыванию даты
            dates = [survey["created_at"] for survey in data]
            assert dates == sorted(dates, reverse=True)

    @pytest.mark.asyncio
    async def test_get_empty_survey_list(self, api_client, db_session):
        """Тест получения пустого списка опросов."""
        # Act
        response = await api_client.get("/api/surveys/active")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Может быть пустым или содержать данные


class TestSurveyUpdatePositive:
    """Positive тесты обновления опросов."""

    @pytest.mark.asyncio
    async def test_update_survey_basic_fields(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления базовых полей опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "title": "Updated Survey Title",
            "description": "Updated description",
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Survey Title"
        assert data["description"] == "Updated description"
        assert data["id"] == sample_survey.id

    @pytest.mark.asyncio
    async def test_update_survey_status(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест изменения статуса опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "is_active": False,
            "is_public": False,
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_active"] is False
        assert data["is_public"] is False

    @pytest.mark.asyncio
    async def test_update_survey_partial(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест частичного обновления опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        original_description = sample_survey.description
        update_data = {
            "title": "Partially Updated Title",
            # description не обновляем
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Partially Updated Title"
        assert data["description"] == original_description  # Не изменился

    @pytest.mark.asyncio
    async def test_update_survey_settings(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления настроек опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "max_responses": 500,
            "allow_anonymous": False,
            "telegram_notifications": False,
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["max_responses"] == 500
        assert data["allow_anonymous"] is False
        assert data["telegram_notifications"] is False

    @pytest.mark.asyncio
    async def test_update_survey_expiration(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления даты истечения опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        from datetime import datetime, timedelta

        new_expires_at = (datetime.utcnow() + timedelta(days=60)).isoformat()

        update_data = {"expires_at": new_expires_at}

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["expires_at"] is not None
        assert data["expires_at"] != sample_survey.expires_at

    @pytest.mark.asyncio
    async def test_update_survey_admin_permissions(
        self, api_client, db_session, sample_survey, admin_user, auth_headers_factory
    ):
        """Тест обновления опроса администратором."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)
        update_data = {
            "title": "Admin Updated Survey",
            "is_active": False,
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Admin Updated Survey"
        assert data["is_active"] is False


class TestSurveyDeletionPositive:
    """Positive тесты удаления опросов."""

    @pytest.mark.asyncio
    async def test_delete_survey_by_creator(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест удаления опроса его создателем."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_id = sample_survey.id

        # Act
        response = await api_client.delete(f"/api/surveys/{survey_id}", headers=headers)

        # Assert
        assert response.status_code == 204

        # Проверяем что опрос удален
        get_response = await api_client.get(f"/api/surveys/{survey_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_survey_with_questions(
        self,
        api_client,
        db_session,
        survey_with_questions,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления опроса с вопросами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_id = survey_with_questions.id

        # Act
        response = await api_client.delete(f"/api/surveys/{survey_id}", headers=headers)

        # Assert
        assert response.status_code == 204

        # Проверяем что опрос и вопросы удалены
        get_response = await api_client.get(f"/api/surveys/{survey_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_survey_admin_permissions(
        self, api_client, db_session, sample_survey, admin_user, auth_headers_factory
    ):
        """Тест удаления опроса администратором."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)
        survey_id = sample_survey.id

        # Act
        response = await api_client.delete(f"/api/surveys/{survey_id}", headers=headers)

        # Assert
        assert response.status_code == 204

        # Проверяем что опрос удален
        get_response = await api_client.get(f"/api/surveys/{survey_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_inactive_survey(
        self,
        api_client,
        db_session,
        sample_inactive_survey,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления неактивного опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_id = sample_inactive_survey.id

        # Act
        response = await api_client.delete(f"/api/surveys/{survey_id}", headers=headers)

        # Assert
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_private_survey(
        self,
        api_client,
        db_session,
        sample_private_survey,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления приватного опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_id = sample_private_survey.id

        # Act
        response = await api_client.delete(f"/api/surveys/{survey_id}", headers=headers)

        # Assert
        assert response.status_code == 204
