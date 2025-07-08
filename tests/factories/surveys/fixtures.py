"""
Утилиты и фикстуры для создания опросов в тестах.

Этот модуль предоставляет удобные функции для создания:
- Опросов с различными настройками
- Вопросов разных типов
- Ответов пользователей
- Сложных сценариев тестирования
"""

import asyncio
from typing import Optional, Dict, Any, List, Union
from sqlalchemy.ext.asyncio import AsyncSession

import pytest
from polyfactory.pytest_plugin import register_fixture

from src.models.survey import Survey
from src.models.question import Question
from src.models.response import Response
from src.models.user import User

from .model_factories import (
    SurveyModelFactory,
    PublicSurveyModelFactory,
    PrivateSurveyModelFactory,
    ActiveSurveyModelFactory,
    QuestionModelFactory,
    TextQuestionModelFactory,
    ChoiceQuestionModelFactory,
    ResponseModelFactory,
    TextResponseModelFactory,
    ChoiceResponseModelFactory,
)
from .pydantic_factories import (
    SurveyCreateDataFactory,
    ValidSurveyCreateDataFactory,
    PublicSurveyCreateDataFactory,
    PrivateSurveyCreateDataFactory,
)


# ============================================================================
# УТИЛИТЫ ДЛЯ СОЗДАНИЯ ОПРОСОВ
# ============================================================================


async def create_survey_for_test(
    session: AsyncSession,
    creator: User,
    factory_class: type = SurveyModelFactory,
    commit: bool = True,
    **kwargs,
) -> Survey:
    """
    Создает опрос для тестирования.

    Args:
        session: Async сессия БД
        creator: Пользователь-создатель опроса
        factory_class: Класс фабрики для создания опроса
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры для фабрики

    Returns:
        Survey: Созданный опрос

    Example:
        ```python
        survey = await create_survey_for_test(session, user, title="Test Survey")
        public_survey = await create_survey_for_test(session, user, PublicSurveyModelFactory)
        ```
    """
    # Создаем опрос через фабрику
    survey_data = factory_class.build(created_by=creator.id, **kwargs)

    # Создаем Survey объект
    survey = Survey(**survey_data.__dict__)

    # Сохраняем в БД
    session.add(survey)
    if commit:
        await session.commit()
        await session.refresh(survey)
    else:
        await session.flush()
        await session.refresh(survey)

    return survey


async def create_question_for_test(
    session: AsyncSession,
    survey: Survey,
    factory_class: type = QuestionModelFactory,
    commit: bool = True,
    **kwargs,
) -> Question:
    """
    Создает вопрос для опроса.

    Args:
        session: Async сессия БД
        survey: Опрос для вопроса
        factory_class: Класс фабрики для создания вопроса
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры для фабрики

    Returns:
        Question: Созданный вопрос
    """
    # Создаем вопрос через фабрику
    question_data = factory_class.build(survey_id=survey.id, **kwargs)

    # Создаем Question объект
    question = Question(**question_data.__dict__)

    # Сохраняем в БД
    session.add(question)
    if commit:
        await session.commit()
        await session.refresh(question)
    else:
        await session.flush()
        await session.refresh(question)

    return question


async def create_response_for_test(
    session: AsyncSession,
    question: Question,
    user: Optional[User] = None,
    factory_class: type = ResponseModelFactory,
    commit: bool = True,
    **kwargs,
) -> Response:
    """
    Создает ответ на вопрос.

    Args:
        session: Async сессия БД
        question: Вопрос для ответа
        user: Пользователь (опционально, для анонимных ответов)
        factory_class: Класс фабрики для создания ответа
        commit: Коммитить изменения в БД
        **kwargs: Дополнительные параметры для фабрики

    Returns:
        Response: Созданный ответ
    """
    # Создаем ответ через фабрику
    response_kwargs = {"question_id": question.id, **kwargs}
    if user:
        response_kwargs["user_id"] = user.id

    response_data = factory_class.build(**response_kwargs)

    # Создаем Response объект
    response = Response(**response_data.__dict__)

    # Сохраняем в БД
    session.add(response)
    if commit:
        await session.commit()
        await session.refresh(response)
    else:
        await session.flush()
        await session.refresh(response)

    return response


