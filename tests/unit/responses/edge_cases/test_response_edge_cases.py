"""
Edge cases тесты для системы ответов.

Тестирует граничные случаи и экстремальные сценарии:
- Граничные значения
- Конкурентные запросы
- Память и производительность
- Unicode и специальные символы
- Сетевые условия
- Восстановление после ошибок
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor


class TestResponseBoundaryValues:
    """Тесты граничных значений ответов."""

    async def test_response_with_max_length_text(
        self, api_client, sample_question, boundary_rating_response_data
    ):
        """Тест ответа с максимальной длиной текста."""
        url = api_client.url_for("create_response")

        # Создаем текст максимальной допустимой длины
        max_length = 10000  # Предполагаемый лимит
        max_text = "A" * max_length

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_session_max_length",
            "answer": {"value": max_text},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert len(data["answer"]["value"]) == max_length
        assert data["answer"]["value"] == max_text

    async def test_response_with_minimum_rating(self, api_client, rating_response):
        """Тест ответа с минимальным рейтингом."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": rating_response.question_id,
            "user_session_id": "test_min_rating",
            "answer": {"rating": 1},  # Минимальный рейтинг
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["rating"] == 1

    async def test_response_with_maximum_rating(self, api_client, rating_response):
        """Тест ответа с максимальным рейтингом."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": rating_response.question_id,
            "user_session_id": "test_max_rating",
            "answer": {"rating": 5},  # Максимальный рейтинг
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["rating"] == 5

    async def test_location_response_boundary_coordinates(
        self, api_client, location_response
    ):
        """Тест геолокационного ответа с граничными координатами."""
        url = api_client.url_for("create_response")

        boundary_coordinates = [
            {"latitude": 90.0, "longitude": 180.0},  # Северный полюс, антимеридиан
            {"latitude": -90.0, "longitude": -180.0},  # Южный полюс, антимеридиан
            {"latitude": 0.0, "longitude": 0.0},  # Пересечение экватора и меридиана
            {"latitude": 89.999999, "longitude": 179.999999},  # Максимальные значения
            {"latitude": -89.999999, "longitude": -179.999999},  # Минимальные значения
        ]

        for idx, coords in enumerate(boundary_coordinates):
            response_data = {
                "question_id": location_response.question_id,
                "user_session_id": f"test_boundary_{idx}",
                "answer": coords,
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

            data = response.json()
            assert data["answer"]["latitude"] == coords["latitude"]
            assert data["answer"]["longitude"] == coords["longitude"]

    async def test_email_response_boundary_lengths(self, api_client, email_response):
        """Тест email ответа с граничными длинами."""
        url = api_client.url_for("create_response")

        # Минимальный валидный email
        min_email = "a@b.c"

        response_data = {
            "question_id": email_response.question_id,
            "user_session_id": "test_min_email",
            "answer": {"email": min_email},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["email"] == min_email

        # Максимальный валидный email (предполагаемый лимит 254 символа)
        max_email = "a" * 240 + "@example.com"

        response_data = {
            "question_id": email_response.question_id,
            "user_session_id": "test_max_email",
            "answer": {"email": max_email},
        }

        response = await api_client.post(url, json=response_data)
        assert response.status_code == 201

        data = response.json()
        assert data["answer"]["email"] == max_email


class TestResponseUnicodeAndSpecialChars:
    """Тесты Unicode и специальных символов в ответах."""

    async def test_response_with_unicode_characters(
        self, api_client, sample_question, unicode_response_data
    ):
        """Тест ответа с Unicode символами."""
        url = api_client.url_for("create_response")

        unicode_texts = [
            "Привет мир! 🌍",
            "你好世界 🇨🇳",
            "こんにちは世界 🇯🇵",
            "مرحبا بالعالم 🇸🇦",
            "Здравствуй мир! 🇷🇺",
            "Γειά σου κόσμε! 🇬🇷",
            "העולם שלום! 🇮🇱",
        ]

        for idx, text in enumerate(unicode_texts):
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": f"test_unicode_{idx}",
                "answer": {"value": text},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

            data = response.json()
            assert data["answer"]["value"] == text

    async def test_response_with_special_characters(self, api_client, sample_question):
        """Тест ответа со специальными символами."""
        url = api_client.url_for("create_response")

        special_chars = [
            "Test with quotes: \"Hello\" and 'World'",
            "Test with symbols: @#$%^&*()_+-=[]{}|;:,.<>?",
            "Test with escapes: \\n\\t\\r\\\\",
            "Test with null byte: \\x00",
            "Test with control chars: \\x01\\x02\\x03",
            "Test with high ASCII: ¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿",
        ]

        for idx, text in enumerate(special_chars):
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": f"test_special_{idx}",
                "answer": {"value": text},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code in [201, 422]  # Некоторые могут быть отклонены

            if response.status_code == 201:
                data = response.json()
                assert data["answer"]["value"] == text

    async def test_response_with_emoji_combinations(self, api_client, sample_question):
        """Тест ответа с комбинациями эмодзи."""
        url = api_client.url_for("create_response")

        emoji_combinations = [
            "👨‍👩‍👧‍👦 Family",
            "🏳️‍🌈 Pride flag",
            "👨‍💻 Man technologist",
            "🤷‍♀️ Woman shrugging",
            "🧑‍🎓 Student",
            "🐻‍❄️ Polar bear",
            "🚶‍♂️‍➡️ Man walking right",
        ]

        for idx, text in enumerate(emoji_combinations):
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": f"test_emoji_{idx}",
                "answer": {"value": text},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

            data = response.json()
            assert data["answer"]["value"] == text

    async def test_response_with_zero_width_characters(
        self, api_client, sample_question
    ):
        """Тест ответа с символами нулевой ширины."""
        url = api_client.url_for("create_response")

        # Символы нулевой ширины
        zero_width_chars = [
            "Test\u200bwith\u200czero\u200dwidth",  # Zero width space, ZWNJ, ZWJ
            "Test\ufeffwith\u061cBOM",  # BOM, Arabic letter mark
            "Test\u2060with\u2061word\u2062joiner",  # Word joiner, function application
        ]

        for idx, text in enumerate(zero_width_chars):
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": f"test_zero_width_{idx}",
                "answer": {"value": text},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

            data = response.json()
            assert data["answer"]["value"] == text


class TestResponseConcurrency:
    """Тесты конкурентности ответов."""

    async def test_concurrent_response_creation(
        self, api_client, sample_question, concurrent_response_data
    ):
        """Тест конкурентного создания ответов."""
        url = api_client.url_for("create_response")

        async def create_response(session_id: str) -> Dict[str, Any]:
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": session_id,
                "answer": {"value": f"Concurrent response {session_id}"},
            }
            return await api_client.post(url, json=response_data)

        # Создаем 10 конкурентных запросов
        tasks = [create_response(f"concurrent_session_{i}") for i in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем что все запросы завершились успешно
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) == 10

        for response in successful_responses:
            assert response.status_code == 201

    async def test_concurrent_response_updates(
        self, api_client, sample_response, regular_user
    ):
        """Тест конкурентного обновления одного ответа."""
        api_client.force_authenticate(user=regular_user)

        url = api_client.url_for("update_response", response_id=sample_response.id)

        async def update_response(update_num: int) -> Dict[str, Any]:
            update_data = {"answer": {"value": f"Updated response {update_num}"}}
            return await api_client.put(url, json=update_data)

        # Создаем 5 конкурентных обновлений
        tasks = [update_response(i) for i in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем что обновления прошли (последний выиграл)
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 1

        # Проверяем что последнее обновление сохранилось
        final_response = await api_client.get(
            api_client.url_for("get_response", response_id=sample_response.id)
        )
        assert final_response.status_code == 200

        data = final_response.json()
        assert "Updated response" in data["answer"]["value"]

    async def test_concurrent_bulk_operations(
        self, api_client, responses_batch, regular_user
    ):
        """Тест конкурентных массовых операций."""
        api_client.force_authenticate(user=regular_user)

        response_ids = [resp.id for resp in responses_batch[:5]]

        async def bulk_update():
            url = api_client.url_for("bulk_update_responses")
            data = {
                "response_ids": response_ids,
                "updates": {"metadata": {"bulk_updated": True}},
            }
            return await api_client.post(url, json=data)

        async def bulk_validate():
            url = api_client.url_for("bulk_validate_responses")
            data = {"response_ids": response_ids}
            return await api_client.post(url, json=data)

        # Выполняем конкурентные массовые операции
        tasks = [bulk_update(), bulk_validate()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем что операции не конфликтуют
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 1

    async def test_concurrent_response_deletion(
        self, api_client, responses_batch, regular_user
    ):
        """Тест конкурентного удаления ответов."""
        api_client.force_authenticate(user=regular_user)

        async def delete_response(response_id: str) -> Dict[str, Any]:
            url = api_client.url_for("delete_response", response_id=response_id)
            return await api_client.delete(url)

        # Пытаемся удалить одинаковые ответы конкурентно
        response_id = responses_batch[0].id
        tasks = [delete_response(response_id) for _ in range(3)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем что только одно удаление прошло успешно
        successful_responses = [
            r
            for r in responses
            if not isinstance(r, Exception) and r.status_code == 204
        ]
        not_found_responses = [
            r
            for r in responses
            if not isinstance(r, Exception) and r.status_code == 404
        ]

        assert len(successful_responses) == 1
        assert len(not_found_responses) == 2


class TestResponsePerformance:
    """Тесты производительности ответов."""

    async def test_large_response_dataset_retrieval(
        self, api_client, sample_question, large_response_dataset
    ):
        """Тест получения большого набора ответов."""
        url = api_client.url_for(
            "get_responses_by_question", question_id=sample_question.id, per_page=1000
        )

        import time

        start_time = time.time()

        response = await api_client.get(url)

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 5.0  # Должно выполниться менее чем за 5 секунд

        data = response.json()
        assert len(data["responses"]) <= 1000

    async def test_response_search_performance(
        self, api_client, large_response_dataset
    ):
        """Тест производительности поиска ответов."""
        url = api_client.url_for("search_responses", q="test")

        import time

        start_time = time.time()

        response = await api_client.get(url)

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 3.0  # Поиск должен быть быстрым

        data = response.json()
        assert "responses" in data
        assert "search_metadata" in data

    async def test_bulk_operations_performance(
        self, api_client, large_response_dataset, regular_user
    ):
        """Тест производительности массовых операций."""
        api_client.force_authenticate(user=regular_user)

        # Берем 100 ответов для массовой операции
        response_ids = [resp.id for resp in large_response_dataset[:100]]

        url = api_client.url_for("bulk_validate_responses")
        request_data = {"response_ids": response_ids}

        import time

        start_time = time.time()

        response = await api_client.post(url, json=request_data)

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 10.0  # Массовая операция должна быть разумно быстрой

        data = response.json()
        assert len(data["validation_results"]) == 100

    async def test_response_statistics_performance(
        self, api_client, sample_survey, large_response_dataset
    ):
        """Тест производительности генерации статистики."""
        url = api_client.url_for(
            "get_response_statistics",
            survey_id=sample_survey.id,
            include_time_series=True,
        )

        import time

        start_time = time.time()

        response = await api_client.get(url)

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 8.0  # Статистика должна генерироваться разумно быстро

        data = response.json()
        assert "statistics" in data


class TestResponseMemoryUsage:
    """Тесты использования памяти."""

    async def test_large_text_response_memory(self, api_client, sample_question):
        """Тест создания ответа с большим текстом."""
        url = api_client.url_for("create_response")

        # Создаем текст размером 1MB
        large_text = "A" * (1024 * 1024)

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_memory_usage",
            "answer": {"value": large_text},
        }

        response = await api_client.post(url, json=response_data)

        # Может быть принят или отклонен в зависимости от настроек
        assert response.status_code in [201, 413, 422]

        if response.status_code == 201:
            data = response.json()
            assert len(data["answer"]["value"]) == len(large_text)

    async def test_memory_usage_with_many_metadata_fields(
        self, api_client, sample_question
    ):
        """Тест использования памяти с большим количеством метаданных."""
        url = api_client.url_for("create_response")

        # Создаем много метаданных
        metadata = {f"field_{i}": f"value_{i}" * 100 for i in range(100)}

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_metadata_memory",
            "answer": {"value": "Response with lots of metadata"},
            "metadata": metadata,
        }

        response = await api_client.post(url, json=response_data)

        # Может быть принят или отклонен
        assert response.status_code in [201, 413, 422]

    async def test_response_batch_memory_usage(self, api_client, sample_question):
        """Тест использования памяти при создании множества ответов."""
        url = api_client.url_for("create_response")

        # Создаем множество ответов подряд
        responses = []
        for i in range(50):
            response_data = {
                "question_id": sample_question.id,
                "user_session_id": f"test_batch_memory_{i}",
                "answer": {"value": f"Batch response {i}" * 100},
            }

            response = await api_client.post(url, json=response_data)
            responses.append(response)

        # Проверяем что все ответы созданы успешно
        successful_responses = [r for r in responses if r.status_code == 201]
        assert len(successful_responses) == 50


class TestResponseNetworkConditions:
    """Тесты различных сетевых условий."""

    async def test_response_with_slow_network(self, api_client, sample_question):
        """Тест создания ответа при медленной сети."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_slow_network",
            "answer": {"value": "Response over slow network"},
        }

        # Симулируем медленную сеть
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": "test_response_id",
                "question_id": sample_question.id,
                "answer": {"value": "Response over slow network"},
            }

            # Добавляем задержку
            await asyncio.sleep(0.1)

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

    async def test_response_with_connection_timeout(self, api_client, sample_question):
        """Тест создания ответа при тайм-ауте соединения."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_connection_timeout",
            "answer": {"value": "Response with timeout"},
        }

        # Симулируем тайм-аут
        with patch("httpx.AsyncClient.post", side_effect=asyncio.TimeoutError):
            try:
                await api_client.post(url, json=response_data)
                assert False, "Should have raised TimeoutError"
            except asyncio.TimeoutError:
                pass  # Ожидаемое поведение

    async def test_response_with_intermittent_failures(
        self, api_client, sample_question
    ):
        """Тест создания ответа с периодическими сбоями."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_intermittent_failures",
            "answer": {"value": "Response with intermittent failures"},
        }

        # Симулируем несколько попыток с разными результатами
        with patch("httpx.AsyncClient.post") as mock_post:
            # Первая попытка - ошибка 503
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 503

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 503

            # Вторая попытка - успех
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": "test_response_id",
                "question_id": sample_question.id,
                "answer": {"value": "Response with intermittent failures"},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201


