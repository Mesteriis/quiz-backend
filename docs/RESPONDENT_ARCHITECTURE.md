# 🎯 Архитектура Респондента - Quiz Application

## 📋 Обзор

Предлагаемая архитектура разделяет ответственность между основными сущностями:

- **User** - авторизация и идентификация пользователей
- **Profile** - профильные данные пользователей (1:1 с User)
- **Respondent** - участники опросов (анонимные или связанные с User)
- **RespondentSurvey** - связь респондентов с опросами
- **ConsentLog** - журнал согласий на сбор данных
- **RespondentEvent** - журнал событий респондента
- **SurveyDataRequirements** - требования к данным для каждого опроса

## 🏗️ Модели данных

### 🧑‍💻 User - Авторизация и идентификация

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # === СПОСОБЫ АВТОРИЗАЦИИ (уникальные идентификаторы) ===
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    tg_id: Mapped[int | None] = mapped_column(unique=True, nullable=True)  # Telegram ID

    # === СИСТЕМНЫЕ ДАННЫЕ ===
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Может быть NULL для Telegram-only
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # === SOFT DELETE ===
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    # === СВЯЗИ ===
    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False)
    respondents: Mapped[list["Respondent"]] = relationship("Respondent", back_populates="user")

    # === УНИКАЛЬНЫЕ ИНДЕКСЫ ===
    __table_args__ = (
        # Один из способов авторизации должен быть заполнен
        CheckConstraint(
            "email IS NOT NULL OR username IS NOT NULL OR tg_id IS NOT NULL",
            name="user_must_have_identifier"
        ),
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_username", "username", unique=True),
        Index("ix_users_tg_id", "tg_id", unique=True),
        Index("ix_users_deleted", "is_deleted"),
    )
```

### 👤 Profile - Профиль пользователя

```python
class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # === ЛИЧНЫЕ ДАННЫЕ ===
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # === КОНТАКТЫ ===
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # === МЕТАДАННЫЕ ===
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # === СВЯЗИ ===
    user: Mapped["User"] = relationship("User", back_populates="profile")
```

### 🎭 Respondent - Участник опроса

```python
class Respondent(Base):
    __tablename__ = "respondents"

    id: Mapped[int] = mapped_column(primary_key=True)

    # === ИДЕНТИФИКАЦИЯ ===
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    browser_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # === 📗 ЯВНЫЕ ДАННЫЕ (без разрешения) ===
    # Технические данные
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_info: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"name": "Chrome", "version": "120.0", "language": "ru"}

    device_info: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"type": "mobile", "os": "iOS", "screen": {"width": 390, "height": 844}}

    # Геолокация по IP
    geo_info: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"country": "RU", "city": "Moscow", "timezone": "Europe/Moscow", "isp": "Beeline"}

    # Поведенческие данные
    referrer_info: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"source": "google", "medium": "organic", "campaign": null, "utm_params": {...}}

    # === КОНТЕКСТНЫЕ ДАННЫЕ TELEGRAM ===
    telegram_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"webapp_data": {...}, "chat_id": 123, "username": "user123"}

    # === ИСТОЧНИК ТРАФИКА ===
    entry_point: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # "web", "pwa", "telegram_webapp", "telegram_bot"

    # === 📙 ДАННЫЕ С РАЗРЕШЕНИЕМ (хранятся только при согласии) ===
    precise_location: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"lat": 55.7558, "lng": 37.6176, "accuracy": 10, "timestamp": "2024-01-01T12:00:00"}

    # === АНОНИМНЫЕ ДАННЫЕ ===
    anonymous_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    anonymous_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # === ВРЕМЕННЫЕ МЕТКИ ===
    first_seen_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # === СТАТУСЫ ===
    is_anonymous: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_merged: Mapped[bool] = mapped_column(default=False)  # Был объединен с другим
    merged_into_id: Mapped[int | None] = mapped_column(ForeignKey("respondents.id"), nullable=True)

    # === SOFT DELETE ===
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    # === СВЯЗИ ===
    user: Mapped["User"] = relationship("User", back_populates="respondents")
    responses: Mapped[list["Response"]] = relationship("Response", back_populates="respondent")
    survey_participations: Mapped[list["RespondentSurvey"]] = relationship("RespondentSurvey", back_populates="respondent")
    events: Mapped[list["RespondentEvent"]] = relationship("RespondentEvent", back_populates="respondent")
    consents: Mapped[list["ConsentLog"]] = relationship("ConsentLog", back_populates="respondent")

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_respondents_fingerprint", "browser_fingerprint"),
        Index("ix_respondents_session", "session_id"),
        Index("ix_respondents_user_id", "user_id"),
        Index("ix_respondents_deleted", "is_deleted"),
        Index("ix_respondents_merged", "is_merged"),
    )
