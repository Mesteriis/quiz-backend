"""
Граничные тесты для профилей пользователей.

Этот модуль содержит тесты для граничных случаев и особых условий:
- Лимиты размеров данных
- Специальные символы и кодировки
- Конкурентные изменения
- Производительность при больших объемах
- Экстремальные значения
"""

import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from tests.factories import UserFactory, ProfileFactory


class TestProfileSizeLimits:
    """Тесты лимитов размеров данных профилей."""

    async def test_create_profile_maximum_field_lengths(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с максимальными допустимыми длинами полей."""
        # Arrange - данные на границе лимитов
        profile_data = {
            "first_name": "A" * 50,  # максимальная длина имени
            "last_name": "B" * 50,  # максимальная длина фамилии
            "bio": "C" * 500,  # максимальная длина биографии
            "phone": "+1234567890123",  # максимальная длина телефона
            "website": "https://" + "w" * 235 + ".com",  # максимальная длина URL (255)
            "location": "L" * 100,  # максимальная длина локации
            "job_title": "J" * 100,  # максимальная длина должности
            "company": "C" * 100,  # максимальная длина компании
            "interests": [
                f"interest{i}" for i in range(30)
            ],  # максимальное количество интересов
            "languages": [
                f"l{i:02d}" for i in range(15)
            ],  # максимальное количество языков
            "social_links": {
                f"platform{i}": f"user{i}" for i in range(10)
            },  # максимальное количество соцсетей
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert len(data["first_name"]) == 50
        assert len(data["bio"]) == 500
        assert len(data["interests"]) == 30
        assert len(data["languages"]) == 15
        assert len(data["social_links"]) == 10

    async def test_create_profile_exceeding_field_limits(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с превышением лимитов полей."""
        # Arrange - данные превышающие лимиты
        profile_data = {
            "first_name": "A" * 51,  # превышение лимита имени
            "bio": "B" * 501,  # превышение лимита биографии
            "interests": [
                f"interest{i}" for i in range(31)
            ],  # превышение лимита интересов
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        detail_str = str(data["detail"]).lower()
        assert any(field in detail_str for field in ["first_name", "bio", "interests"])

    async def test_create_profile_minimum_valid_data(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с минимально допустимыми данными."""
        # Arrange - минимальные данные
        profile_data = {
            "first_name": "A"  # минимальная длина имени (1 символ)
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "A"
        assert data["last_name"] is None
        assert data["bio"] is None

    async def test_update_profile_large_social_links(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления профиля с большим количеством социальных ссылок."""
        # Arrange
        user, profile = user_with_complete_profile

        # Создаем много социальных ссылок
        large_social_links = {}
        for i in range(20):  # больше обычного лимита
            large_social_links[f"platform_{i}"] = f"user_handle_{i}"

        update_data = {"social_links": large_social_links}

        # Act
        api_client.force_authenticate(user=user)
        response = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        if response.status_code == 422:
            # Если есть лимит на количество социальных ссылок
            data = response.json()
            assert "social_links" in str(data["detail"]).lower()
        else:
            # Если лимита нет, должно обновиться успешно
            assert response.status_code == 200
            data = response.json()
            assert len(data["social_links"]) == 20


class TestProfileSpecialCharacters:
    """Тесты специальных символов и кодировок."""

    async def test_create_profile_unicode_emoji(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с Unicode и эмодзи."""
        # Arrange
        profile_data = {
            "first_name": "Анна 👩‍💻",
            "last_name": "Смирнова 🇷🇺",
            "bio": "Программистка из России 🐍 Python разработчик 💻 Люблю создавать крутые приложения ✨",
            "location": "Москва, Россия 🏙️",
            "interests": ["программирование 💻", "путешествия ✈️", "фотография 📸"],
            "languages": ["ru", "en", "de"],
            "social_links": {"telegram": "@anna_dev 📱", "github": "anna-codes 🐙"},
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "👩‍💻" in data["first_name"]
        assert "🇷🇺" in data["last_name"]
        assert "🐍" in data["bio"]
        assert "✨" in data["bio"]
        assert "🏙️" in data["location"]
        assert "💻" in data["interests"][0]
        assert "📱" in data["social_links"]["telegram"]

    async def test_create_profile_special_characters(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля со специальными символами."""
        # Arrange
        profile_data = {
            "first_name": "Marie-José",
            "last_name": "O'Connor-Smith",
            "bio": "Développeur & Designer @ Tech Co. (2019-2024) - Spécialisé en UX/UI",
            "location": "São Paulo, Brazil",
            "phone": "+55 (11) 98765-4321",
            "website": "https://marie-josé.dev",
            "social_links": {
                "linkedin": "marie-josé-o'connor",
                "email": "marie.josé@example.com",
            },
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Marie-José"
        assert data["last_name"] == "O'Connor-Smith"
        assert "Développeur" in data["bio"]
        assert "São Paulo" in data["location"]
        assert "marie-josé" in data["social_links"]["linkedin"]

    async def test_create_profile_html_xss_attempt(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с попыткой XSS через HTML."""
        # Arrange
        profile_data = {
            "first_name": "<script>alert('XSS')</script>John",
            "bio": "<img src=x onerror=alert('XSS')>Developer bio",
            "website": "javascript:alert('XSS')",
            "social_links": {"twitter": "<script>alert('XSS')</script>username"},
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        if response.status_code == 201:
            # Если создание прошло успешно, проверяем что HTML экранирован
            data = response.json()
            assert "<script>" not in data["first_name"]
            assert "<img" not in data["bio"]
            assert "javascript:" not in data["website"]
        else:
            # Если валидация отклонила данные
            assert response.status_code == 422

    async def test_create_profile_sql_injection_attempt(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с попыткой SQL инъекции."""
        # Arrange
        profile_data = {
            "first_name": "'; DROP TABLE profiles; --",
            "bio": "1' OR '1'='1",
            "location": "' UNION SELECT * FROM users --",
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        # SQL инъекция должна быть предотвращена ORM
        if response.status_code == 201:
            data = response.json()
            # Данные должны быть сохранены как есть (как строки)
            assert data["first_name"] == "'; DROP TABLE profiles; --"
        # Или валидация может отклонить подозрительные данные
        else:
            assert response.status_code in [400, 422]


class TestProfileConcurrency:
    """Тесты конкурентных изменений профилей."""

    async def test_concurrent_profile_updates(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест конкурентного обновления профиля."""
        # Arrange
        user, profile = user_with_complete_profile

        async def update_profile(field_name: str, value: str):
            """Функция для конкурентного обновления."""
            client = api_client
            client.force_authenticate(user=user)

            update_data = {field_name: value}
            response = await client.put(
                client.url_for("update_profile", profile_id=profile.id),
                json=update_data,
            )
            return response

        # Act - конкурентные обновления разных полей
        tasks = [
            update_profile("first_name", "Updated1"),
            update_profile("last_name", "Updated2"),
            update_profile("bio", "Updated bio"),
            update_profile("location", "Updated location"),
            update_profile("phone", "+1111111111"),
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        success_count = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 200:
                success_count += 1

        # Хотя бы одно обновление должно быть успешным
        assert success_count >= 1

    async def test_concurrent_profile_creation_same_user(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест конкурентного создания профилей для одного пользователя."""

        # Arrange
        async def create_profile(suffix: str):
            """Функция для конкурентного создания."""
            client = api_client
            client.force_authenticate(user=basic_user)

            profile_data = {"first_name": f"Test{suffix}"}
            response = await client.post(
                client.url_for("create_profile"), json=profile_data
            )
            return response

        # Act - конкурентные попытки создания
        tasks = [create_profile("1"), create_profile("2"), create_profile("3")]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        success_count = 0
        conflict_count = 0

        for response in responses:
            if not isinstance(response, Exception):
                if response.status_code == 201:
                    success_count += 1
                elif response.status_code == 409:  # Conflict
                    conflict_count += 1

        # Только один профиль должен быть создан
        assert success_count == 1
        assert conflict_count >= 1

    async def test_profile_optimistic_locking(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест оптимистичной блокировки при обновлении профилей."""
        # Arrange
        user, profile = user_with_complete_profile

        # Получаем текущую версию профиля
        api_client.force_authenticate(user=user)
        response1 = await api_client.get(api_client.url_for("get_my_profile"))
        assert response1.status_code == 200
        current_version = response1.json().get("version", 1)

        # Act - пытаемся обновить с устаревшей версией
        update_data = {
            "first_name": "Updated",
            "version": current_version - 1,  # устаревшая версия
        }

        response2 = await api_client.put(
            api_client.url_for("update_profile", profile_id=profile.id),
            json=update_data,
        )

        # Assert
        if "version" in update_data:
            # Если система поддерживает версионирование
            assert response2.status_code == 409  # Conflict
            data = response2.json()
            assert (
                "version" in str(data["detail"]).lower()
                or "conflict" in str(data["detail"]).lower()
            )
        else:
            # Если версионирование не поддерживается, обновление должно пройти
            assert response2.status_code == 200


class TestProfilePerformance:
    """Тесты производительности профилей."""

    async def test_bulk_profile_retrieval(
        self, api_client: AsyncClient, admin_user, multiple_users_with_profiles
    ):
        """Тест массового получения профилей."""
        # Arrange
        users_and_profiles = multiple_users_with_profiles
        user_ids = [user.id for user, _ in users_and_profiles]

        # Act
        api_client.force_authenticate(user=admin_user)
        start_time = datetime.utcnow()

        response = await api_client.post(
            api_client.url_for("bulk_get_profiles"), json={"user_ids": user_ids}
        )

        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["profiles"]) == len(user_ids)
        # Проверяем что запрос выполнился быстро (менее 2 секунд)
        assert response_time < 2.0

    async def test_profile_search_performance(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест производительности поиска профилей."""
        # Arrange
        search_queries = ["John", "Developer", "Moscow", "Python", "john@example.com"]

        # Act
        api_client.force_authenticate(user=admin_user)
        response_times = []

        for query in search_queries:
            start_time = datetime.utcnow()

            response = await api_client.get(
                api_client.url_for("search_profiles"),
                params={"query": query, "limit": 100},
            )

            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            response_times.append(response_time)

            assert response.status_code == 200

        # Assert
        # Все поисковые запросы должны выполняться быстро
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.0  # менее 1 секунды в среднем
        assert max(response_times) < 2.0  # максимум 2 секунды

    async def test_profile_pagination_large_dataset(
        self, api_client: AsyncClient, admin_user
    ):
        """Тест пагинации на большом наборе данных."""
        # Arrange
        large_page_size = 1000

        # Act
        api_client.force_authenticate(user=admin_user)
        start_time = datetime.utcnow()

        response = await api_client.get(
            api_client.url_for("list_profiles"),
            params={"page": 1, "size": large_page_size},
        )

        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
        assert "pagination" in data
        # Даже большая страница должна загружаться быстро
        assert response_time < 3.0


class TestProfileEdgeDates:
    """Тесты граничных дат в профилях."""

    async def test_create_profile_very_old_birth_date(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с очень старой датой рождения."""
        # Arrange
        profile_data = {
            "first_name": "Ancient",
            "birth_date": "1900-01-01",  # очень старая дата
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["birth_date"] == "1900-01-01"

    async def test_create_profile_recent_birth_date(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с недавней датой рождения (несовершеннолетний)."""
        # Arrange
        recent_date = (datetime.utcnow() - timedelta(days=365 * 10)).strftime(
            "%Y-%m-%d"
        )  # 10 лет назад
        profile_data = {"first_name": "Young", "birth_date": recent_date}

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        if response.status_code == 201:
            # Если система разрешает несовершеннолетних
            data = response.json()
            assert data["birth_date"] == recent_date
        else:
            # Если есть ограничение по возрасту
            assert response.status_code == 422
            data = response.json()
            assert (
                "age" in str(data["detail"]).lower()
                or "birth_date" in str(data["detail"]).lower()
            )

    async def test_create_profile_leap_year_date(
        self, api_client: AsyncClient, basic_user
    ):
        """Тест создания профиля с датой 29 февраля високосного года."""
        # Arrange
        profile_data = {
            "first_name": "Leap",
            "birth_date": "2000-02-29",  # 29 февраля високосного года
        }

        # Act
        api_client.force_authenticate(user=basic_user)
        response = await api_client.post(
            api_client.url_for("create_profile"), json=profile_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["birth_date"] == "2000-02-29"

    async def test_update_profile_timezone_edge_cases(
        self, api_client: AsyncClient, user_with_complete_profile
    ):
        """Тест обновления профиля с граничными временными зонами."""
        # Arrange
        user, profile = user_with_complete_profile

        edge_timezones = [
            "UTC",
            "Pacific/Kiritimati",  # UTC+14 (самая восточная зона)
            "Pacific/Midway",  # UTC-11 (одна из самых западных)
            "Asia/Kathmandu",  # UTC+5:45 (нестандартное смещение)
            "Australia/Adelaide",  # UTC+9:30 (другое нестандартное смещение)
        ]

        # Act & Assert
        api_client.force_authenticate(user=user)

        for timezone in edge_timezones:
            update_data = {"timezone": timezone}
            response = await api_client.put(
                api_client.url_for("update_profile", profile_id=profile.id),
                json=update_data,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["timezone"] == timezone
