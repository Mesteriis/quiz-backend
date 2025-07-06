"""
Monitoring API Router for Quiz App.

This module provides API endpoints for monitoring, analytics, and system health.
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from services.monitoring_service import (
        get_monitoring_service,
        MetricType,
        AlertLevel,
    )
    from services.redis_service import get_redis_service

    MONITORING_AVAILABLE = True
except ImportError as e:
    print(f"Monitoring service not available: {e}")
    MONITORING_AVAILABLE = False

    class MetricType:
        pass

    class AlertLevel:
        pass

    async def get_monitoring_service():
        class MockMonitoringService:
            async def get_system_health(self):
                return {"status": "mocked", "error": "Monitoring service not available"}

        return MockMonitoringService()

    async def get_redis_service():
        return None


from services.jwt_service import get_current_user
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MetricRequest(BaseModel):
    """Request model for tracking metrics."""

    name: str
    value: float
    type: str
    tags: Optional[Dict[str, str]] = None


class AlertRequest(BaseModel):
    """Request model for creating alerts."""

    name: str
    level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


class DashboardRequest(BaseModel):
    """Request model for creating dashboards."""

    name: str
    metrics: List[str]


@router.get("/health")
async def get_system_health():
    """Get comprehensive system health status."""
    try:
        monitoring_service = get_monitoring_service()
        health_data = await monitoring_service.get_system_health()

        # Determine HTTP status based on system health
        status_code = 200
        if health_data.get("status") == "degraded":
            status_code = 206  # Partial Content
        elif health_data.get("status") in ["unhealthy", "error"]:
            status_code = 503  # Service Unavailable

        return JSONResponse(content=health_data, status_code=status_code)

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return JSONResponse(
            content={"status": "error", "error": str(e)}, status_code=500
        )


@router.get("/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time system metrics."""
    try:
        monitoring_service = get_monitoring_service()
        metrics = await monitoring_service.get_real_time_metrics()

        return metrics

    except Exception as e:
        logger.error(f"Error getting realtime metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/track")
async def track_metric(
    metric_request: MetricRequest, current_user: User = Depends(get_current_user)
):
    """Track a custom metric."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        monitoring_service = get_monitoring_service()

        # Validate metric type
        try:
            metric_type = MetricType(metric_request.type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid metric type")

        await monitoring_service.track_metric(
            name=metric_request.name,
            value=metric_request.value,
            metric_type=metric_type,
            tags=metric_request.tags,
        )

        return {"success": True, "message": "Metric tracked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/users")
async def get_user_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
):
    """Get user behavior analytics."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        monitoring_service = get_monitoring_service()
        analytics = await monitoring_service.get_user_analytics(days)

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/telegram")
async def get_telegram_analytics(current_user: User = Depends(get_current_user)):
    """Get Telegram bot analytics."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        redis_service = await get_redis_service()
        if not redis_service:
            raise HTTPException(status_code=503, detail="Redis not available")

        # Get Telegram-specific analytics
        telegram_analytics = {
            "bot_interactions": await redis_service.get_counter(
                "telegram:interactions"
            ),
            "commands_used": await redis_service.get_counter("telegram:commands"),
            "surveys_started": await redis_service.get_counter(
                "telegram:surveys_started"
            ),
            "inline_queries": await redis_service.get_counter(
                "telegram:inline_queries"
            ),
            "webhook_requests": await redis_service.get_counter(
                "telegram:webhook_requests"
            ),
        }

        # Get advanced features analytics
        from services.telegram_advanced import get_advanced_service

        advanced_service = get_advanced_service()
        advanced_analytics = advanced_service.get_analytics()

        return {
            "basic_analytics": telegram_analytics,
            "advanced_analytics": advanced_analytics,
            "timestamp": "2024-01-01T00:00:00",  # Current timestamp would be added
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting telegram analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard/create")
async def create_dashboard(
    dashboard_request: DashboardRequest, current_user: User = Depends(get_current_user)
):
    """Create a custom monitoring dashboard."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        monitoring_service = get_monitoring_service()
        dashboard = await monitoring_service.create_custom_dashboard(
            dashboard_request.name, dashboard_request.metrics
        )

        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary")
async def get_performance_summary(current_user: User = Depends(get_current_user)):
    """Get performance metrics summary."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        monitoring_service = get_monitoring_service()

        return {
            "performance_operations": monitoring_service.performance_data,
            "summary": await monitoring_service._get_performance_summary(),
            "average": await monitoring_service._get_avg_performance(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(current_user: User = Depends(get_current_user)):
    """Get active system alerts."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        monitoring_service = get_monitoring_service()

        active_alerts = [
            {
                "id": alert.id,
                "name": alert.name,
                "level": alert.level.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
            }
            for alert in monitoring_service.alerts
            if not alert.resolved
        ]

        return {
            "active_alerts": active_alerts,
            "total_count": len(active_alerts),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, current_user: User = Depends(get_current_user)):
    """Resolve an active alert."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        monitoring_service = get_monitoring_service()

        # Find and resolve alert
        alert = next((a for a in monitoring_service.alerts if a.id == alert_id), None)

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert.resolved = True

        # Update in Redis
        redis_service = await get_redis_service()
        if redis_service:
            from dataclasses import asdict

            await redis_service.set_hash(
                f"alert:{alert_id}",
                asdict(alert),
                ttl=604800,  # 7 days
            )

        return {"success": True, "message": "Alert resolved"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """Get Redis cache statistics."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        redis_service = await get_redis_service()
        if not redis_service:
            raise HTTPException(status_code=503, detail="Redis not available")

        cache_stats = await redis_service.get_cache_stats()

        return cache_stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/flush")
async def flush_cache(
    pattern: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    """Flush Redis cache."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        redis_service = await get_redis_service()
        if not redis_service:
            raise HTTPException(status_code=503, detail="Redis not available")

        success = await redis_service.flush_cache(pattern)

        if success:
            return {
                "success": True,
                "message": f"Cache flushed successfully{' for pattern: ' + pattern if pattern else ''}",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to flush cache")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error flushing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status")
async def get_system_status():
    """Get overall system status (public endpoint)."""
    try:
        monitoring_service = get_monitoring_service()
        health_data = await monitoring_service.get_system_health()

        # Return simplified status for public consumption
        return {
            "status": health_data.get("status", "unknown"),
            "timestamp": health_data.get("timestamp"),
            "components_count": len(health_data.get("components", {})),
            "healthy_components": len(
                [
                    comp
                    for comp in health_data.get("components", {}).values()
                    if comp.get("status") == "healthy"
                ]
            ),
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "status": "error",
            "error": "Unable to determine system status",
            "timestamp": "2024-01-01T00:00:00",
        }