```

### 🔗 RespondentSurvey - Связь респондента с опросом

```python
class RespondentSurvey(Base):
    __tablename__ = "respondent_surveys"

    id: Mapped[int] = mapped_column(primary_key=True)
    respondent_id: Mapped[int] = mapped_column(ForeignKey("respondents.id"), nullable=False)
    survey_id: Mapped[int] = mapped_column(ForeignKey("surveys.id"), nullable=False)

    # === СТАТУСЫ ПРОХОЖДЕНИЯ ===
    status: Mapped[str] = mapped_column(String(20), default="started")
    # "started", "in_progress", "completed", "abandoned"

    # === ПРОГРЕСС ===
    progress_percentage: Mapped[float] = mapped_column(default=0.0)
    questions_answered: Mapped[int] = mapped_column(default=0)
    total_questions: Mapped[int] = mapped_column(nullable=False)

    # === ВРЕМЕННЫЕ МЕТКИ ===
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # === МЕТАДАННЫЕ ===
    time_spent_seconds: Mapped[int] = mapped_column(default=0)
    completion_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # "web", "telegram_webapp", "telegram_bot"

    # === СВЯЗИ ===
    respondent: Mapped["Respondent"] = relationship("Respondent", back_populates="survey_participations")
    survey: Mapped["Survey"] = relationship("Survey", back_populates="respondent_participations")

    # === УНИКАЛЬНЫЕ ИНДЕКСЫ ===
    __table_args__ = (
        UniqueConstraint("respondent_id", "survey_id", name="uq_respondent_survey"),
        Index("ix_respondent_surveys_status", "status"),
        Index("ix_respondent_surveys_started", "started_at"),
    )
```

### 📋 SurveyDataRequirements - Требования к данным опроса

```python
class SurveyDataRequirements(Base):
    __tablename__ = "survey_data_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("surveys.id"), nullable=False)

    # === ТРЕБОВАНИЯ К ГЕОЛОКАЦИИ ===
    requires_location: Mapped[bool] = mapped_column(default=False)
    location_is_required: Mapped[bool] = mapped_column(default=False)  # Обязательно или можно пропустить
    location_precision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # "country", "city", "precise"

    # === ТРЕБОВАНИЯ К ЛИЧНЫМ ДАННЫМ ===
    requires_name: Mapped[bool] = mapped_column(default=False)
    name_is_required: Mapped[bool] = mapped_column(default=False)

    requires_email: Mapped[bool] = mapped_column(default=False)
    email_is_required: Mapped[bool] = mapped_column(default=False)

    requires_phone: Mapped[bool] = mapped_column(default=False)
    phone_is_required: Mapped[bool] = mapped_column(default=False)

    # === ТРЕБОВАНИЯ К ТЕХНИЧЕСКИМ ДАННЫМ ===
    requires_device_info: Mapped[bool] = mapped_column(default=False)
    device_info_is_required: Mapped[bool] = mapped_column(default=False)

    # === ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ ===
    custom_requirements: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"camera_access": {"required": true, "mandatory": false}}

    # === СВЯЗИ ===
    survey: Mapped["Survey"] = relationship("Survey", back_populates="data_requirements")

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_survey_requirements_survey", "survey_id"),
    )
```

### 📝 ConsentLog - Журнал согласий

```python
class ConsentLog(Base):
    __tablename__ = "consent_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    respondent_id: Mapped[int] = mapped_column(ForeignKey("respondents.id"), nullable=False)
    survey_id: Mapped[int | None] = mapped_column(ForeignKey("surveys.id"), nullable=True)

    # === ТИПЫ СОГЛАСИЙ ===
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # "location", "device_info", "personal_data", "marketing", "analytics"

    # === СТАТУС СОГЛАСИЯ ===
    is_granted: Mapped[bool] = mapped_column(nullable=False)
    granted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # === МЕТАДАННЫЕ ===
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_version: Mapped[str] = mapped_column(String(20), default="1.0")

    # === ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ===
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"precision": "city", "purpose": "survey_analytics"}

    # === СВЯЗИ ===
    respondent: Mapped["Respondent"] = relationship("Respondent", back_populates="consents")
    survey: Mapped["Survey"] = relationship("Survey")

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_consent_logs_respondent", "respondent_id"),
        Index("ix_consent_logs_type", "consent_type"),
        Index("ix_consent_logs_granted", "granted_at"),
    )
