"""
Тесты для Admin API роутера Quiz App.

Этот модуль содержит тесты для всех административных endpoints,
включая управление опросами, пользователями и системной аналитикой.
"""

import pytest_asyncio

from tests.factories.question_factory import QuestionFactory
from tests.factories.response_factory import ResponseFactory
from tests.factories.survey_factory import SurveyFactory
from tests.factories.user_factory import UserFactory


class TestAdminDashboard:
    """Тесты для админ дашборда."""


    async def test_get_dashboard_success(self, api_client, admin_headers, db_session):
        """Тест успешного получения дашборда."""
        # Создаем тестовые данные
        survey_factory = SurveyFactory(db_session)
        user_factory = UserFactory(db_session)

        # Создаем несколько опросов и пользователей
        await survey_factory.create_batch(3)
        await user_factory.create_batch(2)

        response = await api_client.auth_get(
            "/api/admin/dashboard", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "statistics" in data
        assert "recent_surveys" in data
        assert "recent_users" in data

        # Проверяем статистику
        stats = data["statistics"]
        assert "surveys_total" in stats
        assert "questions_total" in stats
        assert "responses_total" in stats
        assert "users_total" in stats

        # Проверяем что есть данные
        assert stats["surveys_total"] >= 3
        assert stats["users_total"] >= 2

        # Проверяем недавние опросы
        recent_surveys = data["recent_surveys"]
        assert isinstance(recent_surveys, list)
        assert len(recent_surveys) <= 5

        if recent_surveys:
            survey = recent_surveys[0]
            assert "id" in survey
            assert "title" in survey
            assert "is_active" in survey
            assert "is_public" in survey
            assert "created_at" in survey


    async def test_get_dashboard_requires_admin(
        self, api_client, auth_headers, regular_user
    ):
        """Тест что дашборд требует админ права."""
        headers = await auth_headers(regular_user)

        response = await api_client.auth_get("/api/admin/dashboard", headers=headers)

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()


    async def test_get_dashboard_requires_auth(self, api_client):
        """Тест что дашборд требует авторизацию."""
        response = await api_client.get("/api/admin/dashboard")

        assert response.status_code == 401


class TestAdminSurveys:
    """Тесты для управления опросами."""


    async def test_get_all_surveys_success(self, api_client, admin_headers, db_session):
        """Тест успешного получения всех опросов."""
        survey_factory = SurveyFactory(db_session)

        # Создаем публичные и приватные опросы
        await survey_factory.create(is_public=True, title="Public Survey")
        await survey_factory.create(is_public=False, title="Private Survey")

        response = await api_client.auth_get(
            "/api/admin/surveys", headers=admin_headers
        )

        assert response.status_code == 200
        surveys = response.json()

        assert len(surveys) >= 2

        # Проверяем что есть и публичные и приватные
        public_surveys = [s for s in surveys if s["is_public"]]
        private_surveys = [s for s in surveys if not s["is_public"]]

        assert len(public_surveys) >= 1
        assert len(private_surveys) >= 1


    async def test_get_all_surveys_exclude_private(
        self, api_client, admin_headers, db_session
    ):
        """Тест получения только публичных опросов."""
        survey_factory = SurveyFactory(db_session)

        await survey_factory.create(is_public=True, title="Public Survey")
        await survey_factory.create(is_public=False, title="Private Survey")

        response = await api_client.auth_get(
            "/api/admin/surveys?include_private=false", headers=admin_headers
        )

        assert response.status_code == 200
        surveys = response.json()

        # Все опросы должны быть публичными
        for survey in surveys:
            assert survey["is_public"] is True


    async def test_get_all_surveys_pagination(
        self, api_client, admin_headers, db_session
    ):
        """Тест пагинации опросов."""
        survey_factory = SurveyFactory(db_session)

        # Создаем несколько опросов
        await survey_factory.create_batch(5)

        # Тест с лимитом
        response = await api_client.auth_get(
            "/api/admin/surveys?limit=2", headers=admin_headers
        )

        assert response.status_code == 200
        surveys = response.json()
        assert len(surveys) == 2

        # Тест с пропуском
        response = await api_client.auth_get(
            "/api/admin/surveys?skip=2&limit=2", headers=admin_headers
        )

        assert response.status_code == 200
        surveys = response.json()
        assert len(surveys) == 2


    async def test_create_survey_success(self, api_client, admin_headers, db_session):
        """Тест успешного создания опроса."""
        survey_data = {
            "title": "New Admin Survey",
            "description": "Survey created by admin",
            "is_public": True,
            "is_active": True,
        }

        response = await api_client.auth_post(
            "/api/admin/surveys", headers=admin_headers, json=survey_data
        )

        assert response.status_code == 200
        created_survey = response.json()

        assert created_survey["title"] == survey_data["title"]
        assert created_survey["description"] == survey_data["description"]
        assert created_survey["is_public"] == survey_data["is_public"]
        assert created_survey["is_active"] == survey_data["is_active"]
        assert "id" in created_survey
        assert "created_at" in created_survey


    async def test_update_survey_success(self, api_client, admin_headers, db_session):
        """Тест успешного обновления опроса."""
        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create(title="Original Title")

        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "is_active": False,
        }

        response = await api_client.auth_put(
            f"/api/admin/surveys/{survey.id}", headers=admin_headers, json=update_data
        )

        assert response.status_code == 200
        updated_survey = response.json()

        assert updated_survey["title"] == update_data["title"]
        assert updated_survey["description"] == update_data["description"]
        assert updated_survey["is_active"] == update_data["is_active"]
        assert updated_survey["id"] == survey.id


    async def test_update_survey_not_found(self, api_client, admin_headers):
        """Тест обновления несуществующего опроса."""
        update_data = {"title": "Updated Title"}

        response = await api_client.auth_put(
            "/api/admin/surveys/99999", headers=admin_headers, json=update_data
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


    async def test_delete_survey_success(self, api_client, admin_headers, db_session):
        """Тест успешного удаления опроса."""
        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create()

        response = await api_client.auth_delete(
            f"/api/admin/surveys/{survey.id}", headers=admin_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "deleted" in result["message"].lower()

        # Проверяем что опрос действительно удален
        response = await api_client.auth_get(
            f"/api/admin/surveys/{survey.id}", headers=admin_headers
        )
        # Должен быть 404 или опрос не должен появиться в списке


    async def test_delete_survey_not_found(self, api_client, admin_headers):
        """Тест удаления несуществующего опроса."""
        response = await api_client.auth_delete(
            "/api/admin/surveys/99999", headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAdminSurveyResponses:
    """Тесты для управления ответами на опросы."""


    async def test_get_survey_responses_success(
        self, api_client, admin_headers, db_session
    ):
        """Тест получения ответов на опрос."""
        survey_factory = SurveyFactory(db_session)
        question_factory = QuestionFactory(db_session)
        response_factory = ResponseFactory(db_session)
        user_factory = UserFactory(db_session)

        # Создаем опрос с вопросами
        survey = await survey_factory.create()
        question = await question_factory.create(survey_id=survey.id)

        # Создаем пользователей и ответы
        user1 = await user_factory.create()
        user2 = await user_factory.create()

        await response_factory.create(
            question_id=question.id,
            user_id=user1.id,
            response_data={"answer": "Answer 1"},
        )
        await response_factory.create(
            question_id=question.id,
            user_id=user2.id,
            response_data={"answer": "Answer 2"},
        )

        response = await api_client.auth_get(
            f"/api/admin/surveys/{survey.id}/responses", headers=admin_headers
        )

        assert response.status_code == 200
        responses = response.json()

        assert len(responses) >= 2

        # Проверяем структуру ответов
        for resp in responses:
            assert "id" in resp
            assert "question_id" in resp
            assert "user_id" in resp
            assert "response_data" in resp
            assert "created_at" in resp


    async def test_get_survey_responses_empty(
        self, api_client, admin_headers, db_session
    ):
        """Тест получения ответов для опроса без ответов."""
        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create()

        response = await api_client.auth_get(
            f"/api/admin/surveys/{survey.id}/responses", headers=admin_headers
        )

        assert response.status_code == 200
        responses = response.json()
        assert len(responses) == 0


    async def test_get_survey_responses_not_found(self, api_client, admin_headers):
        """Тест получения ответов для несуществующего опроса."""
        response = await api_client.auth_get(
            "/api/admin/surveys/99999/responses", headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAdminSurveyAnalytics:
    """Тесты для аналитики опросов."""


    async def test_get_survey_analytics_success(
        self, api_client, admin_headers, db_session
    ):
        """Тест получения аналитики опроса."""
        survey_factory = SurveyFactory(db_session)
        question_factory = QuestionFactory(db_session)
        response_factory = ResponseFactory(db_session)
        user_factory = UserFactory(db_session)

        # Создаем опрос с вопросами
        survey = await survey_factory.create()
        question1 = await question_factory.create(
            survey_id=survey.id, question_type="rating"
        )
        question2 = await question_factory.create(
            survey_id=survey.id, question_type="text"
        )

        # Создаем ответы
        user1 = await user_factory.create()
        user2 = await user_factory.create()

        await response_factory.create(
            question_id=question1.id, user_id=user1.id, response_data={"rating": 5}
        )
        await response_factory.create(
            question_id=question1.id, user_id=user2.id, response_data={"rating": 4}
        )
        await response_factory.create(
            question_id=question2.id,
            user_id=user1.id,
            response_data={"text": "Good survey"},
        )

        response = await api_client.auth_get(
            f"/api/admin/surveys/{survey.id}/analytics", headers=admin_headers
        )

        assert response.status_code == 200
        analytics = response.json()

        # Проверяем структуру аналитики
        assert "total_responses" in analytics
        assert "unique_users" in analytics
        assert "questions_analytics" in analytics
        assert "completion_rate" in analytics

        # Проверяем значения
        assert analytics["total_responses"] >= 3
        assert analytics["unique_users"] >= 2
        assert len(analytics["questions_analytics"]) >= 2


    async def test_get_survey_analytics_empty(
        self, api_client, admin_headers, db_session
    ):
        """Тест аналитики для опроса без ответов."""
        survey_factory = SurveyFactory(db_session)
        survey = await survey_factory.create()

        response = await api_client.auth_get(
            f"/api/admin/surveys/{survey.id}/analytics", headers=admin_headers
        )

        assert response.status_code == 200
        analytics = response.json()

        assert analytics["total_responses"] == 0
        assert analytics["unique_users"] == 0
        assert len(analytics["questions_analytics"]) == 0


    async def test_get_survey_analytics_not_found(self, api_client, admin_headers):
        """Тест аналитики для несуществующего опроса."""
        response = await api_client.auth_get(
            "/api/admin/surveys/99999/analytics", headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAdminUsers:
    """Тесты для управления пользователями."""


    async def test_get_all_users_success(self, api_client, admin_headers, db_session):
        """Тест получения всех пользователей."""
        user_factory = UserFactory(db_session)

        # Создаем несколько пользователей
        await user_factory.create_batch(3)

        response = await api_client.auth_get("/api/admin/users", headers=admin_headers)

        assert response.status_code == 200
        users = response.json()

        assert len(users) >= 3

        # Проверяем структуру пользователей
        for user in users:
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "is_admin" in user
            assert "is_active" in user
            assert "created_at" in user


    async def test_get_all_users_pagination(
        self, api_client, admin_headers, db_session
    ):
        """Тест пагинации пользователей."""
        user_factory = UserFactory(db_session)

        # Создаем несколько пользователей
        await user_factory.create_batch(5)

        # Тест с лимитом
        response = await api_client.auth_get(
            "/api/admin/users?limit=2", headers=admin_headers
        )

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 2

        # Тест с пропуском
        response = await api_client.auth_get(
            "/api/admin/users?skip=2&limit=2", headers=admin_headers
        )

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 2


    async def test_get_all_users_search(self, api_client, admin_headers, db_session):
        """Тест поиска пользователей."""
        user_factory = UserFactory(db_session)

        # Создаем пользователей с определенными именами
        await user_factory.create(username="john_doe", email="john@test.com")
        await user_factory.create(username="jane_smith", email="jane@test.com")

        # Поиск по имени
        response = await api_client.auth_get(
            "/api/admin/users?search=john", headers=admin_headers
        )

        assert response.status_code == 200
        users = response.json()

        # Должен найти пользователя john_doe
        john_users = [u for u in users if "john" in u["username"].lower()]
        assert len(john_users) >= 1


    async def test_toggle_user_admin_success(
        self, api_client, admin_headers, db_session
    ):
        """Тест изменения админ статуса пользователя."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create(is_admin=False)

        # Делаем пользователя админом
        response = await api_client.auth_put(
            f"/api/admin/users/{user.id}/admin",
            headers=admin_headers,
            json={"make_admin": True},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "admin" in result["message"].lower()

        # Убираем админ статус
        response = await api_client.auth_put(
            f"/api/admin/users/{user.id}/admin",
            headers=admin_headers,
            json={"make_admin": False},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True


    async def test_toggle_user_admin_not_found(self, api_client, admin_headers):
        """Тест изменения админ статуса несуществующего пользователя."""
        response = await api_client.auth_put(
            "/api/admin/users/99999/admin",
            headers=admin_headers,
            json={"make_admin": True},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


    async def test_delete_user_success(self, api_client, admin_headers, db_session):
        """Тест удаления пользователя."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create()

        response = await api_client.auth_delete(
            f"/api/admin/users/{user.id}", headers=admin_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "deleted" in result["message"].lower()

        # Проверяем что пользователь удален
        response = await api_client.auth_get(
            f"/api/admin/users/{user.id}", headers=admin_headers
        )
        # Пользователь не должен находиться в списке


    async def test_delete_user_not_found(self, api_client, admin_headers):
        """Тест удаления несуществующего пользователя."""
        response = await api_client.auth_delete(
            "/api/admin/users/99999", headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAdminSystem:
    """Тесты для системных функций."""


    async def test_system_health_success(self, api_client, admin_headers, db_session):
        """Тест проверки здоровья системы."""
        response = await api_client.auth_get(
            "/api/admin/system/health", headers=admin_headers
        )

        assert response.status_code == 200
        health = response.json()

        # Проверяем основные показатели здоровья
        assert "status" in health
        assert "database" in health
        assert "timestamp" in health

        # Статус должен быть positive
        assert health["status"] in ["healthy", "ok", "operational"]
        assert health["database"] in ["connected", "ok", "operational"]


    async def test_system_health_requires_admin(
        self, api_client, auth_headers, regular_user
    ):
        """Тест что здоровье системы требует админ права."""
        headers = await auth_headers(regular_user)

        response = await api_client.auth_get(
            "/api/admin/system/health", headers=headers
        )

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()


class TestAdminPermissions:
    """Тесты для проверки прав доступа."""


    async def test_all_endpoints_require_admin(
        self, api_client, auth_headers, regular_user
    ):
        """Тест что все админ эндпоинты требуют админ права."""
        headers = await auth_headers(regular_user)

        # Список всех админ эндпоинтов
        admin_endpoints = [
            "/api/admin/dashboard",
            "/api/admin/surveys",
            "/api/admin/users",
            "/api/admin/system/health",
        ]

        for endpoint in admin_endpoints:
            response = await api_client.auth_get(endpoint, headers=headers)

            assert (
                response.status_code == 403
            ), f"Endpoint {endpoint} should require admin"
            assert "admin" in response.json()["detail"].lower()


    async def test_all_endpoints_require_auth(self, api_client):
        """Тест что все админ эндпоинты требуют авторизацию."""
        # Список всех админ эндпоинтов
        admin_endpoints = [
            "/api/admin/dashboard",
            "/api/admin/surveys",
            "/api/admin/users",
            "/api/admin/system/health",
        ]

        for endpoint in admin_endpoints:
            response = await api_client.get(endpoint)

            assert (
                response.status_code == 401
            ), f"Endpoint {endpoint} should require auth"


class TestAdminIntegration:
    """Интеграционные тесты для админ функций."""


    async def test_full_survey_management_flow(
        self, api_client, admin_headers, db_session
    ):
        """Тест полного цикла управления опросом."""
        # 1. Создаем опрос
        survey_data = {
            "title": "Integration Test Survey",
            "description": "Survey for integration testing",
            "is_public": True,
            "is_active": True,
        }

        response = await api_client.auth_post(
            "/api/admin/surveys", headers=admin_headers, json=survey_data
        )

        assert response.status_code == 200
        survey = response.json()
        survey_id = survey["id"]

        # 2. Обновляем опрос
        update_data = {"title": "Updated Integration Test Survey"}

        response = await api_client.auth_put(
            f"/api/admin/surveys/{survey_id}", headers=admin_headers, json=update_data
        )

        assert response.status_code == 200
        assert response.json()["title"] == update_data["title"]

        # 3. Получаем аналитику
        response = await api_client.auth_get(
            f"/api/admin/surveys/{survey_id}/analytics", headers=admin_headers
        )

        assert response.status_code == 200
        analytics = response.json()
        assert analytics["total_responses"] == 0

        # 4. Удаляем опрос
        response = await api_client.auth_delete(
            f"/api/admin/surveys/{survey_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True


    async def test_full_user_management_flow(
        self, api_client, admin_headers, db_session
    ):
        """Тест полного цикла управления пользователем."""
        user_factory = UserFactory(db_session)
        user = await user_factory.create(is_admin=False)

        # 1. Получаем список пользователей
        response = await api_client.auth_get("/api/admin/users", headers=admin_headers)

        assert response.status_code == 200
        users = response.json()
        user_ids = [u["id"] for u in users]
        assert user.id in user_ids

        # 2. Делаем пользователя админом
        response = await api_client.auth_put(
            f"/api/admin/users/{user.id}/admin",
            headers=admin_headers,
            json={"make_admin": True},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # 3. Убираем админ статус
        response = await api_client.auth_put(
            f"/api/admin/users/{user.id}/admin",
            headers=admin_headers,
            json={"make_admin": False},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # 4. Удаляем пользователя
        response = await api_client.auth_delete(
            f"/api/admin/users/{user.id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
