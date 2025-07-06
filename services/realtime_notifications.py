"""
Realtime Notifications Service for Quiz App.

This module provides realtime push notifications through multiple channels:
- WebSocket connections for web clients
- Telegram bot messages
- Push notifications for PWA
- Email notifications
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_async_session
from models.user import User
from models.survey import Survey
from models.question import Question
from models.response import Response
from services.telegram_service import get_telegram_service
from services.push_notification_service import send_push_notification

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationType(str, Enum):
    """Types of notifications."""

    NEW_SURVEY = "new_survey"
    SURVEY_COMPLETED = "survey_completed"
    SURVEY_REMINDER = "survey_reminder"
    ADMIN_ALERT = "admin_alert"
    SYSTEM_MESSAGE = "system_message"
    USER_JOINED = "user_joined"
    SURVEY_STATISTICS = "survey_statistics"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    WEBSOCKET = "websocket"
    TELEGRAM = "telegram"
    PUSH = "push"
    EMAIL = "email"
    ALL = "all"


@dataclass
class Notification:
    """Notification data structure."""

    id: str
    type: NotificationType
    title: str
    message: str
    user_id: int | None = None
    survey_id: int | None = None
    channels: List[NotificationChannel] = None
    data: Dict[str, Any] = None
    created_at: datetime = None
    expires_at: datetime = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(hours=24)
        if self.channels is None:
            self.channels = [NotificationChannel.ALL]
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["expires_at"] = self.expires_at.isoformat()
        return data


class ConnectionManager:
    """Manages WebSocket connections for realtime notifications."""

    def __init__(self):
        # Active connections: user_id -> WebSocket
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Connection metadata: WebSocket -> user info
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(
        self, websocket: WebSocket, user_id: int, user_info: Dict[str, Any] = None
    ):
        """Connect a new WebSocket client."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "user_info": user_info or {},
        }

        logger.info(f"WebSocket client connected - User ID: {user_id}")

        # Send connection confirmation
        await self.send_personal_message(
            {
                "type": "connection_established",
                "message": "Realtime notifications connected",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
            user_id,
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.connection_metadata:
            user_id = self.connection_metadata[websocket]["user_id"]

            # Remove from active connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # Remove metadata
            del self.connection_metadata[websocket]

            logger.info(f"WebSocket client disconnected - User ID: {user_id}")

    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """Send message to specific user's connections."""
        if user_id in self.active_connections:
            disconnected_connections = set()

            for connection in self.active_connections[user_id].copy():
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    disconnected_connections.add(connection)

            # Clean up disconnected connections
            for connection in disconnected_connections:
                self.disconnect(connection)

    async def broadcast_message(
        self, message: Dict[str, Any], exclude_user_ids: Set[int] = None
    ):
        """Broadcast message to all connected users."""
        exclude_user_ids = exclude_user_ids or set()

        for user_id, connections in self.active_connections.items():
            if user_id not in exclude_user_ids:
                await self.send_personal_message(message, user_id)

    async def send_to_admins(self, message: Dict[str, Any]):
        """Send message to all connected admin users."""
        # This would need to check user roles in database
        # For now, we'll implement basic version
        admin_message = {**message, "admin_only": True}
        await self.broadcast_message(admin_message)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": sum(
                len(connections) for connections in self.active_connections.values()
            ),
            "unique_users": len(self.active_connections),
            "connection_details": {
                user_id: len(connections)
                for user_id, connections in self.active_connections.items()
            },
        }


