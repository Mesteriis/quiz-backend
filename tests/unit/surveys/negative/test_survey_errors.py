"""
Negative тесты для опросов - обработка ошибок.

Содержит тесты для различных ошибочных сценариев:
- Невалидные данные
- Отсутствие авторизации
- Неправильные права доступа
- Несуществующие ресурсы
- Нарушения бизнес-логики
"""

import pytest


class TestSurveyCreationErrors:
    """Negative тесты создания опросов."""

    @pytest.mark.asyncio
    async def test_create_survey_unauthorized(
        self, api_client, db_session, valid_survey_data
    ):
        """Тест создания опроса без авторизации."""
        # Act
        response = await api_client.post("/api/surveys", json=valid_survey_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert (
            "unauthorized" in data["detail"].lower()
            or "authentication" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_create_survey_invalid_token(
        self, api_client, db_session, valid_survey_data
    ):
        """Тест создания опроса с невалидным токеном."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = await api_client.post(
            "/api/surveys", json=valid_survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_survey_empty_title(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с пустым заголовком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "",
            "description": "Valid description",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("title" in str(error).lower() for error in data["detail"])

    @pytest.mark.asyncio
    async def test_create_survey_missing_required_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса без обязательных полей."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            # Отсутствуют title и description
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_survey_invalid_data_types(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с неправильными типами данных."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "Valid Title",
            "description": "Valid description",
            "is_public": "not_a_boolean",  # Должно быть boolean
            "max_responses": "not_a_number",  # Должно быть число
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_survey_negative_max_responses(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с отрицательным количеством ответов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "Valid Title",
            "description": "Valid description",
            "is_public": True,
            "max_responses": -1,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_survey_too_long_title(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса со слишком длинным заголовком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "A" * 1000,  # Слишком длинный заголовок
            "description": "Valid description",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_survey_invalid_expiration_date(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с невалидной датой истечения."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "Valid Title",
            "description": "Valid description",
            "is_public": True,
            "expires_at": "2020-01-01",  # Прошедшая дата
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_survey_malformed_json(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с некорректным JSON."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        headers["Content-Type"] = "application/json"

        # Act
        response = await api_client.post(
            "/api/surveys", data="invalid json", headers=headers
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_survey_with_invalid_questions(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с невалидными вопросами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "Valid Title",
            "description": "Valid description",
            "is_public": True,
            "questions": [
                {
                    "text": "",  # Пустой текст
                    "question_type": "invalid_type",  # Невалидный тип
                    "order": -1,  # Отрицательный порядок
                }
            ],
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestSurveyAccessErrors:
    """Negative тесты доступа к опросам."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_survey(self, api_client, db_session):
        """Тест получения несуществующего опроса."""
        # Act
        response = await api_client.get("/api/surveys/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_private_survey_without_token(
        self, api_client, db_session, sample_private_survey
    ):
        """Тест доступа к приватному опросу без токена."""
        # Act
        response = await api_client.get(f"/api/surveys/{sample_private_survey.id}")

        # Assert
        assert response.status_code in [403, 404]  # Зависит от реализации
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_private_survey_invalid_token(
        self, api_client, db_session, sample_private_survey
    ):
        """Тест доступа к приватному опросу с невалидным токеном."""
        # Act
        response = await api_client.get(
            f"/api/surveys/{sample_private_survey.id}?token=invalid_token"
        )

        # Assert
        assert response.status_code in [403, 404]
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_inactive_survey(
        self, api_client, db_session, sample_inactive_survey
    ):
        """Тест доступа к неактивному опросу."""
        # Act
        response = await api_client.get(f"/api/surveys/{sample_inactive_survey.id}")

        # Assert
        assert response.status_code in [403, 404]
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_survey_invalid_id_format(self, api_client, db_session):
        """Тест получения опроса с невалидным форматом ID."""
        # Act
        response = await api_client.get("/api/surveys/not_a_number")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestSurveyUpdateErrors:
    """Negative тесты обновления опросов."""

    @pytest.mark.asyncio
    async def test_update_survey_unauthorized(
        self, api_client, db_session, sample_survey
    ):
        """Тест обновления опроса без авторизации."""
        # Arrange
        update_data = {
            "title": "Updated Title",
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_survey_forbidden_user(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления чужого опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "title": "Updated Title",
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
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
    async def test_update_nonexistent_survey(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест обновления несуществующего опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "title": "Updated Title",
        }

        # Act
        response = await api_client.put(
            "/api/surveys/99999", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_survey_invalid_data(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления опроса с невалидными данными."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "",  # Пустой заголовок
            "max_responses": -1,  # Отрицательное число
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_survey_with_responses_restricted_fields(
        self,
        api_client,
        db_session,
        survey_with_responses,
        regular_user,
        auth_headers_factory,
    ):
        """Тест обновления опроса с ответами - ограниченные поля."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "is_public": False,  # Нельзя изменять публичность у опроса с ответами
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{survey_with_responses.id}",
            json=update_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_survey_past_expiration(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления опроса с истекшей датой."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        from datetime import datetime, timedelta

        past_date = (datetime.utcnow() - timedelta(days=1)).isoformat()

        update_data = {
            "expires_at": past_date,
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_survey_invalid_json(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления опроса с некорректным JSON."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        headers["Content-Type"] = "application/json"

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", data="invalid json", headers=headers
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_survey_conflicting_data(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест обновления опроса с противоречивыми данными."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        conflicting_data = {
            "is_public": False,
            "allow_anonymous": True,  # Противоречие: приватный опрос с анонимными ответами
        }

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=conflicting_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestSurveyDeletionErrors:
    """Negative тесты удаления опросов."""

    @pytest.mark.asyncio
    async def test_delete_survey_unauthorized(
        self, api_client, db_session, sample_survey
    ):
        """Тест удаления опроса без авторизации."""
        # Act
        response = await api_client.delete(f"/api/surveys/{sample_survey.id}")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_survey_forbidden_user(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест удаления чужого опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete(
            f"/api/surveys/{sample_survey.id}", headers=headers
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_nonexistent_survey(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест удаления несуществующего опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete("/api/surveys/99999", headers=headers)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_survey_with_responses(
        self,
        api_client,
        db_session,
        survey_with_responses,
        regular_user,
        auth_headers_factory,
    ):
        """Тест удаления опроса с ответами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete(
            f"/api/surveys/{survey_with_responses.id}", headers=headers
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
    async def test_double_delete_survey(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест повторного удаления опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_id = sample_survey.id

        # Первое удаление
        first_response = await api_client.delete(
            f"/api/surveys/{survey_id}", headers=headers
        )
        assert first_response.status_code == 204

        # Act - второе удаление
        response = await api_client.delete(f"/api/surveys/{survey_id}", headers=headers)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_survey_invalid_id_format(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест удаления опроса с невалидным форматом ID."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.delete("/api/surveys/not_a_number", headers=headers)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestSurveyListErrors:
    """Negative тесты списков опросов."""

    @pytest.mark.asyncio
    async def test_get_user_surveys_unauthorized(self, api_client, db_session):
        """Тест получения опросов пользователя без авторизации."""
        # Act
        response = await api_client.get("/api/surveys/my")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_surveys_invalid_pagination(self, api_client, db_session):
        """Тест получения списка опросов с невалидной пагинацией."""
        # Act
        response = await api_client.get("/api/surveys/active?skip=-1&limit=0")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_surveys_excessive_limit(self, api_client, db_session):
        """Тест получения списка опросов с чрезмерным лимитом."""
        # Act
        response = await api_client.get("/api/surveys/active?limit=10000")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_surveys_invalid_sort_field(self, api_client, db_session):
        """Тест получения списка опросов с невалидным полем сортировки."""
        # Act
        response = await api_client.get("/api/surveys/active?sort=invalid_field")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_surveys_invalid_status_filter(self, api_client, db_session):
        """Тест получения списка опросов с невалидным статусом."""
        # Act
        response = await api_client.get("/api/surveys/active?status=invalid_status")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_surveys_malformed_search(self, api_client, db_session):
        """Тест получения списка опросов с некорректным поиском."""
        # Act - поиск с слишком короткой строкой
        response = await api_client.get("/api/surveys/active?search=a")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_surveys_sql_injection_attempt(self, api_client, db_session):
        """Тест защиты от SQL инъекций в поиске."""
        # Act
        response = await api_client.get(
            "/api/surveys/active?search='; DROP TABLE surveys; --"
        )

        # Assert
        # Должно вернуть безопасный ответ, не ошибку SQL
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestSurveyBusinessLogicErrors:
    """Negative тесты бизнес-логики опросов."""

    @pytest.mark.asyncio
    async def test_exceed_survey_limit_per_user(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест превышения лимита опросов на пользователя."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем много опросов (предполагаем лимит 100)
        for i in range(101):
            survey_data = {
                "title": f"Survey {i}",
                "description": f"Description {i}",
                "is_public": True,
            }

            response = await api_client.post(
                "/api/surveys", json=survey_data, headers=headers
            )

            if i < 100:
                # Первые 100 должны создаться успешно
                assert response.status_code == 201
            else:
                # 101-й должен вернуть ошибку
                assert response.status_code == 422
                data = response.json()
                assert "detail" in data
                assert "limit" in data["detail"].lower()
                break

    @pytest.mark.asyncio
    async def test_create_survey_with_duplicate_title(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с дублирующимся заголовком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        survey_data = {
            "title": "Duplicate Title Survey",
            "description": "First survey",
            "is_public": True,
        }

        # Создаем первый опрос
        response1 = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )
        assert response1.status_code == 201

        # Act - создаем второй опрос с тем же заголовком
        survey_data["description"] = "Second survey"
        response2 = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response2.status_code == 422
        data = response2.json()
        assert "detail" in data
        assert (
            "duplicate" in data["detail"].lower()
            or "already exists" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_activate_expired_survey(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест активации истекшего опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        from datetime import datetime, timedelta

        past_date = (datetime.utcnow() - timedelta(days=1)).isoformat()

        # Создаем опрос с истекшей датой
        survey_data = {
            "title": "Expired Survey",
            "description": "This survey has expired",
            "is_public": True,
            "is_active": False,
            "expires_at": past_date,
        }

        create_response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )
        assert create_response.status_code == 201
        survey_id = create_response.json()["id"]

        # Act - пытаемся активировать истекший опрос
        update_data = {"is_active": True}
        response = await api_client.put(
            f"/api/surveys/{survey_id}", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_set_max_responses_below_current_count(
        self,
        api_client,
        db_session,
        survey_with_responses,
        regular_user,
        auth_headers_factory,
    ):
        """Тест установки max_responses ниже текущего количества ответов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Пытаемся установить max_responses = 1, когда уже есть 50 ответов
        update_data = {"max_responses": 1}

        # Act
        response = await api_client.put(
            f"/api/surveys/{survey_with_responses.id}",
            json=update_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert (
            "responses" in data["detail"].lower()
            or "cannot reduce" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_private_survey_without_access_method(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания приватного опроса без метода доступа."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        invalid_data = {
            "title": "Private Survey",
            "description": "Private survey without access method",
            "is_public": False,
            # Отсутствует access_password или другой метод доступа
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=invalid_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "access" in data["detail"].lower() or "private" in data["detail"].lower()
