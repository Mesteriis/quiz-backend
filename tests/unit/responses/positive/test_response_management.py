"""
Positive тесты для управления ответами на вопросы опросов.

Тестирует успешное управление ответами:
- Обновление ответов
- Удаление ответов
- Частичное обновление ответов
- Массовые операции
- Управление метаданными
- Версионирование ответов
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import patch


class TestResponseUpdate:
    """Тесты обновления ответов."""

    async def test_update_response_success(
        self, api_client, sample_response, regular_user, response_test_utils
    ):
        """Тест успешного обновления ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {
            "answer": {"value": "Updated response text"},
            "metadata": {"updated_reason": "User correction"},
        }

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        await response_test_utils.assert_response_structure(data)
        assert data["answer"]["value"] == "Updated response text"
        assert data["metadata"]["updated_reason"] == "User correction"

    async def test_update_response_partial(
        self, api_client, sample_response, regular_user
    ):
        """Тест частичного обновления ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {"answer": {"value": "Partially updated response"}}

        response = await api_client.patch(url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["answer"]["value"] == "Partially updated response"

    async def test_update_rating_response(
        self, api_client, rating_response, regular_user
    ):
        """Тест обновления рейтингового ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=rating_response.id)

        update_data = {
            "answer": {"rating": 5, "comment": "Updated: Excellent service!"}
        }

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["answer"]["rating"] == 5
        assert data["answer"]["comment"] == "Updated: Excellent service!"

    async def test_update_multiple_choice_response(
        self, api_client, multiple_choice_response, regular_user
    ):
        """Тест обновления ответа множественного выбора."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for(
            "update_response", response_id=multiple_choice_response.id
        )

        update_data = {"answer": {"choices": ["Option 2", "Option 3"]}}

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert set(data["answer"]["choices"]) == {"Option 2", "Option 3"}

    async def test_update_response_with_validation(
        self, api_client, sample_response, regular_user, response_test_utils
    ):
        """Тест обновления ответа с валидацией."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {"answer": {"value": "Valid updated response"}, "validate": True}

        response = await api_client.put(url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["answer"]["value"] == "Valid updated response"
        assert data.get("validation_status", {}).get("is_valid") is True

    async def test_update_response_metadata(
        self, api_client, sample_response, regular_user
    ):
        """Тест обновления метаданных ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        update_data = {
            "metadata": {
                "tags": ["updated", "important"],
                "priority": "high",
                "notes": "Updated by user request",
            }
        }

        response = await api_client.patch(url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["metadata"]["tags"] == ["updated", "important"]
        assert data["metadata"]["priority"] == "high"
        assert data["metadata"]["notes"] == "Updated by user request"


class TestResponseDeletion:
    """Тесты удаления ответов."""

    async def test_delete_response_success(
        self, api_client, sample_response, regular_user
    ):
        """Тест успешного удаления ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id=sample_response.id)

        response = await api_client.delete(url)
        assert response.status_code == 204

    async def test_delete_response_with_reason(
        self, api_client, sample_response, regular_user
    ):
        """Тест удаления ответа с указанием причины."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id=sample_response.id)

        delete_data = {"reason": "User requested deletion", "permanent": False}

        response = await api_client.delete(url, json=delete_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "deleted"
        assert data["reason"] == "User requested deletion"
        assert data["permanent"] is False

    async def test_soft_delete_response(
        self, api_client, sample_response, regular_user
    ):
        """Тест мягкого удаления ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id=sample_response.id)

        delete_data = {"soft_delete": True, "reason": "Temporary removal"}

        response = await api_client.delete(url, json=delete_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "soft_deleted"
        assert data["can_restore"] is True

    async def test_delete_response_cascade(
        self, api_client, sample_response, regular_user
    ):
        """Тест каскадного удаления ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("delete_response", response_id=sample_response.id)

        delete_data = {"cascade": True, "delete_related": ["files", "analytics"]}

        response = await api_client.delete(url, json=delete_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "deleted"
        assert "deleted_related" in data
        assert "files" in data["deleted_related"]
        assert "analytics" in data["deleted_related"]


class TestBulkResponseOperations:
    """Тесты массовых операций с ответами."""

    async def test_bulk_update_responses(
        self, api_client, responses_batch, regular_user
    ):
        """Тест массового обновления ответов."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_update_responses")

        response_ids = [resp.id for resp in responses_batch[:3]]
        update_data = {
            "response_ids": response_ids,
            "updates": {"metadata": {"bulk_updated": True}, "tags": ["bulk_operation"]},
        }

        response = await api_client.post(url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["updated_count"] == len(response_ids)
        assert "updated_responses" in data
        assert len(data["updated_responses"]) == len(response_ids)

    async def test_bulk_delete_responses(
        self, api_client, responses_batch, regular_user
    ):
        """Тест массового удаления ответов."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_delete_responses")

        response_ids = [resp.id for resp in responses_batch[:3]]
        delete_data = {
            "response_ids": response_ids,
            "reason": "Bulk cleanup operation",
            "soft_delete": True,
        }

        response = await api_client.post(url, json=delete_data)
        assert response.status_code == 200

        data = response.json()
        assert data["deleted_count"] == len(response_ids)
        assert data["soft_delete"] is True

    async def test_bulk_validate_responses(
        self, api_client, responses_batch, regular_user
    ):
        """Тест массовой валидации ответов."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_validate_responses")

        response_ids = [resp.id for resp in responses_batch[:5]]
        validate_data = {
            "response_ids": response_ids,
            "validation_rules": ["required", "format", "length"],
        }

        response = await api_client.post(url, json=validate_data)
        assert response.status_code == 200

        data = response.json()
        assert "validation_results" in data
        assert len(data["validation_results"]) == len(response_ids)

        for validation in data["validation_results"]:
            assert "response_id" in validation
            assert "is_valid" in validation
            assert validation["response_id"] in response_ids

    async def test_bulk_export_responses(
        self, api_client, responses_batch, regular_user
    ):
        """Тест массового экспорта ответов."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("bulk_export_responses")

        response_ids = [resp.id for resp in responses_batch[:10]]
        export_data = {
            "response_ids": response_ids,
            "format": "json",
            "include_metadata": True,
        }

        response = await api_client.post(url, json=export_data)
        assert response.status_code == 200

        data = response.json()
        assert "export_url" in data
        assert "export_id" in data
        assert data["total_responses"] == len(response_ids)


class TestResponseRestore:
    """Тесты восстановления ответов."""

    async def test_restore_soft_deleted_response(
        self, api_client, sample_response, regular_user
    ):
        """Тест восстановления мягко удаленного ответа."""
        api_client.force_authenticate(user=regular_user)

        # Сначала мягко удаляем
        delete_url = api_client.url_for(
            "delete_response", response_id=sample_response.id
        )
        delete_data = {"soft_delete": True}

        await api_client.delete(delete_url, json=delete_data)

        # Затем восстанавливаем
        restore_url = api_client.url_for(
            "restore_response", response_id=sample_response.id
        )

        response = await api_client.post(restore_url)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "restored"
        assert data["response_id"] == sample_response.id

    async def test_restore_response_with_reason(
        self, api_client, sample_response, regular_user
    ):
        """Тест восстановления ответа с указанием причины."""
        api_client.force_authenticate(user=regular_user)

        # Сначала мягко удаляем
        delete_url = api_client.url_for(
            "delete_response", response_id=sample_response.id
        )
        delete_data = {"soft_delete": True}

        await api_client.delete(delete_url, json=delete_data)

        # Затем восстанавливаем
        restore_url = api_client.url_for(
            "restore_response", response_id=sample_response.id
        )
        restore_data = {
            "reason": "User requested restoration",
            "restore_metadata": True,
        }

        response = await api_client.post(restore_url, json=restore_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "restored"
        assert data["reason"] == "User requested restoration"

    async def test_bulk_restore_responses(
        self, api_client, responses_batch, regular_user
    ):
        """Тест массового восстановления ответов."""
        api_client.force_authenticate(user=regular_user)

        response_ids = [resp.id for resp in responses_batch[:3]]

        # Сначала мягко удаляем
        delete_url = api_client.url_for("bulk_delete_responses")
        delete_data = {"response_ids": response_ids, "soft_delete": True}

        await api_client.post(delete_url, json=delete_data)

        # Затем восстанавливаем
        restore_url = api_client.url_for("bulk_restore_responses")
        restore_data = {
            "response_ids": response_ids,
            "reason": "Bulk restoration operation",
        }

        response = await api_client.post(restore_url, json=restore_data)
        assert response.status_code == 200

        data = response.json()
        assert data["restored_count"] == len(response_ids)
        assert "restored_responses" in data


class TestResponseVersioning:
    """Тесты версионирования ответов."""

    async def test_get_response_history(
        self, api_client, sample_response, regular_user
    ):
        """Тест получения истории версий ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("get_response_history", response_id=sample_response.id)

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "history" in data
        assert "versions" in data["history"]
        assert len(data["history"]["versions"]) >= 1

    async def test_get_response_version(
        self, api_client, sample_response, regular_user
    ):
        """Тест получения конкретной версии ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for(
            "get_response_version", response_id=sample_response.id, version=1
        )

        response = await api_client.get(url)
        assert response.status_code == 200

        data = response.json()
        assert "version" in data
        assert data["version"] == 1
        assert "response_data" in data

    async def test_revert_response_to_version(
        self, api_client, sample_response, regular_user
    ):
        """Тест возврата ответа к предыдущей версии."""
        api_client.force_authenticate(user=regular_user)

        # Сначала обновляем ответ
        update_url = api_client.url_for(
            "update_response", response_id=sample_response.id
        )
        update_data = {"answer": {"value": "Updated response"}}

        await api_client.put(update_url, json=update_data)

        # Затем возвращаем к предыдущей версии
        revert_url = api_client.url_for(
            "revert_response", response_id=sample_response.id
        )
        revert_data = {"version": 1, "reason": "Revert to original version"}

        response = await api_client.post(revert_url, json=revert_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "reverted"
        assert data["reverted_to_version"] == 1

    async def test_compare_response_versions(
        self, api_client, sample_response, regular_user
    ):
        """Тест сравнения версий ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for(
            "compare_response_versions", response_id=sample_response.id
        )

        compare_data = {"version_from": 1, "version_to": 2}

        response = await api_client.post(url, json=compare_data)
        assert response.status_code == 200

        data = response.json()
        assert "comparison" in data
        assert "differences" in data["comparison"]
        assert "version_from" in data["comparison"]
        assert "version_to" in data["comparison"]