async def create_survey_with_questions(
    session: AsyncSession,
    creator: User,
    question_count: int = 3,
    survey_factory: type = SurveyModelFactory,
    question_types: Optional[List[str]] = None,
    commit: bool = True,
    **survey_kwargs,
) -> tuple[Survey, List[Question]]:
    """
    Создает опрос с вопросами.

    Args:
        session: Async сессия БД
        creator: Пользователь-создатель
        question_count: Количество вопросов
        survey_factory: Фабрика для опроса
        question_types: Типы вопросов (если не указаны, генерируются случайно)
        commit: Коммитить изменения в БД
        **survey_kwargs: Дополнительные параметры для опроса

    Returns:
        tuple[Survey, List[Question]]: Опрос и список вопросов
    """
    # Создаем опрос
    survey = await create_survey_for_test(
        session, creator, survey_factory, commit=False, **survey_kwargs
    )

    # Создаем вопросы
    questions = []
    for i in range(question_count):
        question_kwargs = {"order": i + 1}

        # Выбираем тип вопроса
        if question_types and i < len(question_types):
            question_type = question_types[i]
            if question_type == "TEXT":
                factory_class = TextQuestionModelFactory
            elif question_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
                factory_class = ChoiceQuestionModelFactory
                question_kwargs["question_type"] = question_type
            else:
                factory_class = QuestionModelFactory
                question_kwargs["question_type"] = question_type
        else:
            factory_class = QuestionModelFactory

        question = await create_question_for_test(
            session, survey, factory_class, commit=False, **question_kwargs
        )
        questions.append(question)

    if commit:
        await session.commit()
        await session.refresh(survey)
        for question in questions:
            await session.refresh(question)

    return survey, questions


async def create_complete_survey_scenario(
    session: AsyncSession,
    creator: User,
    respondents: List[User],
    survey_type: str = "public",
    commit: bool = True,
) -> Dict[str, Any]:
    """
    Создает полный сценарий опроса с ответами.

    Args:
        session: Async сессия БД
        creator: Создатель опроса
        respondents: Список пользователей для ответов
        survey_type: Тип опроса ("public", "private", "active")
        commit: Коммитить изменения в БД

    Returns:
        Dict[str, Any]: Словарь с созданными объектами
    """
    # Выбираем фабрику опроса
    survey_factories = {
        "public": PublicSurveyModelFactory,
        "private": PrivateSurveyModelFactory,
        "active": ActiveSurveyModelFactory,
    }
    survey_factory = survey_factories.get(survey_type, SurveyModelFactory)

    # Создаем опрос с вопросами
    survey, questions = await create_survey_with_questions(
        session=session,
        creator=creator,
        question_count=3,
        survey_factory=survey_factory,
        question_types=["TEXT", "SINGLE_CHOICE", "SCALE"],
        commit=False,
    )

    # Создаем ответы от пользователей
    responses = []
    for respondent in respondents:
        for question in questions:
            # Выбираем фабрику ответа в зависимости от типа вопроса
            if question.question_type == "TEXT":
                response_factory = TextResponseModelFactory
            elif question.question_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
                response_factory = ChoiceResponseModelFactory
            else:
                response_factory = ResponseModelFactory

            response = await create_response_for_test(
                session=session,
                question=question,
                user=respondent,
                factory_class=response_factory,
                commit=False,
            )
            responses.append(response)

    if commit:
        await session.commit()
        await session.refresh(survey)
        for question in questions:
            await session.refresh(question)
        for response in responses:
            await session.refresh(response)

    return {
        "survey": survey,
        "questions": questions,
        "responses": responses,
        "creator": creator,
        "respondents": respondents,
    }


# ============================================================================
# ГОТОВЫЕ ФИКСТУРЫ ДЛЯ ТЕСТОВ
# ============================================================================


@pytest.fixture
async def basic_survey(async_session: AsyncSession, regular_user: User) -> Survey:
    """Фикстура для базового опроса."""
    return await create_survey_for_test(async_session, regular_user)


@pytest.fixture
async def public_survey(async_session: AsyncSession, regular_user: User) -> Survey:
    """Фикстура для публичного опроса."""
    return await create_survey_for_test(
        async_session, regular_user, PublicSurveyModelFactory
    )


@pytest.fixture
async def private_survey(async_session: AsyncSession, admin_user: User) -> Survey:
    """Фикстура для приватного опроса."""
    return await create_survey_for_test(
        async_session, admin_user, PrivateSurveyModelFactory
    )


