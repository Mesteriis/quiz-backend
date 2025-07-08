"""
Negative тесты для доступа и управления ответами.

Тестирует обработку ошибок при:
- Получении ответов
- Обновлении ответов
- Удалении ответов
- Массовых операциях
- Правах доступа
- Валидации операций
"""

import pytest
from typing import Dict, Any
from unittest.mock import patch


class TestResponseRetrievalErrors:
    """Тесты ошибок получения ответов."""

    async def test_get_response_not_found(self, api_client):
        """Тест получения несуществующего ответа."""
        url = api_client.url_for("get_response", response_id="non_existent_id")

        response = await api_client.get(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    async def test_get_response_invalid_id_format(self, api_client):
        """Тест получения ответа с неправильным форматом ID."""
        url = api_client.url_for("get_response", response_id="invalid-id-format")

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "id" in data["validation_error"]["field_errors"]

    async def test_get_response_unauthorized_access(self, api_client, sample_response):
        """Тест получения ответа без прав доступа."""
        url = api_client.url_for("get_response", response_id=sample_response.id)

        # Симулируем отсутствие прав
        with patch(
            "apps.responses.services.ResponseService.check_access", return_value=False
        ):
            response = await api_client.get(url)
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert "access denied" in data["error"].lower()

    async def test_get_responses_by_question_not_found(self, api_client):
        """Тест получения ответов по несуществующему вопросу."""
        url = api_client.url_for(
            "get_responses_by_question", question_id="non_existent_question"
        )

        response = await api_client.get(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "question not found" in data["error"].lower()

    async def test_get_responses_by_survey_not_found(self, api_client):
        """Тест получения ответов по несуществующему опросу."""
        url = api_client.url_for(
            "get_responses_by_survey", survey_id="non_existent_survey"
        )

        response = await api_client.get(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "survey not found" in data["error"].lower()

    async def test_get_responses_with_invalid_pagination(
        self, api_client, sample_question
    ):
        """Тест получения ответов с неправильными параметрами пагинации."""
        url = api_client.url_for(
            "get_responses_by_question",
            question_id=sample_question.id,
            page=-1,
            per_page=0,
        )

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "page" in data["validation_error"]["field_errors"]
        assert "per_page" in data["validation_error"]["field_errors"]

    async def test_get_responses_with_invalid_date_range(
        self, api_client, sample_question
    ):
        """Тест получения ответов с неправильным диапазоном дат."""
        url = api_client.url_for(
            "get_responses_by_question",
            question_id=sample_question.id,
            date_from="2024-12-31",
            date_to="2024-01-01",  # date_to раньше date_from
        )

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "date_range" in data["validation_error"]["field_errors"]


class TestResponseUpdateErrors:
    """Тесты ошибок обновления ответов."""

    async def test_update_response_not_found(self, api_client, regular_user):
        """Тест обновления несуществующего ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id="non_existent_id")

        update_data = {"answer": {"value": "Updated response"}}

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    async def test_update_response_unauthorized(self, api_client, sample_response):
        """Тест обновления ответа без авторизации."""
        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {"answer": {"value": "Unauthorized update"}}

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "unauthorized" in data["error"].lower()

    async def test_update_response_wrong_user(
        self, api_client, sample_response, regular_user
    ):
        """Тест обновления ответа другого пользователя."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {"answer": {"value": "Wrong user update"}}

        # Симулируем что ответ принадлежит другому пользователю
        with patch(
            "apps.responses.services.ResponseService.check_ownership",
            return_value=False,
        ):
            response = await api_client.put(url, json=update_data)
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert "permission denied" in data["error"].lower()

    async def test_update_response_invalid_data(
        self, api_client, sample_response, regular_user
    ):
        """Тест обновления ответа с неправильными данными."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {
            "answer": {"value": "x" * 100000}  # Слишком длинный ответ
        }

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "answer" in data["validation_error"]["field_errors"]

    async def test_update_response_empty_data(
        self, api_client, sample_response, regular_user
    ):
        """Тест обновления ответа с пустыми данными."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {}  # Пустые данные

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "no data provided" in data["validation_error"]["message"].lower()

    async def test_update_response_after_survey_closed(
        self, api_client, sample_response, regular_user
    ):
        """Тест обновления ответа после закрытия опроса."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {"answer": {"value": "Update after survey closed"}}

        with patch(
            "apps.surveys.services.SurveyService.is_survey_active", return_value=False
        ):
            response = await api_client.put(url, json=update_data)
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert "survey closed" in data["error"].lower()


class TestResponseDeletionErrors:
    """Тесты ошибок удаления ответов."""

    async def test_delete_response_not_found(self, api_client, regular_user):
        """Тест удаления несуществующего ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id="non_existent_id")

        response = await api_client.delete(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    async def test_delete_response_unauthorized(self, api_client, sample_response):
        """Тест удаления ответа без авторизации."""
        url = api_client.url_for("delete_response", response_id=sample_response.id)

        response = await api_client.delete(url)
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "unauthorized" in data["error"].lower()

    async def test_delete_response_wrong_user(
        self, api_client, sample_response, regular_user
    ):
        """Тест удаления ответа другого пользователя."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id=sample_response.id)

        with patch(
            "apps.responses.services.ResponseService.check_ownership",
            return_value=False,
        ):
            response = await api_client.delete(url)
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert "permission denied" in data["error"].lower()

    async def test_delete_response_already_deleted(
        self, api_client, sample_response, regular_user
    ):
        """Тест удаления уже удаленного ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id=sample_response.id)

        # Первое удаление
        response = await api_client.delete(url)
        assert response.status_code == 204

        # Второе удаление того же ответа
        response = await api_client.delete(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert (
            "already deleted" in data["error"].lower()
            or "not found" in data["error"].lower()
        )

    async def test_delete_response_with_dependencies(
        self, api_client, sample_response, regular_user
    ):
        """Тест удаления ответа с зависимостями."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id=sample_response.id)

        # Симулируем наличие зависимостей
        with patch(
            "apps.responses.services.ResponseService.has_dependencies",
            return_value=True,
        ):
            response = await api_client.delete(url)
            assert response.status_code == 409

            data = response.json()
            assert "error" in data
            assert "dependencies" in data["error"].lower()


class TestBulkOperationsErrors:
    """Тесты ошибок массовых операций."""

    async def test_bulk_update_responses_empty_list(self, api_client, regular_user):
        """Тест массового обновления с пустым списком ID."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_update_responses")

        update_data = {
            "response_ids": [],  # Пустой список
            "updates": {"metadata": {"bulk_updated": True}},
        }

        response = await api_client.post(url, json=update_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "response_ids" in data["validation_error"]["field_errors"]

    async def test_bulk_update_responses_too_many_ids(self, api_client, regular_user):
        """Тест массового обновления со слишком многими ID."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_update_responses")

        update_data = {
            "response_ids": ["id_" + str(i) for i in range(1000)],  # Слишком много ID
            "updates": {"metadata": {"bulk_updated": True}},
        }

        response = await api_client.post(url, json=update_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "too many" in data["validation_error"]["field_errors"]["response_ids"]

    async def test_bulk_update_responses_invalid_ids(self, api_client, regular_user):
        """Тест массового обновления с несуществующими ID."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_update_responses")

        update_data = {
            "response_ids": ["non_existent_1", "non_existent_2"],
            "updates": {"metadata": {"bulk_updated": True}},
        }

        response = await api_client.post(url, json=update_data)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    async def test_bulk_update_responses_unauthorized(
        self, api_client, responses_batch
    ):
        """Тест массового обновления без авторизации."""
        url = api_client.url_for("bulk_update_responses")

        response_ids = [resp.id for resp in responses_batch[:3]]
        update_data = {
            "response_ids": response_ids,
            "updates": {"metadata": {"bulk_updated": True}},
        }

        response = await api_client.post(url, json=update_data)
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "unauthorized" in data["error"].lower()

    async def test_bulk_delete_responses_mixed_permissions(
        self, api_client, responses_batch, regular_user
    ):
        """Тест массового удаления с смешанными правами доступа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_delete_responses")

        response_ids = [resp.id for resp in responses_batch[:3]]
        delete_data = {"response_ids": response_ids, "reason": "Bulk delete test"}

        # Симулируем что только часть ответов доступна пользователю
        with patch(
            "apps.responses.services.ResponseService.check_bulk_ownership",
            return_value={"owned": [response_ids[0]], "not_owned": response_ids[1:]},
        ):
            response = await api_client.post(url, json=delete_data)
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert "permission denied" in data["error"].lower()
            assert "not_owned" in data


class TestResponseSearchErrors:
    """Тесты ошибок поиска ответов."""

    async def test_search_responses_empty_query(self, api_client):
        """Тест поиска с пустым запросом."""
        url = api_client.url_for("search_responses", q="")

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "query" in data["validation_error"]["field_errors"]

    async def test_search_responses_invalid_filters(self, api_client):
        """Тест поиска с неправильными фильтрами."""
        url = api_client.url_for(
            "search_responses",
            q="response",
            answer_type="invalid_type",
            date_from="invalid_date",
        )

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "answer_type" in data["validation_error"]["field_errors"]
        assert "date_from" in data["validation_error"]["field_errors"]

    async def test_search_responses_too_broad_query(self, api_client):
        """Тест поиска со слишком широким запросом."""
        url = api_client.url_for("search_responses", q="a")  # Слишком короткий запрос

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "query too short" in data["validation_error"]["field_errors"]["q"]

    async def test_search_responses_service_unavailable(self, api_client):
        """Тест поиска при недоступности сервиса поиска."""
        url = api_client.url_for("search_responses", q="response")

        with patch(
            "core.search.SearchService.search",
            side_effect=Exception("Search service unavailable"),
        ):
            response = await api_client.get(url)
            assert response.status_code == 503

            data = response.json()
            assert "error" in data
            assert "service unavailable" in data["error"].lower()


class TestResponseStatisticsErrors:
    """Тесты ошибок получения статистики ответов."""

    async def test_get_statistics_question_not_found(self, api_client):
        """Тест получения статистики для несуществующего вопроса."""
        url = api_client.url_for(
            "get_response_statistics", question_id="non_existent_question"
        )

        response = await api_client.get(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "question not found" in data["error"].lower()

    async def test_get_statistics_survey_not_found(self, api_client):
        """Тест получения статистики для несуществующего опроса."""
        url = api_client.url_for(
            "get_response_statistics", survey_id="non_existent_survey"
        )

        response = await api_client.get(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "survey not found" in data["error"].lower()

    async def test_get_statistics_unauthorized_access(self, api_client, sample_survey):
        """Тест получения статистики без прав доступа."""
        url = api_client.url_for("get_response_statistics", survey_id=sample_survey.id)

        with patch(
            "apps.surveys.services.SurveyService.check_statistics_access",
            return_value=False,
        ):
            response = await api_client.get(url)
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert "access denied" in data["error"].lower()

    async def test_get_statistics_invalid_parameters(self, api_client, sample_survey):
        """Тест получения статистики с неправильными параметрами."""
        url = api_client.url_for(
            "get_response_statistics",
            survey_id=sample_survey.id,
            breakdown_by="invalid_field",
            period="invalid_period",
        )

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "breakdown_by" in data["validation_error"]["field_errors"]
        assert "period" in data["validation_error"]["field_errors"]


class TestResponseValidationErrors:
    """Тесты ошибок валидации ответов."""

    async def test_validate_response_not_found(self, api_client):
        """Тест валидации несуществующего ответа."""
        url = api_client.url_for(
            "get_response_validation", response_id="non_existent_id"
        )

        response = await api_client.get(url)
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    async def test_bulk_validate_responses_empty_list(self, api_client):
        """Тест массовой валидации с пустым списком ID."""
        url = api_client.url_for("get_bulk_response_validation")

        request_data = {"response_ids": []}

        response = await api_client.post(url, json=request_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "response_ids" in data["validation_error"]["field_errors"]

    async def test_bulk_validate_responses_too_many_ids(self, api_client):
        """Тест массовой валидации со слишком многими ID."""
        url = api_client.url_for("get_bulk_response_validation")

        request_data = {"response_ids": ["id_" + str(i) for i in range(1000)]}

        response = await api_client.post(url, json=request_data)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "too many" in data["validation_error"]["field_errors"]["response_ids"]

    async def test_validate_response_service_error(self, api_client, sample_response):
        """Тест валидации при ошибке сервиса валидации."""
        url = api_client.url_for(
            "get_response_validation", response_id=sample_response.id
        )

        with patch(
            "apps.responses.services.ValidationService.validate_response",
            side_effect=Exception("Validation service error"),
        ):
            response = await api_client.get(url)
            assert response.status_code == 500

            data = response.json()
            assert "error" in data
            assert "internal server error" in data["error"].lower()


class TestResponseExportErrors:
    """Тесты ошибок экспорта ответов."""

    async def test_export_responses_unsupported_format(self, api_client, sample_survey):
        """Тест экспорта в неподдерживаемом формате."""
        url = api_client.url_for(
            "get_responses_by_survey",
            survey_id=sample_survey.id,
            export_format="unsupported_format",
        )

        response = await api_client.get(url)
        assert response.status_code == 422

        data = response.json()
        assert "validation_error" in data
        assert "export_format" in data["validation_error"]["field_errors"]

    async def test_export_responses_too_many_records(self, api_client, sample_survey):
        """Тест экспорта слишком большого количества записей."""
        url = api_client.url_for(
            "get_responses_by_survey", survey_id=sample_survey.id, export_format="csv"
        )

        with patch(
            "apps.responses.services.ResponseService.count_responses",
            return_value=1000000,
        ):
            response = await api_client.get(url)
            assert response.status_code == 413

            data = response.json()
            assert "error" in data
            assert "too many records" in data["error"].lower()

    async def test_export_responses_generation_failed(self, api_client, sample_survey):
        """Тест неудачной генерации экспорта."""
        url = api_client.url_for(
            "get_responses_by_survey", survey_id=sample_survey.id, export_format="csv"
        )

        with patch(
            "core.export.ExportService.generate_csv",
            side_effect=Exception("Export failed"),
        ):
            response = await api_client.get(url)
            assert response.status_code == 500

            data = response.json()
            assert "error" in data
            assert "export failed" in data["error"].lower()

    async def test_bulk_export_responses_unauthorized(
        self, api_client, responses_batch
    ):
        """Тест массового экспорта без авторизации."""
        url = api_client.url_for("bulk_export_responses")

        response_ids = [resp.id for resp in responses_batch[:10]]
        export_data = {"response_ids": response_ids, "format": "json"}

        response = await api_client.post(url, json=export_data)
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "unauthorized" in data["error"].lower()
