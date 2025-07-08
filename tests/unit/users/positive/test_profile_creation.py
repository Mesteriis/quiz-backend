"""
Позитивные тесты для создания профилей пользователей.

Этот модуль содержит все успешные сценарии создания профилей:
- Создание с полными данными
- Создание с минимальными данными
- Создание с Telegram данными
- Создание с дополнительными полями
- Создание с URL и социальными сетями
"""

import pytest
from httpx import AsyncClient
from datetime import datetime

from tests.factories import UserFactory, ProfileFactory


class TestProfileCreationPositive:
    """Позитивные тесты создания профилей пользователей."""

    async def test_create_profile_full_data(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с полными данными."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Software developer with 5+ years experience",
            "phone": "+1234567890",
            "website": "https://johndoe.dev",
            "location": "New York, USA",
            "birth_date": "1990-05-15",
            "avatar_url": "https://example.com/avatar.jpg",
            "social_links": {
                "twitter": "johndoe",
                "linkedin": "john-doe",
                "github": "johndoe",
            },
            "interests": ["programming", "travel", "photography"],
            "languages": ["en", "es", "fr"],
            "timezone": "America/New_York",
            "is_public": True,
            "notification_preferences": {"email": True, "push": True, "sms": False},
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["first_name"] == profile_data["first_name"]
        assert data["last_name"] == profile_data["last_name"]
        assert data["bio"] == profile_data["bio"]
        assert data["phone"] == profile_data["phone"]
        assert data["website"] == profile_data["website"]
        assert data["location"] == profile_data["location"]
        assert data["birth_date"] == profile_data["birth_date"]
        assert data["avatar_url"] == profile_data["avatar_url"]
        assert data["social_links"] == profile_data["social_links"]
        assert data["interests"] == profile_data["interests"]
        assert data["languages"] == profile_data["languages"]
        assert data["timezone"] == profile_data["timezone"]
        assert data["is_public"] == profile_data["is_public"]
        assert (
            data["notification_preferences"] == profile_data["notification_preferences"]
        )
        assert data["user_id"] == user.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_profile_minimal_data(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с минимальными данными."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {"first_name": "Jane"}

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["first_name"] == "Jane"
        assert data["last_name"] is None
        assert data["bio"] is None
        assert data["phone"] is None
        assert data["website"] is None
        assert data["location"] is None
        assert data["birth_date"] is None
        assert data["avatar_url"] is None
        assert data["social_links"] is None
        assert data["interests"] == []
        assert data["languages"] == []
        assert data["is_public"] is False
        assert data["user_id"] == user.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_profile_with_telegram_data(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с данными из Telegram."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "Telegram",
            "last_name": "User",
            "bio": "Connected via Telegram",
            "telegram_username": "telegramuser",
            "telegram_id": 123456789,
            "languages": ["en", "ru"],
            "timezone": "Europe/Moscow",
            "is_public": True,
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["first_name"] == profile_data["first_name"]
        assert data["last_name"] == profile_data["last_name"]
        assert data["bio"] == profile_data["bio"]
        assert data["telegram_username"] == profile_data["telegram_username"]
        assert data["telegram_id"] == profile_data["telegram_id"]
        assert data["languages"] == profile_data["languages"]
        assert data["timezone"] == profile_data["timezone"]
        assert data["is_public"] == profile_data["is_public"]
        assert data["user_id"] == user.id

    async def test_create_profile_with_social_links(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с социальными сетями."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "Social",
            "last_name": "User",
            "bio": "Active on social media",
            "website": "https://mysite.com",
            "social_links": {
                "twitter": "socialuser",
                "linkedin": "social-user",
                "github": "socialuser",
                "instagram": "socialuser",
                "facebook": "socialuser",
                "youtube": "socialuser",
                "tiktok": "socialuser",
            },
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["social_links"]["twitter"] == "socialuser"
        assert data["social_links"]["linkedin"] == "social-user"
        assert data["social_links"]["github"] == "socialuser"
        assert data["social_links"]["instagram"] == "socialuser"
        assert data["social_links"]["facebook"] == "socialuser"
        assert data["social_links"]["youtube"] == "socialuser"
        assert data["social_links"]["tiktok"] == "socialuser"
        assert data["website"] == "https://mysite.com"

    async def test_create_profile_with_interests_and_languages(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с интересами и языками."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "Polyglot",
            "last_name": "Developer",
            "bio": "Multilingual software developer",
            "interests": [
                "programming",
                "machine learning",
                "data science",
                "web development",
                "mobile development",
                "devops",
                "cybersecurity",
                "blockchain",
                "ai",
                "open source",
            ],
            "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
            "timezone": "UTC",
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["interests"] == profile_data["interests"]
        assert data["languages"] == profile_data["languages"]
        assert data["timezone"] == profile_data["timezone"]
        assert len(data["interests"]) == 10
        assert len(data["languages"]) == 10

    async def test_create_profile_with_notification_preferences(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с настройками уведомлений."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "Notification",
            "last_name": "User",
            "bio": "Manages notification preferences",
            "notification_preferences": {
                "email": True,
                "push": True,
                "sms": False,
                "telegram": True,
                "in_app": True,
                "marketing": False,
                "updates": True,
                "reminders": True,
                "survey_invites": True,
                "results": True,
            },
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        preferences = data["notification_preferences"]
        assert preferences["email"] is True
        assert preferences["push"] is True
        assert preferences["sms"] is False
        assert preferences["telegram"] is True
        assert preferences["in_app"] is True
        assert preferences["marketing"] is False
        assert preferences["updates"] is True
        assert preferences["reminders"] is True
        assert preferences["survey_invites"] is True
        assert preferences["results"] is True

    async def test_create_profile_with_privacy_settings(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с настройками приватности."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "Privacy",
            "last_name": "User",
            "bio": "Values privacy and security",
            "is_public": False,
            "show_email": False,
            "show_phone": False,
            "show_location": False,
            "show_birth_date": False,
            "allow_contact": True,
            "allow_marketing": False,
            "data_sharing": False,
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["is_public"] is False
        assert data["show_email"] is False
        assert data["show_phone"] is False
        assert data["show_location"] is False
        assert data["show_birth_date"] is False
        assert data["allow_contact"] is True
        assert data["allow_marketing"] is False
        assert data["data_sharing"] is False

    async def test_create_profile_with_professional_info(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с профессиональной информацией."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "Professional",
            "last_name": "Developer",
            "bio": "Senior Software Engineer specializing in backend development",
            "job_title": "Senior Software Engineer",
            "company": "Tech Corp",
            "industry": "Technology",
            "experience_years": 8,
            "skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
                "Kubernetes",
                "AWS",
                "Redis",
                "GraphQL",
            ],
            "education": "Master's in Computer Science",
            "certifications": [
                "AWS Certified Solutions Architect",
                "Google Cloud Professional",
                "MongoDB Certified Developer",
            ],
            "portfolio_url": "https://portfolio.dev",
            "resume_url": "https://resume.pdf",
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["job_title"] == profile_data["job_title"]
        assert data["company"] == profile_data["company"]
        assert data["industry"] == profile_data["industry"]
        assert data["experience_years"] == profile_data["experience_years"]
        assert data["skills"] == profile_data["skills"]
        assert data["education"] == profile_data["education"]
        assert data["certifications"] == profile_data["certifications"]
        assert data["portfolio_url"] == profile_data["portfolio_url"]
        assert data["resume_url"] == profile_data["resume_url"]

    async def test_create_profile_with_unicode_content(
        self, api_client: AsyncClient, async_session
    ):
        """Тест создания профиля с Unicode контентом."""
        # Arrange
        user = UserFactory()
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        profile_data = {
            "first_name": "Иван",
            "last_name": "Петров",
            "bio": "Программист из России 🇷🇺. Люблю создавать красивые приложения ✨",
            "location": "Москва, Россия",
            "interests": ["программирование", "путешествия", "фотография"],
            "languages": ["ru", "en"],
            "company": "Технологическая компания",
            "job_title": "Старший разработчик",
            "social_links": {"telegram": "ivan_petrov", "vk": "ivan.petrov"},
        }

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["first_name"] == "Иван"
        assert data["last_name"] == "Петров"
        assert "🇷🇺" in data["bio"]
        assert "✨" in data["bio"]
        assert data["location"] == "Москва, Россия"
        assert data["interests"] == ["программирование", "путешествия", "фотография"]
        assert data["company"] == "Технологическая компания"
        assert data["job_title"] == "Старший разработчик"
        assert data["social_links"]["telegram"] == "ivan_petrov"
        assert data["social_links"]["vk"] == "ivan.petrov"
