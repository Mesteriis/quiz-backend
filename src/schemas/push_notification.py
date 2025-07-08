"""
Push notification Pydantic schemas for the Quiz App.

This module contains Pydantic schemas for push notification data validation,
serialization, and API request/response handling.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PushSubscriptionBase(BaseModel):
    """Базовая схема для подписки на push-уведомления"""

    model_config = ConfigDict(from_attributes=True)

    endpoint: str = Field(..., description="URL endpoint для push-уведомлений")
    p256dh_key: str = Field(..., description="Ключ P256DH для шифрования")
    auth_key: str = Field(..., description="Ключ аутентификации")
    enabled_categories: list[str] = Field(
        default_factory=list, description="Активные категории"
    )
    is_active: bool = Field(default=True, description="Активна ли подписка")
    user_agent: str | None = Field(None, description="User agent браузера")
    browser_name: str | None = Field(None, description="Название браузера")
    platform: str | None = Field(None, description="Платформа")


class PushSubscriptionCreate(PushSubscriptionBase):
    """Схема создания подписки"""

    user_id: int = Field(..., description="ID пользователя")


class PushSubscriptionUpdate(BaseModel):
    """Схема обновления подписки"""

    enabled_categories: list[str] | None = Field(None, description="Активные категории")
    is_active: bool | None = Field(None, description="Активна ли подписка")


class PushSubscriptionRead(PushSubscriptionBase):
    """Схема чтения подписки"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None


class PushNotificationBase(BaseModel):
    """Базовая схема для push-уведомления"""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., description="Заголовок уведомления")
    body: str = Field(..., description="Текст уведомления")
    icon: str | None = Field(None, description="URL иконки")
    image: str | None = Field(None, description="URL изображения")
    url: str | None = Field(None, description="URL для перехода")
    category: str = Field(..., description="Категория уведомления")
    priority: str = Field(default="normal", description="Приоритет")
    tag: str | None = Field(None, description="Тег для группировки")
    require_interaction: bool = Field(
        default=False, description="Требует взаимодействия"
    )
    silent: bool = Field(default=False, description="Тихое уведомление")
    vibrate_pattern: list[int] = Field(
        default_factory=lambda: [100, 50, 100], description="Паттерн вибрации"
    )


class PushNotificationCreate(PushNotificationBase):
    """Схема создания уведомления"""

    subscription_id: int = Field(..., description="ID подписки")


class PushNotificationUpdate(BaseModel):
    """Схема обновления уведомления"""

    status: str | None = Field(None, description="Статус уведомления")
    sent_at: datetime | None = Field(None, description="Время отправки")
    delivered_at: datetime | None = Field(None, description="Время доставки")
    clicked: bool | None = Field(None, description="Нажато ли уведомление")
    clicked_at: datetime | None = Field(None, description="Время нажатия")
    dismissed: bool | None = Field(None, description="Отклонено ли уведомление")
    dismissed_at: datetime | None = Field(None, description="Время отклонения")
    error_message: str | None = Field(None, description="Сообщение об ошибке")


