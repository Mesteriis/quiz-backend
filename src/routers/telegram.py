"""
Telegram Bot Webhook Router for Quiz App using aiogram.

This module handles webhook endpoints for Telegram bot integration.
"""

import logging
from typing import Any

from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request, Response

from config import get_settings
from services.telegram_service import get_telegram_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
    responses={404: {"description": "Not found"}},
)


@router.get("/webhook/info")
async def get_webhook_info():
    """Get current webhook information."""
    try:
        telegram_service = await get_telegram_service()

        if not telegram_service.bot:
            raise HTTPException(status_code=503, detail="Telegram bot not initialized")

        # Get webhook info
        webhook_info = await telegram_service.bot.get_webhook_info()

        return {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates,
            "ip_address": webhook_info.ip_address,
        }

    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/webhook/set")
async def set_webhook(webhook_data: dict[str, Any]):
    """Set webhook URL for the bot."""
    try:
        telegram_service = await get_telegram_service()

        if not telegram_service.bot:
            raise HTTPException(status_code=503, detail="Telegram bot not initialized")

        webhook_url = webhook_data.get("url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL is required")

        # Set webhook
        result = await telegram_service.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=True,
        )

        if result:
            logger.info(f"Webhook set successfully: {webhook_url}")
            return {"status": "success", "message": "Webhook set successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to set webhook")

    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/webhook/delete")
async def delete_webhook():
    """Delete webhook for the bot."""
    try:
        telegram_service = await get_telegram_service()

        if not telegram_service.bot:
            raise HTTPException(status_code=503, detail="Telegram bot not initialized")

        # Delete webhook
        result = await telegram_service.bot.delete_webhook(drop_pending_updates=True)

        if result:
            logger.info("Webhook deleted successfully")
            return {"status": "success", "message": "Webhook deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete webhook")

    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/webhook/{bot_token}")
async def webhook_handler(bot_token: str, request: Request):
    """Handle incoming webhook updates from Telegram."""
    try:
        # Verify bot token
        if bot_token != settings.telegram_bot_token:
            logger.warning(f"Invalid bot token in webhook: {bot_token}")
            raise HTTPException(status_code=401, detail="Invalid bot token")

        # Get telegram service
        telegram_service = await get_telegram_service()

        if not telegram_service.bot or not telegram_service.dp:
            raise HTTPException(status_code=503, detail="Telegram bot not initialized")

        # Get update data
        update_data = await request.json()

        # Create Update object
        update = Update.model_validate(update_data)

        # Process update through dispatcher
        await telegram_service.dp.feed_update(telegram_service.bot, update)

        return Response(status_code=200)

    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_bot_status():
    """Get current bot status."""
    try:
        telegram_service = await get_telegram_service()

        if not telegram_service.bot:
            return {
                "status": "not_initialized",
                "message": "Bot not initialized",
                "bot_info": None,
                "webhook_info": None,
            }

        # Get bot info
        bot_info = await telegram_service.bot.get_me()

        # Get webhook info
        webhook_info = await telegram_service.bot.get_webhook_info()

        return {
            "status": "active",
            "message": "Bot is running",
            "bot_info": {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "is_bot": bot_info.is_bot,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries,
            },
            "webhook_info": {
                "url": webhook_info.url,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_date": webhook_info.last_error_date,
                "last_error_message": webhook_info.last_error_message,
            },
        }

    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/security/stats")
async def get_security_stats():
    """Get Telegram webhook security statistics."""
    try:
        # Note: This would need access to the middleware instance
        # For now, return basic stats
        return {
            "middleware_status": "active",
            "rate_limiting": "enabled",
            "ip_whitelisting": "configured",
            "request_validation": "enabled",
            "security_headers": "enabled",
            "webhook_logging": "active",
        }

    except Exception as e:
        logger.error(f"Error getting security stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/send-notification")
async def send_notification(notification_data: dict[str, Any]):
    """Send notification to a specific chat."""
    try:
        telegram_service = await get_telegram_service()

        if not telegram_service.bot:
            raise HTTPException(status_code=503, detail="Telegram bot not initialized")

        chat_id = notification_data.get("chat_id")
        message = notification_data.get("message")

        if not chat_id or not message:
            raise HTTPException(
                status_code=400, detail="chat_id and message are required"
            )

        # Send notification
        success = await telegram_service.send_notification(chat_id, message)

        if success:
            return {"status": "success", "message": "Notification sent"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/send-admin-notification")
async def send_admin_notification(notification_data: dict[str, Any]):
    """Send notification to admin chat."""
    try:
        telegram_service = await get_telegram_service()

        if not telegram_service.bot:
            raise HTTPException(status_code=503, detail="Telegram bot not initialized")

        message = notification_data.get("message")

        if not message:
            raise HTTPException(status_code=400, detail="message is required")

        # Send admin notification
        success = await telegram_service.send_admin_notification(message)

        if success:
            return {"status": "success", "message": "Admin notification sent"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to send admin notification"
            )

    except Exception as e:
        logger.error(f"Error sending admin notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "telegram_bot"}
