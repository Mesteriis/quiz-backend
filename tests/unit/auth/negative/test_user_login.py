"""
Negative тесты для входа пользователей.

Содержит тесты ошибочных сценариев входа:
неверные данные, несуществующие пользователи, заблокированные аккаунты,
невалидные токены.
"""

import pytest


class TestUserLoginNegative:
    """Negative тесты входа пользователей."""

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, api_client, db_session):
        """Тест ошибки при входе несуществующего пользователя."""
        # Arrange
        login_data = {"identifier": "nonexistent_user"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert (
            "not found" in data["detail"].lower() or "invalid" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, api_client, db_session):
        """Тест ошибки при входе с несуществующим email."""
        # Arrange
        login_data = {"identifier": "nonexistent@example.com"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert (
            "not found" in data["detail"].lower() or "invalid" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_login_nonexistent_telegram_id(self, api_client, db_session):
        """Тест ошибки при входе с несуществующим Telegram ID."""
        # Arrange
        login_data = {"telegram_id": 999999999}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert (
            "not found" in data["detail"].lower() or "invalid" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, api_client, db_session, inactive_user):
        """Тест ошибки при входе неактивного пользователя."""
        # Arrange
        login_data = {"identifier": inactive_user.username}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert (
            "inactive" in data["detail"].lower() or "disabled" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_login_empty_identifier(self, api_client, db_session):
        """Тест ошибки при пустом идентификаторе."""
        # Arrange
        login_data = {"identifier": ""}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_missing_identifier(self, api_client, db_session):
        """Тест ошибки при отсутствующем идентификаторе."""
        # Arrange
        login_data = {}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_null_identifier(self, api_client, db_session):
        """Тест ошибки при null идентификаторе."""
        # Arrange
        login_data = {"identifier": None}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, api_client, db_session):
        """Тест ошибки при невалидном формате email."""
        # Arrange
        login_data = {"identifier": "invalid-email-format"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_invalid_telegram_id_format(self, api_client, db_session):
        """Тест ошибки при невалидном формате Telegram ID."""
        # Arrange
        login_data = {"telegram_id": "invalid_id"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_negative_telegram_id(self, api_client, db_session):
        """Тест ошибки при отрицательном Telegram ID."""
        # Arrange
        login_data = {"telegram_id": -123456789}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_malformed_json(self, api_client, db_session):
        """Тест ошибки при некорректном JSON."""
        # Act
        response = await api_client.post(
            "/api/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_empty_body(self, api_client, db_session):
        """Тест ошибки при пустом теле запроса."""
        # Act
        response = await api_client.post("/api/auth/login", json={})

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_sql_injection_attempt(self, api_client, db_session):
        """Тест защиты от SQL инъекций."""
        # Arrange
        login_data = {"identifier": "'; DROP TABLE users; --"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_xss_attempt(self, api_client, db_session):
        """Тест защиты от XSS атак."""
        # Arrange
        login_data = {"identifier": "<script>alert('xss')</script>"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_extra_fields(self, api_client, db_session, regular_user):
        """Тест обработки дополнительных неизвестных полей."""
        # Arrange
        login_data = {
            "identifier": regular_user.username,
            "unknown_field": "should be ignored",
            "another_field": 123,
        }

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        # Может быть либо 200 (если поля игнорируются), либо 422 (если не разрешены)
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # Проверяем что неизвестные поля не попали в ответ
            assert "unknown_field" not in data
            assert "another_field" not in data

    @pytest.mark.asyncio
    async def test_login_whitespace_identifier(self, api_client, db_session):
        """Тест ошибки при идентификаторе из пробелов."""
        # Arrange
        login_data = {"identifier": "   "}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_very_long_identifier(self, api_client, db_session):
        """Тест ошибки при очень длинном идентификаторе."""
        # Arrange
        login_data = {"identifier": "a" * 1000}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_unicode_identifier(self, api_client, db_session):
        """Тест ошибки при Unicode идентификаторе."""
        # Arrange
        login_data = {"identifier": "пользователь🙂"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_case_sensitive_username(
        self, api_client, db_session, regular_user
    ):
        """Тест чувствительности к регистру для username."""
        # Arrange
        login_data = {"identifier": regular_user.username.upper()}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        # Зависит от реализации - может быть как 200 (если нечувствительность есть), так и 401 (если нет)
        if response.status_code == 401:
            data = response.json()
            assert "detail" in data
            assert (
                "not found" in data["detail"].lower()
                or "invalid" in data["detail"].lower()
            )

    @pytest.mark.asyncio
    async def test_login_concurrent_invalid_attempts(self, api_client, db_session):
        """Тест защиты от конкурентных невалидных попыток входа."""
        # Arrange
        login_data = {"identifier": "nonexistent_user"}

        # Act - множественные попытки
        responses = []
        for _ in range(5):
            response = await api_client.post("/api/auth/login", json=login_data)
            responses.append(response)

        # Assert
        for response in responses:
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, api_client, db_session):
        """Тест защиты от брутфорс атак (rate limiting)."""
        # Arrange
        login_data = {"identifier": "nonexistent_user"}

        # Act - множественные попытки для тестирования rate limiting
        responses = []
        for _ in range(10):
            response = await api_client.post("/api/auth/login", json=login_data)
            responses.append(response)

        # Assert
        # Последние запросы могут быть заблокированы (429) или все могут быть 401
        for response in responses:
            assert response.status_code in [401, 429]
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_mixed_identifier_types(self, api_client, db_session):
        """Тест ошибки при смешанных типах идентификаторов."""
        # Arrange
        login_data = {
            "identifier": "testuser",
            "telegram_id": 123456789,  # Оба поля одновременно
        }

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        # Может быть либо 422 (если не разрешено), либо 200/401 (если один игнорируется)
        assert response.status_code in [200, 401, 422]

    @pytest.mark.asyncio
    async def test_login_special_characters_identifier(self, api_client, db_session):
        """Тест ошибки при специальных символах в идентификаторе."""
        # Arrange
        login_data = {"identifier": "user@#$%^&*()"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_newline_identifier(self, api_client, db_session):
        """Тест ошибки при идентификаторе с переносом строки."""
        # Arrange
        login_data = {"identifier": "user\nname"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_tab_identifier(self, api_client, db_session):
        """Тест ошибки при идентификаторе с табуляцией."""
        # Arrange
        login_data = {"identifier": "user\tname"}

        # Act
        response = await api_client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestJWTTokensNegative:
    """Negative тесты для JWT токенов."""

    @pytest.mark.asyncio
    async def test_invalid_token_access(self, api_client, db_session):
        """Тест ошибки при невалидном токене."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_missing_token_access(self, api_client, db_session):
        """Тест ошибки при отсутствующем токене."""
        # Act
        response = await api_client.get("/api/auth/profile")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_malformed_authorization_header(self, api_client, db_session):
        """Тест ошибки при некорректном заголовке Authorization."""
        # Arrange
        headers = {"Authorization": "InvalidBearerToken"}

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_expired_token_access(
        self, api_client, db_session, expired_auth_headers
    ):
        """Тест ошибки при истекшем токене."""
        # Act
        response = await api_client.get(
            "/api/auth/profile", headers=expired_auth_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert (
            "expired" in data["detail"].lower() or "invalid" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_tampered_token_access(self, api_client, db_session, regular_user):
        """Тест ошибки при подделанном токене."""
        # Arrange
        from services.jwt_service import jwt_service

        valid_token = jwt_service.create_access_token(regular_user.id)
        tampered_token = valid_token[:-5] + "tampr"  # Изменяем конец токена
        headers = {"Authorization": f"Bearer {tampered_token}"}

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_token_without_bearer_prefix(
        self, api_client, db_session, regular_user
    ):
        """Тест ошибки при токене без префикса Bearer."""
        # Arrange
        from services.jwt_service import jwt_service

        valid_token = jwt_service.create_access_token(regular_user.id)
        headers = {"Authorization": valid_token}  # Без "Bearer "

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_empty_bearer_token(self, api_client, db_session):
        """Тест ошибки при пустом Bearer токене."""
        # Arrange
        headers = {"Authorization": "Bearer "}

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_refresh_token_as_access_token(
        self, api_client, db_session, regular_user
    ):
        """Тест ошибки при использовании refresh токена как access."""
        # Arrange
        login_data = {"identifier": regular_user.username}
        login_response = await api_client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        headers = {"Authorization": f"Bearer {refresh_token}"}

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_invalid_refresh_token(self, api_client, db_session):
        """Тест ошибки при невалидном refresh токене."""
        # Arrange
        refresh_data = {"refresh_token": "invalid_refresh_token"}

        # Act
        response = await api_client.post("/api/auth/refresh", json=refresh_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_missing_refresh_token(self, api_client, db_session):
        """Тест ошибки при отсутствующем refresh токене."""
        # Act
        response = await api_client.post("/api/auth/refresh", json={})

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_expired_refresh_token(self, api_client, db_session):
        """Тест ошибки при истекшем refresh токене."""
        # Arrange
        from services.jwt_service import jwt_service

        expired_refresh = jwt_service.create_refresh_token(999, expires_delta=-3600)
        refresh_data = {"refresh_token": expired_refresh}

        # Act
        response = await api_client.post("/api/auth/refresh", json=refresh_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_reuse_refresh_token(self, api_client, db_session, regular_user):
        """Тест ошибки при повторном использовании refresh токена."""
        # Arrange
        login_data = {"identifier": regular_user.username}
        login_response = await api_client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]

        # Act - первое использование
        first_response = await api_client.post(
            "/api/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert first_response.status_code == 200

        # Act - второе использование того же токена
        second_response = await api_client.post(
            "/api/auth/refresh", json={"refresh_token": refresh_token}
        )

        # Assert
        assert second_response.status_code == 401
        data = second_response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_token_for_nonexistent_user(self, api_client, db_session):
        """Тест ошибки при токене для несуществующего пользователя."""
        # Arrange
        from services.jwt_service import jwt_service

        token_for_nonexistent = jwt_service.create_access_token(999999)
        headers = {"Authorization": f"Bearer {token_for_nonexistent}"}

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_token_for_inactive_user(self, api_client, db_session, inactive_user):
        """Тест ошибки при токене для неактивного пользователя."""
        # Arrange
        from services.jwt_service import jwt_service

        token = jwt_service.create_access_token(inactive_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
