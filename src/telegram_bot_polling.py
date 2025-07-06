#!/usr/bin/env python3
"""
Telegram Bot Polling Script for Quiz App using aiogram.

This script runs the Telegram bot in polling mode for local development.
For production, use webhook mode instead.

Usage:
    python backend/telegram_bot_polling.py
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import get_settings
from services.telegram_service import get_telegram_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("telegram_bot.log"),
    ],
)
logger = logging.getLogger(__name__)

# Reduce noise from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.INFO)


async def main():
    """Main function to run the Telegram bot."""
    settings = get_settings()

    if not settings.telegram_bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not configured in environment variables")
        logger.error("Please add TELEGRAM_BOT_TOKEN to your .env file")
        return

    logger.info("🚀 Starting Quiz App Telegram Bot in polling mode...")
    logger.info(f"📋 Bot token: {settings.telegram_bot_token[:10]}...")

    try:
        # Get the telegram service
        telegram_service = await get_telegram_service()

        if not telegram_service.bot:
            logger.error("❌ Failed to initialize Telegram bot")
            return

        # Start polling
        await telegram_service.start_polling()

    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")
        logger.exception("Full traceback:")
    finally:
        logger.info("🔄 Cleaning up...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
