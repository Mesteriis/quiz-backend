# Типы вопросов в Quiz App

Этот документ описывает все доступные типы вопросов и форматы ответов.

## Базовые типы вопросов

### 1. TEXT - Текстовый вопрос

**Описание**: Свободный текстовый ввод

**Пример создания вопроса**:

```json
{
  "title": "Расскажите о своем опыте",
  "question_type": "TEXT",
  "is_required": true,
  "order": 1
}
```

**Формат ответа**:

```json
{
  "answer": {
    "value": "Мой опыт работы составляет 5 лет"
  }
}
```

### 2. YES_NO - Да/Нет вопрос

**Описание**: Булевый вопрос с вариантами да/нет

**Пример создания вопроса**:

```json
{
  "title": "Вам нравится наше приложение?",
  "question_type": "YES_NO",
  "is_required": true,
  "order": 2
}
```

**Формат ответа**:

```json
{
  "answer": {
    "value": true
  }
}
```

### 3. RATING_1_10 - Рейтинг от 1 до 10

**Описание**: Числовая оценка от 1 до 10

**Пример создания вопроса**:

```json
{
  "title": "Оцените качество обслуживания",
  "question_type": "RATING_1_10",
  "is_required": true,
  "order": 3
}
```

**Формат ответа**:

```json
{
  "answer": {
    "value": 8
  }
}
```

## Контактные данные

### 4. EMAIL - Email адрес

**Описание**: Ввод и валидация email адреса

**Пример создания вопроса**:

```json
{
  "title": "Введите ваш email",
  "question_type": "EMAIL",
  "is_required": true,
  "order": 4
}
```

**Формат ответа**:

```json
{
  "answer": {
    "value": "user@example.com"
  }
}
```

### 5. PHONE - Номер телефона

**Описание**: Ввод и валидация номера телефона

**Пример создания вопроса**:

```json
{
  "title": "Введите ваш номер телефона",
  "question_type": "PHONE",
  "is_required": true,
  "order": 5
}
```

**Формат ответа**:

```json
{
  "answer": {
    "value": "+7 (999) 123-45-67"
  }
}
```

## Файлы и медиа

### 6. IMAGE_UPLOAD - Загрузка изображения

**Описание**: Загрузка изображения с валидацией формата

**Пример создания вопроса**:

```json
{
  "title": "Загрузите фотографию",
  "question_type": "IMAGE_UPLOAD",
  "is_required": true,
  "order": 6,
  "question_data": {
    "max_size_mb": 5,
    "accepted_formats": ["jpg", "jpeg", "png", "gif"]
  }
}
```

**Формат ответа**:

```json
{
  "answer": {
    "file": {
      "filename": "photo.jpg",
      "content_type": "image/jpeg",
      "size": 1024000,
      "url": "https://storage.example.com/uploads/photo.jpg"
    }
  }
}
```

### 7. FILE_UPLOAD - Загрузка файла

**Описание**: Загрузка файла любого типа

**Пример создания вопроса**:

```json
{
  "title": "Загрузите документ",
  "question_type": "FILE_UPLOAD",
  "is_required": true,
  "order": 7,
  "question_data": {
    "max_size_mb": 10,
    "accepted_formats": ["pdf", "doc", "docx", "txt"]
  }
}
```

**Формат ответа**:

```json
{
  "answer": {
    "file": {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 2048000,
      "url": "https://storage.example.com/uploads/document.pdf"
    }
  }
}
```

## Специальные типы

### 8. GEOLOCATION - Геоданные

**Описание**: Получение координат местоположения

**Пример создания вопроса**:

```json
{
  "title": "Укажите ваше местоположение",
  "question_type": "GEOLOCATION",
  "is_required": true,
  "order": 8,
  "question_data": {
    "accuracy_required": true,
    "allow_manual_input": false
  }
}
```

**Формат ответа**:

```json
{
  "answer": {
    "location": {
      "latitude": 55.7558,
      "longitude": 37.6173,
      "accuracy": 10,
      "address": "Москва, Красная площадь, 1"
    }
  }
}
```

### 9. NFC_SCAN - NFC сканирование

**Описание**: Сканирование NFC меток

**Пример создания вопроса**:

```json
{
  "title": "Отсканируйте NFC метку",
  "question_type": "NFC_SCAN",
  "is_required": true,
  "order": 9,
  "question_data": {
    "expected_tag_types": ["NDEF", "Mifare"],
    "timeout_seconds": 30
  }
}
```

**Формат ответа**:

```json
{
  "answer": {
    "nfc_data": {
      "tag_id": "04:A3:B2:C1:D0:E5:F6",
      "tag_type": "NDEF",
      "data": "Hello World",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

## Валидация ответов

### Автоматическая валидация

Система автоматически валидирует ответы на основе типа вопроса:

- **TEXT**: Проверка на непустую строку
- **YES_NO**: Проверка булевого значения
- **RATING_1_10**: Проверка числа от 1 до 10
- **EMAIL**: Проверка формата email
- **PHONE**: Проверка формата телефона
- **IMAGE_UPLOAD**: Проверка типа файла и размера
- **FILE_UPLOAD**: Проверка типа файла и размера
- **GEOLOCATION**: Проверка координат
- **NFC_SCAN**: Проверка структуры NFC данных

### Endpoint для валидации

```
POST /api/responses/validate-before-save
```

**Пример запроса**:

```json
{
  "question_id": 1,
  "answer": {
    "value": "test@example.com"
  }
}
```

**Пример ответа**:

```json
{
  "question_id": 1,
  "is_valid": true,
  "message": "Response is valid",
  "question_type": "EMAIL",
  "question_title": "Введите ваш email"
}
```

## Примеры использования

### Создание опроса с разными типами вопросов

```python
# Создание вопросов разных типов
questions = [
    {
        "title": "Как вас зовут?",
        "question_type": "TEXT",
        "order": 1,
        "is_required": True
    },
    {
        "title": "Ваш email",
        "question_type": "EMAIL",
        "order": 2,
        "is_required": True
    },
    {
        "title": "Загрузите фото профиля",
        "question_type": "IMAGE_UPLOAD",
        "order": 3,
        "is_required": False,
        "question_data": {
            "max_size_mb": 2,
            "accepted_formats": ["jpg", "png"]
        }
    },
    {
        "title": "Ваше местоположение",
        "question_type": "GEOLOCATION",
        "order": 4,
        "is_required": False
    }
]
```

### Отправка ответов

```python
# Отправка ответов на вопросы
responses = [
    {
        "question_id": 1,
        "user_session_id": "session_123",
        "answer": {"value": "Иван Иванов"}
    },
    {
        "question_id": 2,
        "user_session_id": "session_123",
        "answer": {"value": "ivan@example.com"}
    },
    {
        "question_id": 3,
        "user_session_id": "session_123",
        "answer": {
            "file": {
                "filename": "avatar.jpg",
                "content_type": "image/jpeg",
                "url": "https://storage.example.com/avatar.jpg"
            }
        }
    }
]
```

## Заключение

Система поддерживает широкий спектр типов вопросов для создания интерактивных опросов с различными типами данных. Все ответы автоматически валидируются и сохраняются в структурированном формате JSON.
