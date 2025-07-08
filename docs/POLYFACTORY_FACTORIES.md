# 🏭 Polyfactory Factories - Современная система тестовых данных

Полное руководство по новой архитектуре фабрик на базе [Polyfactory](https://github.com/litestar-org/polyfactory) для Quiz App.

## 🎯 Философия и принципы

### Принципы KISS и DRY

- **Keep It Simple, Stupid**: Простота использования превыше всего
- **Don't Repeat Yourself**: Избегаем дублирования кода
- **Lazy Evaluation**: Ленивые атрибуты для избежания коллизий
- **Type Safety**: Полная типизация с Pydantic

### Архитектурные принципы

```python
# ❌ Плохо: Хардкод и дублирование
user = User(
    id=1,  # Может конфликтовать!
    username="testuser",  # Не уникальный!
    email="test@test.com"  # Может дублироваться!
)

# ✅ Хорошо: Polyfactory с LazyAttribute
user = UserModelFactory.build()
# Автоматически: уникальные ID, username, email
```

## 🗂️ Структура фабрик

```
tests/factories/
├── __init__.py                 # Главный экспорт
├── conftest.py                 # Только инфраструктура
├── users/                      # Домен пользователей
│   ├── __init__.py
│   ├── model_factories.py      # SQLAlchemy модели
│   ├── pydantic_factories.py   # API схемы
│   └── fixtures.py            # Готовые фикстуры
├── surveys/                    # Домен опросов
│   ├── __init__.py
│   ├── model_factories.py
│   ├── pydantic_factories.py
│   └── fixtures.py
└── responses/                  # Домен ответов
    ├── __init__.py
    ├── model_factories.py
    ├── pydantic_factories.py
    └── fixtures.py
```

## 👥 Фабрики пользователей

### Model Factories (SQLAlchemy)

```python
from tests.factories.users import (
    UserModelFactory,
    AdminUserModelFactory,
    TelegramUserModelFactory,
    InactiveUserModelFactory
)

# Создание пользователей
user = UserModelFactory.build()
admin = AdminUserModelFactory.build()
telegram_user = TelegramUserModelFactory.build(telegram_id=123456)

# Пакетное создание
users = UserModelFactory.build_batch(5)
```

### Pydantic Factories (API данные)

```python
from tests.factories.users import (
    UserCreateDataFactory,
    UserUpdateDataFactory,
    UserLoginDataFactory,
    ValidUserCreateDataFactory
)

# Данные для API запросов
create_data = UserCreateDataFactory.build()
login_data = UserLoginDataFactory.build(username="specific_user")
valid_data = ValidUserCreateDataFactory.build()  # Гарантированно валидные
```

### Готовые фикстуры

```python
# В тестах используйте готовые фикстуры
def test_user_creation(regular_user: User):
    assert regular_user.is_active

def test_admin_permissions(admin_user: User):
    assert admin_user.is_admin

def test_telegram_integration(telegram_user: User):
    assert telegram_user.telegram_id is not None
```

## 📊 Фабрики опросов

### Создание опросов с вопросами

```python
from tests.factories.surveys import (
    create_survey_for_test,
    create_survey_with_questions,
    create_complete_survey_scenario
)

# Простой опрос
survey = await create_survey_for_test(session, creator_user)

# Опрос с вопросами
survey, questions = await create_survey_with_questions(
    session=session,
    creator=creator_user,
    question_count=3,
    question_types=["TEXT", "SINGLE_CHOICE", "SCALE"]
)

# Полный сценарий с ответами
scenario = await create_complete_survey_scenario(
    session=session,
    creator=creator_user,
    respondents=[user1, user2, user3],
    survey_type="public"
)
```

### Различные типы опросов

```python
from tests.factories.surveys import (
    PublicSurveyModelFactory,
    PrivateSurveyModelFactory,
    ActiveSurveyModelFactory
)

# Публичный опрос
public_survey = PublicSurveyModelFactory.build(
    created_by=user.id,
    title="Public Survey"
)

# Приватный опрос
private_survey = PrivateSurveyModelFactory.build(
    created_by=admin.id,
    is_public=False
)

# Активный опрос (с датами в будущем)
active_survey = ActiveSurveyModelFactory.build(created_by=user.id)
```

## 🔧 Утилиты для тестирования

### Контекстные менеджеры

```python
from tests.factories.users.fixtures import UserTestContext
from tests.factories.surveys.fixtures import SurveyTestContext

# Автоматическая очистка после теста
async with UserTestContext(session) as ctx:
    user = ctx.user
    auth_headers = ctx.auth_headers

    # Работа с пользователем
    response = await api_client.get("/profile", headers=auth_headers)

# Пользователь автоматически удален

# Сложные сценарии
async with SurveyTestContext(session, creator) as ctx:
    survey = ctx.survey

    # Добавляем вопросы
    question1 = await ctx.add_question(TextQuestionModelFactory)
    question2 = await ctx.add_question(ChoiceQuestionModelFactory)

    # Добавляем ответы
    response1 = await ctx.add_response(question1, user)

# Все объекты автоматически очищены
```

### Сценарии тестирования

```python
from tests.factories.surveys.fixtures import create_survey_test_scenario

# Готовые сценарии
basic_scenario = await create_survey_test_scenario(
    session, "basic_survey", creator
)

complex_scenario = await create_survey_test_scenario(
    session, "complex_survey", creator, respondents
)

# Доступны сценарии:
# - "basic_survey": простой опрос с текстовым вопросом
# - "public_survey_with_responses": публичный опрос с ответами
# - "complex_survey": сложный опрос с разными типами вопросов
# - "private_survey": приватный опрос
```

## 🎨 Кастомизация фабрик

### LazyAttribute для уникальности

```python
from polyfactory.fields import Use, PostGenerated
import uuid

class MyCustomFactory(BaseFactory[MyModel]):
    # Простое значение
    name = Use(lambda: f"user_{uuid.uuid4().hex[:8]}")

    # Зависимые значения
    @classmethod
    def updated_at(cls) -> PostGenerated[datetime]:
        def generate_updated_at(name: str, values: Dict[str, Any]) -> datetime:
            created = values.get('created_at', datetime.utcnow())
            return created + timedelta(minutes=fake.random_int(min=1, max=60))

        return PostGenerated(generate_updated_at)
```

### Вероятностные распределения

```python
class RealisticUserFactory(UserModelFactory):
    # 85% пользователей активны
    is_active = Use(lambda: fake.boolean(chance_of_getting_true=85))

    # 60% пользователей верифицированы
    is_verified = Use(lambda: fake.boolean(chance_of_getting_true=60))

    # 5% пользователей являются админами
    is_admin = Use(lambda: fake.boolean(chance_of_getting_true=5))
```

## 📁 Файловая база данных для анализа

### Настройка

```bash
# Использовать файловую БД (по умолчанию)
export TEST_USE_FILE_DB=true

# Использовать in-memory БД
export TEST_USE_FILE_DB=false
```

### Анализ данных тестов

```bash
# Файлы БД сохраняются в tests/data/
ls tests/data/quiz_test_*.db

# Анализ последней БД
sqlite3 tests/data/quiz_test_$(ls tests/data/ | grep quiz_test | sort -n | tail -1)

# SQL запросы для анализа
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;
SELECT * FROM surveys WHERE is_public = 1;
SELECT question_type, COUNT(*) FROM questions GROUP BY question_type;
```

### Автоматическая очистка

```python
# Система автоматически сохраняет только последние 5 БД
# Старые файлы удаляются при запуске новых тестов
```

## 🔍 Примеры использования

### Тест регистрации пользователя

```python
import pytest
from tests.factories.users import (
    ValidUserCreateDataFactory,
    create_user_with_auth
)

@pytest.mark.asyncio
async def test_user_registration(api_client, async_session):
    # Создаем валидные данные для регистрации
    registration_data = ValidUserCreateDataFactory.build()

    # Отправляем запрос
    response = await api_client.post("/auth/register", json=registration_data.dict())

    # Проверяем результат
    assert response.status_code == 201
    assert "id" in response.json()

@pytest.mark.asyncio
async def test_user_profile_update(api_client, async_session):
    # Создаем пользователя с авторизацией
    user, auth_headers = await create_user_with_auth(async_session, "regular")

    # Создаем данные для обновления
    update_data = UserUpdateDataFactory.build()

    # Обновляем профиль
    response = await api_client.put(
        f"/users/{user.id}/profile",
        json=update_data.dict(exclude_unset=True),
        headers=auth_headers
    )

    assert response.status_code == 200
```

### Тест создания опроса

```python
import pytest
from tests.factories.surveys import (
    PublicSurveyCreateDataFactory,
    create_survey_with_questions
)

@pytest.mark.asyncio
async def test_survey_creation(api_client, async_session, admin_user, admin_auth_headers):
    # Создаем данные для публичного опроса
    survey_data = PublicSurveyCreateDataFactory.build()

    # Создаем опрос
    response = await api_client.post(
        "/surveys",
        json=survey_data.dict(),
        headers=admin_auth_headers
    )

    assert response.status_code == 201
    assert response.json()["is_public"] == True

@pytest.mark.asyncio
async def test_survey_responses(api_client, async_session, regular_user):
    # Создаем опрос с вопросами
    survey, questions = await create_survey_with_questions(
        session=async_session,
        creator=regular_user,
        question_count=2,
        question_types=["TEXT", "SINGLE_CHOICE"]
    )

    # Создаем ответы на каждый вопрос
    for question in questions:
        if question.question_type == "TEXT":
            answer_data = {"text": "My test answer"}
        else:
            answer_data = {"selected_options": [0]}

        response = await api_client.post(
            f"/responses",
            json={
                "question_id": question.id,
                "answer": answer_data
            }
        )
        assert response.status_code == 201
```

### Интеграционный тест

```python
import pytest
from tests.factories.surveys import create_complete_survey_scenario

@pytest.mark.asyncio
async def test_complete_survey_flow(api_client, async_session, multiple_users):
    creator = multiple_users[0]
    respondents = multiple_users[1:4]

    # Создаем полный сценарий
    scenario = await create_complete_survey_scenario(
        session=async_session,
        creator=creator,
        respondents=respondents,
        survey_type="public"
    )

    survey = scenario["survey"]
    questions = scenario["questions"]
    responses = scenario["responses"]

    # Проверяем, что все создалось корректно
    assert survey.is_public == True
    assert len(questions) == 3
    assert len(responses) == len(questions) * len(respondents)

    # Проверяем через API
    survey_response = await api_client.get(f"/surveys/{survey.id}")
    assert survey_response.status_code == 200

    # Проверяем статистику
    stats_response = await api_client.get(f"/surveys/{survey.id}/stats")
    assert stats_response.json()["response_count"] == len(responses)
```

## 🚀 Команды для разработки

### Makefile команды

```bash
# Установка Polyfactory
make install-polyfactory

# Запуск тестов с файловой БД
make test-with-file-db

# Запуск тестов с in-memory БД
make test-fast

# Анализ последней БД
make analyze-test-db

# Очистка тестовых БД
make clean-test-dbs
```

### Переменные окружения

```bash
# Файловая БД для анализа (по умолчанию)
export TEST_USE_FILE_DB=true

# Уровень логирования тестов
export TEST_LOG_LEVEL=INFO

# Количество сохраняемых БД файлов
export TEST_DB_KEEP_COUNT=5
```

## 🎯 Best Practices

### 1. Избегайте хардкода

```python
# ❌ Плохо
user = User(id=1, username="testuser", email="test@test.com")

# ✅ Хорошо
user = UserModelFactory.build()
user_with_specific_email = UserModelFactory.build(email="specific@test.com")
```

### 2. Используйте правильные фабрики для сценариев

```python
# ❌ Плохо: универсальная фабрика для всех случаев
user = UserModelFactory.build(is_admin=True, telegram_id=123)

# ✅ Хорошо: специализированные фабрики
admin = AdminUserModelFactory.build()
telegram_user = TelegramUserModelFactory.build()
```

### 3. Группируйте связанные данные

```python
# ✅ Хорошо: создавайте связанные объекты вместе
survey, questions = await create_survey_with_questions(
    session, creator, question_count=3
)

# ✅ Еще лучше: используйте готовые сценарии
scenario = await create_complete_survey_scenario(
    session, creator, respondents, "public"
)
```

### 4. Очистка данных

```python
# ✅ Используйте контекстные менеджеры для автоочистки
async with UserTestContext(session) as ctx:
    # Все объекты автоматически удалятся
    pass

# ✅ Или явную очистку в teardown
@pytest.fixture
async def clean_user(async_session):
    user = await create_user_for_test(async_session, commit=True)
    yield user
    await async_session.delete(user)
    await async_session.commit()
```

### 5. Производительность

```python
# ✅ Пакетное создание для больших наборов данных
users = UserModelFactory.build_batch(100)
for user_data in users:
    session.add(User(**user_data.__dict__))
await session.commit()

# ✅ Используйте commit=False для транзакционных тестов
user = await create_user_for_test(session, commit=False)
survey = await create_survey_for_test(session, user, commit=False)
await session.commit()  # Один коммит для всех объектов
```

## 🔧 Расширение системы

### Добавление новых доменов

1. Создайте структуру директорий:

```bash
mkdir tests/factories/new_domain
touch tests/factories/new_domain/{__init__.py,model_factories.py,pydantic_factories.py,fixtures.py}
```

2. Создайте фабрики по образцу существующих
3. Добавьте экспорты в `__init__.py`
4. Обновите документацию

### Кастомные фабрики

```python
from polyfactory.factories import BaseFactory
from polyfactory.fields import Use, PostGenerated

class MySpecialFactory(BaseFactory[MyModel]):
    __model__ = MyModel

    # Ваша логика генерации
    special_field = Use(lambda: generate_special_value())

    @classmethod
    def dependent_field(cls) -> PostGenerated[str]:
        def generate_dependent(name: str, values: Dict[str, Any]) -> str:
            # Логика зависимого поля
            return f"dependent_{values.get('id', 'unknown')}"

        return PostGenerated(generate_dependent)
```

## 📈 Мониторинг и отладка

### Логирование

```python
import logging

# Фабрики логируют создание объектов
logger = logging.getLogger("factories")
logger.info(f"Created user: {user.username}")
```

### Метрики

```python
# Анализ использования фабрик
SELECT factory_name, COUNT(*) as usage_count
FROM factory_usage_log
GROUP BY factory_name
ORDER BY usage_count DESC;
```

## 🎊 Заключение

Новая система фабрик с Polyfactory обеспечивает:

- **🎯 Простоту использования**: KISS принцип
- **🔒 Безопасность типов**: Полная типизация
- **⚡ Производительность**: Ленивые вычисления
- **🧪 Изоляцию тестов**: Уникальные данные
- **📊 Анализ**: Файловая БД для исследований
- **🔧 Расширяемость**: Легко добавлять новые домены

Система готова к enterprise использованию и масштабированию! 🚀
