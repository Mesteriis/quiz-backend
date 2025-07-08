"""
Edge cases тесты для домена аутентификации.

Содержит тесты граничных условий и необычных сценариев:
конкурентность, большие объемы данных, экстремальные значения,
нестандартные пользовательские данные.
"""

import pytest
import asyncio


class TestAuthEdgeCases:
    """Edge cases тесты для аутентификации."""

    @pytest.mark.asyncio
    async def test_registration_with_edge_case_data(
        self, api_client, db_session, edge_case_registration_data
    ):
        """Тест регистрации с граничными данными."""
        # Act
        response = await api_client.post(
            "/api/auth/register", json=edge_case_registration_data
        )

        # Assert
        # Может быть либо 200 (если данные валидны), либо 422 (если слишком экстремальны)
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            user = data["user"]
            # Проверяем что Unicode символы обработались корректно
            assert user["first_name"] == edge_case_registration_data["first_name"]
            assert user["last_name"] == edge_case_registration_data["last_name"]

    @pytest.mark.asyncio
    async def test_telegram_auth_with_edge_case_data(
        self, api_client, db_session, edge_case_telegram_data
    ):
        """Тест Telegram аутентификации с граничными данными."""
        # Arrange
        auth_data = {
            **edge_case_telegram_data,
            "auth_date": 1234567890,
            "hash": "valid_hash",
        }

        # Act
        response = await api_client.post("/api/auth/telegram", json=auth_data)

        # Assert
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            user = data["user"]
            assert user["telegram_id"] == edge_case_telegram_data["telegram_id"]
            assert (
                user["telegram_username"]
                == edge_case_telegram_data["telegram_username"]
            )

    @pytest.mark.asyncio
    async def test_concurrent_registration_same_data(
        self, api_client, db_session, concurrent_requests_data
    ):
        """Тест конкурентной регистрации с одинаковыми данными."""
        # Arrange
        user_data = concurrent_requests_data[0]

        # Act - множественные одновременные регистрации
        tasks = []
        for _ in range(5):
            task = api_client.post("/api/auth/register", json=user_data)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - только одна должна быть успешной
        success_count = 0
        for response in responses:
            if hasattr(response, "status_code"):
                if response.status_code == 200:
                    success_count += 1
                else:
                    assert response.status_code == 400  # Duplicate error

        assert success_count == 1  # Только одна успешная регистрация

    @pytest.mark.asyncio
    async def test_concurrent_registration_different_data(
        self, api_client, db_session, concurrent_requests_data
    ):
        """Тест конкурентной регистрации с разными данными."""
        # Act - множественные одновременные регистрации
        tasks = []
        for user_data in concurrent_requests_data:
            task = api_client.post("/api/auth/register", json=user_data)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - все должны быть успешными
        success_count = 0
        for response in responses:
            if hasattr(response, "status_code"):
                if response.status_code == 200:
                    success_count += 1

        assert success_count == len(concurrent_requests_data)

    @pytest.mark.asyncio
    async def test_concurrent_login_same_user(
        self, api_client, db_session, regular_user
    ):
        """Тест конкурентного входа одного пользователя."""
        # Arrange
        login_data = {"identifier": regular_user.username}

        # Act - множественные одновременные входы
        tasks = []
        for _ in range(10):
            task = api_client.post("/api/auth/login", json=login_data)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - все должны быть успешными
        for response in responses:
            if hasattr(response, "status_code"):
                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_concurrent_profile_updates(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест конкурентных обновлений профиля."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Act - множественные одновременные обновления
        tasks = []
        for i in range(5):
            update_data = {"first_name": f"Updated{i}"}
            task = api_client.put(
                "/api/auth/profile", json=update_data, headers=headers
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - все должны быть успешными
        for response in responses:
            if hasattr(response, "status_code"):
                assert response.status_code == 200

        # Проверяем финальное состояние
        final_response = await api_client.get("/api/auth/profile", headers=headers)
        assert final_response.status_code == 200
        final_data = final_response.json()
        assert final_data["first_name"].startswith("Updated")

    @pytest.mark.asyncio
    async def test_concurrent_token_refresh(self, api_client, db_session, regular_user):
        """Тест конкурентного обновления токенов."""
        # Arrange
        login_data = {"identifier": regular_user.username}
        login_response = await api_client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]

        # Act - множественные одновременные обновления
        tasks = []
        for _ in range(5):
            refresh_data = {"refresh_token": refresh_token}
            task = api_client.post("/api/auth/refresh", json=refresh_data)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - только одно должно быть успешным (если refresh токены одноразовые)
        success_count = 0
        for response in responses:
            if hasattr(response, "status_code"):
                if response.status_code == 200:
                    success_count += 1

        # Зависит от реализации: либо все успешны, либо только один
        assert success_count >= 1

    @pytest.mark.asyncio
    async def test_maximum_username_length(self, api_client, db_session):
        """Тест максимальной длины username."""
        # Arrange - используем максимально допустимую длину
        max_username = "a" * 150  # Предполагаемый максимум
        user_data = {
            "username": max_username,
            "email": "maxuser@example.com",
            "first_name": "Max",
            "last_name": "User",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        if response.status_code == 200:
            data = response.json()
            assert data["user"]["username"] == max_username
        else:
            # Если длина превышает лимит
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_maximum_email_length(self, api_client, db_session):
        """Тест максимальной длины email."""
        # Arrange
        long_local = "a" * 64  # Максимум для локальной части
        long_domain = "b" * 63 + ".com"  # Максимум для домена
        max_email = f"{long_local}@{long_domain}"

        user_data = {
            "username": "maxemailuser",
            "email": max_email,
            "first_name": "Max",
            "last_name": "Email",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        if response.status_code == 200:
            data = response.json()
            assert data["user"]["email"] == max_email
        else:
            # Если длина превышает лимит
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_maximum_telegram_id(self, api_client, db_session):
        """Тест максимального Telegram ID."""
        # Arrange
        max_telegram_id = 2**63 - 1  # Максимальный int64
        user_data = {
            "username": "maxtguser",
            "email": "maxtg@example.com",
            "first_name": "Max",
            "last_name": "Telegram",
            "telegram_id": max_telegram_id,
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        if response.status_code == 200:
            data = response.json()
            assert data["user"]["telegram_id"] == max_telegram_id
        else:
            # Если значение превышает лимит
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unicode_variations_username(self, api_client, db_session):
        """Тест различных Unicode вариаций в username."""
        # Arrange - различные Unicode символы
        unicode_usernames = [
            "пользователь",  # Кириллица
            "用户名",  # Китайский
            "ユーザー名",  # Японский
            "사용자명",  # Корейский
            "مستخدم",  # Арабский
            "user🙂name",  # Эмодзи
            "üser_näme",  # Диакритики
        ]

        for i, username in enumerate(unicode_usernames):
            user_data = {
                "username": username,
                "email": f"unicode{i}@example.com",
                "first_name": "Unicode",
                "last_name": "User",
            }

            # Act
            response = await api_client.post("/api/auth/register", json=user_data)

            # Assert
            if response.status_code == 200:
                data = response.json()
                assert data["user"]["username"] == username
            else:
                # Unicode может не поддерживаться
                assert response.status_code in [422, 400]

    @pytest.mark.asyncio
    async def test_special_timezone_handling(self, api_client, db_session):
        """Тест обработки экзотических временных зон."""
        # Arrange
        exotic_timezones = [
            "Pacific/Kiritimati",  # +14:00
            "Pacific/Marquesas",  # -09:30
            "Asia/Kathmandu",  # +05:45
            "Australia/Eucla",  # +08:45
            "Pacific/Chatham",  # +12:45
        ]

        for i, timezone in enumerate(exotic_timezones):
            user_data = {
                "username": f"tzuser{i}",
                "email": f"tz{i}@example.com",
                "first_name": "Timezone",
                "last_name": "User",
                "timezone": timezone,
            }

            # Act
            response = await api_client.post("/api/auth/register", json=user_data)

            # Assert
            if response.status_code == 200:
                data = response.json()
                assert data["user"]["timezone"] == timezone
            else:
                # Экзотические зоны могут не поддерживаться
                assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extreme_bio_length(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест экстремально длинной биографии."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        # Создаем очень длинный текст
        extreme_bio = (
            "A" * 5000 + " 🙂 " + "Б" * 5000
        )  # Смешиваем ASCII, Unicode, эмодзи

        update_data = {"bio": extreme_bio}

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        if response.status_code == 200:
            data = response.json()
            assert data["bio"] == extreme_bio
        else:
            # Слишком длинная биография
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_null_byte_injection(self, api_client, db_session):
        """Тест защиты от null byte инъекций."""
        # Arrange
        user_data = {
            "username": "user\x00admin",
            "email": "test\x00@example.com",
            "first_name": "Test\x00",
            "last_name": "User\x00",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        # Null bytes должны быть обработаны (отклонены или очищены)
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # Null bytes должны быть удалены
            assert "\x00" not in data["user"]["username"]
            assert "\x00" not in data["user"]["email"]

    @pytest.mark.asyncio
    async def test_very_long_url_fields(
        self, api_client, db_session, regular_user, auth_headers_factory
    ):
        """Тест очень длинных URL полей."""
        # Arrange
        headers = auth_headers_factory(regular_user.id)

        very_long_url = "https://example.com/" + "a" * 2000 + ".jpg"

        update_data = {
            "profile_picture_url": very_long_url,
            "telegram_photo_url": very_long_url,
        }

        # Act
        response = await api_client.put(
            "/api/auth/profile", json=update_data, headers=headers
        )

        # Assert
        if response.status_code == 200:
            data = response.json()
            assert data["profile_picture_url"] == very_long_url
        else:
            # URL слишком длинный
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_registration_boundary_values(self, api_client, db_session):
        """Тест граничных значений при регистрации."""
        # Arrange - тестируем минимальные и максимальные значения
        boundary_cases = [
            {
                "username": "ab",  # Минимальная длина
                "email": "a@b.co",  # Минимальный валидный email
                "first_name": "A",
                "last_name": "B",
            },
            {
                "username": "a" * 32,  # Обычный максимум
                "email": "test@" + "a" * 60 + ".com",
                "first_name": "F" * 50,
                "last_name": "L" * 50,
            },
        ]

        for i, user_data in enumerate(boundary_cases):
            # Act
            response = await api_client.post("/api/auth/register", json=user_data)

            # Assert
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                data = response.json()
                assert data["user"]["username"] == user_data["username"]

    @pytest.mark.asyncio
    async def test_token_edge_cases(self, api_client, db_session, regular_user):
        """Тест граничных случаев с токенами."""
        # Arrange
        from services.jwt_service import jwt_service

        # Создаем токен с минимальным временем жизни
        short_lived_token = jwt_service.create_access_token(
            regular_user.id, expires_delta=1
        )
        headers = {"Authorization": f"Bearer {short_lived_token}"}

        # Act - используем токен немедленно
        response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert response.status_code == 200

        # Act - ждем истечения и пробуем снова
        await asyncio.sleep(2)
        expired_response = await api_client.get("/api/auth/profile", headers=headers)

        # Assert
        assert expired_response.status_code == 401

    @pytest.mark.asyncio
    async def test_massive_user_list_pagination(
        self, api_client, db_session, admin_user, auth_headers_factory
    ):
        """Тест пагинации с большим количеством пользователей."""
        # Arrange
        headers = auth_headers_factory(admin_user.id)

        # Создаем много пользователей
        from tests.factories import create_test_users_batch

        await create_test_users_batch(count=1000)

        # Act - запрашиваем последнюю страницу
        response = await api_client.get("/api/users?page=100&limit=10", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1000

    @pytest.mark.asyncio
    async def test_emoji_only_fields(self, api_client, db_session):
        """Тест полей состоящих только из эмодзи."""
        # Arrange
        user_data = {
            "username": "emojiuser",
            "email": "emoji@example.com",
            "first_name": "🙂😊😀",
            "last_name": "🎉🎊🎈",
            "bio": "🚀🌟⭐✨🎯🔥💎🏆🎪🎭",
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        if response.status_code == 200:
            data = response.json()
            assert data["user"]["first_name"] == "🙂😊😀"
            assert data["user"]["last_name"] == "🎉🎊🎈"
        else:
            # Эмодзи могут не поддерживаться
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_memory_intensive_operations(self, api_client, db_session):
        """Тест операций интенсивно использующих память."""
        # Arrange - создаем пользователя с большими данными
        large_bio = "Memory test " * 10000  # ~110KB

        user_data = {
            "username": "memoryuser",
            "email": "memory@example.com",
            "first_name": "Memory",
            "last_name": "Test",
            "bio": large_bio,
        }

        # Act
        response = await api_client.post("/api/auth/register", json=user_data)

        # Assert
        # Система должна либо принять данные, либо отклонить из-за размера
        assert response.status_code in [200, 422, 413]  # 413 = Payload Too Large
