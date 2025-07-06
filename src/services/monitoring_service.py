"""
Monitoring and Analytics Service for Quiz App.

This module provides comprehensive monitoring including:
- Performance metrics
- User behavior analytics
- System health monitoring
- Real-time dashboards
- Alerts and notifications
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any, Optional

from sqlalchemy import func, select

from database import get_async_session
from models.question import Question
from models.response import Response
from models.survey import Survey
from models.user import User

logger = logging.getLogger(__name__)

try:
    from services.redis_service import get_redis_service

    REDIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Redis service not available: {e}")
    REDIS_AVAILABLE = False

    def get_redis_service():
        return None


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data structure."""

    name: str
    value: float
    type: MetricType
    timestamp: datetime
    tags: dict[str, str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    resolved: bool = False
    metadata: dict[str, Any] = None


class MonitoringService:
    """Service for monitoring and analytics."""

    def __init__(self):
        self.metrics: list[Metric] = []
        self.alerts: list[Alert] = []
        self.performance_data: dict[str, list[float]] = {}
        self.user_analytics: dict[str, Any] = {}
        self.system_stats: dict[str, Any] = {}

        # Performance thresholds
        self.thresholds = {
            "response_time_ms": 1000,
            "error_rate_percent": 5.0,
            "memory_usage_percent": 85.0,
            "active_connections": 1000,
        }

    async def track_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: dict[str, str] = None,
    ):
        """Track a metric."""
        try:
            metric = Metric(
                name=name,
                value=value,
                type=metric_type,
                timestamp=datetime.now(),
                tags=tags or {},
            )

            self.metrics.append(metric)

            # Store in Redis for persistence
            redis_service = await get_redis_service()
            if redis_service:
                await redis_service.set_hash(
                    f"metric:{name}:{int(time.time())}",
                    metric.to_dict(),
                    ttl=86400,  # 24 hours
                )

            # Check for alerts
            await self._check_metric_alerts(metric)

            # Maintain metrics list size
            if len(self.metrics) > 10000:
                self.metrics = self.metrics[-8000:]  # Keep last 8000

        except Exception as e:
            logger.error(f"Error tracking metric {name}: {e}")

    async def track_user_action(
        self, user_id: int, action: str, metadata: dict[str, Any] = None
    ):
        """Track user action for analytics."""
        try:
            redis_service = await get_redis_service()
            if not redis_service:
                return

            # Increment action counter
            await redis_service.increment_counter(f"user_action:{action}", ttl=86400)
            await redis_service.increment_counter("user_action:total", ttl=86400)

            # Track per-user actions
            user_key = f"user_analytics:{user_id}"
            current_data = await redis_service.get_hash(user_key)

            action_count = int(current_data.get(action, 0)) + 1
            current_data[action] = str(action_count)
            current_data["last_action"] = action
            current_data["last_seen"] = datetime.now().isoformat()

            await redis_service.set_hash(user_key, current_data, ttl=604800)  # 7 days

            # Track hourly analytics
            hour_key = f"analytics:hourly:{datetime.now().strftime('%Y%m%d%H')}"
            await redis_service.increment_counter(hour_key, ttl=172800)  # 48 hours

        except Exception as e:
            logger.error(f"Error tracking user action: {e}")

    async def track_performance(
        self, operation: str, duration_ms: float, status: str = "success"
    ):
        """Track operation performance."""
        try:
            # Add to performance data
            if operation not in self.performance_data:
                self.performance_data[operation] = []

            self.performance_data[operation].append(duration_ms)

            # Keep only last 1000 measurements per operation
            if len(self.performance_data[operation]) > 1000:
                self.performance_data[operation] = self.performance_data[operation][
                    -800:
                ]

            # Track metrics
            await self.track_metric(
                f"performance.{operation}.duration",
                duration_ms,
                MetricType.TIMER,
                {"status": status},
            )

            # Check performance thresholds
            if duration_ms > self.thresholds["response_time_ms"]:
                await self._create_alert(
                    f"slow_operation_{operation}",
                    "Slow operation detected",
                    AlertLevel.WARNING,
                    f"Operation {operation} took {duration_ms}ms (threshold: {self.thresholds['response_time_ms']}ms)",
                )

        except Exception as e:
            logger.error(f"Error tracking performance: {e}")

    async def get_system_health(self) -> dict[str, Any]:
        """Get comprehensive system health status."""
        try:
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "status": "healthy",
                "components": {},
            }

            # Database health
            db_health = await self._check_database_health()
            health_data["components"]["database"] = db_health

            # Redis health
            redis_health = await self._check_redis_health()
            health_data["components"]["redis"] = redis_health

            # Application metrics
            app_metrics = await self._get_application_metrics()
            health_data["components"]["application"] = app_metrics

            # Telegram bot health
            bot_health = await self._check_telegram_bot_health()
            health_data["components"]["telegram_bot"] = bot_health

            # Overall status
            unhealthy_components = [
                name
                for name, comp in health_data["components"].items()
                if comp.get("status") != "healthy"
            ]

            if unhealthy_components:
                health_data["status"] = (
                    "degraded" if len(unhealthy_components) < 2 else "unhealthy"
                )
                health_data["issues"] = unhealthy_components

            return health_data

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
            }

    async def get_user_analytics(self, days: int = 7) -> dict[str, Any]:
        """Get user behavior analytics."""
        try:
            async with get_async_session() as session:
                # Time range
                start_date = datetime.now() - timedelta(days=days)

                # User registrations
                new_users = await session.execute(
                    select(func.count(User.id)).where(User.created_at >= start_date)
                )

                # Active users (with responses)
                active_users = await session.execute(
                    select(func.count(func.distinct(Response.user_id))).where(
                        Response.created_at >= start_date
                    )
                )

                # Survey completions
                survey_completions = await session.execute(
                    select(func.count(func.distinct(Response.user_session_id))).where(
                        Response.created_at >= start_date
                    )
                )

                # Top surveys by responses
                top_surveys = await session.execute(
                    select(
                        Survey.title, func.count(Response.id).label("response_count")
                    )
                    .join(Question)
                    .join(Response)
                    .where(Response.created_at >= start_date)
                    .group_by(Survey.id, Survey.title)
                    .order_by(func.count(Response.id).desc())
                    .limit(5)
                )

                # Get Redis analytics
                redis_service = await get_redis_service()
                redis_analytics = {}

                if redis_service:
                    # User actions from Redis
                    total_actions = await redis_service.get_counter("user_action:total")

                    # Common actions
                    common_actions = {}
                    for action in [
                        "survey_start",
                        "survey_complete",
                        "question_answer",
                        "telegram_interaction",
                    ]:
                        count = await redis_service.get_counter(f"user_action:{action}")
                        if count > 0:
                            common_actions[action] = count

                    redis_analytics = {
                        "total_actions": total_actions,
                        "common_actions": common_actions,
                    }

                return {
                    "period_days": days,
                    "timestamp": datetime.now().isoformat(),
                    "users": {
                        "new_registrations": new_users.scalar() or 0,
                        "active_users": active_users.scalar() or 0,
                    },
                    "surveys": {
                        "completions": survey_completions.scalar() or 0,
                        "top_surveys": [
                            {"title": row.title, "responses": row.response_count}
                            for row in top_surveys
                        ],
                    },
                    "actions": redis_analytics,
                    "performance": await self._get_performance_summary(),
                }

        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {"error": str(e)}

    async def get_real_time_metrics(self) -> dict[str, Any]:
        """Get real-time system metrics."""
        try:
            redis_service = await get_redis_service()

            # Recent metrics (last 5 minutes)
            recent_metrics = [
                m
                for m in self.metrics
                if m.timestamp >= datetime.now() - timedelta(minutes=5)
            ]

            # Active connections from Redis
            active_connections = 0
            if redis_service:
                # Count WebSocket connections
                websocket_keys = await redis_service.redis.keys("websocket:user:*")
                for key in websocket_keys:
                    connections = await redis_service.redis.scard(key)
                    active_connections += connections

            # Error rate (last hour)
            error_metrics = [
                m
                for m in self.metrics
                if m.name.endswith("error")
                and m.timestamp >= datetime.now() - timedelta(hours=1)
            ]

            return {
                "timestamp": datetime.now().isoformat(),
                "active_connections": active_connections,
                "recent_metrics_count": len(recent_metrics),
                "error_rate_last_hour": len(error_metrics),
                "active_alerts": len([a for a in self.alerts if not a.resolved]),
                "memory_usage": await self._get_memory_usage(),
                "performance_avg": await self._get_avg_performance(),
            }

        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {"error": str(e)}

    async def create_custom_dashboard(
        self, name: str, metrics: list[str]
    ) -> dict[str, Any]:
        """Create custom monitoring dashboard."""
        try:
            dashboard_data = {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "metrics": [],
            }

            for metric_name in metrics:
                # Get recent data for this metric
                metric_data = [
                    m
                    for m in self.metrics
                    if m.name == metric_name
                    and m.timestamp >= datetime.now() - timedelta(hours=24)
                ]

                if metric_data:
                    values = [m.value for m in metric_data]
                    dashboard_data["metrics"].append(
                        {
                            "name": metric_name,
                            "current_value": values[-1] if values else 0,
                            "avg_24h": sum(values) / len(values) if values else 0,
                            "min_24h": min(values) if values else 0,
                            "max_24h": max(values) if values else 0,
                            "data_points": len(values),
                        }
                    )

            return dashboard_data

        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return {"error": str(e)}

    async def _check_database_health(self) -> dict[str, Any]:
        """Check database health."""
        try:
            async with get_async_session() as session:
                start_time = time.time()

                # Simple health query
                result = await session.execute(select(func.count(User.id)))
                user_count = result.scalar()

                response_time = (time.time() - start_time) * 1000

                return {
                    "status": "healthy" if response_time < 1000 else "slow",
                    "response_time_ms": round(response_time, 2),
                    "total_users": user_count,
                    "connected": True,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False,
            }

    async def _check_redis_health(self) -> dict[str, Any]:
        """Check Redis health."""
        try:
            redis_service = await get_redis_service()

            if not redis_service or not await redis_service.is_connected():
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Not connected",
                }

            start_time = time.time()
            await redis_service.redis.ping()
            response_time = (time.time() - start_time) * 1000

            cache_stats = await redis_service.get_cache_stats()

            return {
                "status": "healthy" if response_time < 100 else "slow",
                "response_time_ms": round(response_time, 2),
                "connected": True,
                **cache_stats,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False,
            }

    async def _get_application_metrics(self) -> dict[str, Any]:
        """Get application-specific metrics."""
        try:
            return {
                "status": "healthy",
                "total_metrics": len(self.metrics),
                "active_alerts": len([a for a in self.alerts if not a.resolved]),
                "uptime_seconds": int(time.time()),  # Simplified
                "performance_operations": len(self.performance_data),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def _check_telegram_bot_health(self) -> dict[str, Any]:
        """Check Telegram bot health."""
        try:
            from services.telegram_service import get_telegram_service

            telegram_service = await get_telegram_service()

            if not telegram_service.bot:
                return {
                    "status": "unhealthy",
                    "error": "Bot not initialized",
                    "connected": False,
                }

            # Simple bot health check
            start_time = time.time()
            bot_info = await telegram_service.bot.get_me()
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy" if response_time < 2000 else "slow",
                "response_time_ms": round(response_time, 2),
                "bot_username": bot_info.username,
                "connected": True,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False,
            }

    async def _check_metric_alerts(self, metric: Metric):
        """Check if metric triggers any alerts."""
        try:
            # Example alert rules
            if (
                metric.name == "response_time"
                and metric.value > self.thresholds["response_time_ms"]
            ):
                await self._create_alert(
                    "high_response_time",
                    "High Response Time",
                    AlertLevel.WARNING,
                    f"Response time {metric.value}ms exceeds threshold {self.thresholds['response_time_ms']}ms",
                )

            elif (
                metric.name == "error_rate"
                and metric.value > self.thresholds["error_rate_percent"]
            ):
                await self._create_alert(
                    "high_error_rate",
                    "High Error Rate",
                    AlertLevel.ERROR,
                    f"Error rate {metric.value}% exceeds threshold {self.thresholds['error_rate_percent']}%",
                )

        except Exception as e:
            logger.error(f"Error checking metric alerts: {e}")

    async def _create_alert(
        self, alert_id: str, name: str, level: AlertLevel, message: str
    ):
        """Create a new alert."""
        try:
            # Check if alert already exists and is not resolved
            existing_alert = next(
                (a for a in self.alerts if a.id == alert_id and not a.resolved), None
            )

            if existing_alert:
                return  # Don't create duplicate alerts

            alert = Alert(
                id=alert_id,
                name=name,
                level=level,
                message=message,
                timestamp=datetime.now(),
                resolved=False,
                metadata={},
            )

            self.alerts.append(alert)

            # Store in Redis
            redis_service = await get_redis_service()
            if redis_service:
                await redis_service.set_hash(
                    f"alert:{alert_id}",
                    asdict(alert),
                    ttl=604800,  # 7 days
                )

            logger.warning(f"Alert created: {name} - {message}")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    async def _get_performance_summary(self) -> dict[str, Any]:
        """Get performance metrics summary."""
        try:
            summary = {}

            for operation, durations in self.performance_data.items():
                if durations:
                    summary[operation] = {
                        "avg_ms": round(sum(durations) / len(durations), 2),
                        "min_ms": round(min(durations), 2),
                        "max_ms": round(max(durations), 2),
                        "count": len(durations),
                    }

            return summary

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

    async def _get_memory_usage(self) -> dict[str, Any]:
        """Get memory usage information."""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2),
            }

        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"error": str(e)}

    async def _get_avg_performance(self) -> dict[str, float]:
        """Get average performance across all operations."""
        try:
            all_durations = []
            for durations in self.performance_data.values():
                all_durations.extend(durations)

            if all_durations:
                return {
                    "avg_ms": round(sum(all_durations) / len(all_durations), 2),
                    "total_operations": len(all_durations),
                }

            return {"avg_ms": 0, "total_operations": 0}

        except Exception as e:
            logger.error(f"Error getting avg performance: {e}")
            return {"avg_ms": 0, "total_operations": 0}


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create monitoring service instance."""
    global _monitoring_service

    if _monitoring_service is None:
        _monitoring_service = MonitoringService()

    return _monitoring_service