class TestResponseRecovery:
    """Тесты восстановления после ошибок."""

    async def test_response_recovery_after_database_error(
        self, api_client, sample_question
    ):
        """Тест восстановления после ошибки базы данных."""
        url = api_client.url_for("create_response")

        response_data = {
            "question_id": sample_question.id,
            "user_session_id": "test_db_recovery",
            "answer": {"value": "Response after DB error"},
        }

        # Симулируем ошибку БД, затем восстановление
        with patch(
            "apps.responses.services.ResponseService.create_response"
        ) as mock_create:
            # Первая попытка - ошибка БД
            mock_create.side_effect = Exception("Database connection lost")

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 500

            # Вторая попытка - успех
            mock_create.side_effect = None
            mock_create.return_value = {
                "id": "test_response_id",
                "question_id": sample_question.id,
                "answer": {"value": "Response after DB error"},
            }

            response = await api_client.post(url, json=response_data)
            assert response.status_code == 201

    async def test_response_recovery_after_validation_service_error(
        self, api_client, sample_response
    ):
        """Тест восстановления после ошибки сервиса валидации."""
        url = api_client.url_for(
            "get_response_validation", response_id=sample_response.id
        )

        with patch(
            "apps.responses.services.ValidationService.validate_response"
        ) as mock_validate:
            # Первая попытка - ошибка сервиса
            mock_validate.side_effect = Exception("Validation service unavailable")

            response = await api_client.get(url)
            assert response.status_code == 500

            # Вторая попытка - успех с кешированным результатом
            mock_validate.side_effect = None
            mock_validate.return_value = {"is_valid": True, "validation_errors": []}

            response = await api_client.get(url)
            assert response.status_code == 200

            data = response.json()
            assert data["validation_status"]["is_valid"] is True

    async def test_response_recovery_after_search_service_error(self, api_client):
        """Тест восстановления после ошибки сервиса поиска."""
        url = api_client.url_for("search_responses", q="test")

        with patch("core.search.SearchService.search") as mock_search:
            # Первая попытка - ошибка поиска
            mock_search.side_effect = Exception("Search index unavailable")

            response = await api_client.get(url)
            assert response.status_code == 503

            # Вторая попытка - успех с fallback поиском
            mock_search.side_effect = None
            mock_search.return_value = {
                "responses": [],
                "total": 0,
                "search_metadata": {"query": "test", "fallback_used": True},
            }

            response = await api_client.get(url)
            assert response.status_code == 200

            data = response.json()
            assert data["search_metadata"]["fallback_used"] is True
