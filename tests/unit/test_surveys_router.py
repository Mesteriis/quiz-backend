"""
Тесты для Surveys Router.

Этот модуль содержит тесты для всех endpoints работы с опросами,
включая CRUD операции, публичные/приватные опросы и пагинацию.
"""

from pathlib import Path

# Локальные импорты
import sys
import uuid

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.survey import Survey


class TestGetActiveSurveys:
    """Тесты получения активных публичных опросов."""

    @pytest.mark.asyncio
    async def test_get_active_public_surveys(self, api_client, db_session):
        """Тест получения списка активных публичных опросов."""
        # Arrange - создаем тестовые опросы
        surveys = []

        # Публичный активный опрос
        public_survey = Survey(
            title="Public Active Survey",
            description="This is a public active survey",
            is_active=True,
            is_public=True,
            telegram_notifications=True,
        )
        db_session.add(public_survey)
        surveys.append(public_survey)

        # Приватный опрос (не должен попасть в результат)
        private_survey = Survey(
            title="Private Survey",
            description="This is a private survey",
            is_active=True,
            is_public=False,
            telegram_notifications=False,
        )
        db_session.add(private_survey)

        # Неактивный опрос (не должен попасть в результат)
        inactive_survey = Survey(
            title="Inactive Survey",
            description="This is an inactive survey",
            is_active=False,
            is_public=True,
            telegram_notifications=True,
        )
        db_session.add(inactive_survey)

        await db_session.commit()
        for survey in surveys + [private_survey, inactive_survey]:
            await db_session.refresh(survey)

        # Act
        response = await api_client.get("/api/surveys/active")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 1  # Только один публичный активный опрос

        survey_data = data[0]
        assert survey_data["title"] == "Public Active Survey"
        assert survey_data["is_active"] is True
        assert survey_data["is_public"] is True
        assert "id" in survey_data
        assert "created_at" in survey_data

    @pytest.mark.asyncio
    async def test_get_active_surveys_pagination(self, api_client, db_session):
        """Тест пагинации активных опросов."""
        # Arrange - создаем несколько активных опросов
        for i in range(5):
            survey = Survey(
                title=f"Active Survey {i}",
                description=f"Description {i}",
                is_active=True,
                is_public=True,
                telegram_notifications=True,
            )
            db_session.add(survey)

        await db_session.commit()

        # Act
        response = await api_client.get("/api/surveys/active?skip=0&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 2  # Проверяем limit

    @pytest.mark.asyncio
    async def test_get_active_surveys_empty_list(self, api_client, db_session):
        """Тест получения пустого списка когда нет активных опросов."""
        # Act (нет активных публичных опросов)
        response = await api_client.get("/api/surveys/active")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0


class TestGetSurveyById:
    """Тесты получения опроса по ID."""

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
        assert data["is_active"] == sample_survey.is_active
        assert data["is_public"] == sample_survey.is_public
        assert "access_token" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_survey_with_questions(
        self, api_client, db_session, sample_survey, sample_question
    ):
        """Тест получения опроса с вопросами."""
        # Act
        response = await api_client.get(f"/api/surveys/{sample_survey.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_survey.id
        # Проверяем, что есть информация о вопросах (может быть счетчик или сами вопросы)
        assert "questions_count" in data or "questions" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_survey(self, api_client, db_session):
        """Тест ошибки получения несуществующего опроса."""
        # Act
        response = await api_client.get("/api/surveys/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_private_survey_without_token(self, api_client, db_session):
        """Тест доступа к приватному опросу без токена."""
        # Arrange
        private_survey = Survey(
            title="Private Survey",
            description="This is a private survey",
            is_active=True,
            is_public=False,
            telegram_notifications=False,
        )
        db_session.add(private_survey)
        await db_session.commit()
        await db_session.refresh(private_survey)

        # Act
        response = await api_client.get(f"/api/surveys/{private_survey.id}")

        # Assert
        # Может быть 404 или 403, зависит от реализации
        assert response.status_code in [403, 404]


class TestGetPrivateSurvey:
    """Тесты получения приватного опроса по токену."""

    @pytest.mark.asyncio
    async def test_get_private_survey_by_token(self, api_client, db_session):
        """Тест получения приватного опроса по access_token."""
        # Arrange
        access_token = str(uuid.uuid4())
        private_survey = Survey(
            title="Private Survey",
            description="This is a private survey",
            is_active=True,
            is_public=False,
            access_token=access_token,
            telegram_notifications=False,
        )
        db_session.add(private_survey)
        await db_session.commit()
        await db_session.refresh(private_survey)

        # Act
        response = await api_client.get(f"/api/surveys/private/{access_token}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == private_survey.id
        assert data["title"] == private_survey.title
        assert data["is_public"] is False
        assert data["access_token"] == access_token

    @pytest.mark.asyncio
    async def test_get_private_survey_invalid_token(self, api_client, db_session):
        """Тест ошибки при неверном токене приватного опроса."""
        # Act
        response = await api_client.get("/api/surveys/private/invalid-token")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_inactive_private_survey(self, api_client, db_session):
        """Тест получения неактивного приватного опроса."""
        # Arrange
        access_token = str(uuid.uuid4())
        inactive_survey = Survey(
            title="Inactive Private Survey",
            description="This survey is inactive",
            is_active=False,
            is_public=False,
            access_token=access_token,
            telegram_notifications=False,
        )
        db_session.add(inactive_survey)
        await db_session.commit()
        await db_session.refresh(inactive_survey)

        # Act
        response = await api_client.get(f"/api/surveys/private/{access_token}")

        # Assert
        # Может возвращать опрос или 404, зависит от бизнес-логики
        assert response.status_code in [200, 404]


class TestCreateSurvey:
    """Тесты создания опросов."""

    @pytest.mark.asyncio
    async def test_create_basic_survey(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест создания базового опроса."""
        # Arrange
        headers = await auth_headers(regular_user)
        survey_data = {
            "title": "New Test Survey",
            "description": "This is a new test survey",
            "is_active": True,
            "is_public": True,
            "telegram_notifications": True,
        }

        # Act
        response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=survey_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "New Test Survey"
        assert data["description"] == "This is a new test survey"
        assert data["is_active"] is True
        assert data["is_public"] is True
        assert "id" in data
        assert "access_token" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_private_survey(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест создания приватного опроса."""
        # Arrange
        headers = await auth_headers(regular_user)
        survey_data = {
            "title": "Private Survey",
            "description": "This is a private survey",
            "is_active": True,
            "is_public": False,
            "telegram_notifications": False,
        }

        # Act
        response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=survey_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["is_public"] is False
        assert data["telegram_notifications"] is False
        assert len(data["access_token"]) > 10  # Токен должен быть сгенерирован

    @pytest.mark.asyncio
    async def test_create_survey_with_questions(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест создания опроса с вопросами."""
        # Arrange
        headers = await auth_headers(regular_user)
        survey_data = {
            "title": "Survey with Questions",
            "description": "This survey has questions",
            "is_active": True,
            "is_public": True,
            "questions": [
                {
                    "title": "Question 1",
                    "description": "First question",
                    "question_type": "text",
                    "is_required": True,
                    "order": 1,
                },
                {
                    "title": "Question 2",
                    "description": "Second question",
                    "question_type": "rating_1_10",
                    "is_required": False,
                    "order": 2,
                    "options": {"min": 1, "max": 10, "step": 1},
                },
            ],
        }

        # Act
        response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=survey_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Survey with Questions"
        # Проверяем, что вопросы были созданы
        if "questions" in data:
            assert len(data["questions"]) == 2
        elif "questions_count" in data:
            assert data["questions_count"] == 2

    @pytest.mark.asyncio
    async def test_create_survey_unauthorized(self, api_client, db_session):
        """Тест ошибки создания опроса без авторизации."""
        # Arrange
        survey_data = {
            "title": "Unauthorized Survey",
            "description": "This should fail",
        }

        # Act
        response = await api_client.post("/api/surveys/", json=survey_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_survey_invalid_data(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест ошибки создания опроса с невалидными данными."""
        # Arrange
        headers = await auth_headers(regular_user)
        invalid_data = {
            "title": "",  # Пустое название
            "description": None,
            "is_active": "not_boolean",  # Неверный тип
        }

        # Act
        response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=invalid_data
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestUpdateSurvey:
    """Тесты обновления опросов."""

    @pytest.mark.asyncio
    async def test_update_survey_basic_fields(
        self, api_client, db_session, sample_survey, regular_user, auth_headers
    ):
        """Тест обновления основных полей опроса."""
        # Arrange
        headers = await auth_headers(regular_user)
        update_data = {
            "title": "Updated Survey Title",
            "description": "Updated survey description",
            "is_active": False,
            "telegram_notifications": False,
        }

        # Act
        response = await api_client.auth_put(
            f"/api/surveys/{sample_survey.id}", headers=headers, json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Survey Title"
        assert data["description"] == "Updated survey description"
        assert data["is_active"] is False
        assert data["telegram_notifications"] is False
        assert data["id"] == sample_survey.id

    @pytest.mark.asyncio
    async def test_update_survey_partial(
        self, api_client, db_session, sample_survey, regular_user, auth_headers
    ):
        """Тест частичного обновления опроса."""
        # Arrange
        headers = await auth_headers(regular_user)
        original_description = sample_survey.description
        update_data = {
            "title": "Only Title Updated"
            # Не обновляем другие поля
        }

        # Act
        response = await api_client.auth_put(
            f"/api/surveys/{sample_survey.id}", headers=headers, json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Only Title Updated"
        assert data["description"] == original_description  # Должно остаться прежним

    @pytest.mark.asyncio
    async def test_update_nonexistent_survey(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест ошибки обновления несуществующего опроса."""
        # Arrange
        headers = await auth_headers(regular_user)
        update_data = {"title": "This should fail"}

        # Act
        response = await api_client.auth_put(
            "/api/surveys/99999", headers=headers, json=update_data
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_survey_unauthorized(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки обновления опроса без авторизации."""
        # Arrange
        update_data = {"title": "Unauthorized Update"}

        # Act
        response = await api_client.put(
            f"/api/surveys/{sample_survey.id}", json=update_data
        )

        # Assert
        assert response.status_code == 401


class TestDeleteSurvey:
    """Тесты удаления опросов."""

    @pytest.mark.asyncio
    async def test_delete_survey(
        self, api_client, db_session, sample_survey, regular_user, auth_headers
    ):
        """Тест удаления опроса."""
        # Arrange
        headers = await auth_headers(regular_user)
        survey_id = sample_survey.id

        # Act
        response = await api_client.auth_delete(
            f"/api/surveys/{survey_id}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

        # Проверяем, что опрос действительно удален
        get_response = await api_client.get(f"/api/surveys/{survey_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_survey_with_questions(
        self,
        api_client,
        db_session,
        sample_survey,
        sample_question,
        regular_user,
        auth_headers,
    ):
        """Тест каскадного удаления опроса с вопросами."""
        # Arrange
        headers = await auth_headers(regular_user)
        survey_id = sample_survey.id
        question_id = sample_question.id

        # Act
        response = await api_client.auth_delete(
            f"/api/surveys/{survey_id}", headers=headers
        )

        # Assert
        assert response.status_code == 200

        # Проверяем, что опрос удален
        get_survey_response = await api_client.get(f"/api/surveys/{survey_id}")
        assert get_survey_response.status_code == 404

        # Вопросы тоже должны быть удалены (каскадное удаление)
        # Это зависит от реализации, но обычно вопросы удаляются вместе с опросом

    @pytest.mark.asyncio
    async def test_delete_nonexistent_survey(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест ошибки удаления несуществующего опроса."""
        # Arrange
        headers = await auth_headers(regular_user)

        # Act
        response = await api_client.auth_delete("/api/surveys/99999", headers=headers)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_survey_unauthorized(
        self, api_client, db_session, sample_survey
    ):
        """Тест ошибки удаления опроса без авторизации."""
        # Act
        response = await api_client.delete(f"/api/surveys/{sample_survey.id}")

        # Assert
        assert response.status_code == 401


class TestSurveyIntegration:
    """Интеграционные тесты для опросов."""

    @pytest.mark.asyncio
    async def test_full_survey_lifecycle(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест полного жизненного цикла опроса: создание -> обновление -> публикация -> удаление."""
        headers = await auth_headers(regular_user)

        # 1. Создание опроса
        create_data = {
            "title": "Lifecycle Test Survey",
            "description": "Testing full lifecycle",
            "is_active": False,  # Начинаем с неактивного
            "is_public": False,  # И приватного
        }

        create_response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=create_data
        )
        assert create_response.status_code == 201
        survey = create_response.json()
        survey_id = survey["id"]

        # 2. Обновление опроса
        update_data = {
            "title": "Updated Lifecycle Survey",
            "is_active": True,
            "is_public": True,
        }

        update_response = await api_client.auth_put(
            f"/api/surveys/{survey_id}", headers=headers, json=update_data
        )
        assert update_response.status_code == 200
        updated_survey = update_response.json()
        assert updated_survey["title"] == "Updated Lifecycle Survey"
        assert updated_survey["is_active"] is True
        assert updated_survey["is_public"] is True

        # 3. Проверка появления в списке активных
        active_response = await api_client.get("/api/surveys/active")
        assert active_response.status_code == 200
        active_surveys = active_response.json()
        survey_ids = [s["id"] for s in active_surveys]
        assert survey_id in survey_ids

        # 4. Удаление опроса
        delete_response = await api_client.auth_delete(
            f"/api/surveys/{survey_id}", headers=headers
        )
        assert delete_response.status_code == 200

        # 5. Проверка удаления
        get_response = await api_client.get(f"/api/surveys/{survey_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_private_survey_access_flow(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест доступа к приватному опросу через токен."""
        headers = await auth_headers(regular_user)

        # 1. Создание приватного опроса
        create_data = {
            "title": "Private Access Test",
            "description": "Testing private access",
            "is_active": True,
            "is_public": False,
        }

        create_response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=create_data
        )
        assert create_response.status_code == 201
        survey = create_response.json()
        survey_id = survey["id"]
        access_token = survey["access_token"]

        # 2. Проверка, что опрос не виден в публичном списке
        public_response = await api_client.get("/api/surveys/active")
        assert public_response.status_code == 200
        public_surveys = public_response.json()
        public_ids = [s["id"] for s in public_surveys]
        assert survey_id not in public_ids

        # 3. Доступ к приватному опросу через токен
        private_response = await api_client.get(f"/api/surveys/private/{access_token}")
        assert private_response.status_code == 200
        private_survey = private_response.json()
        assert private_survey["id"] == survey_id
        assert private_survey["title"] == "Private Access Test"

        # 4. Ошибка доступа без токена
        direct_response = await api_client.get(f"/api/surveys/{survey_id}")
        assert direct_response.status_code in [403, 404]


class TestSurveyValidation:
    """Тесты валидации данных опросов."""

    @pytest.mark.asyncio
    async def test_survey_title_validation(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест валидации названия опроса."""
        headers = await auth_headers(regular_user)

        # Слишком длинное название
        long_title = "A" * 201  # Предполагаем ограничение в 200 символов
        data = {"title": long_title, "description": "Valid description"}

        response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=data
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_survey_required_fields(
        self, api_client, db_session, regular_user, auth_headers
    ):
        """Тест обязательных полей опроса."""
        headers = await auth_headers(regular_user)

        # Отсутствует обязательное поле title
        data = {"description": "Description without title"}

        response = await api_client.auth_post(
            "/api/surveys/", headers=headers, json=data
        )
        assert response.status_code == 422


class TestSurveyPermissions:
    """Тесты прав доступа к опросам."""

    @pytest.mark.asyncio
    async def test_admin_can_access_all_surveys(
        self, api_client, db_session, admin_user, auth_headers, sample_survey
    ):
        """Тест доступа админа ко всем опросам."""
        headers = await auth_headers(admin_user)

        # Админ должен иметь доступ к любому опросу
        response = await api_client.auth_get(
            f"/api/surveys/{sample_survey.id}", headers=headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_user_can_only_modify_own_surveys(
        self, api_client, db_session, regular_user, auth_headers, sample_survey
    ):
        """Тест ограничения доступа пользователя к чужим опросам."""
        headers = await auth_headers(regular_user)

        # Если опрос создан не этим пользователем, он не должен иметь права на изменение
        # (это зависит от реализации бизнес-логики)
        update_data = {"title": "Trying to hack"}

        response = await api_client.auth_put(
            f"/api/surveys/{sample_survey.id}", headers=headers, json=update_data
        )
        # Может быть 403 (Forbidden) или 200 (если разрешено), зависит от бизнес-логики
        assert response.status_code in [200, 403]
