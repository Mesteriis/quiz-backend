from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlmodel import SQLModel

from .user import User


class PushSubscription(SQLModel, table=True):
    """Модель подписки пользователя на push-уведомления"""

    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Данные подписки от браузера
    endpoint = Column(String(500), nullable=False)
    p256dh_key = Column(String(255), nullable=False)
    auth_key = Column(String(255), nullable=False)

    # Настройки подписки
    enabled_categories = Column(JSON, default=list)  # Список активных категорий
    is_active = Column(Boolean, default=True)

    # Метаданные
    user_agent = Column(String(500))
    browser_name = Column(String(100))
    platform = Column(String(100))

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime)

    # Связи
    user = relationship("User", back_populates="push_subscriptions")
    notifications = relationship("PushNotification", back_populates="subscription")

    def __repr__(self):
        return f"<PushSubscription(user_id={self.user_id}, active={self.is_active})>"


class PushNotification(Base):
    """Модель отправленного push-уведомления"""

    __tablename__ = "push_notifications"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(
        Integer, ForeignKey("push_subscriptions.id"), nullable=False
    )

    # Содержимое уведомления
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    icon = Column(String(500))
    image = Column(String(500))
    url = Column(String(500))

    # Метаданные
    category = Column(String(100), nullable=False)  # quiz_completed, new_response, etc.
    priority = Column(String(50), default="normal")  # low, normal, high, urgent
    tag = Column(String(100))  # Для группировки уведомлений

    # Настройки отображения
    require_interaction = Column(Boolean, default=False)
    silent = Column(Boolean, default=False)
    vibrate_pattern = Column(JSON, default=[100, 50, 100])

    # Статус доставки
    status = Column(String(50), default="pending")  # pending, sent, delivered, failed
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    error_message = Column(Text)

    # Аналитика
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime)
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    subscription = relationship("PushSubscription", back_populates="notifications")

    def __repr__(self):
        return f"<PushNotification(title='{self.title}', category='{self.category}', status='{self.status}')>"


class NotificationTemplate(Base):
    """Модель шаблона уведомления"""

    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Идентификация
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(100), nullable=False)

    # Содержимое шаблона
    title_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)

    # Настройки по умолчанию
    default_icon = Column(String(500))
    default_image = Column(String(500))
    default_url = Column(String(500))

    # Поведение
    default_priority = Column(String(50), default="normal")
    default_require_interaction = Column(Boolean, default=False)
    default_silent = Column(Boolean, default=False)
    default_vibrate_pattern = Column(JSON, default=[100, 50, 100])

    # Метаданные
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NotificationTemplate(name='{self.name}', category='{self.category}')>"


class NotificationAnalytics(Base):
    """Модель аналитики уведомлений"""

    __tablename__ = "notification_analytics"

    id = Column(Integer, primary_key=True, index=True)

    # Идентификация события
    notification_id = Column(
        Integer, ForeignKey("push_notifications.id"), nullable=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Данные события
    event_type = Column(
        String(50), nullable=False
    )  # sent, delivered, clicked, dismissed, failed
    category = Column(String(100))
    browser_name = Column(String(100))
    platform = Column(String(100))

    # Дополнительные данные
    metadata = Column(JSON)
    error_details = Column(Text)

    # Временная метка
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    notification = relationship("PushNotification", foreign_keys=[notification_id])
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<NotificationAnalytics(event_type='{self.event_type}', category='{self.category}')>"


# Обновляем модель User для добавления связи с подписками
def update_user_model():
    """Обновление модели User для связи с push-подписками"""
    if not hasattr(User, "push_subscriptions"):
        User.push_subscriptions = relationship(
            "PushSubscription", back_populates="user", cascade="all, delete-orphan"
        )