@pytest.fixture
async def active_survey(async_session: AsyncSession, regular_user: User) -> Survey:
    """Фикстура для активного опроса."""
    return await create_survey_for_test(
        async_session, regular_user, ActiveSurveyModelFactory
    )


@pytest.fixture
async def survey_with_questions(
    async_session: AsyncSession, regular_user: User
) -> tuple[Survey, List[Question]]:
    """Фикстура для опроса с вопросами."""
    return await create_survey_with_questions(async_session, regular_user)


@pytest.fixture
async def text_question(async_session: AsyncSession, basic_survey: Survey) -> Question:
    """Фикстура для текстового вопроса."""
    return await create_question_for_test(
        async_session, basic_survey, TextQuestionModelFactory
    )


@pytest.fixture
async def choice_question(
    async_session: AsyncSession, basic_survey: Survey
) -> Question:
    """Фикстура для вопроса с выбором."""
    return await create_question_for_test(
        async_session, basic_survey, ChoiceQuestionModelFactory
    )


@pytest.fixture
async def question_response(
    async_session: AsyncSession, text_question: Question, regular_user: User
) -> Response:
    """Фикстура для ответа на вопрос."""
    return await create_response_for_test(
        async_session, text_question, regular_user, TextResponseModelFactory
    )


# ============================================================================
# ФИКСТУРЫ ДЛЯ PYDANTIC ДАННЫХ
# ============================================================================


@pytest.fixture
def survey_create_data():
    """Фикстура для данных создания опроса."""
    return SurveyCreateDataFactory.build()


@pytest.fixture
def valid_survey_create_data():
    """Фикстура для валидных данных создания опроса."""
    return ValidSurveyCreateDataFactory.build()


@pytest.fixture
def public_survey_create_data():
    """Фикстура для данных создания публичного опроса."""
    return PublicSurveyCreateDataFactory.build()


@pytest.fixture
def private_survey_create_data():
    """Фикстура для данных создания приватного опроса."""
    return PrivateSurveyCreateDataFactory.build()


@pytest.fixture
def question_create_data():
    """Фикстура для данных создания вопроса."""
    return {
        "title": "Test Question",
        "description": "This is a test question",
        "question_type": "TEXT",
        "is_required": True,
        "order": 1,
    }


@pytest.fixture
def text_question_create_data():
    """Фикстура для данных создания текстового вопроса."""
    return {
        "title": "Text Question",
        "description": "Enter your answer",
        "question_type": "TEXT",
        "is_required": True,
        "order": 1,
    }


@pytest.fixture
def response_create_data():
    """Фикстура для данных создания ответа."""
    return {"answer": {"text": "Test answer"}, "user_session_id": "test_session_123"}


# ============================================================================
# ПАКЕТНЫЕ ФИКСТУРЫ
# ============================================================================


@pytest.fixture
async def multiple_surveys(
    async_session: AsyncSession, regular_user: User, admin_user: User
) -> List[Survey]:
    """Фикстура для создания нескольких опросов."""
    surveys = []

    # Создаем опросы разных типов
    surveys.append(
        await create_survey_for_test(
            async_session, regular_user, PublicSurveyModelFactory, commit=False
        )
    )
    surveys.append(
        await create_survey_for_test(
            async_session, admin_user, PrivateSurveyModelFactory, commit=False
        )
    )
    surveys.append(
        await create_survey_for_test(
            async_session, regular_user, ActiveSurveyModelFactory, commit=False
        )
    )

    await async_session.commit()
    for survey in surveys:
        await async_session.refresh(survey)

    return surveys


@pytest.fixture
async def survey_scenario_complete(
    async_session: AsyncSession, regular_user: User, multiple_users: List[User]
) -> Dict[str, Any]:
    """Фикстура для полного сценария опроса."""
    return await create_complete_survey_scenario(
        session=async_session,
        creator=regular_user,
        respondents=multiple_users[:3],  # Берем первых 3 пользователей
        survey_type="public",
    )


# ============================================================================
# КОНТЕКСТНЫЕ МЕНЕДЖЕРЫ
# ============================================================================


