"""
Telegram Webhook Middleware for Quiz App.

This module provides middleware for Telegram webhook security, logging,
rate limiting, and request validation.
"""

from collections import defaultdict
from datetime import datetime, timedelta
import json
import logging
import time
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramWebhookMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Telegram webhook security and monitoring.

    Features:
    - Request validation
    - Rate limiting
    - IP whitelisting
    - Request logging
    - Error handling
    - Security headers
    """

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.request_counter: dict[str, list] = defaultdict(list)
        self.blocked_ips: dict[str, datetime] = {}
        self.max_requests_per_minute = 20
        self.max_requests_per_hour = 1000
        self.block_duration = timedelta(minutes=10)

        # Telegram IP ranges (approximate)
        self.telegram_ip_ranges = [
            "149.154.160.0/20",
            "91.108.4.0/22",
            "91.108.8.0/22",
            "91.108.12.0/22",
            "91.108.16.0/22",
            "91.108.20.0/22",
            "91.108.56.0/22",
            "149.154.164.0/22",
            "149.154.168.0/22",
            "149.154.172.0/22",
        ]

        logger.info("Telegram webhook middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Process incoming webhook requests."""
        start_time = time.time()
        client_ip = get_remote_address(request)

        try:
            # Check if IP is blocked
            if self._is_ip_blocked(client_ip):
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                return JSONResponse(status_code=403, content={"error": "Access denied"})

            # Only apply security checks to webhook endpoints
            if "/telegram/webhook/" in str(request.url):
                # Validate webhook request
                validation_result = await self._validate_webhook_request(request)
                if not validation_result["valid"]:
                    logger.warning(
                        f"Invalid webhook request from {client_ip}: {validation_result['error']}"
                    )
                    return JSONResponse(
                        status_code=400, content={"error": "Invalid request"}
                    )

                # Check rate limits
                if self._check_rate_limit(client_ip):
                    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                    return JSONResponse(
                        status_code=429, content={"error": "Rate limit exceeded"}
                    )

                # Log webhook request
                await self._log_webhook_request(request, client_ip)

            # Process request
            response = await call_next(request)

            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request processed in {process_time:.3f}s - {client_ip} - {response.status_code}"
            )

            return response

        except Exception as e:
            logger.error(f"Middleware error: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Internal server error"}
            )

    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is temporarily blocked."""
        if ip in self.blocked_ips:
            if datetime.now() - self.blocked_ips[ip] < self.block_duration:
                return True
            else:
                # Remove expired block
                del self.blocked_ips[ip]
        return False

    def _check_rate_limit(self, ip: str) -> bool:
        """Check if IP has exceeded rate limits."""
        now = datetime.now()

        # Clean old requests
        self.request_counter[ip] = [
            req_time
            for req_time in self.request_counter[ip]
            if now - req_time < timedelta(hours=1)
        ]

        # Check minute limit
        minute_requests = [
            req_time
            for req_time in self.request_counter[ip]
            if now - req_time < timedelta(minutes=1)
        ]

        if len(minute_requests) >= self.max_requests_per_minute:
            self.blocked_ips[ip] = now
            return True

        # Check hourly limit
        if len(self.request_counter[ip]) >= self.max_requests_per_hour:
            self.blocked_ips[ip] = now
            return True

        # Add current request
        self.request_counter[ip].append(now)
        return False

    async def _validate_webhook_request(self, request: Request) -> dict[str, Any]:
        """Validate webhook request authenticity."""
        try:
            # Check content type
            if request.headers.get("content-type") != "application/json":
                return {"valid": False, "error": "Invalid content type"}

            # Get request body
            body = await request.body()
            if not body:
                return {"valid": False, "error": "Empty request body"}

            # Try to parse JSON
            try:
                json_data = json.loads(body)
            except json.JSONDecodeError:
                return {"valid": False, "error": "Invalid JSON"}

            # Check required Telegram fields
            if "update_id" not in json_data:
                return {"valid": False, "error": "Missing update_id"}

            # Basic structure validation
            if not any(
                key in json_data
                for key in ["message", "callback_query", "inline_query"]
            ):
                return {"valid": False, "error": "Invalid update structure"}

            return {"valid": True, "error": None}

        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return {"valid": False, "error": "Validation failed"}

    async def _log_webhook_request(self, request: Request, client_ip: str):
        """Log webhook request details."""
        try:
            body = await request.body()
            data = json.loads(body) if body else {}

            # Extract relevant info
            update_id = data.get("update_id", "unknown")
            message_type = "unknown"

            if "message" in data:
                message_type = "message"
            elif "callback_query" in data:
                message_type = "callback_query"
            elif "inline_query" in data:
                message_type = "inline_query"

            # Log request
            logger.info(
                f"Webhook request - IP: {client_ip}, "
                f"Update ID: {update_id}, "
                f"Type: {message_type}, "
                f"Size: {len(body)} bytes"
            )

        except Exception as e:
            logger.error(f"Webhook logging error: {e}")

    def get_security_stats(self) -> dict[str, Any]:
        """Get security statistics."""
        return {
            "active_rate_limits": len(self.request_counter),
            "blocked_ips": len(self.blocked_ips),
            "total_requests": sum(len(reqs) for reqs in self.request_counter.values()),
            "middleware_status": "active",
        }


class TelegramIPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP whitelist middleware for Telegram webhooks.

    Only allows requests from Telegram's IP ranges.
    """

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.enabled = getattr(settings, "telegram_ip_whitelist_enabled", False)

        if self.enabled:
            logger.info("Telegram IP whitelist middleware enabled")
        else:
            logger.info("Telegram IP whitelist middleware disabled")

    async def dispatch(self, request: Request, call_next):
        """Check IP whitelist for webhook requests."""
        if not self.enabled:
            return await call_next(request)

        # Only check webhook endpoints
        if "/telegram/webhook/" not in str(request.url):
            return await call_next(request)

        client_ip = get_remote_address(request)

        # Check if IP is in Telegram ranges (simplified check)
        if not self._is_telegram_ip(client_ip):
            logger.warning(f"Non-Telegram IP attempted webhook access: {client_ip}")
            return JSONResponse(status_code=403, content={"error": "Access denied"})

        return await call_next(request)

    def _is_telegram_ip(self, ip: str) -> bool:
        """Check if IP belongs to Telegram (simplified)."""
        # This is a simplified check - in production, use proper IP range validation
        telegram_prefixes = [
            "149.154.",
            "91.108.",
            "127.0.0.1",  # For local testing
            "localhost",
        ]

        return any(ip.startswith(prefix) for prefix in telegram_prefixes)


