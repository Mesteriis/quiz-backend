"""
Позитивные тесты для получения профилей пользователей.

Этот модуль содержит все успешные сценарии получения профилей:
- Получение собственного профиля
- Получение профиля по ID
- Получение публичного профиля
- Получение профиля с фильтрацией данных
- Получение профиля с включенными связями
"""

import pytest
from httpx import AsyncClient
from datetime import datetime

from tests.factories import UserFactory, ProfileFactory


class TestProfileRetrievalPositive:
    """Позитивные тесты получения профилей пользователей."""

    @pytest.fixture
    async def user_with_profile(self, async_session):
        """Пользователь с полным профилем."""
        user = UserFactory()
        profile_data = {
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Software developer",
            "phone": "+1234567890",
            "website": "https://johndoe.dev",
            "location": "New York, USA",
            "birth_date": "1990-05-15",
            "avatar_url": "https://example.com/avatar.jpg",
            "social_links": {"twitter": "johndoe", "linkedin": "john-doe"},
            "interests": ["programming", "travel"],
            "languages": ["en", "es"],
            "timezone": "America/New_York",
            "is_public": True,
            "job_title": "Senior Developer",
            "company": "Tech Corp",
        }

        profile = ProfileFactory(**profile_data, user=user)

        async_session.add(user)
        async_session.add(profile)
        await async_session.commit()
        await async_session.refresh(user)
        await async_session.refresh(profile)

        return user, profile

    @pytest.fixture
    async def private_user_with_profile(self, async_session):
        """Пользователь с приватным профилем."""
        user = UserFactory()
        profile_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "bio": "Private user",
            "phone": "+9876543210",
            "location": "Los Angeles, USA",
            "is_public": False,
            "show_email": False,
            "show_phone": False,
            "show_location": False,
        }

        profile = ProfileFactory(**profile_data, user=user)

        async_session.add(user)
        async_session.add(profile)
        await async_session.commit()
        await async_session.refresh(user)
        await async_session.refresh(profile)

        return user, profile

    async def test_get_my_profile_success(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения собственного профиля."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(api_client.url_for("get_my_profile"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        assert data["user_id"] == user.id
        assert data["first_name"] == profile.first_name
        assert data["last_name"] == profile.last_name
        assert data["bio"] == profile.bio
        assert data["phone"] == profile.phone
        assert data["website"] == profile.website
        assert data["location"] == profile.location
        assert data["birth_date"] == profile.birth_date
        assert data["avatar_url"] == profile.avatar_url
        assert data["social_links"] == profile.social_links
        assert data["interests"] == profile.interests
        assert data["languages"] == profile.languages
        assert data["timezone"] == profile.timezone
        assert data["is_public"] == profile.is_public
        assert data["job_title"] == profile.job_title
        assert data["company"] == profile.company
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_profile_by_id_success(
        self, api_client: AsyncClient, user_with_profile, async_session
    ):
        """Тест получения профиля по ID."""
        # Arrange
        user, profile = user_with_profile

        # Создаем другого пользователя для запроса
        requesting_user = UserFactory()
        async_session.add(requesting_user)
        await async_session.commit()
        await async_session.refresh(requesting_user)

        # Act
        api_client.force_authenticate(user=requesting_user)
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=user.id)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        assert data["user_id"] == user.id
        assert data["first_name"] == profile.first_name
        assert data["last_name"] == profile.last_name
        assert data["bio"] == profile.bio
        # Публичный профиль показывает все данные
        assert data["website"] == profile.website
        assert data["location"] == profile.location
        assert data["social_links"] == profile.social_links
        assert data["interests"] == profile.interests
        assert data["languages"] == profile.languages
        assert data["timezone"] == profile.timezone
        assert data["is_public"] == profile.is_public

    async def test_get_public_profile_filtered_data(
        self, api_client: AsyncClient, private_user_with_profile, async_session
    ):
        """Тест получения приватного профиля с фильтрацией данных."""
        # Arrange
        user, profile = private_user_with_profile

        # Создаем другого пользователя для запроса
        requesting_user = UserFactory()
        async_session.add(requesting_user)
        await async_session.commit()
        await async_session.refresh(requesting_user)

        # Act
        api_client.force_authenticate(user=requesting_user)
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=user.id)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        assert data["user_id"] == user.id
        assert data["first_name"] == profile.first_name
        assert data["last_name"] == profile.last_name
        # Приватные данные скрыты
        assert data["phone"] is None  # show_phone = False
        assert data["location"] is None  # show_location = False
        assert data["is_public"] == profile.is_public

    async def test_get_profile_with_includes(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения профиля с включенными связями."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(
            api_client.url_for("get_my_profile"),
            params={"include": "user,statistics,activity"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        # Проверяем включенные данные пользователя
        assert "user" in data
        assert data["user"]["id"] == user.id
        assert data["user"]["email"] == user.email
        # Проверяем статистику
        assert "statistics" in data
        assert "surveys_completed" in data["statistics"]
        assert "profile_views" in data["statistics"]
        # Проверяем активность
        assert "activity" in data
        assert "last_login" in data["activity"]
        assert "last_profile_update" in data["activity"]

    async def test_get_profile_with_fields_filter(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения профиля с фильтром полей."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(
            api_client.url_for("get_my_profile"),
            params={"fields": "first_name,last_name,bio,website"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем что возвращены только запрошенные поля
        assert "first_name" in data
        assert "last_name" in data
        assert "bio" in data
        assert "website" in data
        # Проверяем что остальные поля отсутствуют
        assert "phone" not in data
        assert "location" not in data
        assert "social_links" not in data
        assert "interests" not in data

    async def test_get_profile_with_minimal_fields(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения профиля с минимальными полями."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(
            api_client.url_for("get_my_profile"),
            params={"fields": "id,first_name,avatar_url"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем только основные поля
        assert len(data.keys()) == 3
        assert data["id"] == profile.id
        assert data["first_name"] == profile.first_name
        assert data["avatar_url"] == profile.avatar_url

    async def test_get_profile_for_card_view(
        self, api_client: AsyncClient, user_with_profile, async_session
    ):
        """Тест получения профиля для отображения в карточке."""
        # Arrange
        user, profile = user_with_profile

        requesting_user = UserFactory()
        async_session.add(requesting_user)
        await async_session.commit()
        await async_session.refresh(requesting_user)

        # Act
        api_client.force_authenticate(user=requesting_user)
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=user.id),
            params={
                "fields": "id,first_name,last_name,avatar_url,bio,job_title,company,location",
                "format": "card",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем поля для карточки
        assert data["id"] == profile.id
        assert data["first_name"] == profile.first_name
        assert data["last_name"] == profile.last_name
        assert data["avatar_url"] == profile.avatar_url
        assert data["bio"] == profile.bio
        assert data["job_title"] == profile.job_title
        assert data["company"] == profile.company
        assert data["location"] == profile.location

    async def test_get_profile_for_list_view(
        self, api_client: AsyncClient, user_with_profile, async_session
    ):
        """Тест получения профиля для отображения в списке."""
        # Arrange
        user, profile = user_with_profile

        requesting_user = UserFactory()
        async_session.add(requesting_user)
        await async_session.commit()
        await async_session.refresh(requesting_user)

        # Act
        api_client.force_authenticate(user=requesting_user)
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=user.id),
            params={
                "fields": "id,first_name,last_name,avatar_url,job_title",
                "format": "list",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем минимальные поля для списка
        assert len(data.keys()) == 5
        assert data["id"] == profile.id
        assert data["first_name"] == profile.first_name
        assert data["last_name"] == profile.last_name
        assert data["avatar_url"] == profile.avatar_url
        assert data["job_title"] == profile.job_title

    async def test_get_profile_with_localization(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения профиля с локализацией."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(
            api_client.url_for("get_my_profile"), headers={"Accept-Language": "ru-RU"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        # Проверяем что поля возвращены с локализованными значениями
        if "metadata" in data:
            assert data["metadata"]["locale"] == "ru-RU"

    async def test_get_profile_with_timezone_conversion(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения профиля с конвертацией временных зон."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(
            api_client.url_for("get_my_profile"),
            headers={"X-Timezone": "Europe/London"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        # Проверяем что временные данные возвращены в правильной зоне
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_profile_with_cache_headers(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения профиля с заголовками кеширования."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(api_client.url_for("get_my_profile"))

        # Assert
        assert response.status_code == 200

        # Проверяем заголовки кеширования
        assert "ETag" in response.headers
        assert "Last-Modified" in response.headers
        assert "Cache-Control" in response.headers

    async def test_get_profile_conditional_request(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест условного запроса профиля с If-None-Match."""
        # Arrange
        user, profile = user_with_profile

        # Первый запрос
        api_client.force_authenticate(user=user)
        response1 = await api_client.get(api_client.url_for("get_my_profile"))

        assert response1.status_code == 200
        etag = response1.headers.get("ETag")

        # Act - второй запрос с ETag
        response2 = await api_client.get(
            api_client.url_for("get_my_profile"), headers={"If-None-Match": etag}
        )

        # Assert
        assert response2.status_code == 304  # Not Modified

    async def test_get_profile_performance_metrics(
        self, api_client: AsyncClient, user_with_profile
    ):
        """Тест получения профиля с метриками производительности."""
        # Arrange
        user, profile = user_with_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.get(
            api_client.url_for("get_my_profile"), headers={"X-Include-Metrics": "true"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        # Проверяем метрики в заголовках
        assert "X-Response-Time" in response.headers
        assert "X-Query-Count" in response.headers