class PushNotificationRead(PushNotificationBase):
    """Схема чтения уведомления"""

    id: int
    subscription_id: int
    status: str
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    clicked: bool = False
    clicked_at: datetime | None = None
    dismissed: bool = False
    dismissed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class NotificationTemplateBase(BaseModel):
    """Базовая схема для шаблона уведомления"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Название шаблона")
    category: str = Field(..., description="Категория шаблона")
    title_template: str = Field(..., description="Шаблон заголовка")
    body_template: str = Field(..., description="Шаблон текста")
    default_icon: str | None = Field(None, description="Иконка по умолчанию")
    default_image: str | None = Field(None, description="Изображение по умолчанию")
    default_url: str | None = Field(None, description="URL по умолчанию")
    default_priority: str = Field(
        default="normal", description="Приоритет по умолчанию"
    )
    default_require_interaction: bool = Field(
        default=False, description="Требует взаимодействия по умолчанию"
    )
    default_silent: bool = Field(default=False, description="Тихое по умолчанию")
    default_vibrate_pattern: list[int] = Field(
        default_factory=lambda: [100, 50, 100],
        description="Паттерн вибрации по умолчанию",
    )
    description: str | None = Field(None, description="Описание шаблона")
    is_active: bool = Field(default=True, description="Активен ли шаблон")


class NotificationTemplateCreate(NotificationTemplateBase):
    """Схема создания шаблона уведомления"""

    pass


class NotificationTemplateUpdate(BaseModel):
    """Схема обновления шаблона уведомления"""

    title_template: str | None = Field(None, description="Шаблон заголовка")
    body_template: str | None = Field(None, description="Шаблон текста")
    default_icon: str | None = Field(None, description="Иконка по умолчанию")
    default_image: str | None = Field(None, description="Изображение по умолчанию")
    default_url: str | None = Field(None, description="URL по умолчанию")
    default_priority: str | None = Field(None, description="Приоритет по умолчанию")
    default_require_interaction: bool | None = Field(
        None, description="Требует взаимодействия по умолчанию"
    )
    default_silent: bool | None = Field(None, description="Тихое по умолчанию")
    default_vibrate_pattern: list[int] | None = Field(
        None, description="Паттерн вибрации по умолчанию"
    )
    description: str | None = Field(None, description="Описание шаблона")
    is_active: bool | None = Field(None, description="Активен ли шаблон")


class NotificationTemplateRead(NotificationTemplateBase):
    """Схема чтения шаблона уведомления"""

    id: int
    created_at: datetime
    updated_at: datetime


class NotificationAnalyticsBase(BaseModel):
    """Базовая схема для аналитики уведомлений"""

    model_config = ConfigDict(from_attributes=True)

    event_type: str = Field(..., description="Тип события")
    category: str | None = Field(None, description="Категория")
    browser_name: str | None = Field(None, description="Название браузера")
    platform: str | None = Field(None, description="Платформа")
    metadata: dict | None = Field(None, description="Дополнительные данные")
    error_details: str | None = Field(None, description="Детали ошибки")


class NotificationAnalyticsCreate(NotificationAnalyticsBase):
    """Схема создания записи аналитики"""

    notification_id: int | None = Field(None, description="ID уведомления")
    user_id: int | None = Field(None, description="ID пользователя")


class NotificationAnalyticsRead(NotificationAnalyticsBase):
    """Схема чтения записи аналитики"""

    id: int
    notification_id: int | None = None
    user_id: int | None = None
    created_at: datetime


class PushNotificationBulkCreate(BaseModel):
    """Схема массового создания уведомлений"""

    notifications: list[PushNotificationCreate] = Field(
        ..., description="Список уведомлений для создания"
    )


class PushNotificationStatsResponse(BaseModel):
    """Схема ответа статистики уведомлений"""

    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    clicked_notifications: int
    dismissed_notifications: int
    failed_notifications: int
    click_rate: float
    delivery_rate: float

    model_config = ConfigDict(from_attributes=True)


class PushSubscriptionListResponse(BaseModel):
    """Схема ответа списка подписок"""

    subscriptions: list[PushSubscriptionRead]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class PushNotificationListResponse(BaseModel):
    """Схема ответа списка уведомлений"""

    notifications: list[PushNotificationRead]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class NotificationCategoriesUpdate(BaseModel):
    """Схема обновления категорий уведомлений"""

    model_config = ConfigDict(from_attributes=True)

    categories: list[str] = Field(..., description="Список активных категорий")


class VapidKeyResponse(BaseModel):
    """Схема ответа с VAPID ключом"""

    model_config = ConfigDict(from_attributes=True)

    public_key: str = Field(..., description="Публичный VAPID ключ")


# Переименовываем для совместимости
PushSubscriptionResponse = PushSubscriptionRead
PushNotificationResponse = PushNotificationRead
NotificationStats = PushNotificationStatsResponse