class TelegramRequestLogger:
    """
    Advanced request logger for Telegram webhook debugging.
    """

    def __init__(self):
        self.logger = logging.getLogger("telegram_webhook")
        self.logger.setLevel(logging.INFO)

        # Create file handler for webhook logs
        handler = logging.FileHandler("telegram_webhook.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    async def log_request(
        self, request: Request, response: Response, process_time: float
    ):
        """Log detailed request information."""
        try:
            client_ip = get_remote_address(request)

            log_data = {
                "timestamp": datetime.now().isoformat(),
                "client_ip": client_ip,
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "status_code": response.status_code,
                "process_time": process_time,
                "user_agent": request.headers.get("user-agent", "unknown"),
            }

            # Log request body for webhook endpoints (be careful with sensitive data)
            if "/telegram/webhook/" in str(request.url):
                body = await request.body()
                if body:
                    try:
                        log_data["body_size"] = len(body)
                        # Don't log full body in production for security
                        if getattr(settings, "debug", False):
                            log_data["body"] = json.loads(body)
                    except:
                        pass

            self.logger.info(f"Request: {json.dumps(log_data, indent=2)}")

        except Exception as e:
            self.logger.error(f"Logging error: {e}")


# Rate limiter instance
limiter = Limiter(
    key_func=get_remote_address, default_limits=["1000 per hour", "20 per minute"]
)


def get_telegram_middleware():
    """Get configured Telegram middleware."""
    return TelegramWebhookMiddleware


def get_ip_whitelist_middleware():
    """Get IP whitelist middleware."""
    return TelegramIPWhitelistMiddleware


def get_request_logger():
    """Get request logger instance."""
    return TelegramRequestLogger()