class TestResponseMetadata:
    """Тесты управления метаданными ответов."""

    async def test_add_response_tags(self, api_client, sample_response, regular_user):
        """Тест добавления тегов к ответу."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("add_response_tags", response_id=sample_response.id)

        tags_data = {"tags": ["important", "verified", "quality-check"]}

        response = await api_client.post(url, json=tags_data)
        assert response.status_code == 200

        data = response.json()
        assert "tags" in data
        assert set(data["tags"]) == {"important", "verified", "quality-check"}

    async def test_remove_response_tags(
        self, api_client, sample_response, regular_user
    ):
        """Тест удаления тегов ответа."""
        api_client.force_authenticate(user=regular_user)

        # Сначала добавляем теги
        add_url = api_client.url_for(
            "add_response_tags", response_id=sample_response.id
        )
        add_data = {"tags": ["tag1", "tag2", "tag3"]}

        await api_client.post(add_url, json=add_data)

        # Затем удаляем некоторые теги
        remove_url = api_client.url_for(
            "remove_response_tags", response_id=sample_response.id
        )
        remove_data = {"tags": ["tag2"]}

        response = await api_client.post(remove_url, json=remove_data)
        assert response.status_code == 200

        data = response.json()
        assert "tags" in data
        assert set(data["tags"]) == {"tag1", "tag3"}

    async def test_update_response_priority(
        self, api_client, sample_response, regular_user
    ):
        """Тест обновления приоритета ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for(
            "update_response_priority", response_id=sample_response.id
        )

        priority_data = {"priority": "high", "reason": "Important customer feedback"}

        response = await api_client.post(url, json=priority_data)
        assert response.status_code == 200

        data = response.json()
        assert data["priority"] == "high"
        assert data["priority_reason"] == "Important customer feedback"

    async def test_add_response_notes(self, api_client, sample_response, regular_user):
        """Тест добавления заметок к ответу."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("add_response_notes", response_id=sample_response.id)

        notes_data = {
            "notes": "This response needs follow-up action",
            "note_type": "admin_comment",
        }

        response = await api_client.post(url, json=notes_data)
        assert response.status_code == 200

        data = response.json()
        assert "notes" in data
        assert data["notes"][-1]["content"] == "This response needs follow-up action"
        assert data["notes"][-1]["type"] == "admin_comment"