```

### 📊 RespondentEvent - Журнал событий

```python
class RespondentEvent(Base):
    __tablename__ = "respondent_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    respondent_id: Mapped[int] = mapped_column(ForeignKey("respondents.id"), nullable=False)

    # === СОБЫТИЕ ===
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # "created", "authorized", "merged", "survey_started", "survey_completed", "consent_granted"

    event_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # {"from_anonymous": true, "merged_respondent_id": 123, "survey_id": 456}

    # === ВРЕМЕННЫЕ МЕТКИ ===
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # === МЕТАДАННЫЕ ===
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # === СВЯЗИ ===
    respondent: Mapped["Respondent"] = relationship("Respondent", back_populates="events")

    # === ИНДЕКСЫ ===
    __table_args__ = (
        Index("ix_respondent_events_respondent", "respondent_id"),
        Index("ix_respondent_events_type", "event_type"),
        Index("ix_respondent_events_created", "created_at"),
    )
```

## 🔧 Связи между сущностями

```
User (1) <---> (1) Profile                    # Один пользователь = один профиль
User (1) <---> (0,N) Respondent              # Пользователь может иметь несколько респондентов
Respondent (1) <---> (N) Response            # Респондент делает много ответов
Respondent (1) <---> (N) RespondentSurvey    # Респондент участвует в опросах
Survey (1) <---> (N) RespondentSurvey        # Опрос имеет много участников
Survey (1) <---> (1) SurveyDataRequirements  # Опрос имеет требования к данным
Respondent (1) <---> (N) ConsentLog          # Респондент дает согласия
Respondent (1) <---> (N) RespondentEvent     # Респондент имеет события
```

## 🏛️ Репозитории

### UserRepository

```python
class UserRepository(BaseRepository[User]):

    async def get_by_email(self, email: str) -> User | None:
        """Получить пользователя по email"""

    async def get_by_username(self, username: str) -> User | None:
        """Получить пользователя по username"""

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        """Получить пользователя по Telegram ID"""

    async def soft_delete(self, user_id: int) -> bool:
        """Мягкое удаление пользователя"""
```

### ProfileRepository

```python
class ProfileRepository(BaseRepository[Profile]):

    async def get_by_user_id(self, user_id: int) -> Profile | None:
        """Получить профиль пользователя"""

    async def create_for_user(self, user_id: int, profile_data: dict) -> Profile:
        """Создать профиль для пользователя"""
```

### RespondentRepository

```python
class RespondentRepository(BaseRepository[Respondent]):

    async def get_by_session_id(self, session_id: str) -> Respondent | None:
        """Получить респондента по session_id"""

    async def get_by_fingerprint(self, fingerprint: str) -> list[Respondent]:
        """Получить респондентов по отпечатку браузера"""

    async def get_by_user_id(self, user_id: int) -> list[Respondent]:
        """Получить всех респондентов пользователя"""

    async def merge_respondents(self, source_id: int, target_id: int) -> bool:
        """Объединить респондентов"""

    async def auto_merge_for_user(self, user_id: int) -> list[int]:
        """Автоматически объединить анонимных респондентов пользователя"""
```

### RespondentSurveyRepository

```python
class RespondentSurveyRepository(BaseRepository[RespondentSurvey]):

    async def get_participation(self, respondent_id: int, survey_id: int) -> RespondentSurvey | None:
        """Получить участие респондента в опросе"""

    async def update_progress(self, respondent_id: int, survey_id: int, progress: dict) -> bool:
        """Обновить прогресс прохождения"""

    async def complete_survey(self, respondent_id: int, survey_id: int) -> bool:
        """Отметить опрос как завершенный"""
```

### ConsentLogRepository

```python
class ConsentLogRepository(BaseRepository[ConsentLog]):

    async def has_consent(self, respondent_id: int, consent_type: str) -> bool:
        """Проверить наличие согласия"""

    async def grant_consent(self, respondent_id: int, consent_type: str, details: dict) -> ConsentLog:
        """Зарегистрировать согласие"""

    async def get_consents(self, respondent_id: int) -> list[ConsentLog]:
        """Получить все согласия респондента"""
```

### RespondentEventRepository

```python
class RespondentEventRepository(BaseRepository[RespondentEvent]):

    async def log_event(self, respondent_id: int, event_type: str, event_data: dict) -> RespondentEvent:
        """Записать событие"""

    async def get_events(self, respondent_id: int, event_type: str = None) -> list[RespondentEvent]:
        """Получить события респондента"""
