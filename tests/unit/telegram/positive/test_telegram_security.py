"""
Позитивные тесты для безопасности и интеграции Telegram.

Этот модуль содержит тесты для:
- Безопасности Telegram Bot API
- Интеграции между Bot API и WebApp
- Комплексных сценариев использования
- Мониторинга и статистики безопасности
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from tests.factories import UserFactory, SurveyFactory


class TestTelegramSecurityFeatures:
    """Позитивные тесты функций безопасности Telegram."""

    async def test_get_security_stats(self, api_client: AsyncClient, admin_user):
        """Тест получения статистики безопасности."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.get_security_stats = MagicMock(
                return_value={
                    "blocked_users": 12,
                    "spam_messages": 45,
                    "failed_auth_attempts": 8,
                    "webhook_errors": 3,
                    "rate_limited_requests": 25,
                    "security_incidents": 2,
                    "last_security_scan": "2024-01-20T15:00:00Z",
                    "security_level": "high",
                    "threat_detection": {
                        "enabled": True,
                        "rules_count": 15,
                        "last_update": "2024-01-20T12:00:00Z",
                    },
                    "audit_log": {
                        "enabled": True,
                        "entries_count": 1250,
                        "retention_days": 90,
                    },
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(
                api_client.url_for("get_telegram_security_stats")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["blocked_users"] == 12
        assert data["spam_messages"] == 45
        assert data["failed_auth_attempts"] == 8
        assert data["webhook_errors"] == 3
        assert data["rate_limited_requests"] == 25
        assert data["security_incidents"] == 2
        assert data["security_level"] == "high"

        threat_detection = data["threat_detection"]
        assert threat_detection["enabled"] is True
        assert threat_detection["rules_count"] == 15

        audit_log = data["audit_log"]
        assert audit_log["enabled"] is True
        assert audit_log["entries_count"] == 1250
        assert audit_log["retention_days"] == 90

    async def test_webhook_security_validation(
        self, api_client: AsyncClient, test_settings
    ):
        """Тест валидации безопасности webhook."""
        # Arrange
        webhook_data = {
            "url": "https://secure.example.com/webhook/telegram",
            "secret_token": "secure_webhook_token_456",
            "max_connections": 10,
            "allowed_updates": ["message", "callback_query"],
            "drop_pending_updates": True,
        }

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.validate_webhook_security = MagicMock(
                return_value={
                    "valid": True,
                    "security_score": 95,
                    "recommendations": [],
                    "ssl_grade": "A+",
                    "certificate_valid": True,
                    "secret_token_strength": "strong",
                    "url_security": "secure",
                }
            )
            mock_telegram_service.bot.set_webhook.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(
                api_client.url_for("set_secure_webhook"), json=webhook_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["security_validation"]["valid"] is True
        assert data["security_validation"]["security_score"] == 95
        assert data["security_validation"]["ssl_grade"] == "A+"
        assert data["security_validation"]["certificate_valid"] is True
        assert data["security_validation"]["secret_token_strength"] == "strong"

    async def test_rate_limit_status(self, api_client: AsyncClient, admin_user):
        """Тест получения статуса rate limiting."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.get_rate_limit_status = MagicMock(
                return_value={
                    "global_rate_limit": {
                        "requests_per_minute": 30,
                        "current_usage": 15,
                        "remaining": 15,
                        "reset_time": "2024-01-20T16:01:00Z",
                    },
                    "per_user_rate_limit": {
                        "requests_per_minute": 10,
                        "burst_limit": 20,
                        "users_at_limit": 5,
                    },
                    "webhook_rate_limit": {
                        "updates_per_second": 100,
                        "current_load": 45,
                        "queue_size": 0,
                    },
                    "blocked_ips": 3,
                    "rate_limit_violations": 12,
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_rate_limit_status"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        global_limit = data["global_rate_limit"]
        assert global_limit["requests_per_minute"] == 30
        assert global_limit["current_usage"] == 15
        assert global_limit["remaining"] == 15

        per_user_limit = data["per_user_rate_limit"]
        assert per_user_limit["requests_per_minute"] == 10
        assert per_user_limit["burst_limit"] == 20
        assert per_user_limit["users_at_limit"] == 5

        webhook_limit = data["webhook_rate_limit"]
        assert webhook_limit["updates_per_second"] == 100
        assert webhook_limit["current_load"] == 45
        assert webhook_limit["queue_size"] == 0

    async def test_bot_permissions_check(self, api_client: AsyncClient, admin_user):
        """Тест проверки разрешений бота."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.check_bot_permissions = AsyncMock(
                return_value={
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_polls": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True,
                    "can_change_info": False,
                    "can_invite_users": False,
                    "can_pin_messages": False,
                    "can_manage_topics": False,
                    "permissions_score": 85,
                    "missing_permissions": ["can_change_info", "can_invite_users"],
                    "security_recommendations": [
                        "Enable message deletion permissions",
                        "Configure admin rights for group management",
                    ],
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("check_bot_permissions"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["can_send_messages"] is True
        assert data["can_send_media_messages"] is True
        assert data["can_send_polls"] is True
        assert data["can_change_info"] is False
        assert data["can_invite_users"] is False
        assert data["permissions_score"] == 85
        assert len(data["missing_permissions"]) == 2
        assert len(data["security_recommendations"]) == 2

    async def test_audit_log_retrieval(self, api_client: AsyncClient, admin_user):
        """Тест получения журнала аудита."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.get_audit_log = AsyncMock(
                return_value={
                    "entries": [
                        {
                            "id": 1,
                            "timestamp": "2024-01-20T15:30:00Z",
                            "event_type": "webhook_updated",
                            "user_id": 987654321,
                            "details": {
                                "old_url": "https://old.example.com/webhook",
                                "new_url": "https://new.example.com/webhook",
                            },
                            "ip_address": "192.168.1.100",
                            "user_agent": "TelegramBot/1.0",
                        },
                        {
                            "id": 2,
                            "timestamp": "2024-01-20T15:25:00Z",
                            "event_type": "failed_authentication",
                            "user_id": None,
                            "details": {"reason": "invalid_token", "attempts": 3},
                            "ip_address": "192.168.1.200",
                            "user_agent": "curl/7.68.0",
                        },
                    ],
                    "pagination": {
                        "total": 150,
                        "page": 1,
                        "per_page": 50,
                        "total_pages": 3,
                    },
                    "filters": {
                        "event_type": None,
                        "user_id": None,
                        "date_from": "2024-01-20T00:00:00Z",
                        "date_to": "2024-01-20T23:59:59Z",
                    },
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(
                api_client.url_for("get_audit_log"), params={"page": 1, "per_page": 50}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "entries" in data
        assert "pagination" in data
        assert len(data["entries"]) == 2

        entry = data["entries"][0]
        assert entry["event_type"] == "webhook_updated"
        assert entry["user_id"] == 987654321
        assert "old_url" in entry["details"]
        assert "new_url" in entry["details"]

        pagination = data["pagination"]
        assert pagination["total"] == 150
        assert pagination["page"] == 1
        assert pagination["total_pages"] == 3


class TestTelegramIntegrationFlows:
    """Позитивные тесты интеграционных потоков Telegram."""

    async def test_complete_webhook_management_flow(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест полного потока управления webhook."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act & Assert - Step 1: Получить текущий webhook
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()

            # Mock для получения webhook info
            mock_webhook_info = MagicMock()
            mock_webhook_info.url = ""
            mock_webhook_info.pending_update_count = 0
            mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_webhook_info"))
            assert response.status_code == 200
            assert response.json()["url"] == ""

        # Step 2: Установить webhook
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.set_webhook.return_value = True
            mock_service.return_value = mock_telegram_service

            webhook_data = {"url": "https://example.com/webhook/telegram"}
            response = await api_client.post(
                api_client.url_for("set_webhook"), json=webhook_data
            )
            assert response.status_code == 200
            assert response.json()["status"] == "success"

        # Step 3: Проверить установленный webhook
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()

            mock_webhook_info = MagicMock()
            mock_webhook_info.url = "https://example.com/webhook/telegram"
            mock_webhook_info.pending_update_count = 0
            mock_telegram_service.bot.get_webhook_info.return_value = mock_webhook_info
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_webhook_info"))
            assert response.status_code == 200
            assert response.json()["url"] == "https://example.com/webhook/telegram"

        # Step 4: Удалить webhook
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.bot.delete_webhook.return_value = True
            mock_service.return_value = mock_telegram_service

            response = await api_client.post(api_client.url_for("delete_webhook"))
            assert response.status_code == 200
            assert response.json()["status"] == "success"

    async def test_bot_status_and_notifications_flow(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест потока проверки статуса бота и отправки уведомлений."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act & Assert - Step 1: Проверить статус бота
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()

            mock_bot_info = MagicMock()
            mock_bot_info.id = 987654321
            mock_bot_info.username = "quiz_bot"
            mock_telegram_service.bot.get_me.return_value = mock_bot_info
            mock_telegram_service.get_bot_status = MagicMock(
                return_value={"status": "online", "uptime": "5d 12h 30m"}
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("get_bot_status"))
            assert response.status_code == 200
            assert response.json()["status"]["status"] == "online"

        # Step 2: Отправить тестовое уведомление
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_admin_notification = AsyncMock(
                return_value={"success": True, "sent_count": 1, "failed_count": 0}
            )
            mock_service.return_value = mock_telegram_service

            notification_data = {
                "message": "Bot status check completed successfully",
                "type": "info",
                "priority": "normal",
            }
            response = await api_client.post(
                api_client.url_for("send_admin_notification"), json=notification_data
            )
            assert response.status_code == 200
            assert response.json()["success"] is True

        # Step 3: Проверить health check
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.health_check = AsyncMock(
                return_value={
                    "status": "healthy",
                    "checks": {"bot_api": True, "webhook": True, "database": True},
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(api_client.url_for("telegram_health_check"))
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            assert all(response.json()["checks"].values())

    async def test_webapp_survey_completion_flow(
        self, api_client: AsyncClient, regular_user
    ):
        """Тест полного потока завершения опроса через WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act & Assert - Step 1: Получить конфигурацию WebApp
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.generate_webapp_config = MagicMock(
                return_value={
                    "theme": "dark",
                    "user_id": regular_user.id,
                    "features": {"main_button": True, "haptic_feedback": True},
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_config"))
            assert response.status_code == 200
            assert response.json()["user_id"] == regular_user.id

        # Step 2: Получить список опросов
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_surveys = AsyncMock(
                return_value={
                    "surveys": [
                        {
                            "id": 1,
                            "title": "Customer Survey",
                            "questions_count": 5,
                            "is_completed": False,
                        }
                    ],
                    "pagination": {"total": 1},
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(api_client.url_for("get_webapp_surveys"))
            assert response.status_code == 200
            assert len(response.json()["surveys"]) == 1

        # Step 3: Получить детали опроса
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_survey_details = AsyncMock(
                return_value={
                    "survey": {"id": 1, "title": "Customer Survey"},
                    "questions": [
                        {
                            "id": 1,
                            "type": "multiple_choice",
                            "title": "Rate our service",
                            "options": [
                                {"id": 1, "text": "Excellent"},
                                {"id": 2, "text": "Good"},
                            ],
                        }
                    ],
                    "progress": {"completion_percentage": 0},
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_survey_details", survey_id=1)
            )
            assert response.status_code == 200
            assert response.json()["survey"]["id"] == 1

        # Step 4: Отправить ответы
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.submit_survey_answers = AsyncMock(
                return_value={
                    "success": True,
                    "response_id": 456,
                    "completion_percentage": 100,
                    "status": "completed",
                }
            )
            mock_service.return_value = mock_webapp_service

            answers_data = {
                "survey_id": 1,
                "answers": [
                    {
                        "question_id": 1,
                        "answer_type": "multiple_choice",
                        "value": "Excellent",
                        "option_id": 1,
                    }
                ],
            }
            response = await api_client.post(
                api_client.url_for("submit_webapp_survey_answers"), json=answers_data
            )
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert response.json()["completion_percentage"] == 100

        # Step 5: Получить профиль пользователя с обновленной статистикой
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_user_profile = AsyncMock(
                return_value={
                    "user": {"id": regular_user.id, "username": regular_user.username},
                    "statistics": {"surveys_completed": 1, "total_responses": 1},
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_user_profile")
            )
            assert response.status_code == 200
            assert response.json()["statistics"]["surveys_completed"] == 1

    async def test_bot_webapp_integration_flow(
        self, api_client: AsyncClient, regular_user, test_settings
    ):
        """Тест интеграции между Bot API и WebApp."""
        # Arrange
        api_client.force_authenticate(user=regular_user)

        # Act & Assert - Step 1: Получить update от бота с WebApp запросом
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.dp = MagicMock()
            mock_telegram_service.dp.feed_update = AsyncMock()
            mock_service.return_value = mock_telegram_service

            update_data = {
                "update_id": 123456,
                "message": {
                    "message_id": 1,
                    "date": 1642680000,
                    "chat": {"id": 123456789, "type": "private"},
                    "from": {"id": 123456789, "username": "testuser"},
                    "web_app_data": {
                        "data": "survey_123_start",
                        "button_text": "Start Survey",
                    },
                },
            }

            response = await api_client.post(
                api_client.url_for(
                    "handle_webhook", token=test_settings.telegram_bot_token
                ),
                json=update_data,
            )
            assert response.status_code == 200

        # Step 2: Аутентифицировать пользователя в WebApp
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.authenticate_user = AsyncMock(
                return_value={
                    "user": {
                        "id": regular_user.id,
                        "telegram_id": 123456789,
                        "username": "testuser",
                    },
                    "access_token": "jwt_token_123",
                    "webapp_session_id": "session_456",
                }
            )
            mock_service.return_value = mock_webapp_service

            auth_data = {
                "init_data": "user=%7B%22id%22%3A123456789%2C%22username%22%3A%22testuser%22%7D"
            }
            response = await api_client.post(
                api_client.url_for("authenticate_webapp_user"), json=auth_data
            )
            assert response.status_code == 200
            assert response.json()["user"]["telegram_id"] == 123456789

        # Step 3: Получить данные опроса через WebApp
        with patch("src.routers.telegram_webapp.get_webapp_service") as mock_service:
            mock_webapp_service = MagicMock()
            mock_webapp_service.get_webapp_survey_details = AsyncMock(
                return_value={
                    "survey": {
                        "id": 123,
                        "title": "Bot Integration Survey",
                        "created_via": "telegram_bot",
                    },
                    "questions": [
                        {"id": 1, "type": "text", "title": "How do you like our bot?"}
                    ],
                }
            )
            mock_service.return_value = mock_webapp_service

            response = await api_client.get(
                api_client.url_for("get_webapp_survey_details", survey_id=123)
            )
            assert response.status_code == 200
            assert response.json()["survey"]["created_via"] == "telegram_bot"

        # Step 4: Отправить уведомление о завершении через Bot API
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.send_notification = AsyncMock(
                return_value={
                    "success": True,
                    "message_id": 789,
                    "delivery_status": "delivered",
                }
            )
            mock_service.return_value = mock_telegram_service

            notification_data = {
                "user_id": regular_user.id,
                "message": "Survey completed via WebApp! 🎉",
                "type": "success",
                "source": "webapp_integration",
            }
            response = await api_client.post(
                api_client.url_for("send_telegram_notification"), json=notification_data
            )
            assert response.status_code == 200
            assert response.json()["success"] is True


class TestTelegramMonitoringIntegration:
    """Позитивные тесты интеграции с мониторингом."""

    async def test_telegram_health_monitoring(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест мониторинга здоровья Telegram сервисов."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.get_comprehensive_health = AsyncMock(
                return_value={
                    "overall_status": "healthy",
                    "components": {
                        "bot_api": {
                            "status": "healthy",
                            "response_time": 0.05,
                            "last_check": "2024-01-20T16:00:00Z",
                        },
                        "webhook": {
                            "status": "healthy",
                            "pending_updates": 0,
                            "last_update": "2024-01-20T15:59:45Z",
                        },
                        "webapp": {
                            "status": "healthy",
                            "active_sessions": 25,
                            "avg_response_time": 0.08,
                        },
                        "database": {
                            "status": "healthy",
                            "connection_pool": "optimal",
                            "query_performance": "good",
                        },
                    },
                    "metrics": {
                        "uptime": "99.9%",
                        "availability": "99.95%",
                        "error_rate": "0.01%",
                        "throughput": "1250 req/min",
                    },
                    "alerts": [],
                    "performance_grade": "A",
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(
                api_client.url_for("get_telegram_health_comprehensive")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["overall_status"] == "healthy"
        assert data["performance_grade"] == "A"

        components = data["components"]
        assert components["bot_api"]["status"] == "healthy"
        assert components["webhook"]["status"] == "healthy"
        assert components["webapp"]["status"] == "healthy"
        assert components["database"]["status"] == "healthy"

        metrics = data["metrics"]
        assert metrics["uptime"] == "99.9%"
        assert metrics["availability"] == "99.95%"
        assert metrics["error_rate"] == "0.01%"
        assert len(data["alerts"]) == 0

    async def test_telegram_performance_metrics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения метрик производительности Telegram."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.get_performance_metrics = AsyncMock(
                return_value={
                    "real_time": {
                        "requests_per_second": 15.5,
                        "avg_response_time": 0.08,
                        "error_rate": 0.01,
                        "active_connections": 25,
                    },
                    "historical": {
                        "requests_24h": 22500,
                        "errors_24h": 12,
                        "avg_response_time_24h": 0.09,
                        "peak_requests_per_minute": 45,
                    },
                    "bot_api": {
                        "successful_requests": 22488,
                        "failed_requests": 12,
                        "timeout_requests": 0,
                        "rate_limit_hits": 0,
                    },
                    "webhook": {
                        "updates_received": 1850,
                        "updates_processed": 1850,
                        "processing_time_avg": 0.05,
                        "queue_size": 0,
                    },
                    "webapp": {
                        "active_sessions": 25,
                        "page_views": 450,
                        "avg_session_duration": 8.5,
                        "bounce_rate": 0.15,
                    },
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(
                api_client.url_for("get_telegram_performance_metrics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        real_time = data["real_time"]
        assert real_time["requests_per_second"] == 15.5
        assert real_time["avg_response_time"] == 0.08
        assert real_time["error_rate"] == 0.01

        historical = data["historical"]
        assert historical["requests_24h"] == 22500
        assert historical["errors_24h"] == 12

        bot_api = data["bot_api"]
        assert bot_api["successful_requests"] == 22488
        assert bot_api["failed_requests"] == 12
        assert bot_api["rate_limit_hits"] == 0

        webhook = data["webhook"]
        assert webhook["updates_received"] == 1850
        assert webhook["updates_processed"] == 1850
        assert webhook["queue_size"] == 0

        webapp = data["webapp"]
        assert webapp["active_sessions"] == 25
        assert webapp["avg_session_duration"] == 8.5

    async def test_telegram_usage_analytics(self, api_client: AsyncClient, admin_user):
        """Тест аналитики использования Telegram."""
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        with patch("src.routers.telegram.get_telegram_service") as mock_service:
            mock_telegram_service = MagicMock()
            mock_telegram_service.get_usage_analytics = AsyncMock(
                return_value={
                    "user_engagement": {
                        "total_users": 1250,
                        "active_users_24h": 350,
                        "active_users_7d": 850,
                        "active_users_30d": 1100,
                        "new_users_24h": 25,
                        "retention_rate": 0.85,
                    },
                    "feature_usage": {
                        "bot_commands": {
                            "start": 450,
                            "help": 89,
                            "create": 156,
                            "list": 234,
                            "stats": 67,
                        },
                        "webapp_features": {
                            "survey_creation": 156,
                            "survey_completion": 234,
                            "profile_views": 123,
                            "settings_changes": 45,
                        },
                    },
                    "content_stats": {
                        "surveys_created": 156,
                        "surveys_completed": 234,
                        "responses_submitted": 1250,
                        "avg_survey_completion_time": 4.5,
                    },
                    "geographic_distribution": {
                        "countries": {
                            "US": 450,
                            "GB": 250,
                            "CA": 150,
                            "AU": 100,
                            "DE": 90,
                        },
                        "top_cities": [
                            {"city": "New York", "users": 85},
                            {"city": "London", "users": 78},
                            {"city": "Toronto", "users": 65},
                        ],
                    },
                }
            )
            mock_service.return_value = mock_telegram_service

            response = await api_client.get(
                api_client.url_for("get_telegram_usage_analytics")
            )

        # Assert
        assert response.status_code == 200
        data = response.json()

        user_engagement = data["user_engagement"]
        assert user_engagement["total_users"] == 1250
        assert user_engagement["active_users_24h"] == 350
        assert user_engagement["retention_rate"] == 0.85

        feature_usage = data["feature_usage"]
        assert feature_usage["bot_commands"]["start"] == 450
        assert feature_usage["webapp_features"]["survey_creation"] == 156

        content_stats = data["content_stats"]
        assert content_stats["surveys_created"] == 156
        assert content_stats["avg_survey_completion_time"] == 4.5

        geographic = data["geographic_distribution"]
        assert geographic["countries"]["US"] == 450
        assert len(geographic["top_cities"]) == 3
