"""
Негативные тесты для ошибок профилей пользователей.

Этот модуль содержит тесты для всех негативных сценариев:
- Валидационные ошибки (400)
- Ошибки аутентификации (401/403)
- Ошибки не найдено (404)
- Ошибки конфликтов (409)
- Ошибки доступа (403)
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch

from tests.factories import UserFactory, ProfileFactory


class TestProfileCreationErrors:
    """Негативные тесты создания профилей."""

    async def test_create_profile_unauthorized(self, api_client: AsyncClient):
        """Тест создания профиля без аутентификации."""
        # Arrange
        profile_data = {"first_name": "John", "last_name": "Doe"}

        # Act
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()

    async def test_create_profile_already_exists(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест создания профиля когда он уже существует."""
        # Arrange
        user, profile = user_with_complete_profile

        new_profile_data = {"first_name": "Another", "last_name": "Name"}

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=new_profile_data
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()

    async def test_create_profile_empty_first_name(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с пустым именем."""
        # Arrange
        profile_data = {"first_name": "", "last_name": "Doe"}

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "first_name" in str(data["detail"]).lower()

    async def test_create_profile_invalid_phone(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с неправильным номером телефона."""
        # Arrange
        profile_data = {"first_name": "John", "phone": "invalid-phone-number"}

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "phone" in str(data["detail"]).lower()

    async def test_create_profile_invalid_website_url(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с неправильным URL сайта."""
        # Arrange
        profile_data = {"first_name": "John", "website": "not-a-valid-url"}

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "website" in str(data["detail"]).lower()

    async def test_create_profile_invalid_birth_date(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с неправильной датой рождения."""
        # Arrange
        profile_data = {"first_name": "John", "birth_date": "invalid-date-format"}

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "birth_date" in str(data["detail"]).lower()

    async def test_create_profile_future_birth_date(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с датой рождения в будущем."""
        # Arrange
        profile_data = {
            "first_name": "John",
            "birth_date": "2025-01-01",  # будущая дата
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "future" in str(data["detail"]).lower()
            or "birth_date" in str(data["detail"]).lower()
        )

    async def test_create_profile_invalid_social_links_format(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с неправильным форматом социальных ссылок."""
        # Arrange
        profile_data = {
            "first_name": "John",
            "social_links": "not-a-dict",  # должен быть dict
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "social_links" in str(data["detail"]).lower()

    async def test_create_profile_invalid_interests_format(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с неправильным форматом интересов."""
        # Arrange
        profile_data = {
            "first_name": "John",
            "interests": "not-a-list",  # должен быть list
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "interests" in str(data["detail"]).lower()

    async def test_create_profile_invalid_languages_format(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с неправильным форматом языков."""
        # Arrange
        profile_data = {
            "first_name": "John",
            "languages": "not-a-list",  # должен быть list
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "languages" in str(data["detail"]).lower()

    async def test_create_profile_too_long_fields(
        self, api_client: AsyncClient, basic_user, large_profile_data
    ):
        """Тест создания профиля с слишком длинными полями."""
        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=large_profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        # Проверяем что хотя бы одно из длинных полей вызвало ошибку
        detail_str = str(data["detail"]).lower()
        assert any(
            field in detail_str
            for field in ["first_name", "last_name", "bio", "website"]
        )


class TestProfileRetrievalErrors:
    """Негативные тесты получения профилей."""

    async def test_get_profile_unauthorized(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест получения профиля без аутентификации."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=user.id)
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()

    async def test_get_profile_not_found(self, api_client: AsyncClient, verified_user):
        """Тест получения несуществующего профиля."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=99999)  # несуществующий ID
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_my_profile_not_found(self, api_client: AsyncClient, basic_user):
        """Тест получения собственного профиля когда его нет."""
        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.get(api_client.url_for("get_my_profile"))

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_profile_invalid_user_id(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения профиля с неправильным ID пользователя."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_profile", user_id="invalid-id")
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "user_id" in str(data["detail"]).lower()

    async def test_get_profile_blocked_user(
        self, api_client: AsyncClient, verified_user, async_session
    ):
        """Тест получения профиля заблокированного пользователя."""
        # Arrange
        blocked_user = UserFactory(is_active=False, is_blocked=True)
        profile = ProfileFactory(user=blocked_user)

        async_session.add(blocked_user)
        async_session.add(profile)
        await async_session.commit()
        await async_session.refresh(blocked_user)

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=blocked_user.id)
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "blocked" in data["detail"].lower()
            or "access denied" in data["detail"].lower()
        )


class TestProfileUpdateErrors:
    """Негативные тесты обновления профилей."""

    async def test_update_profile_unauthorized(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления профиля без аутентификации."""
        # Arrange
        user, profile = user_with_complete_profile
        update_data = {"first_name": "Updated"}

        # Act
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()

    async def test_update_profile_not_found(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест обновления несуществующего профиля."""
        # Arrange
        update_data = {"first_name": "Updated"}

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=99999), json=update_data
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_update_profile_forbidden(
        self, api_client: AsyncClient, user_with_complete_profile, verified_user
    ):
        """Тест обновления чужого профиля."""
        # Arrange
        user, profile = user_with_complete_profile
        update_data = {"first_name": "Hacked"}

        # Act
        api_client.force_authenticate(user=verified_user)  # другой пользователь
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "permission" in data["detail"].lower()
            or "forbidden" in data["detail"].lower()
        )

    async def test_update_profile_invalid_data(
        self, api_client: AsyncClient, user_with_complete_profile, invalid_profile_data
    ):
        """Тест обновления профиля с невалидными данными."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=invalid_profile_data,
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        # Проверяем что есть ошибки валидации
        detail_str = str(data["detail"]).lower()
        assert any(
            field in detail_str
            for field in ["first_name", "phone", "website", "birth_date"]
        )

    async def test_update_profile_database_error(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления профиля при ошибке базы данных."""
        # Arrange
        user, profile = user_with_complete_profile
        update_data = {"first_name": "Updated"}

        # Act
        api_client.force_authenticate(user=user)
        with patch("src.repositories.profile.ProfileRepository.update") as mock_update:
            mock_update.side_effect = Exception("Database error")

            response = await api_client.put(
                api_client.url_for("update_profile", profile_id=profile.id),
                json=update_data,
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "internal error" in data["detail"].lower()


class TestProfileDeletionErrors:
    """Негативные тесты удаления профилей."""

    async def test_delete_profile_unauthorized(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест удаления профиля без аутентификации."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        response = await api_client.delete(
            api_client.url_for("delete_profile", profile_id=profile.id)
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()

    async def test_delete_profile_not_found(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест удаления несуществующего профиля."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.delete(
            api_client.url_for("delete_profile", profile_id=99999)
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_delete_profile_forbidden(
        self, api_client: AsyncClient, user_with_complete_profile, verified_user
    ):
        """Тест удаления чужого профиля."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        api_client.force_authenticate(user=verified_user)  # другой пользователь
        response = await api_client.delete(
            api_client.url_for("delete_profile", profile_id=profile.id)
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "permission" in data["detail"].lower()
            or "forbidden" in data["detail"].lower()
        )

    async def test_delete_profile_admin_required(
        self, api_client: AsyncClient, user_with_complete_profile, verified_user
    ):
        """Тест попытки администраторского удаления без прав."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.delete(
            api_client.url_for("admin_delete_profile", profile_id=profile.id)
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "permission" in data["detail"].lower()
        )


class TestProfileSearchErrors:
    """Негативные тесты поиска профилей."""

    async def test_search_profiles_unauthorized(self, api_client: AsyncClient):
        """Тест поиска профилей без аутентификации."""
        # Act
        response = await api_client.get(
            api_client.url_for("search_profiles"), params={"query": "test"}
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()

    async def test_search_profiles_admin_required(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест поиска профилей без админских прав."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(
            api_client.url_for("admin_search_profiles"), params={"query": "test"}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "permission" in data["detail"].lower()
        )

    async def test_search_profiles_invalid_parameters(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска профилей с неправильными параметрами."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("search_profiles"),
            params={
                "page": -1,  # неправильная страница
                "size": 1000,  # слишком большой размер
                "sort": "invalid_field",  # несуществующее поле
            },
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        detail_str = str(data["detail"]).lower()
        assert any(param in detail_str for param in ["page", "size", "sort"])

    async def test_search_profiles_empty_query(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска профилей с пустым запросом."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("search_profiles"),
            params={"query": ""},  # пустой запрос
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "query" in str(data["detail"]).lower()

    async def test_search_profiles_too_short_query(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска профилей со слишком коротким запросом."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("search_profiles"),
            params={"query": "a"},  # слишком короткий запрос
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert (
            "query" in str(data["detail"]).lower()
            and "length" in str(data["detail"]).lower()
        )


class TestProfileStatisticsErrors:
    """Негативные тесты статистики профилей."""

    async def test_get_profile_statistics_unauthorized(self, api_client: AsyncClient):
        """Тест получения статистики без аутентификации."""
        # Act
        response = await api_client.get(api_client.url_for("get_profile_statistics"))

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()

    async def test_get_profile_statistics_admin_required(
        self, api_client: AsyncClient, verified_user
    ):
        """Тест получения статистики без админских прав."""
        # Act
        api_client.force_authenticate(user=verified_user)
        response = await api_client.get(api_client.url_for("get_profile_statistics"))

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert (
            "admin" in data["detail"].lower() or "permission" in data["detail"].lower()
        )

    async def test_get_profile_statistics_invalid_date_range(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики с неправильным диапазоном дат."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("get_profile_statistics"),
            params={
                "start_date": "2024-12-31",
                "end_date": "2024-01-01",  # конец раньше начала
            },
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "date" in str(data["detail"]).lower()

    async def test_get_profile_statistics_invalid_date_format(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики с неправильным форматом даты."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("get_profile_statistics"),
            params={"start_date": "invalid-date", "end_date": "also-invalid"},
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "date" in str(data["detail"]).lower()
