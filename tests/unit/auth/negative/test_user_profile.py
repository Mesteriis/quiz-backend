"""
Negative тесты для профиля пользователя.

Содержит тесты ошибочных сценариев работы с профилем:
неавторизованный доступ, невалидные данные, нарушение прав доступа.
"""

import pytest


class TestUserProfileNegative:
    """Negative тесты профиля пользователя."""

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, api_client, db_session):
        """Тест ошибки получения профиля без авторизации."""
        # Act
        response = await api_client.get("/api/auth/profile")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_unauthorized(self, api_client, db_session):
        """Тест ошибки обновления профиля без авторизации."""
        # Arrange
        update_data = {"first_name": "Updated"}

        # Act
        response = await api_client.put("/api/auth/profile", json=update_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_profile_invalid_token(
        self, api_client, db_session, invalid_auth_headers
    ):
        """Тест ошибки получения профиля с невалидным токеном."""
        # Act
        response = await api_client.get(
            "/api/auth/profile", headers=invalid_auth_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_invalid_token(
        self, api_client, db_session, invalid_auth_headers
    ):
        """Тест ошибки обновления профиля с невалидным токеном."""
        # Arrange
        update_data = {"first_name": "Updated"}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=invalid_auth_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_empty_data(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с пустыми данными."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        # Может быть 422 (если требуется хотя бы одно поле) или 200 (если пустое обновление разрешено)
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_update_profile_invalid_email(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с невалидным email."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"email": "invalid-email"}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_email(
        self, api_client, db_session, regular_user, admin_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с существующим email."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"email": admin_user.email}  # Email уже используется

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert (
            "already exists" in data["detail"].lower()
            or "duplicate" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_username(
        self, api_client, db_session, regular_user, admin_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с существующим username."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"username": admin_user.username}  # Username уже используется

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert (
            "already exists" in data["detail"].lower()
            or "duplicate" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_update_profile_invalid_username(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с невалидным username."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"username": "user@name!"}  # Недопустимые символы

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_empty_username(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с пустым username."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"username": ""}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_username_too_short(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля со слишком коротким username."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"username": "a"}  # Слишком короткий

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_username_too_long(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля со слишком длинным username."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"username": "a" * 256}  # Слишком длинный

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_invalid_language(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с невалидным языком."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"language": "invalid_lang"}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_invalid_timezone(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с невалидной временной зоной."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"timezone": "Invalid/Timezone"}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_null_values(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с null значениями."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "first_name": None,
            "last_name": None,
            "email": None,
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_invalid_telegram_id(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с невалидным Telegram ID."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"telegram_id": "invalid_id"}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_telegram_id(
        self, api_client, db_session, regular_user, telegram_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с существующим Telegram ID."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"telegram_id": telegram_user.telegram_id}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert (
            "already exists" in data["detail"].lower()
            or "duplicate" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_update_profile_read_only_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест попытки обновления read-only полей."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "id": 999,  # Read-only
            "created_at": "2023-01-01T00:00:00Z",  # Read-only
            "is_admin": True,  # Read-only для обычных пользователей
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        if response.status_code == 200:
            # Поля должны игнорироваться
            data = response.json()
            assert data["id"] == regular_user.id  # Не изменился
            assert data["is_admin"] is False  # Не изменился
        else:
            # Или возвращается ошибка
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_malformed_json(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с некорректным JSON."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        headers["Content-Type"] = "application/json"

        # Act
        response = await api_client.put(
            "/api/auth/profile", data="invalid json", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_very_long_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с очень длинными полями."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "first_name": "a" * 1000,
            "last_name": "b" * 1000,
            "bio": "c" * 10000,
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_profile_invalid_url_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки обновления профиля с невалидными URL."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "profile_picture_url": "not-a-url",
            "telegram_photo_url": "invalid://url",
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_nonexistent(self, api_client, db_session):
        """Тест ошибки получения профиля несуществующего пользователя."""
        # Act
        response = await api_client.get("/api/users/999999/profile")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_user_profile_invalid_id(self, api_client, db_session):
        """Тест ошибки получения профиля с невалидным ID."""
        # Act
        response = await api_client.get("/api/users/invalid_id/profile")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_negative_id(self, api_client, db_session):
        """Тест ошибки получения профиля с отрицательным ID."""
        # Act
        response = await api_client.get("/api/users/-1/profile")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_zero_id(self, api_client, db_session):
        """Тест ошибки получения профиля с нулевым ID."""
        # Act
        response = await api_client.get("/api/users/0/profile")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestUsersListNegative:
    """Negative тесты списка пользователей."""

    @pytest.mark.asyncio
    async def test_get_users_list_regular_user(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест ошибки получения списка пользователей обычным пользователем."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.get("/api/users", headers=headers)

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert (
            "permission" in data["detail"].lower()
            or "forbidden" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_get_users_list_unauthorized(self, api_client, db_session):
        """Тест ошибки получения списка пользователей без авторизации."""
        # Act
        response = await api_client.get("/api/users")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_users_list_invalid_token(
        self, api_client, db_session, invalid_auth_headers
    ):
        """Тест ошибки получения списка пользователей с невалидным токеном."""
        # Act
        response = await api_client.get("/api/users", headers=invalid_auth_headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_users_list_invalid_pagination(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест ошибки получения списка пользователей с невалидной пагинацией."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get("/api/users?page=-1&limit=0", headers=headers)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_users_list_invalid_page_type(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест ошибки получения списка пользователей с невалидным типом страницы."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get(
            "/api/users?page=invalid&limit=10", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_users_list_excessive_limit(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест ошибки получения списка пользователей с слишком большим лимитом."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get(
            "/api/users?page=1&limit=10000", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_users_list_invalid_filter(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест ошибки получения списка пользователей с невалидным фильтром."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get("/api/users?is_active=invalid", headers=headers)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_users_list_invalid_sort(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест ошибки получения списка пользователей с невалидной сортировкой."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get(
            "/api/users?sort=invalid_field&order=asc", headers=headers
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_users_list_sql_injection_search(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест защиты от SQL инъекций в поиске пользователей."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get(
            "/api/users?search='; DROP TABLE users; --", headers=headers
        )

        # Assert
        # Должен вернуть либо пустой результат, либо ошибку, но не выполнить SQL
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "users" in data
            # SQL инъекция не должна сработать, таблица должна существовать

    @pytest.mark.asyncio
    async def test_get_users_list_inactive_admin(
        self, api_client, db_session, auth_headers_factory
    ):
        """Тест ошибки получения списка пользователей неактивным админом."""
        # Arrange - создаем неактивного админа
        from tests.factories import AdminUserFactory

        inactive_admin = await AdminUserFactory.create(is_active=False)
        headers = auth_headers_factory(inactive_admin.id)

        # Act
        response = await api_client.get("/api/users", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
