"""
Comprehensive Monitoring Pydantic Schemas for Quiz App.

This module provides Pydantic schemas for monitoring, analytics, and performance tracking.
Includes schemas for metrics, alerts, dashboards, system health, and user analytics.

All schemas follow best practices:
- Type hints with Python 3.11+ syntax
- Field validation and descriptions
- ConfigDict for modern Pydantic
- Proper separation of concerns
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MetricType(str, Enum):
    """Types of metrics for monitoring."""

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


class SystemStatus(str, Enum):
    """System health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    ERROR = "error"


class ComponentStatus(str, Enum):
    """Individual component status."""

    HEALTHY = "healthy"
    SLOW = "slow"
    UNHEALTHY = "unhealthy"
    ERROR = "error"


# ============================================================================
# METRIC SCHEMAS
# ============================================================================


class MetricCreate(BaseModel):
    """Schema for creating metrics."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Metric name", min_length=1, max_length=100)
    value: float = Field(..., description="Metric value")
    type: MetricType = Field(..., description="Metric type")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Metric tags")


class MetricResponse(BaseModel):
    """Schema for metric responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Metric ID")
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    type: MetricType = Field(..., description="Metric type")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Metric tags")
    timestamp: datetime = Field(..., description="Metric timestamp")


class MetricBatch(BaseModel):
    """Schema for batch metric creation."""

    model_config = ConfigDict(from_attributes=True)

    batch_id: Optional[str] = Field(default=None, description="Batch ID")
    metrics: List[MetricCreate] = Field(..., description="List of metrics to create")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Batch metadata"
    )


# ============================================================================
# ALERT SCHEMAS
# ============================================================================


class AlertCreate(BaseModel):
    """Schema for creating alerts."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Alert name", min_length=1, max_length=100)
    description: str = Field(
        ..., description="Alert description", min_length=1, max_length=500
    )
    metric_name: str = Field(..., description="Metric name for alert")
    threshold: float = Field(..., description="Alert threshold value")
    level: AlertLevel = Field(..., description="Alert severity level")
    conditions: Dict[str, Any] = Field(..., description="Alert conditions")


class AlertResponse(BaseModel):
    """Schema for alert responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Alert ID")
    name: str = Field(..., description="Alert name")
    description: str = Field(..., description="Alert description")
    level: AlertLevel = Field(..., description="Alert severity level")
    is_active: bool = Field(default=True, description="Alert active status")
    triggered_count: int = Field(default=0, description="Number of times triggered")
    last_triggered: Optional[datetime] = Field(None, description="Last triggered time")
    created_at: datetime = Field(..., description="Creation timestamp")


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================


class DashboardCreate(BaseModel):
    """Schema for creating dashboards."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Dashboard name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Dashboard description")
    metrics: List[str] = Field(..., description="List of metric names")
    layout: Optional[Dict[str, Any]] = Field(None, description="Dashboard layout")


class DashboardResponse(BaseModel):
    """Schema for dashboard response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Dashboard ID")
    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    metrics: List[str] = Field(..., description="List of metric names")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


# ============================================================================
# SYSTEM HEALTH SCHEMAS
# ============================================================================


class ComponentHealth(BaseModel):
    """Schema for individual component health."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Component name")
    status: ComponentStatus = Field(..., description="Component status")
    connected: bool = Field(default=True, description="Connection status")
    response_time_ms: Optional[float] = Field(
        None, description="Response time in milliseconds"
    )
    error_message: Optional[str] = Field(None, description="Error message if any")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional component data"
    )


class SystemHealthResponse(BaseModel):
    """Schema for system health response."""

    model_config = ConfigDict(from_attributes=True)

    status: SystemStatus = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    components: Dict[str, ComponentHealth] = Field(
        ..., description="Component health status"
    )
    issues: Optional[List[str]] = Field(
        default=None, description="List of issues found"
    )


# ============================================================================
# USER ANALYTICS SCHEMAS
# ============================================================================


class UserAnalyticsResponse(BaseModel):
    """Schema for user analytics response."""

    model_config = ConfigDict(from_attributes=True)

    period_days: int = Field(..., description="Analysis period in days")
    timestamp: datetime = Field(..., description="Analytics timestamp")
    users: Dict[str, Any] = Field(..., description="User statistics")
    surveys: Dict[str, Any] = Field(..., description="Survey statistics")
    actions: Dict[str, Any] = Field(..., description="Action statistics")
    performance: Dict[str, Any] = Field(..., description="Performance statistics")


# ============================================================================
# PERFORMANCE SCHEMAS (simplified)
# ============================================================================


class PerformanceData(BaseModel):
    """Schema for performance tracking data."""

    model_config = ConfigDict(from_attributes=True)

    operation: str = Field(..., description="Operation name")
    duration_ms: float = Field(..., description="Duration in milliseconds")
    status: str = Field(default="success", description="Operation status")
    timestamp: Optional[datetime] = Field(
        default=None, description="Performance timestamp"
    )


# ============================================================================
# ADDITIONAL SCHEMAS FOR TESTING
# ============================================================================


class MonitoringConfig(BaseModel):
    """Schema for monitoring configuration."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(default=True, description="Enable monitoring")
    retention_days: int = Field(default=30, description="Data retention in days")
    alert_channels: List[str] = Field(
        default_factory=list, description="Alert channels"
    )
    thresholds: Dict[str, float] = Field(
        default_factory=dict, description="Monitoring thresholds"
    )


class RealTimeMetrics(BaseModel):
    """Schema for real-time metrics."""

    model_config = ConfigDict(from_attributes=True)

    timestamp: str = Field(..., description="Metrics timestamp")
    recent_metrics_count: int = Field(..., description="Recent metrics count")
    active_alerts: int = Field(..., description="Active alerts count")
    performance_avg: Dict[str, float] = Field(
        default_factory=dict, description="Average performance"
    )


class UserActionRequest(BaseModel):
    """Schema for user action tracking."""

    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., description="Action name")
    user_id: int = Field(..., description="User ID")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Action metadata"
    )
