"""
Позитивные тесты для управления профилями пользователей.

Этот модуль содержит все успешные сценарии управления профилями:
- Обновление профилей
- Удаление профилей
- Поиск и фильтрация профилей
- Получение статистики профилей
- Массовые операции
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

from tests.factories import UserFactory, ProfileFactory


class TestProfileUpdates:
    """Позитивные тесты обновления профилей."""

    async def test_update_profile_basic_fields(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления основных полей профиля."""
        # Arrange
        user, profile = user_with_complete_profile

        update_data = {
            "first_name": "Updated John",
            "last_name": "Updated Doe",
            "bio": "Updated bio with new exciting information about my career",
            "phone": "+9876543210",
            "location": "Updated City, Updated Country",
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["bio"] == update_data["bio"]
        assert data["phone"] == update_data["phone"]
        assert data["location"] == update_data["location"]
        assert "updated_at" in data

        # Проверяем что updated_at изменился
        original_updated_at = datetime.fromisoformat(profile.updated_at.isoformat())
        new_updated_at = datetime.fromisoformat(data["updated_at"])
        assert new_updated_at > original_updated_at

    async def test_update_profile_partial_fields(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест частичного обновления профиля."""
        # Arrange
        user, profile = user_with_complete_profile
        original_last_name = profile.last_name

        update_data = {
            "first_name": "Partially Updated"
            # Остальные поля не обновляем
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == "Partially Updated"
        assert data["last_name"] == original_last_name  # не изменилось
        assert data["bio"] == profile.bio  # не изменилось

    async def test_update_profile_social_links(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления социальных ссылок."""
        # Arrange
        user, profile = user_with_complete_profile

        update_data = {
            "social_links": {
                "twitter": "updated_twitter",
                "linkedin": "updated-linkedin",
                "github": "updated_github",
                "instagram": "updated_instagram",
                "youtube": "updated_youtube",
                "tiktok": "updated_tiktok",
            }
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        social_links = data["social_links"]
        assert social_links["twitter"] == "updated_twitter"
        assert social_links["linkedin"] == "updated-linkedin"
        assert social_links["github"] == "updated_github"
        assert social_links["instagram"] == "updated_instagram"
        assert social_links["youtube"] == "updated_youtube"
        assert social_links["tiktok"] == "updated_tiktok"

    async def test_update_profile_interests_and_languages(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления интересов и языков."""
        # Arrange
        user, profile = user_with_complete_profile

        update_data = {
            "interests": [
                "artificial intelligence",
                "machine learning",
                "blockchain",
                "quantum computing",
                "robotics",
            ],
            "languages": ["en", "es", "fr", "de", "it", "pt"],
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["interests"] == update_data["interests"]
        assert data["languages"] == update_data["languages"]
        assert len(data["interests"]) == 5
        assert len(data["languages"]) == 6

    async def test_update_profile_professional_info(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления профессиональной информации."""
        # Arrange
        user, profile = user_with_complete_profile

        update_data = {
            "job_title": "Senior Software Architect",
            "company": "Updated Tech Corporation",
            "industry": "Software Development",
            "experience_years": 10,
            "skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
                "Kubernetes",
                "AWS",
                "React",
                "TypeScript",
            ],
            "education": "Master's in Computer Science from MIT",
            "certifications": [
                "AWS Solutions Architect Professional",
                "Google Cloud Professional",
                "Kubernetes Administrator",
            ],
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["job_title"] == update_data["job_title"]
        assert data["company"] == update_data["company"]
        assert data["industry"] == update_data["industry"]
        assert data["experience_years"] == update_data["experience_years"]
        assert data["skills"] == update_data["skills"]
        assert data["education"] == update_data["education"]
        assert data["certifications"] == update_data["certifications"]

    async def test_update_profile_privacy_settings(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления настроек приватности."""
        # Arrange
        user, profile = user_with_complete_profile

        update_data = {
            "is_public": False,
            "show_email": False,
            "show_phone": False,
            "show_location": True,
            "show_birth_date": False,
            "allow_contact": True,
            "allow_marketing": False,
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["is_public"] is False
        assert data["show_email"] is False
        assert data["show_phone"] is False
        assert data["show_location"] is True
        assert data["show_birth_date"] is False
        assert data["allow_contact"] is True
        assert data["allow_marketing"] is False


class TestProfileDeletion:
    """Позитивные тесты удаления профилей."""

    async def test_delete_own_profile(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест удаления собственного профиля."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.delete(
            api_client.url_for("delete_profile", profile_id=profile.id)
        )

        # Assert
        assert response.status_code == 204

        # Проверяем что профиль действительно удален
        response = await api_client.get(api_client.url_for("get_my_profile"))
        assert response.status_code == 404

    async def test_admin_delete_profile(
        self, api_client: AsyncClient, user_with_complete_profile, admin_user
    ):
        """Тест удаления профиля администратором."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.delete(
            api_client.url_for("admin_delete_profile", profile_id=profile.id)
        )

        # Assert
        assert response.status_code == 204

        # Проверяем что профиль удален
        response = await api_client.get(
            api_client.url_for("get_profile", user_id=user.id)
        )
        assert response.status_code == 404

    async def test_soft_delete_profile(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест мягкого удаления профиля."""
        # Arrange
        user, profile = user_with_complete_profile

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("soft_delete_profile", profile_id=profile.id)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_deleted"] is True
        assert "deleted_at" in data

        # Профиль должен быть скрыт из обычных запросов
        response = await api_client.get(api_client.url_for("get_my_profile"))
        assert response.status_code == 404


class TestProfileSearch:
    """Позитивные тесты поиска профилей."""

    async def test_search_profiles_by_name(
        self, api_client: AsyncClient, admin_user, multiple_users_with_profiles
    ):
        """Тест поиска профилей по имени."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("search_profiles"), params={"query": "John", "limit": 10}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "profiles" in data
        assert "pagination" in data
        assert isinstance(data["profiles"], list)

        # Проверяем что все результаты содержат запрос
        for profile in data["profiles"]:
            assert (
                "john"
                in (profile["first_name"] + " " + profile.get("last_name", "")).lower()
            )

    async def test_search_profiles_by_location(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска профилей по локации."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("search_profiles"),
            params={"query": "New York", "filter": "location", "limit": 10},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "profiles" in data
        for profile in data["profiles"]:
            if profile.get("location"):
                assert "new york" in profile["location"].lower()

    async def test_search_profiles_by_company(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска профилей по компании."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("search_profiles"),
            params={"query": "Tech Corp", "filter": "company", "limit": 10},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "profiles" in data
        for profile in data["profiles"]:
            if profile.get("company"):
                assert "tech corp" in profile["company"].lower()

    async def test_search_profiles_with_filters(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест поиска профилей с дополнительными фильтрами."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("search_profiles"),
            params={
                "query": "developer",
                "is_public": True,
                "has_avatar": True,
                "languages": "en,es",
                "sort": "created_at",
                "order": "desc",
                "limit": 20,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "profiles" in data
        assert "pagination" in data

        for profile in data["profiles"]:
            assert profile["is_public"] is True
            if profile.get("avatar_url"):
                assert profile["avatar_url"] is not None

    async def test_search_profiles_pagination(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест пагинации в поиске профилей."""
        # Act - первая страница
        api_client.force_authenticate(user=admin_user)
        response1 = await api_client.get(
            api_client.url_for("search_profiles"),
            params={"query": "user", "page": 1, "size": 5},
        )

        # Act - вторая страница
        response2 = await api_client.get(
            api_client.url_for("search_profiles"),
            params={"query": "user", "page": 2, "size": 5},
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Проверяем пагинацию
        assert len(data1["profiles"]) <= 5
        assert len(data2["profiles"]) <= 5

        # Результаты на разных страницах должны быть разными
        ids1 = {p["id"] for p in data1["profiles"]}
        ids2 = {p["id"] for p in data2["profiles"]}
        assert ids1.isdisjoint(ids2)  # нет пересечений


class TestProfileStatistics:
    """Позитивные тесты статистики профилей."""

    async def test_get_profile_statistics_overview(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения общей статистики профилей."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(api_client.url_for("get_profile_statistics"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем основные метрики
        assert "total_profiles" in data
        assert "active_profiles" in data
        assert "public_profiles" in data
        assert "private_profiles" in data
        assert "verified_profiles" in data
        assert "profiles_with_avatars" in data

        # Проверяем типы данных
        assert isinstance(data["total_profiles"], int)
        assert isinstance(data["active_profiles"], int)
        assert data["total_profiles"] >= 0
        assert data["active_profiles"] >= 0

    async def test_get_profile_statistics_by_period(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения статистики профилей за период."""
        # Arrange
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(
            api_client.url_for("get_profile_statistics"),
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "period" in data
        assert "profiles_created" in data
        assert "profiles_updated" in data
        assert "profiles_deleted" in data

        # Проверяем период
        assert data["period"]["start"] == start_date.isoformat()
        assert data["period"]["end"] == end_date.isoformat()

    async def test_get_profile_statistics_by_demographics(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения демографической статистики профилей."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(api_client.url_for("get_profile_demographics"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем демографические данные
        assert "by_location" in data
        assert "by_language" in data
        assert "by_industry" in data
        assert "by_experience" in data
        assert "by_age_group" in data

        # Проверяем структуру данных
        assert isinstance(data["by_location"], dict)
        assert isinstance(data["by_language"], dict)
        assert isinstance(data["by_industry"], dict)

    async def test_get_popular_interests_and_skills(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест получения популярных интересов и навыков."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.get(api_client.url_for("get_popular_tags"))

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "popular_interests" in data
        assert "popular_skills" in data
        assert "trending_topics" in data

        # Проверяем структуру
        for category in ["popular_interests", "popular_skills", "trending_topics"]:
            assert isinstance(data[category], list)
            if data[category]:
                # Каждый элемент должен содержать название и количество
                item = data[category][0]
                assert "name" in item
                assert "count" in item
                assert isinstance(item["count"], int)


class TestBulkProfileOperations:
    """Позитивные тесты массовых операций с профилями."""

    async def test_bulk_update_profiles(
        self, api_client: AsyncClient, admin_user, multiple_users_with_profiles
    ):
        """Тест массового обновления профилей."""
        # Arrange
        users_and_profiles = multiple_users_with_profiles
        profile_ids = [profile.id for _, profile in users_and_profiles[:3]]

        update_data = {
            "profile_ids": profile_ids,
            "updates": {"is_public": True, "allow_contact": True},
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.post(
            api_client.url_for("bulk_update_profiles"), json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "updated_count" in data
        assert data["updated_count"] == 3
        assert "updated_profiles" in data
        assert len(data["updated_profiles"]) == 3

        # Проверяем что обновления применились
        for profile in data["updated_profiles"]:
            assert profile["is_public"] is True
            assert profile["allow_contact"] is True

    async def test_bulk_export_profiles(self, api_client: AsyncClient, admin_user):
        """Тест массового экспорта профилей."""
        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.post(
            api_client.url_for("export_profiles"),
            json={
                "format": "csv",
                "fields": ["first_name", "last_name", "email", "company", "location"],
                "filters": {"is_public": True},
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "export_id" in data
        assert "download_url" in data
        assert "status" in data
        assert data["status"] == "processing"

    async def test_bulk_import_profiles(self, api_client: AsyncClient, admin_user):
        """Тест массового импорта профилей."""
        # Arrange
        import_data = {
            "profiles": [
                {
                    "first_name": "Import1",
                    "last_name": "User1",
                    "email": "import1@example.com",
                    "company": "Import Corp",
                },
                {
                    "first_name": "Import2",
                    "last_name": "User2",
                    "email": "import2@example.com",
                    "location": "Import City",
                },
            ]
        }

        # Act
        api_client.force_authenticate(user=admin_user)
        response = await api_client.post(
            api_client.url_for("import_profiles"), json=import_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "import_id" in data
        assert "status" in data
        assert "imported_count" in data
        assert "failed_count" in data
        assert data["status"] == "processing"