```

## 📗 Явные данные (без разрешения)

### 🌐 Технические данные и браузер

- IP-адрес
- Геолокация по IP (страна, регион, город)
- User-Agent
- Браузер (название, версия)
- Операционная система (название, версия)
- Тип устройства (ПК, телефон, планшет)
- Язык браузера
- HTTP Referer (откуда перешел пользователь)
- Время захода и активности
- Время, проведённое на странице
- Размер экрана и разрешение
- Цветовая схема (тёмная/светлая тема)
- Browser Fingerprint (хэш на основе параметров браузера)

### 🔗 Telegram-контекст

- chat_id, username, first_name, last_name
- Данные об аутентификации (Telegram Login Widget/WebApp)
- Данные inline-кнопок или команд Telegram бота
- WebApp-платформа и версия приложения Telegram

## 📙 Данные с запросом разрешения

### 🗺️ Точная геолокация

- Координаты GPS (широта и долгота)
- Высота над уровнем моря
- Скорость и направление движения
- Точность определения местоположения

### 📱 Данные устройства

- Доступ к камере
- Доступ к микрофону
- Доступ к файлам
- Push-уведомления

## 🎯 Логика работы с данными

### Проверка требований опроса:

```python
async def check_survey_requirements(respondent_id: int, survey_id: int) -> dict:
    """
    Проверяет, какие данные нужны для опроса и какие согласия требуются
    """
    requirements = await survey_requirements_repo.get_by_survey_id(survey_id)
    consents = await consent_repo.get_consents(respondent_id)

    missing_required = []
    missing_optional = []

    if requirements.requires_location:
        has_consent = any(c.consent_type == "location" and c.is_granted for c in consents)
        if not has_consent:
            if requirements.location_is_required:
                missing_required.append("location")
            else:
                missing_optional.append("location")

    return {
        "can_proceed": len(missing_required) == 0,
        "missing_required": missing_required,
        "missing_optional": missing_optional
    }
```

### Автоматическое объединение респондентов:

```python
async def auto_merge_respondents(user_id: int) -> list[int]:
    """
    Автоматически объединяет анонимных респондентов
    когда пользователь авторизуется
    """
    # Найти всех анонимных респондентов этого пользователя
    anonymous_respondents = await respondent_repo.get_anonymous_by_fingerprint_or_session(user_id)

    if len(anonymous_respondents) <= 1:
        return []

    # Выбрать основной респондент (самый активный)
    main_respondent = max(anonymous_respondents, key=lambda r: r.last_activity_at)

    merged_ids = []
    for respondent in anonymous_respondents:
        if respondent.id != main_respondent.id:
            await respondent_repo.merge_respondents(respondent.id, main_respondent.id)
            merged_ids.append(respondent.id)

    # Связать основной респондент с пользователем
    main_respondent.user_id = user_id
    main_respondent.is_anonymous = False

    return merged_ids
```

## 🚀 Сценарии использования

### Сценарий 1: Анонимное прохождение с проверкой требований

```python
# 1. Пользователь начинает опрос
respondent = await create_anonymous_respondent(session_data)

# 2. Проверяем требования опроса
requirements = await check_survey_requirements(respondent.id, survey_id)

if not requirements["can_proceed"]:
    # 3. Запрашиваем обязательные согласия
    for consent_type in requirements["missing_required"]:
        await request_consent(respondent.id, consent_type, required=True)

# 4. Предлагаем дать необязательные согласия
for consent_type in requirements["missing_optional"]:
    await request_consent(respondent.id, consent_type, required=False)

# 5. Начинаем опрос
await start_survey_participation(respondent.id, survey_id)
```

### Сценарий 2: Авторизация с объединением данных

```python
# 1. Пользователь авторизуется
user = await authenticate_user(credentials)

# 2. Автоматически объединяем его анонимных респондентов
merged_ids = await auto_merge_respondents(user.id)

# 3. Логируем событие
await log_event(respondent.id, "authorized", {
    "from_anonymous": True,
    "merged_respondents": merged_ids
})

# 4. Обновляем текущий респондент
current_respondent.user_id = user.id
current_respondent.is_anonymous = False
```

## 📊 Аналитика и отчеты

### Статистика по источникам:

```python
# Участники по источникам входа
stats = await respondent_repo.get_stats_by_entry_point()
# {"telegram_webapp": 150, "web": 80, "telegram_bot": 30}

# Конверсия согласий
consent_stats = await consent_repo.get_consent_conversion_rates()
# {"location": 0.75, "device_info": 0.45, "marketing": 0.20}
```

## 🎯 Заключение

Обновленная архитектура обеспечивает:

- **Четкое разделение ответственности** между сущностями
- **Гибкую систему согласий** на сбор данных
- **Автоматическое объединение** анонимных данных
- **Полное логирование** событий и действий
- **Соответствие GDPR** и другим требованиям приватности
- **Богатую аналитику** поведения пользователей
- **Масштабируемость** для будущего развития

---

_Документ обновлен с учетом системы согласий, связей с опросами и автоматического объединения данных_
