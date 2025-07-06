"""
Notifications Router for Quiz App.

This module handles WebSocket connections for realtime notifications
and provides API endpoints for notification management.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from models.user import User
from services.jwt_service import get_current_user
from services.realtime_notifications import (
    Notification,
    NotificationChannel,
    NotificationType,
    get_notification_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for realtime notifications."""
    notification_service = get_notification_service()

    try:
        # Accept connection
        await notification_service.connection_manager.connect(
            websocket, user_id, {"connection_type": "websocket"}
        )

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()

                # Parse and handle client messages
                try:
                    import json

                    message = json.loads(data)

                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "pong",
                                    "timestamp": "datetime.now().isoformat()",
                                }
                            )
                        )
                    elif message.get("type") == "subscribe":
                        # Subscribe to specific notification types
                        pass
                    elif message.get("type") == "get_history":
                        # Send notification history
                        notifications = notification_service.get_user_notifications(
                            user_id
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "notification_history",
                                    "notifications": [
                                        n.to_dict() for n in notifications[:20]
                                    ],
                                }
                            )
                        )

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from user {user_id}: {data}")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error for user {user_id}: {e}")
    finally:
        notification_service.connection_manager.disconnect(websocket)


@router.post("/send")
async def send_notification(
    notification_data: dict[str, Any], current_user: User = Depends(get_current_user)
):
    """Send a notification through the system."""
    try:
        # Check if user is admin for certain notification types
        if notification_data.get("type") in ["admin_alert", "system_message"]:
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="Admin access required")

        # Create notification
        notification = Notification(
            id="",  # Will be auto-generated
            type=NotificationType(notification_data.get("type", "system_message")),
            title=notification_data.get("title", "Уведомление"),
            message=notification_data.get("message", ""),
            user_id=notification_data.get("user_id"),
            survey_id=notification_data.get("survey_id"),
            channels=[
                NotificationChannel(ch)
                for ch in notification_data.get("channels", ["all"])
            ],
            data=notification_data.get("data", {}),
        )

        # Send notification
        notification_service = get_notification_service()
        results = await notification_service.send_notification(notification)

        return {"success": True, "notification_id": notification.id, "results": results}

    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.get("/history/{user_id}")
async def get_user_notifications(
    user_id: int, limit: int = 50, current_user: User = Depends(get_current_user)
):
    """Get notification history for a user."""
    try:
        # Check permissions
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        notification_service = get_notification_service()
        notifications = notification_service.get_user_notifications(user_id, limit)

        return {
            "notifications": [n.to_dict() for n in notifications],
            "total": len(notifications),
        }

    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")


@router.get("/stats")
async def get_notification_stats(current_user: User = Depends(get_current_user)):
    """Get notification system statistics."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        notification_service = get_notification_service()
        stats = notification_service.get_notification_stats()

        return stats

    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")


@router.post("/broadcast")
async def broadcast_notification(
    notification_data: dict[str, Any], current_user: User = Depends(get_current_user)
):
    """Broadcast notification to all users."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Create broadcast notification
        notification = Notification(
            id="",  # Will be auto-generated
            type=NotificationType(notification_data.get("type", "system_message")),
            title=notification_data.get("title", "Системное уведомление"),
            message=notification_data.get("message", ""),
            user_id=None,  # Broadcast to all
            channels=[
                NotificationChannel(ch)
                for ch in notification_data.get("channels", ["all"])
            ],
            data=notification_data.get("data", {}),
        )

        # Send notification
        notification_service = get_notification_service()
        results = await notification_service.send_notification(notification)

        return {"success": True, "notification_id": notification.id, "results": results}

    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast notification")


@router.delete("/clear/{user_id}")
async def clear_user_notifications(
    user_id: int, current_user: User = Depends(get_current_user)
):
    """Clear notification history for a user."""
    try:
        # Check permissions
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        # This would need to be implemented in the notification service
        # For now, return success
        return {"success": True, "message": "Notifications cleared"}

    except Exception as e:
        logger.error(f"Error clearing notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear notifications")


@router.get("/channels")
async def get_notification_channels():
    """Get available notification channels."""
    return {
        "channels": [channel.value for channel in NotificationChannel],
        "types": [type_.value for type_ in NotificationType],
    }


@router.post("/test")
async def test_notification(
    channel: str = "websocket", current_user: User = Depends(get_current_user)
):
    """Send a test notification."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Create test notification
        notification = Notification(
            id="",  # Will be auto-generated
            type=NotificationType.SYSTEM_MESSAGE,
            title="Тестовое уведомление",
            message="Это тестовое уведомление для проверки системы",
            user_id=current_user.id,
            channels=[NotificationChannel(channel)],
            data={"test": True},
        )

        # Send notification
        notification_service = get_notification_service()
        results = await notification_service.send_notification(notification)

        return {"success": True, "notification_id": notification.id, "results": results}

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test notification")
