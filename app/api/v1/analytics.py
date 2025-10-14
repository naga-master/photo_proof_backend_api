"""Analytics and metrics API endpoints."""

from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.analytics import (
    AnalyticsDashboard,
    AnalyticsRequest,
    HeatmapData,
    InsightRecommendation,
    EngagementData,
    BusinessMetrics,
    PerformanceMetrics,
)
from app.schemas.users import UserRead
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get complete analytics dashboard data."""
    service = AnalyticsService(db)
    
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).date()
    if not end_date:
        end_date = datetime.now().date()
    
    return await service.get_dashboard_data(
        current_user.studio_id, start_date, end_date
    )


@router.get("/engagement", response_model=EngagementData)
async def get_engagement_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get engagement analytics data."""
    service = AnalyticsService(db)
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).date()
    if not end_date:
        end_date = datetime.now().date()
    
    return await service.get_engagement_data(
        current_user.studio_id, start_date, end_date
    )


@router.get("/engagement/heatmap", response_model=HeatmapData)
async def get_engagement_heatmap(
    granularity: str = Query("hour", regex="^(hour|day)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get engagement heatmap data."""
    service = AnalyticsService(db)
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).date()
    if not end_date:
        end_date = datetime.now().date()
    
    return await service.get_engagement_heatmap(
        current_user.studio_id, start_date, end_date, granularity
    )


@router.get("/business", response_model=BusinessMetrics)
async def get_business_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get business intelligence metrics."""
    service = AnalyticsService(db)
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).date()
    if not end_date:
        end_date = datetime.now().date()
    
    return await service.get_business_metrics(
        current_user.studio_id, start_date, end_date
    )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get system performance metrics."""
    service = AnalyticsService(db)
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).date()
    if not end_date:
        end_date = datetime.now().date()
    
    return await service.get_performance_metrics(
        current_user.studio_id, start_date, end_date
    )


@router.get("/insights", response_model=List[InsightRecommendation])
async def get_ai_insights(
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get AI-generated insights and recommendations."""
    service = AnalyticsService(db)
    return await service.get_ai_insights(
        current_user.studio_id, limit, category
    )


@router.post("/insights/{insight_id}/acknowledge")
async def acknowledge_insight(
    insight_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Mark an insight as acknowledged."""
    service = AnalyticsService(db)
    insight = await service.get_insight(insight_id)
    
    if not insight or insight.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Insight not found"
        )
    
    await service.acknowledge_insight(insight_id)
    return {"message": "Insight acknowledged"}


@router.get("/export")
async def export_analytics_data(
    start_date: date = Query(...),
    end_date: date = Query(...),
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    metrics: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Export analytics data in various formats."""
    service = AnalyticsService(db)
    
    export_url = await service.export_data(
        current_user.studio_id, start_date, end_date, format, metrics
    )
    
    return {"export_url": export_url}


@router.get("/trends")
async def get_trend_analysis(
    metric: str = Query(...),
    period: str = Query("week", regex="^(day|week|month|quarter)$"),
    compare_previous: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get trend analysis for a specific metric."""
    service = AnalyticsService(db)
    return await service.get_trend_analysis(
        current_user.studio_id, metric, period, compare_previous
    )