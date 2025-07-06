"""
Main FastAPI application for Quiz App.

This is the entry point for the Quiz application with all routers,
middleware, and startup/shutdown events configured.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from database import create_db_and_tables, close_db_connection
from middleware import get_telegram_middleware, get_ip_whitelist_middleware


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan management.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting up Quiz App...")

    # Create database tables
    await create_db_and_tables()
    logger.info("Database tables created/verified")

    # Initialize Telegram service
    try:
        from services.telegram_service import get_telegram_service

        telegram_service = await get_telegram_service()
        if telegram_service.bot:
            logger.info("Telegram bot initialized successfully")
        else:
            logger.warning("Telegram bot not initialized (token may be missing)")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram service: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Quiz App...")

    # Stop Telegram service
    try:
        telegram_service = await get_telegram_service()
        await telegram_service.stop_polling()
        logger.info("Telegram service stopped")
    except Exception as e:
        logger.error(f"Error stopping Telegram service: {e}")

    await close_db_connection()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Interactive Quiz Application with Telegram integration",
    docs_url=settings.docs_url if settings.is_development else None,
    redoc_url=settings.redoc_url if settings.is_development else None,
    lifespan=lifespan,
)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address, default_limits=["1000/hour", "20/minute"]
)
app.state.limiter = limiter
# Add middleware in correct order (reverse order of execution)
app.add_middleware(SlowAPIMiddleware)

# Add Telegram security middleware
telegram_middleware = get_telegram_middleware()
app.add_middleware(telegram_middleware)

# Add IP whitelist middleware for Telegram
ip_whitelist_middleware = get_ip_whitelist_middleware()
app.add_middleware(ip_whitelist_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup Jinja2 templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": f"Welcome to {settings.app_name}!",
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    from database import check_db_health

    db_healthy = await check_db_health()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# Include API routers
from routers import (
    surveys,
    responses,
    user_data,
    validation,
    auth,
    admin,
    reports,
    telegram,
    notifications,
)

# Monitoring router temporarily disabled due to Redis issues
try:
    from routers import monitoring

    MONITORING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Monitoring router disabled: {e}")
    MONITORING_AVAILABLE = False
    monitoring = None

app.include_router(
    auth.router, prefix=f"{settings.api_prefix}/auth", tags=["authentication"]
)
app.include_router(
    surveys.router, prefix=f"{settings.api_prefix}/surveys", tags=["surveys"]
)
app.include_router(
    responses.router, prefix=f"{settings.api_prefix}/responses", tags=["responses"]
)
app.include_router(
    user_data.router, prefix=f"{settings.api_prefix}/user-data", tags=["user-data"]
)
app.include_router(
    validation.router, prefix=f"{settings.api_prefix}/validation", tags=["validation"]
)
app.include_router(
    admin.router, prefix=f"{settings.api_prefix}/admin", tags=["administration"]
)
app.include_router(
    reports.router, prefix=f"{settings.api_prefix}/reports", tags=["reports"]
)
app.include_router(telegram.router, tags=["telegram"])  # Uses its own prefix
app.include_router(
    notifications.router, prefix=f"{settings.api_prefix}", tags=["notifications"]
)
if MONITORING_AVAILABLE and monitoring:
    app.include_router(
        monitoring.router, prefix=f"{settings.api_prefix}", tags=["monitoring"]
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
