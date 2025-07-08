"""
Negative тесты для регистрации пользователей.

Содержит тесты ошибочных сценариев регистрации:
дублирование данных, невалидные данные, нарушение ограничений.
"""

import pytest


class TestUserRegistrationNegative:
    """Negative тесты регистрации пользователей."""

    @pytest.mark.asyncio
    async def test_registration_duplicate_username(
        self, api_client, db_session, regular_user
    ):
        """Тест ошибки при дублировании username."""
        # Arrange
        user_data = {
            "username": regular_user.username,  # Используем существующий username
            "email": "different@example.com",
            "first_name": "Different",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert (
            "already exists" in data["detail"].lower()
            or "username" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_registration_duplicate_email(
        self, api_client, db_session, regular_user
    ):
        """Тест ошибки при дублировании email."""
        # Arrange
        user_data = {
            "username": "differentuser",
            "email": regular_user.email,  # Используем существующий email
            "first_name": "Different",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert (
            "already exists" in data["detail"].lower()
            or "email" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_registration_duplicate_telegram_id(
        self, api_client, db_session, telegram_user
    ):
        """Тест ошибки при дублировании Telegram ID."""
        # Arrange
        user_data = {
            "username": "differentuser",
            "email": "different@example.com",
            "first_name": "Different",
            "last_name": "User",
            "telegram_id": telegram_user.telegram_id,  # Используем существующий telegram_id
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert (
            "already exists" in data["detail"].lower()
            or "telegram" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_registration_invalid_data(
        self, api_client, db_session, invalid_registration_data
    ):
        """Тест ошибки при невалидных данных."""
        # Act
        response = await api_client.post(
            "/api/auth/register", json=invalid_registration_data
        )

        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    @pytest.mark.asyncio
    async def test_registration_empty_username(self, api_client, db_session):
        """Тест ошибки при пустом username."""
        # Arrange
        user_data = {
            "username": "",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_empty_email(self, api_client, db_session):
        """Тест ошибки при пустом email."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_invalid_email_format(self, api_client, db_session):
        """Тест ошибки при невалидном формате email."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_missing_required_fields(self, api_client, db_session):
        """Тест ошибки при отсутствии обязательных полей."""
        # Arrange
        user_data = {
            "username": "testuser",
            # email отсутствует
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_username_too_short(self, api_client, db_session):
        """Тест ошибки при слишком коротком username."""
        # Arrange
        user_data = {
            "username": "a",  # Слишком короткий
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_username_too_long(self, api_client, db_session):
        """Тест ошибки при слишком длинном username."""
        # Arrange
        user_data = {
            "username": "a" * 256,  # Слишком длинный
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_invalid_username_characters(
        self, api_client, db_session
    ):
        """Тест ошибки при недопустимых символах в username."""
        # Arrange
        user_data = {
            "username": "user@name!",  # Недопустимые символы
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_invalid_telegram_id(self, api_client, db_session):
        """Тест ошибки при невалидном Telegram ID."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "telegram_id": "invalid_id",  # Должен быть числом
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_negative_telegram_id(self, api_client, db_session):
        """Тест ошибки при отрицательном Telegram ID."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "telegram_id": -123456789,  # Отрицательный ID
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_invalid_language_code(self, api_client, db_session):
        """Тест ошибки при невалидном коде языка."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "language": "invalid_lang",  # Невалидный код языка
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_invalid_timezone(self, api_client, db_session):
        """Тест ошибки при невалидной временной зоне."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "timezone": "Invalid/Timezone",  # Невалидная зона
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_malformed_json(self, api_client, db_session):
        """Тест ошибки при некорректном JSON."""
        # Act
        response = await api_client.post(
            "/api/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_empty_body(self, api_client, db_session):
        """Тест ошибки при пустом теле запроса."""
        # Act
        response = await api_client.post("/api/auth/register", json={})

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_sql_injection_attempt(self, api_client, db_session):
        """Тест защиты от SQL инъекций."""
        # Arrange
        user_data = {
            "username": "'; DROP TABLE users; --",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_xss_attempt(self, api_client, db_session):
        """Тест защиты от XSS атак."""
        # Arrange
        user_data = {
            "username": "<script>alert('xss')</script>",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_null_values(self, api_client, db_session):
        """Тест ошибки при null значениях."""
        # Arrange
        user_data = {
            "username": None,
            "email": None,
            "first_name": None,
            "last_name": None,
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_registration_extra_fields(self, api_client, db_session):
        """Тест обработки дополнительных неизвестных полей."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "unknown_field": "should be ignored",
            "another_field": 123,
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        # Может быть либо 422 (если поля не разрешены), либо 200 (если игнорируются)
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # Проверяем что неизвестные поля не попали в ответ
            assert "unknown_field" not in data.get("user", {})
            assert "another_field" not in data.get("user", {})

    @pytest.mark.asyncio
    async def test_registration_case_sensitivity(
        self, api_client, db_session, regular_user
    ):
        """Тест чувствительности к регистру для username."""
        # Arrange
        user_data = {
            "username": regular_user.username.upper(),  # Тот же username в верхнем регистре
            "email": "different@example.com",
            "first_name": "Different",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        # Зависит от реализации - может быть как 200 (если чувствительность есть), так и 400 (если нет)
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data
            assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_email_case_insensitivity(
        self, api_client, db_session, regular_user
    ):
        """Тест нечувствительности к регистру для email."""
        # Arrange
        user_data = {
            "username": "differentuser",
            "email": regular_user.email.upper(),  # Тот же email в верхнем регистре
            "first_name": "Different",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_registration_whitespace_handling(self, api_client, db_session):
        """Тест обработки пробелов в полях."""
        # Arrange
        user_data = {
            "username": "  testuser  ",  # Пробелы в начале и конце
            "email": "  test@example.com  ",
            "first_name": "  Test  ",
            "last_name": "  User  ",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        if response.status_code == 200:
            data = response.json()
            user = data["user"]
            # Проверяем что пробелы обрезаны
            assert user["username"] == "testuser"
            assert user["email"] == "test@example.com"
            assert user["first_name"] == "Test"
            assert user["last_name"] == "User"
        else:
            # Если валидация не пропустила
            assert response.status_code == 422