class RealtimeNotificationService:
    """Service for managing realtime notifications across multiple channels."""

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.notification_queue: List[Notification] = []
        self.notification_history: List[Notification] = []
        self.max_history_size = 1000

    async def send_notification(self, notification: Notification) -> Dict[str, bool]:
        """Send notification through specified channels."""
        results = {}

        try:
            # Add to queue and history
            self.notification_queue.append(notification)
            self._add_to_history(notification)

            # Send through each channel
            if (
                NotificationChannel.ALL in notification.channels
                or NotificationChannel.WEBSOCKET in notification.channels
            ):
                results["websocket"] = await self._send_websocket_notification(
                    notification
                )

            if (
                NotificationChannel.ALL in notification.channels
                or NotificationChannel.TELEGRAM in notification.channels
            ):
                results["telegram"] = await self._send_telegram_notification(
                    notification
                )

            if (
                NotificationChannel.ALL in notification.channels
                or NotificationChannel.PUSH in notification.channels
            ):
                results["push"] = await self._send_push_notification(notification)

            logger.info(f"Notification sent: {notification.id} - Results: {results}")
            return results

        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {e}")
            return {"error": str(e)}

    async def _send_websocket_notification(self, notification: Notification) -> bool:
        """Send notification via WebSocket."""
        try:
            message = {"type": "notification", "notification": notification.to_dict()}

            if notification.user_id:
                # Send to specific user
                await self.connection_manager.send_personal_message(
                    message, notification.user_id
                )
            else:
                # Broadcast to all users
                await self.connection_manager.broadcast_message(message)

            return True

        except Exception as e:
            logger.error(f"WebSocket notification error: {e}")
            return False

    async def _send_telegram_notification(self, notification: Notification) -> bool:
        """Send notification via Telegram bot."""
        try:
            telegram_service = await get_telegram_service()

            if notification.user_id:
                # Send to specific user
                async with get_async_session() as session:
                    stmt = select(User).where(User.id == notification.user_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()

                    if user and user.telegram_id:
                        message = (
                            f"🔔 <b>{notification.title}</b>\n\n{notification.message}"
                        )
                        return await telegram_service.send_notification(
                            user.telegram_id, message
                        )
            else:
                # Send to admin chat
                admin_message = (
                    f"📢 <b>{notification.title}</b>\n\n{notification.message}"
                )
                return await telegram_service.send_admin_notification(admin_message)

            return False

        except Exception as e:
            logger.error(f"Telegram notification error: {e}")
            return False

    async def _send_push_notification(self, notification: Notification) -> bool:
        """Send push notification for PWA."""
        try:
            if notification.user_id:
                # Send to specific user's devices
                async with get_async_session() as session:
                    stmt = select(User).where(User.id == notification.user_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()

                    if user:
                        push_data = {
                            "title": notification.title,
                            "body": notification.message,
                            "data": notification.data,
                        }
                        # This would use the push notification service
                        # return await send_push_notification(user, push_data)
                        return True

            return False

        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return False

    def _add_to_history(self, notification: Notification):
        """Add notification to history."""
        self.notification_history.append(notification)

        # Maintain max history size
        if len(self.notification_history) > self.max_history_size:
            self.notification_history = self.notification_history[
                -self.max_history_size :
            ]

    async def create_survey_notification(
        self, survey_id: int, user_id: int | None = None
    ) -> Notification:
        """Create notification for new survey."""
        async with get_async_session() as session:
            stmt = select(Survey).where(Survey.id == survey_id)
            result = await session.execute(stmt)
            survey = result.scalar_one_or_none()

            if survey:
                return Notification(
                    type=NotificationType.NEW_SURVEY,
                    title="Новый опрос доступен!",
                    message=f"📋 {survey.title}\n\n{survey.description or 'Пройдите новый опрос'}",
                    user_id=user_id,
                    survey_id=survey_id,
                    data={"survey_id": survey_id, "survey_title": survey.title},
                )

    async def create_completion_notification(
        self, survey_id: int, user_id: int
    ) -> Notification:
        """Create notification for survey completion."""
        async with get_async_session() as session:
            # Get survey info
            stmt = select(Survey).where(Survey.id == survey_id)
            result = await session.execute(stmt)
            survey = result.scalar_one_or_none()

            # Count user's responses
            response_stmt = select(Response).where(
                and_(
                    Response.user_id == user_id,
                    Response.question_id.in_(
                        select(Question.id).where(Question.survey_id == survey_id)
                    ),
                )
            )
            response_result = await session.execute(response_stmt)
            responses = response_result.scalars().all()

            if survey:
                return Notification(
                    type=NotificationType.SURVEY_COMPLETED,
                    title="Опрос завершен!",
                    message=f"Спасибо за участие в опросе '{survey.title}'!\n"
                    f"Дано ответов: {len(responses)}",
                    user_id=user_id,
                    survey_id=survey_id,
                    channels=[
                        NotificationChannel.TELEGRAM,
                        NotificationChannel.WEBSOCKET,
                    ],
                    data={
                        "survey_id": survey_id,
                        "survey_title": survey.title,
                        "responses_count": len(responses),
                    },
                )

    async def create_admin_alert(
        self, message: str, data: Dict[str, Any] = None
    ) -> Notification:
        """Create admin alert notification."""
        return Notification(
            type=NotificationType.ADMIN_ALERT,
            title="Административное уведомление",
            message=message,
            channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBSOCKET],
            data=data or {},
        )

    def get_user_notifications(
        self, user_id: int, limit: int = 50
    ) -> List[Notification]:
        """Get recent notifications for user."""
        user_notifications = [
            n
            for n in self.notification_history
            if n.user_id == user_id or n.user_id is None
        ]
        return sorted(user_notifications, key=lambda x: x.created_at, reverse=True)[
            :limit
        ]

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        return {
            "total_notifications": len(self.notification_history),
            "queued_notifications": len(self.notification_queue),
            "notification_types": {
                nt.value: len([n for n in self.notification_history if n.type == nt])
                for nt in NotificationType
            },
            "websocket_stats": self.connection_manager.get_stats(),
        }


# Global service instance
_notification_service: Optional[RealtimeNotificationService] = None


def get_notification_service() -> RealtimeNotificationService:
    """Get or create notification service instance."""
    global _notification_service

    if _notification_service is None:
        _notification_service = RealtimeNotificationService()

    return _notification_service
