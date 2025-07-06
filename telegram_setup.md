# 🤖 Telegram Bot Setup - aiogram

> **Современная асинхронная интеграция с Telegram ботом на базе aiogram**

## 📋 Содержание

1. [Обзор](#обзор)
2. [Настройка](#настройка)
3. [Разработка](#разработка)
4. [Продакшен](#продакшен)
5. [Команды](#команды)
6. [Архитектура](#архитектура)
7. [Troubleshooting](#troubleshooting)

## 🔥 Обзор

Quiz App теперь интегрируется с Telegram через **aiogram v3** - самую современную асинхронную библиотеку для создания Telegram ботов на Python.

### ✨ Преимущества aiogram:

- **🚀 Полная асинхронность** - идеально подходит для FastAPI
- **📝 Богатая типизация** - автокомплит и проверки типов
- **🔄 FSM (Finite State Machine)** - для сложных диалогов
- **🎯 Фильтры** - мощная система фильтрации сообщений
- **🌐 Webhook & Polling** - поддержка обоих режимов
- **🛠️ Middleware** - гибкая система обработки

### 🤖 Функциональность бота:

- **Регистрация пользователей** через Telegram
- **Список опросов** с навигацией
- **Прохождение опросов** в веб-приложении
- **Админ-панель** для администраторов
- **Уведомления** о новых опросах
- **Статистика** и отчеты

## ⚙️ Настройка

### 1. Создание бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду: `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: `Quiz App Bot`)
   - Введите username бота (например: `quizapp_bot`)
4. Получите токен бота

### 2. Настройка переменных окружения

Добавьте в `backend/.env`:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_ADMIN_CHAT_ID=123456789
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook/{token}
```

### 3. Получение Chat ID

Для получения вашего Chat ID:

1. Отправьте сообщение вашему боту
2. Выполните команду:
   ```bash
   curl "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getUpdates"
   ```
3. Найдите `chat.id` в ответе

## 🚀 Разработка

### Запуск в режиме Polling

```bash
# Быстрый старт
make telegram-polling

# Или напрямую
cd backend && python3 telegram_bot_polling.py
```

### Функции для разработки:

- **Автоматический restart** при изменении кода
- **Подробные логи** для отладки
- **Обработка ошибок** без остановки бота
- **Отключение webhook** автоматически

## 🌐 Продакшен

### Настройка Webhook

```bash
# Установка webhook
make telegram-webhook-set

# Проверка статуса
make telegram-info

# Удаление webhook
make telegram-webhook-delete
```

### Структура webhook URL:

```
https://your-domain.com/telegram/webhook/{BOT_TOKEN}
```

**Важно:** Токен в URL обеспечивает безопасность webhook'а.

## 🔧 Команды

### Makefile команды:

```bash
# Основные
make telegram-polling          # Запуск в режиме polling
make telegram-webhook-set      # Настройка webhook
make telegram-webhook-delete   # Удаление webhook
make telegram-info            # Информация о боте
make telegram-test            # Тестирование функций
make telegram-setup           # Пошаговая настройка

# Дополнительные
make telegram-status          # Статус бота
make telegram-health          # Проверка здоровья
```

### API Endpoints:

```bash
# Webhook управление
GET  /telegram/webhook/info     # Информация о webhook
POST /telegram/webhook/set      # Установка webhook
POST /telegram/webhook/delete   # Удаление webhook
POST /telegram/webhook/{token}  # Обработка обновлений

# Уведомления
POST /telegram/send-notification      # Отправка уведомления
POST /telegram/send-admin-notification # Уведомление админу

# Статус
GET  /telegram/status          # Статус бота
GET  /telegram/health          # Проверка здоровья
```

## 🏗️ Архитектура

### Структура проекта:

```
backend/
├── src/
│   ├── services/
│   │   └── telegram_service.py     # Основной сервис (aiogram)
│   ├── routers/
│   │   └── telegram.py            # FastAPI роутеры
│   ├── telegram_bot_polling.py    # Скрипт для polling
│   └── main.py                    # Интеграция с FastAPI
├── migrations/              # Миграции БД
└── tests/                  # Тесты
```

### Компоненты:

#### 1. TelegramService (`telegram_service.py`)

- **Инициализация бота** с aiogram
- **Регистрация хендлеров** команд и сообщений
- **FSM состояния** для диалогов
- **Создание пользователей** из Telegram данных

#### 2. Webhook Router (`telegram.py`)

- **Обработка webhook** обновлений
- **Управление webhook** (установка/удаление)
- **API для уведомлений**

#### 3. Polling Script (`telegram_bot_polling.py`)

- **Режим разработки**
- **Обработка сигналов** остановки
- **Логирование** и отладка

## 🤖 Команды бота

### Пользовательские команды:

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/surveys` - Список доступных опросов

### Администраторские команды:

- `/admin` - Панель администратора
- Статистика системы
- Управление пользователями
- Отчеты и аналитика

### Inline кнопки:

- **📋 Доступные опросы** - Список опросов
- **🌐 Открыть веб-приложение** - Переход в web-app
- **ℹ️ Помощь** - Справочная информация
- **⚙️ Панель администратора** - Для админов

## 🔄 Интеграция с FastAPI

### Жизненный цикл:

```python
# При старте приложения
async def lifespan(app: FastAPI):
    # Инициализация Telegram сервиса
    telegram_service = await get_telegram_service()

    yield

    # Остановка сервиса
    await telegram_service.stop_polling()
```

### Использование в API:

```python
from services.telegram_service import get_telegram_service

async def send_notification():
    service = await get_telegram_service()
    await service.send_notification(chat_id, message)
```

## 🛠️ Troubleshooting

### Частые проблемы:

#### 1. Бот не отвечает

```bash
# Проверьте статус
make telegram-status

# Проверьте логи
make telegram-polling
```

#### 2. Webhook не работает

```bash
# Проверьте URL
make telegram-info

# Переустановите webhook
make telegram-webhook-delete
make telegram-webhook-set
```

#### 3. Ошибки импорта

```bash
# Установите aiogram
pip install aiogram==3.2.0

# Или через uv
uv pip install aiogram==3.2.0
```

#### 4. Проблемы с токеном

- Проверьте правильность токена в `.env`
- Убедитесь, что токен не содержит лишних символов
- Проверьте, что бот создан через @BotFather

### Полезные команды для отладки:

```bash
# Проверка бота через API
curl "https://api.telegram.org/bot{TOKEN}/getMe"

# Проверка webhook
curl "https://api.telegram.org/bot{TOKEN}/getWebhookInfo"

# Тестирование локального API
curl "http://localhost:8000/telegram/status"
```

### Логи:

```bash
# Polling логи
tail -f backend/telegram_bot.log

# FastAPI логи
tail -f backend/logs/app.log
```

## 📖 Дополнительные ресурсы

- [Официальная документация aiogram](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Примеры aiogram](https://github.com/aiogram/aiogram/tree/dev-3.x/examples)

## 🔧 Разработка

### Добавление новых команд:

1. Добавьте хендлер в `TelegramService`
2. Зарегистрируйте в `_register_handlers()`
3. Добавьте логику обработки
4. Протестируйте через `make telegram-test`

### Создание FSM диалогов:

```python
class SurveyStates(StatesGroup):
    waiting_for_answer = State()

@dp.message(SurveyStates.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext):
    # Обработка ответа
    await state.clear()
```

---

**💡 Совет:** Используйте `make telegram-setup` для пошаговой настройки бота!
