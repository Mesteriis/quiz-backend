"""
Positive тесты для профиля пользователя.

Содержит тесты успешных сценариев получения и обновления профиля,
интеграции с Telegram, управления данными пользователя.
"""

import pytest


class TestUserProfilePositive:
    """Positive тесты профиля пользователя."""

    @pytest.mark.asyncio
    async def test_get_current_user_profile(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест успешного получения профиля текущего пользователя."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == regular_user.id
        assert data["username"] == regular_user.username
        assert data["email"] == regular_user.email
        assert data["first_name"] == regular_user.first_name
        assert data["last_name"] == regular_user.last_name
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_by_id(self, api_client, db_session, regular_user):
        """Тест успешного получения профиля пользователя по ID."""
        # Act
        response = await api_client.get(f"/api/users/{regular_user.id}/profile")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == regular_user.id
        assert data["username"] == regular_user.username
        assert data["email"] == regular_user.email
        assert data["first_name"] == regular_user.first_name
        assert data["last_name"] == regular_user.last_name
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_update_profile_basic_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест успешного обновления базовых полей профиля."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "Updated bio",
            "location": "Updated location",
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["bio"] == "Updated bio"
        assert data["location"] == "Updated location"

    @pytest.mark.asyncio
    async def test_update_profile_localization(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест успешного обновления настроек локализации."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "language": "ru",
            "timezone": "Europe/Moscow",
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "ru"
        assert data["timezone"] == "Europe/Moscow"

    @pytest.mark.asyncio
    async def test_update_profile_partial_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест обновления только части полей профиля."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        original_last_name = regular_user.last_name
        update_data = {
            "first_name": "OnlyFirst",
            # last_name не обновляем
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == "OnlyFirst"
        assert data["last_name"] == original_last_name  # Не изменился

    @pytest.mark.asyncio
    async def test_update_profile_telegram_fields(
        self, api_client, db_session, telegram_user, auth_headers_factory
    ):
        """Тест обновления Telegram полей профиля."""
        # Arrange
        headers = auth_headers_factory(telegram_user.id)
        update_data = {
            "telegram_username": "newtgusername",
            "telegram_first_name": "NewTgFirst",
            "telegram_last_name": "NewTgLast",
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["telegram_username"] == "newtgusername"
        assert data["telegram_first_name"] == "NewTgFirst"
        assert data["telegram_last_name"] == "NewTgLast"

    @pytest.mark.asyncio
    async def test_profile_with_complete_information(
        self, api_client, db_session, user_with_profile, auth_headers_factory
    ):
        """Тест профиля с полной информацией."""
        # Arrange
        user, profile = user_with_profile
        headers = auth_headers_factory(user.id)

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user.id
        assert data["first_name"] == profile.first_name
        assert data["last_name"] == profile.last_name
        assert data["bio"] == profile.bio
        assert data["location"] == profile.location
        assert data["profile_picture_url"] == profile.profile_picture_url

    @pytest.mark.asyncio
    async def test_profile_telegram_integration(
        self, api_client, db_session, telegram_user_with_profile, auth_headers_factory
    ):
        """Тест интеграции профиля с Telegram."""
        # Arrange
        user, profile = telegram_user_with_profile
        headers = auth_headers_factory(user.id)

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["telegram_id"] == user.telegram_id
        assert data["telegram_username"] == user.telegram_username
        assert data["telegram_first_name"] == user.telegram_first_name
        assert data["telegram_last_name"] == user.telegram_last_name
        assert data["telegram_photo_url"] == user.telegram_photo_url

    @pytest.mark.asyncio
    async def test_profile_preserves_timestamps(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест что обновление профиля сохраняет временные метки."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Получаем исходные временные метки
        original_response = await api_client.get("/api/auth/profile", headers=headers)
        original_data = original_response.json()
        original_created_at = original_data["created_at"]

        # Act
        update_data = {"first_name": "Updated"}
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["created_at"] == original_created_at  # Не изменился
        assert data["updated_at"] != original_data["updated_at"]  # Обновился

    @pytest.mark.asyncio
    async def test_profile_admin_fields(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест профиля администратора."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == admin_user.id
        assert data["is_admin"] is True
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_profile_includes_statistics(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест что профиль включает статистику пользователя."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем наличие полей статистики
        assert "surveys_created" in data or "total_surveys" in data
        assert "responses_count" in data or "total_responses" in data
        assert "last_activity" in data or "last_login" in data

    @pytest.mark.asyncio
    async def test_profile_privacy_settings(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест настроек приватности профиля."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "profile_visibility": "private",
            "email_notifications": False,
            "telegram_notifications": True,
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["profile_visibility"] == "private"
        assert data["email_notifications"] is False
        assert data["telegram_notifications"] is True

    @pytest.mark.asyncio
    async def test_profile_supports_unicode(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест поддержки Unicode в профиле."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "bio": "Биография с эмодзи 🙂 и символами",
            "location": "Москва, Россия",
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == "Имя"
        assert data["last_name"] == "Фамилия"
        assert data["bio"] == "Биография с эмодзи 🙂 и символами"
        assert data["location"] == "Москва, Россия"

    @pytest.mark.asyncio
    async def test_profile_update_returns_complete_data(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест что обновление профиля возвращает полные данные."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)
        update_data = {"first_name": "Updated"}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем что возвращаются все основные поля
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data


class TestUsersListPositive:
    """Positive тесты списка пользователей."""

    @pytest.mark.asyncio
    async def test_get_users_list_admin(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест получения списка пользователей администратором."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get("/api/users", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert isinstance(data["users"], list)

    @pytest.mark.asyncio
    async def test_get_users_list_pagination(
        self, api_client, db_session, admin_user, auth_headers_factory, users_batch
    ):
        """Тест пагинации списка пользователей."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get("/api/users?page=1&limit=10", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["users"]) <= 10
        assert data["page"] == 1
        assert data["limit"] == 10
        assert data["total"] >= len(users_batch)

    @pytest.mark.asyncio
    async def test_get_users_list_filtering(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест фильтрации списка пользователей."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get("/api/users?is_active=true", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем что все возвращенные пользователи активны
        for user in data["users"]:
            assert user["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_users_list_search(
        self, api_client, db_session, admin_user, regular_user, auth_headers_factory
    ):
        """Тест поиска пользователей."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)
        search_query = regular_user.username[:3]  # Первые 3 символа

        # Act
        response = await api_client.get(
            f"/api/users?search={search_query}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем что поиск работает
        found_user = None
        for user in data["users"]:
            if user["id"] == regular_user.id:
                found_user = user
                break

        assert found_user is not None
        assert regular_user.username in found_user["username"]

    @pytest.mark.asyncio
    async def test_get_users_list_sorting(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест сортировки списка пользователей."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get(
            "/api/users?sort=username&order=asc", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем что пользователи отсортированы по username
        usernames = [user["username"] for user in data["users"]]
        assert usernames == sorted(usernames)

    @pytest.mark.asyncio
    async def test_get_users_list_includes_profiles(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест что список пользователей включает профили."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Act
        response = await api_client.get(
            "/api/users?include_profiles=true", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем что пользователи содержат данные профилей
        for user in data["users"]:
            assert "first_name" in user
            assert "last_name" in user
            assert "email" in user
