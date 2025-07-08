"""
Edge Cases тесты для опросов.

Содержит тесты для граничных случаев, производительности,
конкурентности, Unicode, больших данных и экстремальных условий.
"""

import pytest
import asyncio
from datetime import datetime, timedelta


class TestSurveyBoundaryValues:
    """Тесты граничных значений для опросов."""

    @pytest.mark.asyncio
    async def test_survey_maximum_title_length(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с максимальной длиной заголовка."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        max_title = "A" * 200  # Предполагаем максимум 200 символов

        survey_data = {
            "title": max_title,
            "description": "Valid description",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == max_title
        assert len(data["title"]) == 200

    @pytest.mark.asyncio
    async def test_survey_maximum_description_length(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с максимальной длиной описания."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        max_description = "D" * 2000  # Предполагаем максимум 2000 символов

        survey_data = {
            "title": "Valid Title",
            "description": max_description,
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == max_description
        assert len(data["description"]) == 2000

    @pytest.mark.asyncio
    async def test_survey_maximum_responses_limit(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с максимальным лимитом ответов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        max_responses = 999999  # Максимальное значение

        survey_data = {
            "title": "High Capacity Survey",
            "description": "Survey with maximum response limit",
            "is_public": True,
            "max_responses": max_responses,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["max_responses"] == max_responses

    @pytest.mark.asyncio
    async def test_survey_minimum_values(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с минимальными значениями."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        survey_data = {
            "title": "A",  # Минимальная длина
            "description": "D",  # Минимальная длина
            "is_public": True,
            "max_responses": 1,  # Минимальное значение
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "A"
        assert data["description"] == "D"
        assert data["max_responses"] == 1

    @pytest.mark.asyncio
    async def test_survey_far_future_expiration(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с датой истечения в далеком будущем."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        far_future = (datetime.utcnow() + timedelta(days=36500)).isoformat()  # 100 лет

        survey_data = {
            "title": "Future Survey",
            "description": "Survey expiring in far future",
            "is_public": True,
            "expires_at": far_future,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_survey_near_future_expiration(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с датой истечения в ближайшем будущем."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        near_future = (datetime.utcnow() + timedelta(minutes=1)).isoformat()  # 1 минута

        survey_data = {
            "title": "Quick Survey",
            "description": "Survey expiring soon",
            "is_public": True,
            "expires_at": near_future,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_survey_zero_max_responses(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с нулевым лимитом ответов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        survey_data = {
            "title": "Zero Responses Survey",
            "description": "Survey with zero max responses",
            "is_public": True,
            "max_responses": 0,  # Граничное значение
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        # Может быть валидным (для опросов-черновиков) или невалидным
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_survey_maximum_questions_limit(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с максимальным количеством вопросов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        max_questions = 50  # Предполагаем максимум 50 вопросов

        survey_data = {
            "title": "Large Survey",
            "description": "Survey with maximum questions",
            "is_public": True,
            "questions": [
                {
                    "text": f"Question {i + 1}",
                    "question_type": "text",
                    "is_required": True,
                    "order": i + 1,
                }
                for i in range(max_questions)
            ],
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert len(data["questions"]) == max_questions

    @pytest.mark.asyncio
    async def test_question_maximum_order_value(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания вопроса с максимальным значением порядка."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        max_order = 999  # Максимальное значение порядка

        question_data = {
            "text": "High Order Question",
            "question_type": "text",
            "is_required": True,
            "order": max_order,
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
        assert data["order"] == max_order

    @pytest.mark.asyncio
    async def test_rating_question_extreme_ranges(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания рейтингового вопроса с экстремальными диапазонами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Тест с широким диапазоном
        wide_range_data = {
            "text": "Rate from 1 to 100",
            "question_type": "rating",
            "is_required": True,
            "order": 1,
            "min_rating": 1,
            "max_rating": 100,
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=wide_range_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["min_rating"] == 1
        assert data["max_rating"] == 100

    @pytest.mark.asyncio
    async def test_choice_question_maximum_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания вопроса с максимальным количеством вариантов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        max_options = 50  # Предполагаем максимум 50 вариантов

        choice_data = {
            "text": "Choose from many options",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": [f"Option {i + 1}" for i in range(max_options)],
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=choice_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert len(data["options"]) == max_options


class TestSurveyUnicodeAndSpecialCharacters:
    """Тесты Unicode и специальных символов."""

    @pytest.mark.asyncio
    async def test_survey_unicode_title(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с Unicode заголовком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        unicode_title = "Опрос на русском 🇷🇺 テスト調査 调查问卷 💯 ñáéíóú"

        survey_data = {
            "title": unicode_title,
            "description": "Unicode test survey",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == unicode_title

    @pytest.mark.asyncio
    async def test_survey_emoji_content(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с эмодзи."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        emoji_content = {
            "title": "Emoji Survey 🎉📊💯",
            "description": "Survey with lots of emojis 😊🎯🚀⭐🔥💡🎪🌈",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=emoji_content, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == emoji_content["title"]
        assert data["description"] == emoji_content["description"]

    @pytest.mark.asyncio
    async def test_survey_special_characters(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса со специальными символами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        special_chars = {
            "title": "Special Characters: !@#$%^&*()_+-={}[]|\\:;\"'<>,.?/~`",
            "description": "Description with special chars: ©®™€£¥§¶•‰‡†‚„…‹›«»",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=special_chars, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == special_chars["title"]
        assert data["description"] == special_chars["description"]

    @pytest.mark.asyncio
    async def test_survey_mixed_scripts(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса со смешанными письменностями."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        mixed_scripts = {
            "title": "Mixed Scripts: English Русский 中文 日本語 العربية हिंदी",
            "description": "Description with Cyrillic: Привет, Latin: Hello, Chinese: 你好, Japanese: こんにちは",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=mixed_scripts, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == mixed_scripts["title"]
        assert data["description"] == mixed_scripts["description"]

    @pytest.mark.asyncio
    async def test_question_unicode_text(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания вопроса с Unicode текстом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        unicode_question = {
            "text": "Что вы думаете о новом продукте? 🤔💭 製品についてどう思いますか？",
            "question_type": "text",
            "is_required": True,
            "order": 1,
            "help_text": "Пожалуйста, ответьте честно 😊 正直に答えてください",
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=unicode_question,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == unicode_question["text"]
        assert data["help_text"] == unicode_question["help_text"]

    @pytest.mark.asyncio
    async def test_choice_question_unicode_options(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания вопроса с Unicode вариантами ответов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        unicode_options = {
            "text": "Choose your favorite emoji category:",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": [
                "Лица и эмоции 😊😢😡",
                "Животные 🐶🐱🐭",
                "Еда и напитки 🍕🍔🍟",
                "Спорт ⚽🏀🏈",
                "Путешествия ✈️🚗🚢",
                "Природа 🌳🌺🌈",
            ],
        }

        # Act
        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=unicode_options,
            headers=headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["options"] == unicode_options["options"]

    @pytest.mark.asyncio
    async def test_survey_rtl_text(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с RTL текстом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        rtl_content = {
            "title": "استطلاع باللغة العربية",
            "description": "هذا استطلاع باللغة العربية للاختبار",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=rtl_content, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == rtl_content["title"]
        assert data["description"] == rtl_content["description"]

    @pytest.mark.asyncio
    async def test_survey_null_bytes_handling(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест обработки null bytes в контенте."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        content_with_nulls = {
            "title": "Title with null\x00byte",
            "description": "Description with\x00null byte",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=content_with_nulls, headers=headers
        )

        # Assert
        # Должно быть обработано корректно (удалены null bytes или ошибка)
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_survey_control_characters(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с контрольными символами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        control_chars = {
            "title": "Title with\ttab\nand\rnewline",
            "description": "Description with\bbackspace\fformfeed\vvertical",
            "is_public": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=control_chars, headers=headers
        )

        # Assert
        # Должно быть обработано корректно
        assert response.status_code in [201, 422]


class TestSurveyConcurrency:
    """Тесты конкурентности и параллелизма."""

    @pytest.mark.asyncio
    async def test_concurrent_survey_creation(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест одновременного создания нескольких опросов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        async def create_survey(index):
            survey_data = {
                "title": f"Concurrent Survey {index}",
                "description": f"Survey {index} created concurrently",
                "is_public": True,
            }
            return await api_client.post(
                "/api/surveys", json=survey_data, headers=headers
            )

        # Act
        tasks = [create_survey(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # Assert
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count >= 8  # Большинство должно быть создано успешно

    @pytest.mark.asyncio
    async def test_concurrent_survey_updates(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест одновременного обновления опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        async def update_survey(field, value):
            update_data = {field: value}
            return await api_client.put(
                f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
            )

        # Act
        tasks = [
            update_survey("title", "Updated Title 1"),
            update_survey("description", "Updated Description 1"),
            update_survey("is_active", False),
            update_survey("telegram_notifications", False),
        ]
        responses = await asyncio.gather(*tasks)

        # Assert
        # Хотя бы одно обновление должно быть успешным
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1

    @pytest.mark.asyncio
    async def test_concurrent_question_addition(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест одновременного добавления вопросов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        async def add_question(index):
            question_data = {
                "text": f"Concurrent Question {index}",
                "question_type": "text",
                "is_required": True,
                "order": index,
            }
            return await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )

        # Act
        tasks = [add_question(i) for i in range(1, 11)]
        responses = await asyncio.gather(*tasks)

        # Assert
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count >= 8  # Большинство должно быть создано успешно

    @pytest.mark.asyncio
    async def test_concurrent_read_write_operations(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест одновременных операций чтения и записи."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        async def read_survey():
            return await api_client.get(f"/api/surveys/{sample_survey.id}")

        async def update_survey():
            update_data = {"title": "Concurrently Updated"}
            return await api_client.put(
                f"/api/surveys/{sample_survey.id}", json=update_data, headers=headers
            )

        # Act
        tasks = [read_survey() for _ in range(5)] + [update_survey()]
        responses = await asyncio.gather(*tasks)

        # Assert
        read_responses = responses[:5]
        write_response = responses[5]

        # Все чтения должны быть успешными
        assert all(r.status_code == 200 for r in read_responses)
        # Запись должна быть успешной
        assert write_response.status_code == 200

    @pytest.mark.asyncio
    async def test_survey_access_during_deletion(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест доступа к опросу во время удаления."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        async def delete_survey():
            await asyncio.sleep(0.1)  # Небольшая задержка
            return await api_client.delete(
                f"/api/surveys/{sample_survey.id}", headers=headers
            )

        async def read_survey():
            return await api_client.get(f"/api/surveys/{sample_survey.id}")

        # Act
        delete_task = asyncio.create_task(delete_survey())
        read_task = asyncio.create_task(read_survey())

        responses = await asyncio.gather(delete_task, read_task)

        # Assert
        delete_response, read_response = responses

        # Удаление должно быть успешным
        assert delete_response.status_code == 204
        # Чтение может быть успешным (до удаления) или неуспешным (после удаления)
        assert read_response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_question_reordering_concurrency(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест одновременного переупорядочивания вопросов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем вопросы
        questions = []
        for i in range(5):
            question_data = {
                "text": f"Question {i + 1}",
                "question_type": "text",
                "is_required": True,
                "order": i + 1,
            }
            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )
            assert response.status_code == 201
            questions.append(response.json())

        # Act
        async def reorder_questions(order_map):
            reorder_data = {
                "questions": [
                    {"id": q["id"], "order": order_map[q["order"]]} for q in questions
                ]
            }
            return await api_client.put(
                f"/api/surveys/{sample_survey.id}/questions/reorder",
                json=reorder_data,
                headers=headers,
            )

        # Разные варианты переупорядочивания
        tasks = [
            reorder_questions({1: 5, 2: 4, 3: 3, 4: 2, 5: 1}),  # Обратный порядок
            reorder_questions({1: 1, 2: 3, 3: 5, 4: 2, 5: 4}),  # Случайный порядок
        ]
        responses = await asyncio.gather(*tasks)

        # Assert
        # Хотя бы одна операция должна быть успешной
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1


class TestSurveyPerformance:
    """Тесты производительности."""

    @pytest.mark.asyncio
    async def test_large_survey_creation(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания большого опроса."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        large_survey_data = {
            "title": "Large Survey with Many Questions",
            "description": "A" * 1000,  # Длинное описание
            "is_public": True,
            "questions": [
                {
                    "text": f"Question {i + 1}: {'Q' * 100}",  # Длинные вопросы
                    "question_type": "text",
                    "is_required": True,
                    "order": i + 1,
                    "help_text": f"Help text for question {i + 1}: {'H' * 200}",
                }
                for i in range(25)  # Много вопросов
            ],
        }

        # Act
        start_time = asyncio.get_event_loop().time()
        response = await api_client.post(
            "/api/surveys", json=large_survey_data, headers=headers
        )
        end_time = asyncio.get_event_loop().time()

        # Assert
        assert response.status_code == 201
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Должно выполниться быстро

    @pytest.mark.asyncio
    async def test_survey_list_performance(self, api_client, db_session, surveys_batch):
        """Тест производительности получения списка опросов."""
        # Act
        start_time = asyncio.get_event_loop().time()
        response = await api_client.get("/api/surveys/active?limit=100")
        end_time = asyncio.get_event_loop().time()

        # Assert
        assert response.status_code == 200
        execution_time = end_time - start_time
        assert execution_time < 2.0  # Должно выполниться быстро

    @pytest.mark.asyncio
    async def test_survey_search_performance(
        self, api_client, db_session, surveys_batch
    ):
        """Тест производительности поиска опросов."""
        # Act
        start_time = asyncio.get_event_loop().time()
        response = await api_client.get("/api/surveys/active?search=test&limit=50")
        end_time = asyncio.get_event_loop().time()

        # Assert
        assert response.status_code == 200
        execution_time = end_time - start_time
        assert execution_time < 3.0  # Поиск может быть медленнее

    @pytest.mark.asyncio
    async def test_deep_pagination_performance(
        self, api_client, db_session, surveys_batch
    ):
        """Тест производительности глубокой пагинации."""
        # Act
        start_time = asyncio.get_event_loop().time()
        response = await api_client.get("/api/surveys/active?skip=1000&limit=20")
        end_time = asyncio.get_event_loop().time()

        # Assert
        assert response.status_code == 200
        execution_time = end_time - start_time
        assert execution_time < 3.0  # Глубокая пагинация может быть медленнее

    @pytest.mark.asyncio
    async def test_survey_with_many_questions_retrieval(
        self, api_client, db_session, long_survey
    ):
        """Тест получения опроса с большим количеством вопросов."""
        # Act
        start_time = asyncio.get_event_loop().time()
        response = await api_client.get(f"/api/surveys/{long_survey.id}")
        end_time = asyncio.get_event_loop().time()

        # Assert
        assert response.status_code == 200
        execution_time = end_time - start_time
        assert execution_time < 2.0  # Должно загружаться быстро

    @pytest.mark.asyncio
    async def test_bulk_question_operations(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест массовых операций с вопросами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act - создаем много вопросов одновременно
        start_time = asyncio.get_event_loop().time()

        tasks = []
        for i in range(20):
            question_data = {
                "text": f"Bulk Question {i + 1}",
                "question_type": "text",
                "is_required": True,
                "order": i + 1,
            }
            task = api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 10.0  # Массовые операции должны быть разумно быстрыми

        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count >= 15  # Большинство должно быть создано успешно


class TestSurveyExtremeCases:
    """Тесты экстремальных случаев."""

    @pytest.mark.asyncio
    async def test_survey_with_all_optional_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса со всеми возможными опциональными полями."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        comprehensive_survey = {
            "title": "Comprehensive Survey",
            "description": "Survey with all possible fields",
            "is_public": True,
            "is_active": True,
            "telegram_notifications": True,
            "allow_anonymous": True,
            "max_responses": 1000,
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "category": "research",
            "tags": ["research", "survey", "comprehensive"],
            "custom_css": ".survey { background: #f0f0f0; }",
            "thank_you_message": "Thank you for participating!",
            "redirect_url": "https://example.com/thanks",
            "password_protected": False,
            "require_email": False,
            "collect_ip": False,
            "shuffle_questions": False,
            "show_progress": True,
            "allow_back_navigation": True,
        }

        # Act
        response = await api_client.post(
            "/api/surveys", json=comprehensive_survey, headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == comprehensive_survey["title"]

    @pytest.mark.asyncio
    async def test_survey_with_complex_question_dependencies(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания опроса со сложными зависимостями между вопросами."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем цепочку зависимых вопросов
        questions = []

        # Базовый вопрос
        base_question = {
            "text": "Do you like surveys?",
            "question_type": "choice",
            "is_required": True,
            "order": 1,
            "options": ["Yes", "No"],
        }

        response = await api_client.post(
            f"/api/surveys/{sample_survey.id}/questions",
            json=base_question,
            headers=headers,
        )
        assert response.status_code == 201
        questions.append(response.json())

        # Зависимые вопросы
        for i in range(2, 6):
            dependent_question = {
                "text": f"Follow-up question {i}",
                "question_type": "text",
                "is_required": True,
                "order": i,
                "depends_on": questions[-1]["id"],
                "condition": "equals",
                "condition_value": "Yes",
            }

            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=dependent_question,
                headers=headers,
            )
            assert response.status_code == 201
            questions.append(response.json())

        # Act
        get_response = await api_client.get(
            f"/api/surveys/{sample_survey.id}/questions"
        )

        # Assert
        assert get_response.status_code == 200
        data = get_response.json()
        assert len(data) == 5  # Все вопросы созданы

    @pytest.mark.asyncio
    async def test_survey_timezone_edge_cases(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест создания опроса с граничными случаями временных зон."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Тест с различными форматами времени
        time_formats = [
            "2024-12-31T23:59:59Z",  # UTC
            "2024-12-31T23:59:59+00:00",  # UTC с явным смещением
            "2024-12-31T23:59:59-12:00",  # Максимальное отрицательное смещение
            "2024-12-31T23:59:59+14:00",  # Максимальное положительное смещение
        ]

        for i, expires_at in enumerate(time_formats):
            survey_data = {
                "title": f"Timezone Test Survey {i + 1}",
                "description": f"Testing timezone format: {expires_at}",
                "is_public": True,
                "expires_at": expires_at,
            }

            # Act
            response = await api_client.post(
                "/api/surveys", json=survey_data, headers=headers
            )

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_survey_with_mixed_question_types(
        self, api_client, db_session, sample_survey, regular_user, auth_headers_factory
    ):
        """Тест создания опроса со всеми типами вопросов."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        mixed_questions = [
            {
                "text": "Text question",
                "question_type": "text",
                "is_required": True,
                "order": 1,
            },
            {
                "text": "Number question",
                "question_type": "number",
                "is_required": True,
                "order": 2,
                "min_value": 0,
                "max_value": 100,
            },
            {
                "text": "Rating question",
                "question_type": "rating",
                "is_required": True,
                "order": 3,
                "min_rating": 1,
                "max_rating": 5,
            },
            {
                "text": "Single choice question",
                "question_type": "choice",
                "is_required": True,
                "order": 4,
                "options": ["Option 1", "Option 2", "Option 3"],
                "allow_multiple": False,
            },
            {
                "text": "Multiple choice question",
                "question_type": "choice",
                "is_required": True,
                "order": 5,
                "options": ["Option A", "Option B", "Option C"],
                "allow_multiple": True,
            },
            {
                "text": "Date question",
                "question_type": "date",
                "is_required": True,
                "order": 6,
            },
            {
                "text": "Email question",
                "question_type": "email",
                "is_required": True,
                "order": 7,
            },
            {
                "text": "Long text question",
                "question_type": "textarea",
                "is_required": False,
                "order": 8,
                "max_length": 1000,
            },
        ]

        # Act
        for question_data in mixed_questions:
            response = await api_client.post(
                f"/api/surveys/{sample_survey.id}/questions",
                json=question_data,
                headers=headers,
            )
            assert response.status_code == 201

        # Assert
        get_response = await api_client.get(
            f"/api/surveys/{sample_survey.id}/questions"
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert len(data) == len(mixed_questions)

    @pytest.mark.asyncio
    async def test_survey_stress_test_rapid_operations(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Стресс-тест быстрых операций с опросом."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем опрос
        survey_data = {
            "title": "Stress Test Survey",
            "description": "Survey for stress testing",
            "is_public": True,
        }

        create_response = await api_client.post(
            "/api/surveys", json=survey_data, headers=headers
        )
        assert create_response.status_code == 201
        survey_id = create_response.json()["id"]

        # Act - быстрые операции
        operations = []

        # Множественные обновления
        for i in range(10):
            update_data = {"title": f"Updated Title {i}"}
            operations.append(
                api_client.put(
                    f"/api/surveys/{survey_id}", json=update_data, headers=headers
                )
            )

        # Множественные чтения
        for i in range(10):
            operations.append(api_client.get(f"/api/surveys/{survey_id}"))

        # Выполняем все операции одновременно
        responses = await asyncio.gather(*operations, return_exceptions=True)

        # Assert
        successful_responses = [
            r
            for r in responses
            if not isinstance(r, Exception) and r.status_code in [200, 201]
        ]
        assert (
            len(successful_responses) >= 15
        )  # Большинство операций должно быть успешными
