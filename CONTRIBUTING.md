# Руководство по вкладу в Quiz App 🤝

Спасибо за интерес к развитию Quiz App! Мы ценим каждый вклад в проект и стремимся создать дружелюбное сообщество разработчиков.

## 🎯 Типы вкладов

Мы приветствуем различные типы вкладов:

- 🐛 **Сообщения об ошибках**: Нашли баг? Сообщите нам!
- 💡 **Предложения функций**: Есть идеи для улучшения?
- 🔧 **Исправления кода**: Pull requests с багфиксами
- ✨ **Новые функции**: Реализация новых возможностей
- 📚 **Документация**: Улучшения в документации
- 🧪 **Тесты**: Добавление или улучшение тестов
- 🎨 **UI/UX**: Улучшения интерфейса и пользовательского опыта

## 🚀 Начало работы

### 1. Настройка среды разработки

```bash
# Клонируйте репозиторий
git clone https://github.com/mesteriis/quiz-app.git
cd quiz-app

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
pip install -r tests/requirements.txt

# Настройте pre-commit hooks
pip install pre-commit
pre-commit install
```

### 2. Создание .env файла

```bash
cp env.example .env
# Отредактируйте .env с вашими настройками
```

### 3. Запуск приложения

```bash
# Миграции БД
alembic upgrade head

# Запуск сервера
uvicorn main:app --reload
```

## 📋 Процесс разработки

### 1. Создание Issue

Перед началом работы создайте или найдите существующий Issue:

- Используйте подходящий шаблон Issue
- Четко опишите проблему или предложение
- Добавьте соответствующие лейблы
- Дождитесь обратной связи от мейнтейнеров

### 2. Создание ветки

```bash
# Создайте feature branch
git checkout -b feature/short-description

# Или bugfix branch
git checkout -b fix/issue-number-description
```

### 3. Разработка

- Следуйте стандартам кодирования проекта
- Пишите чистый, читаемый код
- Добавляйте тесты для новой функциональности
- Обновляйте документацию при необходимости

### 4. Коммиты

Мы используем [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Формат коммитов
type(scope): description

# Примеры
feat(auth): add two-factor authentication
fix(api): resolve survey creation bug
docs(readme): update installation instructions
test(auth): add login endpoint tests
```

Типы коммитов:

- `feat`: новая функция
- `fix`: исправление бага
- `docs`: обновление документации
- `test`: добавление тестов
- `refactor`: рефакторинг кода
- `style`: изменения форматирования
- `perf`: улучшения производительности
- `chore`: обновление зависимостей, конфигурации

### 5. Тестирование

```bash
# Запустите все тесты
pytest

# С покрытием кода
pytest --cov=backend

# Конкретные тесты
pytest tests/unit/test_auth_router.py

# Линтинг
black .
flake8 .
mypy .
```

### 6. Pull Request

1. Убедитесь, что все тесты проходят
2. Обновите CHANGELOG.md
3. Создайте Pull Request с описанием изменений
4. Свяжите PR с соответствующим Issue
5. Дождитесь ревью и внесите необходимые изменения

## 📝 Стандарты кода

### Python код

```python
# Используйте type hints
def create_user(name: str, email: str) -> User:
    """Create a new user with given name and email."""
    pass

# Docstrings в Google стиле
def calculate_score(responses: List[Response]) -> int:
    """Calculate survey score based on responses.

    Args:
        responses: List of user responses

    Returns:
        Calculated score as integer

    Raises:
        ValueError: If responses list is empty
    """
    pass
```

### Структура файлов

```python
# Порядок импортов
import os
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from models.user import User
from services.auth import AuthService
```

### Тестирование

```python
# Именование тестов
def test_create_user_success():
    """Test successful user creation."""
    pass

def test_create_user_duplicate_email_raises_error():
    """Test that duplicate email raises validation error."""
    pass

# Используйте фикстуры
@pytest.fixture
def test_user():
    """Create test user."""
    return User(name="Test User", email="test@example.com")
```

## 🔍 Ревью кода

### Что мы проверяем

- **Функциональность**: Код работает как ожидалось
- **Тесты**: Адекватное покрытие тестами
- **Стиль**: Соответствие стандартам проекта
- **Производительность**: Оптимальность решения
- **Безопасность**: Отсутствие уязвимостей
- **Документация**: Актуальность документации

### Критерии приемки

- ✅ Все тесты проходят
- ✅ Покрытие кода не уменьшается
- ✅ Линтеры не выдают ошибок
- ✅ Код соответствует архитектуре проекта
- ✅ Документация обновлена
- ✅ CHANGELOG.md обновлен

## 🐛 Сообщения об ошибках

### Информация для включения

1. **Описание проблемы**: Что произошло?
2. **Ожидаемое поведение**: Что должно было произойти?
3. **Шаги воспроизведения**: Как воспроизвести проблему?
4. **Окружение**: ОС, версия Python, браузер
5. **Логи**: Соответствующие сообщения об ошибках
6. **Скриншоты**: При необходимости

### Шаблон бага

```markdown
## 🐛 Описание бага

Краткое описание проблемы

## 🔄 Шаги воспроизведения

1. Перейдите к '...'
2. Нажмите на '...'
3. Прокрутите вниз до '...'
4. Увидите ошибку

## ✅ Ожидаемое поведение

Что должно было произойти

## 📷 Скриншоты

Если применимо

## 🖥️ Окружение

- ОС: [например, Windows 10]
- Браузер: [например, Chrome 96]
- Версия: [например, 1.0.0]
```

## 💡 Предложения функций

### Шаблон предложения

```markdown
## 🎯 Суть предложения

Краткое описание функции

## 🔍 Обоснование

Почему эта функция нужна?

## 📋 Детальное описание

Подробное описание функции

## 🎨 Дополнительный контекст

Скриншоты, макеты, примеры
```

## 📊 Приоритеты

### Высокий приоритет

- 🔥 Критические баги
- 🔒 Проблемы безопасности
- 📈 Проблемы производительности

### Средний приоритет

- 🆕 Новые функции
- 🎨 Улучшения UI/UX
- 📚 Улучшения документации

### Низкий приоритет

- 🧹 Рефакторинг кода
- 🎯 Оптимизации
- 📝 Обновления README

## 🎉 Признание вклада

Мы признаем и ценим все вклады:

- 🏆 Участники упоминаются в CONTRIBUTORS.md
- 🎖️ Значительные вклады отмечаются в релизах
- 🌟 Активные участники получают роль мейнтейнера

## 📞 Связь с нами

- 💬 **GitHub Issues**: Для багов и предложений
- 📧 **Email**: dev@quizapp.com
- 🐦 **Twitter**: @QuizAppTeam
- 💬 **Discord**: quiz-app-community

## 📚 Дополнительные ресурсы

- [Архитектурное руководство](docs/architecture.md)
- [API документация](docs/api.md)
- [Руководство по тестированию](docs/testing.md)
- [Руководство по деплою](docs/deployment.md)

---

**Спасибо за ваш вклад в Quiz App! 🎉**