class SurveyTestContext:
    """
    Контекстный менеджер для создания опросов в тестах.

    Автоматически создает опрос и очищает данные после теста.
    """

    def __init__(
        self,
        session: AsyncSession,
        creator: User,
        factory_class: type = SurveyModelFactory,
        **kwargs,
    ):
        self.session = session
        self.creator = creator
        self.factory_class = factory_class
        self.kwargs = kwargs
        self.survey: Optional[Survey] = None
        self.questions: List[Question] = []
        self.responses: List[Response] = []

    async def __aenter__(self) -> "SurveyTestContext":
        """Создает опрос при входе в контекст."""
        self.survey = await create_survey_for_test(
            self.session, self.creator, self.factory_class, **self.kwargs
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Очищает данные при выходе из контекста."""
        # Удаляем связанные объекты
        for response in self.responses:
            await self.session.delete(response)
        for question in self.questions:
            await self.session.delete(question)
        if self.survey:
            await self.session.delete(self.survey)

        await self.session.commit()

    async def add_question(
        self, factory_class: type = QuestionModelFactory, **kwargs
    ) -> Question:
        """Добавляет вопрос к опросу."""
        if not self.survey:
            raise ValueError("Survey not created yet")

        question = await create_question_for_test(
            self.session, self.survey, factory_class, **kwargs
        )
        self.questions.append(question)
        return question

    async def add_response(
        self,
        question: Question,
        user: Optional[User] = None,
        factory_class: type = ResponseModelFactory,
        **kwargs,
    ) -> Response:
        """Добавляет ответ к вопросу."""
        response = await create_response_for_test(
            self.session, question, user, factory_class, **kwargs
        )
        self.responses.append(response)
        return response


# ============================================================================
# ПОЛЕЗНЫЕ УТИЛИТЫ
# ============================================================================


def get_survey_factory_by_type(survey_type: str) -> type:
    """
    Получает фабрику по типу опроса.

    Args:
        survey_type: Тип опроса ("basic", "public", "private", "active")

    Returns:
        type: Класс фабрики
    """
    factories = {
        "basic": SurveyModelFactory,
        "public": PublicSurveyModelFactory,
        "private": PrivateSurveyModelFactory,
        "active": ActiveSurveyModelFactory,
    }

    return factories.get(survey_type, SurveyModelFactory)


def get_question_factory_by_type(question_type: str) -> type:
    """
    Получает фабрику по типу вопроса.

    Args:
        question_type: Тип вопроса ("text", "choice", "basic")

    Returns:
        type: Класс фабрики
    """
    factories = {
        "text": TextQuestionModelFactory,
        "choice": ChoiceQuestionModelFactory,
        "basic": QuestionModelFactory,
    }

    return factories.get(question_type, QuestionModelFactory)


async def create_survey_test_scenario(
    session: AsyncSession,
    scenario: str,
    creator: User,
    respondents: Optional[List[User]] = None,
) -> Dict[str, Any]:
    """
    Создает сценарий тестирования для опросов.

    Args:
        session: Async сессия БД
        scenario: Название сценария
        creator: Создатель опроса
        respondents: Список респондентов

    Returns:
        Dict[str, Any]: Данные сценария
    """
    scenarios = {
        "basic_survey": {
            "survey_type": "basic",
            "question_types": ["TEXT"],
            "response_count": 1,
        },
        "public_survey_with_responses": {
            "survey_type": "public",
            "question_types": ["TEXT", "SINGLE_CHOICE"],
            "response_count": 3,
        },
        "complex_survey": {
            "survey_type": "active",
            "question_types": ["TEXT", "SINGLE_CHOICE", "MULTIPLE_CHOICE", "SCALE"],
            "response_count": 5,
        },
        "private_survey": {
            "survey_type": "private",
            "question_types": ["TEXT", "BOOLEAN"],
            "response_count": 2,
        },
    }

    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario}")

    config = scenarios[scenario]

    # Создаем опрос с вопросами
    survey_factory = get_survey_factory_by_type(config["survey_type"])
    survey, questions = await create_survey_with_questions(
        session=session,
        creator=creator,
        question_count=len(config["question_types"]),
        survey_factory=survey_factory,
        question_types=config["question_types"],
        commit=False,
    )

    # Создаем ответы если есть респонденты
    responses = []
    if respondents:
        response_count = min(config["response_count"], len(respondents))
        for i in range(response_count):
            respondent = respondents[i]
            for question in questions:
                response = await create_response_for_test(
                    session, question, respondent, commit=False
                )
                responses.append(response)

    await session.commit()

    return {
        "survey": survey,
        "questions": questions,
        "responses": responses,
        "scenario": scenario,
        "config": config,
    }
