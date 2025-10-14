"""Analytics and metrics schemas."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class AnalyticsMetric(BaseModel):
    """Individual analytics metric."""
    name: str
    value: float
    unit: str
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # 'up', 'down', 'stable'


class EngagementData(BaseModel):
    """Engagement analytics data."""
    total_views: int
    unique_visitors: int
    average_session_duration: float
    bounce_rate: float
    popular_galleries: List[Dict[str, Any]]
    device_breakdown: Dict[str, int]
    location_data: Dict[str, int]
    hourly_activity: List[Dict[str, Any]]


class BusinessMetrics(BaseModel):
    """Business intelligence metrics."""
    revenue_trend: List[Dict[str, Any]]
    client_acquisition_cost: Decimal
    customer_lifetime_value: Decimal
    conversion_rate: float
    project_completion_rate: float
    average_project_value: Decimal
    seasonal_trends: Dict[str, Any]


class PerformanceMetrics(BaseModel):
    """System performance metrics."""
    page_load_times: Dict[str, float]
    api_response_times: Dict[str, float]
    error_rates: Dict[str, float]
    uptime_percentage: float
    storage_usage: Dict[str, float]


class AnalyticsDashboard(BaseModel):
    """Complete analytics dashboard data."""
    overview_metrics: List[AnalyticsMetric]
    engagement: EngagementData
    business_intelligence: BusinessMetrics
    performance: PerformanceMetrics
    last_updated: datetime


class AnalyticsRequest(BaseModel):
    """Request for analytics data."""
    start_date: date
    end_date: date
    metrics: Optional[List[str]] = None
    granularity: Optional[str] = "day"  # 'hour', 'day', 'week', 'month'


class HeatmapData(BaseModel):
    """Heatmap visualization data."""
    data_points: List[Dict[str, Any]]
    max_value: float
    min_value: float
    color_scale: List[str]
    labels: Dict[str, str]


class InsightRecommendation(BaseModel):
    """AI-generated insight and recommendation."""
    id: str
    title: str
    description: str
    impact_level: str  # 'high', 'medium', 'low'
    category: str
    action_items: List[str]
    priority_score: float
    created_at: datetime