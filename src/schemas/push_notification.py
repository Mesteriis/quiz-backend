from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PushSubscriptionCreate(BaseModel):
    """Схема для создания подписки на push-уведомления"""

    subscription: dict[str, Any] = Field(..., description="Данные подписки от браузера")
    categories: list[str] = Field(
        default_factory=list, description="Активные категории"
    )

    class Config:
        schema_extra = {
            "example": {
                "subscription": {
                    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
                    "keys": {
                        "p256dh": "BEl62iUYgUivxIk...",
                        "auth": "tBHItJI5svbpez7K...",
                    },
                },
                "categories": ["quiz_completed", "new_response", "system_updates"],
            }
        }


class PushSubscriptionResponse(BaseModel):
    """Схема ответа подписки"""

    id: int
    is_active: bool
    enabled_categories: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PushNotificationCreate(BaseModel):
    """Схема для создания push-уведомления"""

    title: str = Field(..., max_length=255, description="Заголовок уведомления")
    body: str = Field(..., description="Текст уведомления")
    category: str = Field(..., description="Категория уведомления")

    # Опциональные поля
    icon: Optional[str] = Field(None, description="URL иконки")
    image: Optional[str] = Field(None, description="URL изображения")
    url: Optional[str] = Field(None, description="URL для перехода")
    priority: Optional[str] = Field("normal", description="Приоритет уведомления")
    require_interaction: Optional[bool] = Field(
        False, description="Требовать взаимодействие"
    )
    silent: Optional[bool] = Field(False, description="Тихое уведомление")

    class Config:
        schema_extra = {
            "example": {
                "title": "Новый ответ на опрос",
                "body": "Пользователь ответил на ваш опрос 'Исследование предпочтений'",
                "category": "new_response",
                "icon": "/pwa-192x192.png",
                "url": "/surveys/123/results",
                "priority": "normal",
            }
        }


class PushNotificationResponse(BaseModel):
    """Схема ответа уведомления"""

    id: int
    title: str
    body: str
    category: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationCategoriesUpdate(BaseModel):
    """Схема для обновления категорий уведомлений"""

    categories: list[str] = Field(..., description="Список активных категорий")

    class Config:
        schema_extra = {"example": {"categories": ["quiz_completed", "new_response"]}}


class NotificationAnalytics(BaseModel):
    """Схема для аналитики уведомлений"""

    action: str = Field(..., description="Действие пользователя")
    category: str = Field(..., description="Категория уведомления")
    primary_key: Optional[str] = Field(None, description="Первичный ключ уведомления")
    timestamp: int = Field(..., description="Временная метка")

    class Config:
        schema_extra = {
            "example": {
                "action": "clicked",
                "category": "quiz_completed",
                "primary_key": "123456789",
                "timestamp": 1640995200000,
            }
        }


class VapidKeyResponse(BaseModel):
    """Схема для VAPID ключа"""

    public_key: str = Field(..., description="Публичный VAPID ключ")

    class Config:
        schema_extra = {
            "example": {
                "public_key": "BEl62iUYgUivxIkv69yViEuiBIa40HI0DLb6RDJ5-8N4Am6-YCwdI-V0OKdcUb8qXJ6rN4V8CuGKzqfJbZquJEa4"
            }
        }


class NotificationStats(BaseModel):
    """Схема для статистики уведомлений"""

    total_sent: int = Field(..., description="Всего отправлено")
    total_delivered: int = Field(..., description="Всего доставлено")
    total_clicked: int = Field(..., description="Всего кликов")
    total_dismissed: int = Field(..., description="Всего отклонено")
    categories_stats: dict[str, dict[str, int]] = Field(
        ..., description="Статистика по категориям"
    )

    class Config:
        schema_extra = {
            "example": {
                "total_sent": 150,
                "total_delivered": 142,
                "total_clicked": 89,
                "total_dismissed": 25,
                "categories_stats": {
                    "quiz_completed": {
                        "sent": 75,
                        "delivered": 72,
                        "clicked": 45,
                        "dismissed": 12,
                    },
                    "new_response": {
                        "sent": 50,
                        "delivered": 48,
                        "clicked": 32,
                        "dismissed": 8,
                    },
                },
            }
        }
