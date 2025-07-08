"""
Positive тесты для получения ответов на вопросы опросов.

Тестирует успешное получение ответов:
- Получение отдельных ответов по ID
- Получение ответов по вопросу
- Получение ответов по опросу
- Получение ответов пользователя
- Фильтрация и поиск ответов
- Статистика ответов
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import patch


class TestResponseRetrieval:
    """Тесты получения отдельных ответов."""

    async def test_get_response_by_id_success(
        self, api_client, sample_response, response_test_utils
    ):
        """Тест успешного получения ответа по ID."""
        url = api_client.url_for("get_response", response_id=sample_response.id)

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        await response_test_utils.assert_response_structure(data)
        assert data["id"] == sample_response.id
        assert data["question_id"] == sample_response.question_id

    async def test_get_response_with_metadata(self, api_client, sample_response):
        """Тест получения ответа с метаданными."""
        url = api_client.url_for(
            "get_response", response_id=sample_response.id, include_metadata=True
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "metadata" in data
        assert "created_at" in data["metadata"]
        assert "updated_at" in data["metadata"]

    async def test_get_response_with_question_details(
        self, api_client, sample_response
    ):
        """Тест получения ответа с деталями вопроса."""
        url = api_client.url_for(
            "get_response", response_id=sample_response.id, include_question=True
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "question" in data
        assert data["question"]["id"] == sample_response.question_id
        assert "text" in data["question"]

    async def test_get_response_with_survey_context(self, api_client, sample_response):
        """Тест получения ответа с контекстом опроса."""
        url = api_client.url_for(
            "get_response", response_id=sample_response.id, include_survey=True
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "survey" in data
        assert "id" in data["survey"]
        assert "title" in data["survey"]


class TestResponsesByQuestion:
    """Тесты получения ответов по вопросу."""

    async def test_get_responses_by_question_success(
        self, api_client, sample_question, responses_batch
    ):
        """Тест успешного получения ответов по вопросу."""
        url = api_client.url_for(
            "get_responses_by_question", question_id=sample_question.id
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data
        assert len(data["responses"]) >= 1

        for resp in data["responses"]:
            assert resp["question_id"] == sample_question.id

    async def test_get_responses_by_question_with_pagination(
        self, api_client, sample_question, responses_batch
    ):
        """Тест получения ответов по вопросу с пагинацией."""
        url = api_client.url_for(
            "get_responses_by_question",
            question_id=sample_question.id,
            page=1,
            per_page=10,
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10
        assert "total" in data["pagination"]

    async def test_get_responses_by_question_with_sorting(
        self, api_client, sample_question, responses_batch
    ):
        """Тест получения ответов по вопросу с сортировкой."""
        url = api_client.url_for(
            "get_responses_by_question",
            question_id=sample_question.id,
            sort_by="created_at",
            sort_order="desc",
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data

        # Проверяем что ответы отсортированы по дате создания (убывание)
        if len(data["responses"]) > 1:
            for i in range(len(data["responses"]) - 1):
                current_date = data["responses"][i]["created_at"]
                next_date = data["responses"][i + 1]["created_at"]
                assert current_date >= next_date

    async def test_get_responses_by_question_with_filters(
        self, api_client, sample_question, responses_batch
    ):
        """Тест получения ответов по вопросу с фильтрами."""
        url = api_client.url_for(
            "get_responses_by_question",
            question_id=sample_question.id,
            date_from="2024-01-01",
            date_to="2024-12-31",
            is_anonymous=False,
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data

        # Проверяем применение фильтров
        for resp in data["responses"]:
            assert resp["question_id"] == sample_question.id
            # Проверяем что все ответы не анонимные
            assert resp.get("is_anonymous", True) is False


class TestResponsesBySurvey:
    """Тесты получения ответов по опросу."""

    async def test_get_responses_by_survey_success(
        self, api_client, sample_survey, user_responses
    ):
        """Тест успешного получения ответов по опросу."""
        url = api_client.url_for("get_responses_by_survey", survey_id=sample_survey.id)

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data
        assert len(data["responses"]) >= 1

    async def test_get_responses_by_survey_grouped_by_question(
        self, api_client, sample_survey, user_responses
    ):
        """Тест получения ответов по опросу, сгруппированных по вопросам."""
        url = api_client.url_for(
            "get_responses_by_survey", survey_id=sample_survey.id, group_by="question"
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "questions" in data

        for question_data in data["questions"]:
            assert "question_id" in question_data
            assert "responses" in question_data
            assert len(question_data["responses"]) >= 0

    async def test_get_responses_by_survey_with_statistics(
        self, api_client, sample_survey, user_responses
    ):
        """Тест получения ответов по опросу со статистикой."""
        url = api_client.url_for(
            "get_responses_by_survey",
            survey_id=sample_survey.id,
            include_statistics=True,
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "statistics" in data
        assert "total_responses" in data["statistics"]
        assert "completion_rate" in data["statistics"]
        assert "average_time" in data["statistics"]

    async def test_get_responses_by_survey_export_format(
        self, api_client, sample_survey, user_responses
    ):
        """Тест получения ответов по опросу в экспортном формате."""
        url = api_client.url_for(
            "get_responses_by_survey", survey_id=sample_survey.id, export_format="csv"
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        # Проверяем что возвращается CSV данные
        assert response.headers.get("content-type") == "text/csv"
        assert "attachment" in response.headers.get("content-disposition", "")


class TestResponsesByUser:
    """Тесты получения ответов пользователя."""

    async def test_get_user_responses_success(
        self, api_client, regular_user, user_responses
    ):
        """Тест успешного получения ответов пользователя."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("get_user_responses")

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data

        # Проверяем что все ответы принадлежат пользователю
        for resp in data["responses"]:
            assert resp["user_id"] == regular_user.id

    async def test_get_user_responses_by_survey(
        self, api_client, regular_user, sample_survey, user_responses
    ):
        """Тест получения ответов пользователя по конкретному опросу."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("get_user_responses", survey_id=sample_survey.id)

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data

        # Проверяем что все ответы принадлежат пользователю и опросу
        for resp in data["responses"]:
            assert resp["user_id"] == regular_user.id
            # Проверяем что ответ относится к правильному опросу
            assert "survey_id" in resp and resp["survey_id"] == sample_survey.id

    async def test_get_user_responses_with_progress(
        self, api_client, regular_user, survey_progress_data
    ):
        """Тест получения ответов пользователя с прогрессом."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("get_user_responses", include_progress=True)

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data
        assert "progress" in data

        # Проверяем структуру прогресса
        for survey_progress in data["progress"]:
            assert "survey_id" in survey_progress
            assert "completion_percentage" in survey_progress
            assert "questions_answered" in survey_progress
            assert "total_questions" in survey_progress

    async def test_get_user_responses_history(
        self, api_client, regular_user, user_responses
    ):
        """Тест получения истории ответов пользователя."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for(
            "get_user_responses", include_history=True, date_from="2024-01-01"
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data
        assert "history" in data

        # Проверяем что в истории есть информация о действиях
        for history_item in data["history"]:
            assert "action" in history_item
            assert "timestamp" in history_item
            assert "response_id" in history_item


class TestResponseSearch:
    """Тесты поиска ответов."""

    async def test_search_responses_by_text(self, api_client, responses_batch):
        """Тест поиска ответов по тексту."""
        url = api_client.url_for("search_responses", q="test response")

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data
        assert "search_metadata" in data
        assert data["search_metadata"]["query"] == "test response"

    async def test_search_responses_with_filters(self, api_client, responses_batch):
        """Тест поиска ответов с фильтрами."""
        url = api_client.url_for(
            "search_responses",
            q="response",
            answer_type="text",
            date_from="2024-01-01",
            is_anonymous=False,
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data

        # Проверяем применение фильтров
        for resp in data["responses"]:
            assert resp.get("is_anonymous", True) is False

    async def test_search_responses_with_highlighting(
        self, api_client, responses_batch
    ):
        """Тест поиска ответов с подсветкой найденного текста."""
        url = api_client.url_for("search_responses", q="response", highlight=True)

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "responses" in data

        # Проверяем что есть подсветка в результатах
        for resp in data["responses"]:
            if "highlight" in resp:
                assert isinstance(resp["highlight"], dict)


class TestResponseStatistics:
    """Тесты получения статистики ответов."""

    async def test_get_response_statistics_by_question(
        self, api_client, sample_question, responses_batch
    ):
        """Тест получения статистики ответов по вопросу."""
        url = api_client.url_for(
            "get_response_statistics", question_id=sample_question.id
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "statistics" in data
        assert "total_responses" in data["statistics"]
        assert "response_rate" in data["statistics"]
        assert "average_response_time" in data["statistics"]

    async def test_get_response_statistics_by_survey(
        self, api_client, sample_survey, user_responses
    ):
        """Тест получения статистики ответов по опросу."""
        url = api_client.url_for("get_response_statistics", survey_id=sample_survey.id)

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "statistics" in data
        assert "total_responses" in data["statistics"]
        assert "completion_rate" in data["statistics"]
        assert "questions_stats" in data["statistics"]

    async def test_get_response_statistics_with_breakdown(
        self, api_client, sample_survey, user_responses
    ):
        """Тест получения статистики ответов с разбивкой."""
        url = api_client.url_for(
            "get_response_statistics",
            survey_id=sample_survey.id,
            breakdown_by="question_type",
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "statistics" in data
        assert "breakdown" in data["statistics"]

        # Проверяем структуру разбивки
        for breakdown_item in data["statistics"]["breakdown"]:
            assert "category" in breakdown_item
            assert "count" in breakdown_item
            assert "percentage" in breakdown_item

    async def test_get_response_statistics_time_series(
        self, api_client, sample_survey, user_responses
    ):
        """Тест получения статистики ответов во времени."""
        url = api_client.url_for(
            "get_response_statistics",
            survey_id=sample_survey.id,
            time_series=True,
            period="day",
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "statistics" in data
        assert "time_series" in data["statistics"]

        # Проверяем структуру временных рядов
        for time_point in data["statistics"]["time_series"]:
            assert "date" in time_point
            assert "count" in time_point
            assert "cumulative_count" in time_point


class TestResponseValidation:
    """Тесты валидации ответов при получении."""

    async def test_get_response_validation_status(
        self, api_client, sample_response, validation_test_data
    ):
        """Тест получения статуса валидации ответа."""
        url = api_client.url_for(
            "get_response_validation", response_id=sample_response.id
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "validation_status" in data
        assert "is_valid" in data["validation_status"]
        assert "validation_errors" in data["validation_status"]

    async def test_get_bulk_response_validation(
        self, api_client, responses_batch, validation_test_data
    ):
        """Тест получения валидации для множества ответов."""
        response_ids = [resp.id for resp in responses_batch[:5]]

        url = api_client.url_for("get_bulk_response_validation")
        request_data = {"response_ids": response_ids}

        response = await api_client.post(url, json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "validations" in data
        assert len(data["validations"]) == len(response_ids)

        for validation in data["validations"]:
            assert "response_id" in validation
            assert "is_valid" in validation
            assert validation["response_id"] in response_ids
