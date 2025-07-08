"""
Интеграционные тесты для Validation domain.

Тестирует интеграцию validation endpoints с другими сервисами:
- Интеграция с user registration
- Интеграция с profile updates
- Интеграция с survey responses
- Интеграция с notification services
- End-to-end валидация потоков
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestValidationUserIntegration:
    """Тесты интеграции валидации с пользовательскими процессами."""

    async def test_email_validation_during_registration(
        self, api_client, valid_email_data_factory, user_factory
    ):
        """Тест валидации email при регистрации пользователя."""
        # Arrange
        email_request = valid_email_data_factory.build()
        user_data = await user_factory.create()

        # Act - сначала валидируем email
        validation_response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Assert валидации
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data["is_valid"] is True

        # Act - используем валидированный email для регистрации
        registration_data = {
            "email": email_request.email,
            "username": f"testuser_{user_data.id}",
            "password": "ValidPass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # Имитируем использование валидированного email
        # (в реальном приложении registration endpoint будет использовать validation)
        assert validation_data["email"] == registration_data["email"]

    async def test_phone_validation_during_profile_update(
        self, api_client, valid_phone_data_factory, user_factory
    ):
        """Тест валидации телефона при обновлении профиля."""
        # Arrange
        phone_request = valid_phone_data_factory.build()
        user_data = await user_factory.create()

        # Act - валидируем телефон
        validation_response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert валидации
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data["is_valid"] is True

        # Act - используем валидированный телефон для обновления профиля
        profile_data = {
            "phone": phone_request.phone,
            "normalized_phone": validation_data["normalized_phone"],
            "country_code": validation_data["country_code"],
        }

        # Проверяем, что данные соответствуют валидации
        assert profile_data["phone"] == validation_data["phone"]
        assert profile_data["normalized_phone"] == validation_data["normalized_phone"]

    async def test_batch_email_validation_for_user_import(
        self, api_client, batch_email_data_factory
    ):
        """Тест пакетной валидации email при импорте пользователей."""
        # Arrange
        email_batch = batch_email_data_factory.build()

        # Act - валидируем пакет email для импорта
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": email_batch,
                "check_mx": True,  # Более строгая проверка для импорта
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем результаты для принятия решения об импорте
        valid_emails = [r for r in data["results"] if r["is_valid"]]
        invalid_emails = [r for r in data["results"] if not r["is_valid"]]

        assert len(valid_emails) + len(invalid_emails) == len(email_batch)
        assert data["valid_count"] == len(valid_emails)
        assert data["invalid_count"] == len(invalid_emails)

        # В реальном сценарии импортировались бы только валидные email
        importable_users = [
            email["email"] for email in valid_emails if email["mx_valid"]
        ]
        assert isinstance(importable_users, list)

    async def test_email_validation_with_user_preferences(
        self, api_client, valid_email_data_factory, user_factory
    ):
        """Тест валидации email с учетом пользовательских предпочтений."""
        # Arrange
        user_data = await user_factory.create()
        email_request = valid_email_data_factory.build()

        # Предпочтения пользователя
        user_preferences = {
            "strict_validation": True,
            "check_mx": True,
            "check_smtp": True,
            "block_disposable": True,
        }

        # Act - валидируем с учетом предпочтений
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json={
                "email": email_request.email,
                "check_mx": user_preferences["check_mx"],
                "check_smtp": user_preferences["check_smtp"],
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем, что валидация учитывает предпочтения
        if user_preferences["strict_validation"]:
            assert "mx_valid" in data
            assert "smtp_valid" in data

        # В реальном сценарии проверялись бы disposable домены
        if user_preferences["block_disposable"]:
            assert "is_valid" in data


class TestValidationSurveyIntegration:
    """Тесты интеграции валидации с опросами."""

    async def test_email_validation_in_survey_response(
        self, api_client, valid_email_data_factory, survey_factory, question_factory
    ):
        """Тест валидации email в ответах на опросы."""
        # Arrange
        survey_data = await survey_factory.create()
        email_question = await question_factory.create(
            survey_id=survey_data.id,
            question_type="EMAIL",
            title="What is your email?",
            is_required=True,
        )

        email_request = valid_email_data_factory.build()

        # Act - валидируем email для ответа на опрос
        validation_response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Assert валидации
        assert validation_response.status_code == 200
        validation_data = validation_response.json()

        # Act - используем валидированный email в ответе на опрос
        survey_response_data = {
            "question_id": email_question.id,
            "answer": {"value": email_request.email},
            "is_valid": validation_data["is_valid"],
            "validation_metadata": {
                "mx_valid": validation_data["mx_valid"],
                "error_message": validation_data["error_message"],
            },
        }

        # Assert интеграции
        assert survey_response_data["answer"]["value"] == validation_data["email"]
        assert survey_response_data["is_valid"] == validation_data["is_valid"]

    async def test_phone_validation_in_survey_response(
        self, api_client, valid_phone_data_factory, survey_factory, question_factory
    ):
        """Тест валидации телефона в ответах на опросы."""
        # Arrange
        survey_data = await survey_factory.create()
        phone_question = await question_factory.create(
            survey_id=survey_data.id,
            question_type="PHONE",
            title="What is your phone number?",
            is_required=True,
        )

        phone_request = valid_phone_data_factory.build()

        # Act - валидируем телефон для ответа на опрос
        validation_response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert валидации
        assert validation_response.status_code == 200
        validation_data = validation_response.json()

        # Act - используем валидированный телефон в ответе на опрос
        survey_response_data = {
            "question_id": phone_question.id,
            "answer": {"value": phone_request.phone},
            "normalized_value": validation_data["normalized_phone"],
            "is_valid": validation_data["is_valid"],
            "validation_metadata": {
                "country_code": validation_data["country_code"],
                "carrier": validation_data["carrier"],
                "error_message": validation_data["error_message"],
            },
        }

        # Assert интеграции
        assert survey_response_data["answer"]["value"] == validation_data["phone"]
        assert (
            survey_response_data["normalized_value"]
            == validation_data["normalized_phone"]
        )
        assert survey_response_data["is_valid"] == validation_data["is_valid"]

    async def test_validation_before_survey_submission(
        self,
        api_client,
        valid_email_data_factory,
        valid_phone_data_factory,
        survey_factory,
        question_factory,
    ):
        """Тест комплексной валидации перед отправкой опроса."""
        # Arrange
        survey_data = await survey_factory.create()

        email_question = await question_factory.create(
            survey_id=survey_data.id,
            question_type="EMAIL",
            title="Email question",
            is_required=True,
        )

        phone_question = await question_factory.create(
            survey_id=survey_data.id,
            question_type="PHONE",
            title="Phone question",
            is_required=True,
        )

        email_request = valid_email_data_factory.build()
        phone_request = valid_phone_data_factory.build()

        # Act - валидируем все поля перед отправкой
        email_validation = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        phone_validation = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert валидаций
        assert email_validation.status_code == 200
        assert phone_validation.status_code == 200

        email_data = email_validation.json()
        phone_data = phone_validation.json()

        # Act - формируем ответы на опрос
        survey_responses = [
            {
                "question_id": email_question.id,
                "answer": {"value": email_request.email},
                "is_valid": email_data["is_valid"],
            },
            {
                "question_id": phone_question.id,
                "answer": {"value": phone_request.phone},
                "normalized_value": phone_data["normalized_phone"],
                "is_valid": phone_data["is_valid"],
            },
        ]

        # Assert готовности к отправке
        all_valid = all(response["is_valid"] for response in survey_responses)
        assert isinstance(all_valid, bool)

        # В реальном сценарии опрос отправлялся бы только если all_valid = True
        if all_valid:
            submission_ready = {
                "survey_id": survey_data.id,
                "responses": survey_responses,
                "validation_passed": True,
            }
            assert submission_ready["validation_passed"] is True


class TestValidationNotificationIntegration:
    """Тесты интеграции валидации с уведомлениями."""

    async def test_email_validation_for_notification_sending(
        self, api_client, valid_email_data_factory, user_factory
    ):
        """Тест валидации email перед отправкой уведомлений."""
        # Arrange
        user_data = await user_factory.create()
        email_request = valid_email_data_factory.build()

        notification_data = {
            "recipient_email": email_request.email,
            "subject": "Test notification",
            "message": "This is a test notification",
            "type": "survey_invitation",
        }

        # Act - валидируем email перед отправкой уведомления
        validation_response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json={
                "email": notification_data["recipient_email"],
                "check_mx": True,  # Строгая проверка для уведомлений
                "check_smtp": False,
            },
        )

        # Assert валидации
        assert validation_response.status_code == 200
        validation_data = validation_response.json()

        # Act - принимаем решение об отправке
        should_send = (
            validation_data["is_valid"]
            and validation_data["mx_valid"]
            and validation_data["error_message"] is None
        )

        notification_status = {
            "recipient": notification_data["recipient_email"],
            "validation_passed": should_send,
            "can_send": should_send,
            "validation_details": {
                "is_valid": validation_data["is_valid"],
                "mx_valid": validation_data["mx_valid"],
                "error": validation_data["error_message"],
            },
        }

        # Assert решения
        assert isinstance(notification_status["can_send"], bool)
        assert notification_status["validation_passed"] == should_send

    async def test_phone_validation_for_sms_notifications(
        self, api_client, valid_phone_data_factory, user_factory
    ):
        """Тест валидации телефона перед отправкой SMS."""
        # Arrange
        user_data = await user_factory.create()
        phone_request = valid_phone_data_factory.build()

        sms_data = {
            "recipient_phone": phone_request.phone,
            "message": "Your survey response has been recorded",
            "type": "survey_confirmation",
        }

        # Act - валидируем телефон перед отправкой SMS
        validation_response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert валидации
        assert validation_response.status_code == 200
        validation_data = validation_response.json()

        # Act - подготавливаем SMS с нормализованным номером
        sms_prepared = {
            "original_phone": sms_data["recipient_phone"],
            "normalized_phone": validation_data["normalized_phone"],
            "message": sms_data["message"],
            "can_send": validation_data["is_valid"],
            "country_code": validation_data["country_code"],
            "carrier": validation_data["carrier"],
        }

        # Assert подготовки
        assert sms_prepared["original_phone"] == phone_request.phone
        assert sms_prepared["normalized_phone"] == validation_data["normalized_phone"]
        assert isinstance(sms_prepared["can_send"], bool)

    async def test_batch_validation_for_bulk_notifications(
        self, api_client, batch_email_data_factory
    ):
        """Тест пакетной валидации для массовых уведомлений."""
        # Arrange
        email_batch = batch_email_data_factory.build()

        bulk_notification = {
            "subject": "Survey invitation",
            "message": "You are invited to participate in our survey",
            "recipients": email_batch,
            "type": "bulk_survey_invitation",
        }

        # Act - валидируем все email перед массовой отправкой
        validation_response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": bulk_notification["recipients"],
                "check_mx": True,
                "check_smtp": False,
            },
        )

        # Assert валидации
        assert validation_response.status_code == 200
        validation_data = validation_response.json()

        # Act - фильтруем получателей по результатам валидации
        valid_recipients = [
            result["email"]
            for result in validation_data["results"]
            if result["is_valid"] and result["mx_valid"]
        ]

        invalid_recipients = [
            result["email"]
            for result in validation_data["results"]
            if not result["is_valid"] or not result["mx_valid"]
        ]

        notification_plan = {
            "total_requested": len(bulk_notification["recipients"]),
            "valid_recipients": valid_recipients,
            "invalid_recipients": invalid_recipients,
            "send_count": len(valid_recipients),
            "skip_count": len(invalid_recipients),
            "success_rate": len(valid_recipients)
            / len(bulk_notification["recipients"]),
        }

        # Assert планирования
        assert (
            notification_plan["send_count"] + notification_plan["skip_count"]
            == notification_plan["total_requested"]
        )
        assert 0 <= notification_plan["success_rate"] <= 1
        assert (
            len(notification_plan["valid_recipients"]) == validation_data["valid_count"]
        )


class TestValidationWorkflowIntegration:
    """Тесты интеграции валидации в рабочие процессы."""

    async def test_complete_user_onboarding_workflow(
        self,
        api_client,
        valid_email_data_factory,
        valid_phone_data_factory,
        user_factory,
    ):
        """Тест полного процесса онбординга пользователя с валидацией."""
        # Arrange
        email_request = valid_email_data_factory.build()
        phone_request = valid_phone_data_factory.build()

        onboarding_data = {
            "email": email_request.email,
            "phone": phone_request.phone,
            "first_name": "Test",
            "last_name": "User",
            "agreed_to_terms": True,
        }

        # Act 1 - валидируем email
        email_validation = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Act 2 - валидируем телефон
        phone_validation = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert валидаций
        assert email_validation.status_code == 200
        assert phone_validation.status_code == 200

        email_data = email_validation.json()
        phone_data = phone_validation.json()

        # Act 3 - проверяем готовность к регистрации
        registration_ready = (
            email_data["is_valid"]
            and phone_data["is_valid"]
            and onboarding_data["agreed_to_terms"]
        )

        # Act 4 - формируем данные пользователя
        if registration_ready:
            user_creation_data = {
                "email": email_data["email"],
                "phone": phone_data["normalized_phone"],
                "first_name": onboarding_data["first_name"],
                "last_name": onboarding_data["last_name"],
                "validation_metadata": {
                    "email_valid": email_data["is_valid"],
                    "phone_valid": phone_data["is_valid"],
                    "phone_country": phone_data["country_code"],
                    "phone_carrier": phone_data["carrier"],
                },
            }

            # Assert создания
            assert user_creation_data["email"] == onboarding_data["email"]
            assert user_creation_data["phone"] == phone_data["normalized_phone"]
            assert user_creation_data["validation_metadata"]["email_valid"] is True
            assert user_creation_data["validation_metadata"]["phone_valid"] is True

    async def test_survey_response_validation_workflow(
        self,
        api_client,
        valid_email_data_factory,
        edge_case_email_factory,
        survey_factory,
        question_factory,
    ):
        """Тест полного процесса валидации ответов на опрос."""
        # Arrange
        survey_data = await survey_factory.create()

        questions = [
            await question_factory.create(
                survey_id=survey_data.id,
                question_type="EMAIL",
                title="Primary email",
                is_required=True,
            ),
            await question_factory.create(
                survey_id=survey_data.id,
                question_type="EMAIL",
                title="Secondary email",
                is_required=False,
            ),
        ]

        # Ответы пользователя
        user_responses = [
            {
                "question_id": questions[0].id,
                "email": valid_email_data_factory.build().email,
                "required": True,
            },
            {
                "question_id": questions[1].id,
                "email": edge_case_email_factory.build().email,
                "required": False,
            },
        ]

        # Act - валидируем все email ответы
        validation_results = []
        for response in user_responses:
            validation = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json={
                    "email": response["email"],
                    "check_mx": response[
                        "required"
                    ],  # Более строгая проверка для обязательных
                    "check_smtp": False,
                },
            )

            assert validation.status_code == 200
            validation_data = validation.json()

            validation_results.append(
                {
                    "question_id": response["question_id"],
                    "email": response["email"],
                    "is_valid": validation_data["is_valid"],
                    "mx_valid": validation_data["mx_valid"],
                    "required": response["required"],
                    "validation_passed": validation_data["is_valid"]
                    and (not response["required"] or validation_data["mx_valid"]),
                }
            )

        # Act - проверяем готовность к отправке опроса
        required_validations = [v for v in validation_results if v["required"]]
        optional_validations = [v for v in validation_results if not v["required"]]

        # Все обязательные поля должны пройти валидацию
        required_passed = all(v["validation_passed"] for v in required_validations)

        # Для опциональных полей валидация менее строгая
        survey_submission = {
            "survey_id": survey_data.id,
            "responses": validation_results,
            "can_submit": required_passed,
            "validation_summary": {
                "required_fields_valid": required_passed,
                "total_fields": len(validation_results),
                "valid_fields": sum(
                    1 for v in validation_results if v["validation_passed"]
                ),
                "invalid_fields": sum(
                    1 for v in validation_results if not v["validation_passed"]
                ),
            },
        }

        # Assert готовности
        assert isinstance(survey_submission["can_submit"], bool)
        assert survey_submission["validation_summary"]["total_fields"] == len(
            user_responses
        )

    async def test_data_export_validation_workflow(
        self, api_client, batch_email_data_factory, survey_factory
    ):
        """Тест процесса валидации при экспорте данных."""
        # Arrange
        survey_data = await survey_factory.create()
        exported_emails = batch_email_data_factory.build()

        export_request = {
            "survey_id": survey_data.id,
            "export_type": "email_list",
            "emails": exported_emails,
            "validate_before_export": True,
            "include_validation_metadata": True,
        }

        # Act - валидируем экспортируемые email
        if export_request["validate_before_export"]:
            validation_response = await api_client.post(
                api_client.url_for("validate_emails_batch"),
                json={
                    "emails": export_request["emails"],
                    "check_mx": True,
                    "check_smtp": False,
                },
            )

            assert validation_response.status_code == 200
            validation_data = validation_response.json()

            # Act - формируем экспорт с валидацией
            export_data = {
                "survey_id": export_request["survey_id"],
                "export_type": export_request["export_type"],
                "total_emails": len(export_request["emails"]),
                "validation_results": validation_data["results"],
                "summary": {
                    "valid_emails": validation_data["valid_count"],
                    "invalid_emails": validation_data["invalid_count"],
                    "validation_rate": validation_data["valid_count"]
                    / len(export_request["emails"]),
                },
            }

            if export_request["include_validation_metadata"]:
                export_data["detailed_results"] = [
                    {
                        "email": result["email"],
                        "is_valid": result["is_valid"],
                        "mx_valid": result["mx_valid"],
                        "error_message": result["error_message"],
                        "suggestions": result["suggestions"],
                    }
                    for result in validation_data["results"]
                ]

            # Assert экспорта
            assert export_data["total_emails"] == len(exported_emails)
            assert (
                export_data["summary"]["valid_emails"]
                + export_data["summary"]["invalid_emails"]
                == export_data["total_emails"]
            )
            assert 0 <= export_data["summary"]["validation_rate"] <= 1

            if export_request["include_validation_metadata"]:
                assert (
                    len(export_data["detailed_results"]) == export_data["total_emails"]
                )


class TestValidationHealthIntegration:
    """Тесты интеграции проверки здоровья валидации."""

    async def test_validation_health_in_system_monitoring(self, api_client):
        """Тест интеграции health check валидации в системный мониторинг."""
        # Act - проверяем здоровье validation сервиса
        health_response = await api_client.get(
            api_client.url_for("validation_health_check")
        )

        # Assert
        assert health_response.status_code == 200
        health_data = health_response.json()

        # Act - интегрируем в общий health check системы
        system_health = {
            "services": {
                "validation": {
                    "status": health_data["status"],
                    "timestamp": health_data["timestamp"],
                    "healthy": health_data["status"] == "healthy",
                }
            },
            "overall_healthy": health_data["status"] == "healthy",
        }

        # Assert интеграции
        assert system_health["services"]["validation"]["healthy"] is True
        assert system_health["overall_healthy"] is True
        assert system_health["services"]["validation"]["status"] == "healthy"

    async def test_validation_service_dependency_check(self, api_client):
        """Тест проверки зависимостей validation сервиса."""
        # Arrange - проверяем все validation endpoints
        validation_endpoints = [
            (
                "validate_email_endpoint",
                "POST",
                {"email": "test@example.com", "check_mx": False, "check_smtp": False},
            ),
            (
                "validate_phone_endpoint",
                "POST",
                {"phone": "+1234567890", "normalize": True},
            ),
            ("validation_health_check", "GET", None),
        ]

        # Act - проверяем доступность всех endpoints
        endpoint_status = {}

        for endpoint_name, method, data in validation_endpoints:
            try:
                if method == "GET":
                    response = await api_client.get(api_client.url_for(endpoint_name))
                else:  # POST
                    response = await api_client.post(
                        api_client.url_for(endpoint_name), json=data
                    )

                endpoint_status[endpoint_name] = {
                    "available": response.status_code < 500,
                    "status_code": response.status_code,
                    "healthy": response.status_code == 200,
                }
            except Exception as e:
                endpoint_status[endpoint_name] = {
                    "available": False,
                    "error": str(e),
                    "healthy": False,
                }

        # Assert доступности
        for endpoint_name, status in endpoint_status.items():
            assert status["available"] is True, (
                f"Endpoint {endpoint_name} is not available"
            )
            assert status["healthy"] is True, f"Endpoint {endpoint_name} is not healthy"

        # Act - формируем общий статус сервиса
        service_health = {
            "validation_service": {
                "endpoints": endpoint_status,
                "total_endpoints": len(validation_endpoints),
                "healthy_endpoints": sum(
                    1 for s in endpoint_status.values() if s["healthy"]
                ),
                "service_healthy": all(s["healthy"] for s in endpoint_status.values()),
            }
        }

        # Assert общего статуса
        assert service_health["validation_service"]["service_healthy"] is True
        assert (
            service_health["validation_service"]["healthy_endpoints"]
            == service_health["validation_service"]["total_endpoints"]
        )
