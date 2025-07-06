# Quiz App 🎯

Интерактивное приложение для создания и проведения опросов с интеграцией Telegram бота.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Возможности

- **🎯 Система опросов**: Создание, редактирование и управление опросами
- **🤖 Telegram интеграция**: Полнофункциональный Telegram бот
- **📊 Аналитика**: Подробная статистика и отчеты
- **🔐 Безопасность**: JWT аутентификация и авторизация
- **📱 PWA поддержка**: Прогрессивное веб-приложение
- **🔔 Push уведомления**: Веб-уведомления для пользователей
- **📈 Мониторинг**: Система мониторинга производительности
- **🎨 Современный UI**: Темная тема с фиолетово-золотыми акцентами

## 📋 Требования

- Python 3.11+
- SQLite/PostgreSQL
- Redis (для кэширования)
- Node.js (для frontend)

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/mesteriis/quiz-app.git
cd quiz-app
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка окружения

```bash
cp env.example .env
# Отредактируйте .env файл с вашими настройками
```

### 5. Миграции базы данных

```bash
alembic upgrade head
```

### 6. Запуск приложения

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Конфигурация

### Основные настройки (.env)

```env
# Приложение
APP_NAME=Quiz App
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# База данных
DATABASE_URL=sqlite+aiosqlite:///./quiz.db

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
TELEGRAM_ADMIN_CHAT_ID=your-admin-chat-id

# VAPID ключи для push уведомлений
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_EMAIL=noreply@quizapp.com
```

### Telegram Bot Setup

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Добавьте токен в `.env` файл
4. Настройте webhook (опционально)

## 📖 API Документация

После запуска приложения, API документация доступна по адресам:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты

```
GET    /                    - Главная страница
GET    /health              - Проверка здоровья приложения
POST   /api/auth/login      - Аутентификация
POST   /api/auth/register   - Регистрация
GET    /api/surveys         - Список опросов
POST   /api/surveys         - Создание опроса
GET    /api/responses       - Ответы на опросы
POST   /api/responses       - Отправка ответа
```

## 🏗️ Архитектура

```
backend/
├── main.py              # Главный файл приложения
├── config.py            # Конфигурация
├── database.py          # Настройки базы данных
├── models/              # Модели данных
│   ├── user.py
│   ├── survey.py
│   ├── question.py
│   └── response.py
├── routers/             # API маршруты
│   ├── auth.py
│   ├── surveys.py
│   ├── responses.py
│   └── telegram.py
├── services/            # Бизнес-логика
│   ├── jwt_service.py
│   ├── telegram_service.py
│   └── user_service.py
├── schemas/             # Pydantic схемы
├── middleware/          # Middleware
├── tests/               # Тесты
└── static/              # Статические файлы
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=backend

# E2E тесты
pytest tests/e2e/

# Конкретный тест
pytest tests/unit/test_auth_router.py
```

### Структура тестов

```
tests/
├── conftest.py          # Общие фикстуры
├── factories/           # Фабрики для тестовых данных
├── unit/               # Юнит тесты
├── e2e/                # E2E тесты
└── requirements.txt    # Зависимости для тестов
```

## 🚀 Развертывание

### Docker

```bash
docker build -t quiz-app .
docker run -p 8000:8000 quiz-app
```

### Docker Compose

```bash
docker-compose up -d
```

### Продакшн настройки

1. Установите переменную `ENVIRONMENT=production`
2. Используйте PostgreSQL вместо SQLite
3. Настройте Redis для кэширования
4. Настройте HTTPS
5. Используйте процесс-менеджер (PM2, Supervisor)

## 📊 Мониторинг

Приложение включает встроенную систему мониторинга:

- **Метрики**: `/api/monitoring/metrics`
- **Здоровье**: `/health`
- **Статистика**: `/api/monitoring/stats`

## 🔒 Безопасность

- JWT токены для аутентификации
- Хеширование паролей с bcrypt
- CORS защита
- Rate limiting
- IP whitelist для Telegram webhook
- Валидация данных с Pydantic

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md) для получения подробной информации.

1. Форкните репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте [Issues](https://github.com/mesteriis/quiz-app/issues)
2. Создайте новый Issue
3. Свяжитесь с командой: dev@quizapp.com

## 🔄 Changelog

Все изменения документируются в [CHANGELOG.md](CHANGELOG.md).

## 🎯 Roadmap

- [ ] Мобильное приложение
- [ ] Интеграция с Discord
- [ ] Расширенная аналитика
- [ ] Многоязычная поддержка
- [ ] Система плагинов
- [ ] AI-помощник для создания опросов

## 📚 Дополнительная документация

- [TODO.md](TODO.md) - Список задач
- [CONTRIBUTING.md](CONTRIBUTING.md) - Руководство по вкладу
- [SECURITY.md](SECURITY.md) - Политика безопасности
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Кодекс поведения

---

**Quiz App** - создан с ❤️ для сообщества
