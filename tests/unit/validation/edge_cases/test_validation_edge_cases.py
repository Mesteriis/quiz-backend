"""
Граничные тесты для Validation endpoints.

Тестирует экстремальные сценарии валидации:
- Максимальные и минимальные значения
- Unicode символы и эмодзи
- Редкие форматы и кодировки
- Экстремальные нагрузки
- Временные ограничения
- Память и производительность
"""

import pytest
from unittest.mock import AsyncMock, patch
import asyncio
import time


class TestEmailValidationEdgeCases:
    """Граничные тесты валидации email."""

    async def test_validate_email_unicode_domains(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email с Unicode доменами."""
        # Arrange
        unicode_emails = [
            "test@пример.рф",
            "user@münchen.de",
            "test@café.fr",
            "user@北京.cn",
            "test@москва.рф",
            "user@العربية.com",
            "test@हिन्दी.भारत",
            "user@ελληνικά.gr",
        ]

        # Act & Assert
        for email in unicode_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data
            assert isinstance(data["is_valid"], bool)

    async def test_validate_email_emoji_domains(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email с эмодзи в доменах."""
        # Arrange
        emoji_emails = [
            "test@😀.com",
            "user@🚀.space",
            "email@❤️.love",
            "test@🌍.world",
            "user@🎉.party",
        ]

        # Act & Assert
        for email in emoji_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_maximum_length_parts(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email с максимальной длиной частей."""
        # Arrange
        # Максимальная длина локальной части: 64 символа
        max_local = "a" * 64
        # Максимальная длина домена: 255 символов
        max_domain = "b" * 63 + ".com"  # 63 символа в поддомене

        test_emails = [
            f"{max_local}@example.com",
            f"test@{max_domain}",
            f"{'a' * 32}@{'b' * 32}.com",
        ]

        # Act & Assert
        for email in test_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_ip_addresses(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email с IP адресами."""
        # Arrange
        ip_emails = [
            "user@[192.168.1.1]",
            "test@[127.0.0.1]",
            "email@[255.255.255.255]",
            "user@[::1]",  # IPv6 localhost
            "test@[2001:db8::1]",  # IPv6
            "user@192.168.1.1",  # Без скобок
        ]

        # Act & Assert
        for email in ip_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_special_local_parts(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email со специальными локальными частями."""
        # Arrange
        special_local_emails = [
            '"test user"@example.com',  # Кавычки
            '"test@domain"@example.com',  # @ в кавычках
            '"test\\"user"@example.com',  # Экранированные кавычки
            '"test\\\\user"@example.com',  # Экранированный слэш
            '"test user+tag"@example.com',  # Пробел в кавычках
            "test\\ user@example.com",  # Экранированный пробел
            "test\\@user@example.com",  # Экранированный @
        ]

        # Act & Assert
        for email in special_local_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_deep_subdomain_nesting(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email с глубоким вложением поддоменов."""
        # Arrange
        deep_subdomain_emails = [
            "test@a.b.c.d.e.f.g.h.i.j.example.com",
            "user@level1.level2.level3.level4.level5.domain.com",
            "email@sub.sub.sub.sub.sub.sub.domain.org",
        ]

        # Act & Assert
        for email in deep_subdomain_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_rare_tlds(self, api_client, edge_case_email_factory):
        """Тест валидации email с редкими TLD."""
        # Arrange
        rare_tld_emails = [
            "test@example.museum",
            "user@example.travel",
            "email@example.aero",
            "test@example.coop",
            "user@example.info",
            "email@example.mobi",
            "test@example.tel",
            "user@example.xxx",
            "email@example.онлайн",  # Кириллический TLD
            "test@example.中国",  # Китайский TLD
        ]

        # Act & Assert
        for email in rare_tld_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data

    async def test_validate_email_performance_stress(
        self, api_client, edge_case_email_factory
    ):
        """Тест производительности валидации email под нагрузкой."""
        # Arrange
        stress_emails = [edge_case_email_factory.build().email for _ in range(100)]

        # Act
        start_time = time.time()
        responses = []

        for email in stress_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )
            responses.append(response)

        end_time = time.time()
        execution_time = end_time - start_time

        # Assert
        assert len(responses) == len(stress_emails)
        assert all(r.status_code == 200 for r in responses)
        # Проверяем, что выполнение не заняло слишком много времени
        assert execution_time < 30.0  # Максимум 30 секунд на 100 email

    async def test_validate_email_memory_intensive(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email с большими объемами данных."""
        # Arrange
        # Создаем email с очень длинными частями (но в пределах лимитов)
        long_local = "a" * 63 + "b"  # 64 символа
        long_domain = "c" * 60 + ".com"  # Длинный домен

        email_request = edge_case_email_factory.build()
        email_request.email = f"{long_local}@{long_domain}"

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email_request.email
        assert "is_valid" in data

    async def test_validate_email_concurrent_identical_requests(
        self, api_client, edge_case_email_factory
    ):
        """Тест параллельных одинаковых запросов валидации."""
        # Arrange
        email_request = edge_case_email_factory.build()

        # Act - создаем несколько одинаковых запросов
        tasks = []
        for _ in range(10):
            task = api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # Assert
        assert len(responses) == 10
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email_request.email

    async def test_validate_email_whitespace_edge_cases(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email с различными видами пробелов."""
        # Arrange
        whitespace_emails = [
            "test@example.com\t",  # Табуляция в конце
            "\ntest@example.com",  # Новая строка в начале
            "test@example.com\r",  # Возврат каретки в конце
            "test@example.com\n",  # Новая строка в конце
            "test@example.com\u00a0",  # Неразрывный пробел
            "test@example.com\u2000",  # En quad
            "test@example.com\u2001",  # Em quad
            "test@example.com\u2002",  # En space
            "test@example.com\u2003",  # Em space
            "test@example.com\u2004",  # Three-per-em space
            "test@example.com\u2005",  # Four-per-em space
            "test@example.com\u2006",  # Six-per-em space
            "test@example.com\u2007",  # Figure space
            "test@example.com\u2008",  # Punctuation space
            "test@example.com\u2009",  # Thin space
            "test@example.com\u200a",  # Hair space
            "test@example.com\u202f",  # Narrow no-break space
            "test@example.com\u205f",  # Medium mathematical space
            "test@example.com\u3000",  # Ideographic space
        ]

        # Act & Assert
        for email in whitespace_emails:
            email_request = edge_case_email_factory.build()
            email_request.email = email

            response = await api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["email"] == email
            assert "is_valid" in data


class TestPhoneValidationEdgeCases:
    """Граничные тесты валидации телефонов."""

    async def test_validate_phone_unicode_numbers(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов с Unicode цифрами."""
        # Arrange
        unicode_phones = [
            "＋１２３４５６７８９０",  # Полноширинные цифры
            "１２３４５６７８９０",  # Без плюса
            "₁₂₃₄₅₆₇₈₉₀",  # Подстрочные цифры
            "¹²³⁴⁵⁶⁷⁸⁹⁰",  # Надстрочные цифры
            "①②③④⑤⑥⑦⑧⑨⑩",  # Цифры в кружках
            "𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗𝟎",  # Математические цифры
        ]

        # Act & Assert
        for phone in unicode_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_emoji_separators(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов с эмодзи как разделителями."""
        # Arrange
        emoji_phones = [
            "+1😀234😀567😀8901",
            "8🚀916🚀123🚀45🚀67",
            "+7❤️916❤️123❤️45❤️67",
            "1🌍234🌍567🌍8901",
            "+44🎉20🎉7946🎉0958",
        ]

        # Act & Assert
        for phone in emoji_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_maximum_length_boundary(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов на границе максимальной длины."""
        # Arrange
        boundary_phones = [
            "+" + "1" * 15,  # Ровно 15 цифр (максимум)
            "+" + "1" * 14,  # 14 цифр
            "+" + "1" * 16,  # 16 цифр (превышение)
            "1" * 10,  # 10 цифр (минимум)
            "1" * 9,  # 9 цифр (меньше минимума)
        ]

        # Act & Assert
        for phone in boundary_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_extreme_formatting(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов с экстремальным форматированием."""
        # Arrange
        extreme_phones = [
            "+1-2-3-4-5-6-7-8-9-0",  # Дефис после каждой цифры
            "+1 2 3 4 5 6 7 8 9 0",  # Пробел после каждой цифры
            "+1.2.3.4.5.6.7.8.9.0",  # Точка после каждой цифры
            "+1(2)3(4)5(6)7(8)9(0)",  # Скобки вокруг каждой цифры
            "+1_2_3_4_5_6_7_8_9_0",  # Подчеркивание
            "+1/2/3/4/5/6/7/8/9/0",  # Слэш
            "+1\\2\\3\\4\\5\\6\\7\\8\\9\\0",  # Обратный слэш
            "+1|2|3|4|5|6|7|8|9|0",  # Вертикальная черта
        ]

        # Act & Assert
        for phone in extreme_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_multiple_plus_signs(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов с несколькими знаками +."""
        # Arrange
        multiple_plus_phones = [
            "++1234567890",
            "+++1234567890",
            "+1+234567890",
            "+12+34567890",
            "+123+4567890",
            "+1234567890+",
            "+1234567890++",
        ]

        # Act & Assert
        for phone in multiple_plus_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_mixed_scripts(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов со смешанными скриптами."""
        # Arrange
        mixed_script_phones = [
            "+1２３４５６７８９０",  # Латинские + японские цифры
            "８９１６１２３４５６７",  # Все японские цифры
            "+7９１６１２３４５６７",  # Смешанные цифры
            "+١٢٣٤٥٦٧٨٩٠",  # Арабские цифры
            "+७९१६१२३४५६७",  # Деванагари цифры
        ]

        # Act & Assert
        for phone in mixed_script_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_zero_padding(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов с нулевым заполнением."""
        # Arrange
        zero_padded_phones = [
            "00001234567890",
            "0000079161234567",
            "000012345678901",
            "+000012345678901",
            "001234567890",
            "007916123456",
        ]

        # Act & Assert
        for phone in zero_padded_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_special_country_codes(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов с особыми кодами стран."""
        # Arrange
        special_codes = [
            "+800123456789",  # Международный бесплатный
            "+808123456789",  # Международный общий доступ
            "+870123456789",  # Inmarsat
            "+878123456789",  # Персональная нумерация
            "+881123456789",  # Глобальная мобильная спутниковая связь
            "+882123456789",  # Международные сети
            "+883123456789",  # Международные сети
            "+888123456789",  # Телекоммуникационные услуги
            "+979123456789",  # Международная премиум-тарификация
        ]

        # Act & Assert
        for phone in special_codes:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_phone_performance_stress(
        self, api_client, edge_case_phone_factory
    ):
        """Тест производительности валидации телефонов под нагрузкой."""
        # Arrange
        stress_phones = [edge_case_phone_factory.build().phone for _ in range(100)]

        # Act
        start_time = time.time()
        responses = []

        for phone in stress_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )
            responses.append(response)

        end_time = time.time()
        execution_time = end_time - start_time

        # Assert
        assert len(responses) == len(stress_phones)
        assert all(r.status_code == 200 for r in responses)
        # Проверяем, что выполнение не заняло слишком много времени
        assert execution_time < 30.0  # Максимум 30 секунд на 100 телефонов

    async def test_validate_phone_memory_boundary(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефонов на границе памяти."""
        # Arrange
        # Создаем очень длинный телефон с форматированием
        long_phone = "+1" + "-".join(["23"] * 100)  # Очень длинный

        phone_request = edge_case_phone_factory.build()
        phone_request.phone = long_phone

        # Act
        response = await api_client.post(
            api_client.url_for("validate_phone_endpoint"),
            json=phone_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == long_phone
        assert "is_valid" in data
        # Ожидаем, что такой длинный номер будет невалидным
        assert data["is_valid"] is False


class TestBatchValidationEdgeCases:
    """Граничные тесты пакетной валидации."""

    async def test_validate_emails_batch_maximum_size(self, api_client):
        """Тест пакетной валидации с максимальным размером."""
        # Arrange - ровно 100 email (максимум)
        emails = [f"user{i}@example.com" for i in range(100)]

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 100
        assert len(data["results"]) == 100

    async def test_validate_emails_batch_unicode_mix(self, api_client):
        """Тест пакетной валидации со смешанными Unicode email."""
        # Arrange
        unicode_emails = [
            "test@example.com",
            "тест@пример.рф",
            "テスト@例.jp",
            "test@café.fr",
            "用户@例子.cn",
            "משתמש@דוגמה.com",
            "χρήστης@παράδειγμα.gr",
            "usuário@exemplo.com",
            "пользователь@пример.рф",
            "사용자@예시.kr",
        ]

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": unicode_emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == len(unicode_emails)
        assert len(data["results"]) == len(unicode_emails)

    async def test_validate_emails_batch_performance_timing(self, api_client):
        """Тест временных характеристик пакетной валидации."""
        # Arrange
        emails = [f"user{i}@example{i}.com" for i in range(50)]

        # Act
        start_time = time.time()

        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == len(emails)
        # Проверяем, что пакетная валидация эффективнее одиночной
        assert execution_time < 10.0  # Максимум 10 секунд на 50 email

    async def test_validate_emails_batch_memory_intensive(self, api_client):
        """Тест пакетной валидации с большими email адресами."""
        # Arrange
        large_emails = []
        for i in range(20):
            local_part = "a" * 60  # Длинная локальная часть
            domain_part = f"b{i}" * 30 + ".com"  # Длинный домен
            large_emails.append(f"{local_part}@{domain_part}")

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": large_emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == len(large_emails)
        assert len(data["results"]) == len(large_emails)


class TestValidationConcurrencyEdgeCases:
    """Граничные тесты параллельной валидации."""

    async def test_validate_concurrent_different_emails(
        self, api_client, edge_case_email_factory
    ):
        """Тест параллельной валидации разных email."""
        # Arrange
        email_requests = [edge_case_email_factory.build() for _ in range(20)]

        # Act
        tasks = []
        for email_request in email_requests:
            task = api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # Assert
        assert len(responses) == 20
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email_requests[i].email

    async def test_validate_concurrent_mixed_endpoints(
        self, api_client, edge_case_email_factory, edge_case_phone_factory
    ):
        """Тест параллельного использования разных validation endpoints."""
        # Arrange
        email_request = edge_case_email_factory.build()
        phone_request = edge_case_phone_factory.build()

        # Act
        tasks = [
            api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            ),
            api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            ),
            api_client.get(api_client.url_for("validation_health_check")),
        ]

        responses = await asyncio.gather(*tasks)

        # Assert
        assert len(responses) == 3
        for response in responses:
            assert response.status_code == 200

    async def test_validate_race_condition_simulation(
        self, api_client, edge_case_email_factory
    ):
        """Тест симуляции состояния гонки при валидации."""
        # Arrange
        email_request = edge_case_email_factory.build()

        # Act - множественные одновременные запросы одного и того же
        tasks = []
        for _ in range(50):
            task = api_client.post(
                api_client.url_for("validate_email_endpoint"),
                json=email_request.model_dump(),
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # Assert
        assert len(responses) == 50
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email_request.email
            # Все ответы должны быть идентичными
            assert data["is_valid"] == responses[0].json()["is_valid"]


class TestValidationLimitsAndBoundaries:
    """Тесты лимитов и границ валидации."""

    async def test_validate_email_at_character_limit(
        self, api_client, edge_case_email_factory
    ):
        """Тест валидации email на границе лимита символов."""
        # Arrange - максимальная общая длина email 254 символа
        local_part = "a" * 64  # Максимум для локальной части
        domain_part = "b" * 63 + ".com"  # Длинный домен
        total_length = len(local_part) + 1 + len(domain_part)  # +1 для @

        if total_length <= 254:
            email = f"{local_part}@{domain_part}"
        else:
            # Подгоняем под лимит
            domain_part = "b" * (254 - 64 - 1 - 4) + ".com"
            email = f"{local_part}@{domain_part}"

        email_request = edge_case_email_factory.build()
        email_request.email = email

        # Act
        response = await api_client.post(
            api_client.url_for("validate_email_endpoint"),
            json=email_request.model_dump(),
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email
        assert "is_valid" in data

    async def test_validate_phone_at_digit_limit(
        self, api_client, edge_case_phone_factory
    ):
        """Тест валидации телефона на границе лимита цифр."""
        # Arrange
        boundary_phones = [
            "+" + "1" * 15,  # Максимум 15 цифр
            "+" + "1" * 14,  # 14 цифр
            "1" * 10,  # Минимум 10 цифр
            "1" * 11,  # 11 цифр
        ]

        # Act & Assert
        for phone in boundary_phones:
            phone_request = edge_case_phone_factory.build()
            phone_request.phone = phone

            response = await api_client.post(
                api_client.url_for("validate_phone_endpoint"),
                json=phone_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()

            assert data["phone"] == phone
            assert "is_valid" in data

    async def test_validate_domain_at_length_limit(self, api_client):
        """Тест валидации домена на границе лимита длины."""
        # Arrange - максимальная длина домена 255 символов
        long_domain = (
            "a" * 63 + "." + "b" * 63 + "." + "c" * 63 + "." + "d" * 60 + ".com"
        )

        # Act
        response = await api_client.get(
            api_client.url_for("check_domain_mx_records", domain=long_domain)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["domain"] == long_domain
        assert "mx_valid" in data

    async def test_validate_batch_at_size_limit(self, api_client):
        """Тест пакетной валидации на границе лимита размера."""
        # Arrange - ровно 100 email
        emails = [f"user{i}@example.com" for i in range(100)]

        # Act
        response = await api_client.post(
            api_client.url_for("validate_emails_batch"),
            json={
                "emails": emails,
                "check_mx": False,
                "check_smtp": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 100
        assert len(data["results"]) == 100
