"""
🎭 Демонстрационный тест новой системы фабрик с Polyfactory.

Этот файл показывает все возможности новой архитектуры:
- Создание пользователей и опросов
- Использование LazyAttribute для избежания коллизий
- Файловая база данных для анализа
- Контекстные менеджеры для автоматической очистки
- Pydantic фабрики для API данных
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.users import (
    UserModelFactory,
    AdminUserModelFactory,
    TelegramUserModelFactory,
    ValidUserCreateDataFactory,
    create_user_for_test,
    create_user_with_auth,
    UserTestContext,
)
from tests.factories.surveys import (
    SurveyModelFactory,
    PublicSurveyModelFactory,
    create_survey_for_test,
    create_survey_with_questions,
    create_complete_survey_scenario,
    SurveyTestContext,
    ValidSurveyCreateDataFactory,
)


@pytest.mark.asyncio
class TestPolyfactoryDemo:
    """Демонстрация возможностей Polyfactory фабрик."""

    async def test_user_factories_showcase(self, async_session: AsyncSession):
        """🎭 Демонстрация пользовательских фабрик."""

        # ✅ Создание разных типов пользователей
        regular_user = UserModelFactory.build()
        admin_user = AdminUserModelFactory.build()
        telegram_user = TelegramUserModelFactory.build()

        # Проверяем уникальность данных
        assert regular_user.username != admin_user.username
        assert regular_user.email != admin_user.email
        assert admin_user.is_admin is True
        assert telegram_user.telegram_id is not None

        # Пакетное создание
        users_batch = UserModelFactory.build_batch(5)
        assert len(users_batch) == 5

        # Все пользователи уникальны
        usernames = [user.username for user in users_batch]
        assert len(set(usernames)) == 5  # Все уникальные

    async def test_survey_factories_showcase(self, async_session: AsyncSession):
        """📊 Демонстрация фабрик опросов."""

        # Создаем пользователя-создателя
        creator = await create_user_for_test(async_session, AdminUserModelFactory)

        # Создаем разные типы опросов
        basic_survey = SurveyModelFactory.build(created_by=creator.id)
        public_survey = PublicSurveyModelFactory.build(created_by=creator.id)

        # Проверяем настройки
        assert public_survey.is_public is True
        assert public_survey.allow_anonymous is True
        assert basic_survey.title != public_survey.title  # Уникальные заголовки

    async def test_context_managers_showcase(self, async_session: AsyncSession):
        """🔧 Демонстрация контекстных менеджеров."""

        # Автоматическая очистка пользователя
        async with UserTestContext(async_session) as user_ctx:
            user = user_ctx.user
            auth_headers = user_ctx.auth_headers

            assert user.id is not None
            assert "Authorization" in auth_headers

            # Создаем опрос для этого пользователя
            async with SurveyTestContext(async_session, user) as survey_ctx:
                survey = survey_ctx.survey

                # Добавляем вопросы
                from tests.factories.surveys import (
                    TextQuestionModelFactory,
                    ChoiceQuestionModelFactory,
                )

                text_question = await survey_ctx.add_question(TextQuestionModelFactory)
                choice_question = await survey_ctx.add_question(
                    ChoiceQuestionModelFactory
                )

                assert text_question.question_type == "TEXT"
                assert choice_question.question_type in [
                    "SINGLE_CHOICE",
                    "MULTIPLE_CHOICE",
                ]

                # Добавляем ответы
                from tests.factories.surveys import TextResponseModelFactory

                response = await survey_ctx.add_response(text_question, user)

                assert response.question_id == text_question.id
                assert response.user_id == user.id

        # Все объекты автоматически удалены из БД

    async def test_complete_scenario_showcase(self, async_session: AsyncSession):
        """🎬 Демонстрация полного сценария."""

        # Создаем создателя опроса
        creator = await create_user_for_test(async_session, AdminUserModelFactory)

        # Создаем респондентов
        respondents = []
        for i in range(3):
            respondent = await create_user_for_test(
                async_session,
                UserModelFactory,
                username=f"respondent_{i}",
                commit=False,
            )
            respondents.append(respondent)

        await async_session.commit()

        # Создаем полный сценарий
        scenario = await create_complete_survey_scenario(
            session=async_session,
            creator=creator,
            respondents=respondents,
            survey_type="public",
        )

        survey = scenario["survey"]
        questions = scenario["questions"]
        responses = scenario["responses"]

        # Проверяем результат
        assert survey.is_public is True
        assert len(questions) == 3  # TEXT, SINGLE_CHOICE, SCALE
        assert len(responses) == len(questions) * len(respondents)  # 9 ответов

        # Проверяем типы вопросов
        question_types = [q.question_type for q in questions]
        assert "TEXT" in question_types
        assert "SINGLE_CHOICE" in question_types
        assert "SCALE" in question_types

    async def test_pydantic_factories_showcase(self):
        """🎯 Демонстрация Pydantic фабрик для API."""

        # Создаем данные для API запросов
        user_create_data = ValidUserCreateDataFactory.build()
        survey_create_data = ValidSurveyCreateDataFactory.build()

        # Проверяем структуру
        assert hasattr(user_create_data, "username")
        assert hasattr(user_create_data, "email")
        assert hasattr(user_create_data, "password")

        assert hasattr(survey_create_data, "title")
        assert hasattr(survey_create_data, "description")
        assert survey_create_data.is_public is True

        # Можем конвертировать в dict для API
        user_dict = user_create_data.model_dump()
        survey_dict = survey_create_data.model_dump()

        assert isinstance(user_dict, dict)
        assert isinstance(survey_dict, dict)

    async def test_lazy_attributes_uniqueness(self, async_session: AsyncSession):
        """⚡ Демонстрация LazyAttribute для уникальности."""

        # Создаем много пользователей
        users = []
        for i in range(10):
            user = await create_user_for_test(async_session, commit=False)
            users.append(user)

        await async_session.commit()

        # Проверяем уникальность всех полей
        usernames = [user.username for user in users]
        emails = [user.email for user in users]

        assert len(set(usernames)) == 10  # Все username уникальные
        assert len(set(emails)) == 10  # Все email уникальные

        # Проверяем UUID в именах пользователей
        for username in usernames:
            assert len(username.split("_")[-1]) >= 6  # UUID часть

    async def test_realistic_data_distributions(self, async_session: AsyncSession):
        """📊 Демонстрация реалистичных распределений."""

        # Создаем большую выборку пользователей
        users = []
        for i in range(100):
            user = UserModelFactory.build()
            users.append(user)

        # Проверяем распределения
        active_users = [u for u in users if u.is_active]
        admin_users = [u for u in users if u.is_admin]

        # 85% пользователей должны быть активными (±10%)
        active_percentage = len(active_users) / len(users) * 100
        assert 75 <= active_percentage <= 95

        # 5% пользователей должны быть админами (±5%)
        admin_percentage = len(admin_users) / len(users) * 100
        assert 0 <= admin_percentage <= 10

    async def test_performance_showcase(self, async_session: AsyncSession):
        """⚡ Демонстрация производительности."""

        import time

        # Создаем админа
        admin = await create_user_for_test(async_session, AdminUserModelFactory)

        # Тестируем производительность создания опросов
        start_time = time.time()

        surveys = []
        for i in range(50):
            survey = await create_survey_for_test(
                async_session,
                admin,
                SurveyModelFactory,
                commit=False,
                title=f"Performance Survey {i}",
            )
            surveys.append(survey)

        await async_session.commit()

        end_time = time.time()
        creation_time = end_time - start_time

        # Должно создать 50 опросов быстро
        assert creation_time < 5.0  # Менее 5 секунд
        assert len(surveys) == 50

        # Все опросы должны быть уникальными
        titles = [s.title for s in surveys]
        assert len(set(titles)) == 50


@pytest.mark.asyncio
async def test_file_database_demo(async_session: AsyncSession):
    """📁 Демонстрация работы с файловой БД для анализа."""

    # Этот тест создает данные, которые сохранятся в файл
    # Запустите с: TEST_USE_FILE_DB=true pytest tests/demo_polyfactory_test.py::test_file_database_demo -v

    # Создаем разнообразные данные для анализа
    admin = await create_user_for_test(async_session, AdminUserModelFactory)

    # Создаем опрос с вопросами и ответами
    survey, questions = await create_survey_with_questions(
        session=async_session,
        creator=admin,
        question_count=5,
        question_types=["TEXT", "SINGLE_CHOICE", "MULTIPLE_CHOICE", "SCALE", "BOOLEAN"],
    )

    # Создаем респондентов
    respondents = []
    for i in range(10):
        respondent = await create_user_for_test(
            async_session,
            UserModelFactory if i % 3 != 0 else TelegramUserModelFactory,
            commit=False,
        )
        respondents.append(respondent)

    await async_session.commit()

    # После выполнения этого теста, данные будут доступны для анализа в файле БД
    # Используйте: make analyze-test-db

    print(f"📊 Created survey: {survey.title}")
    print(f"❓ Questions: {len(questions)}")
    print(f"👥 Respondents: {len(respondents)}")
    print("🗄️ Data saved to file database for analysis!")


# Запустите этот тест для демонстрации:
# make test-with-file-db tests/demo_polyfactory_test.py -v
# make analyze-test-db
