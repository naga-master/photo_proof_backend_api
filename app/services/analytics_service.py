"""Analytics service for business intelligence and metrics."""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.schemas.analytics import (
    AnalyticsDashboard,
    HeatmapData,
    InsightRecommendation,
    EngagementData,
    BusinessMetrics,
    PerformanceMetrics,
)


class AnalyticsService:
    """Service for analytics and business intelligence."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_analytics(
        self, 
        user_id: str, 
        studio_id: str,
        date_range: Optional[tuple[date, date]] = None
    ) -> AnalyticsDashboard:
        """Get comprehensive dashboard analytics."""
        if not date_range:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)
        
        # Mock data for now - in production, these would query the database
        business_metrics = self._get_business_metrics(studio_id, date_range)
        engagement_data = self._get_engagement_data(studio_id, date_range)
        performance_metrics = self._get_performance_metrics(studio_id, date_range)
        insights = self._generate_insights(studio_id, date_range)
        
        return AnalyticsDashboard(
            business_metrics=business_metrics,
            engagement_data=engagement_data,
            performance_metrics=performance_metrics,
            insights=insights,
            date_range_start=date_range[0],
            date_range_end=date_range[1],
            generated_at=datetime.utcnow()
        )
    
    def _get_business_metrics(self, studio_id: str, date_range: tuple[date, date]) -> BusinessMetrics:
        """Calculate business metrics for the given date range."""
        # Mock implementation - replace with actual database queries
        return BusinessMetrics(
            total_revenue=25680.50,
            revenue_growth=12.5,
            new_clients=8,
            client_retention_rate=94.2,
            avg_project_value=3210.06,
            total_projects=45,
            completed_projects=42,
            active_projects=3,
            conversion_rate=78.3,
            booking_trends=[
                {"date": "2024-01-01", "bookings": 5, "revenue": 12500.00},
                {"date": "2024-01-02", "bookings": 3, "revenue": 7200.00},
                {"date": "2024-01-03", "bookings": 7, "revenue": 18900.00},
                {"date": "2024-01-04", "bookings": 4, "revenue": 9600.00},
                {"date": "2024-01-05", "bookings": 6, "revenue": 15400.00},
            ]
        )
    
    def _get_engagement_data(self, studio_id: str, date_range: tuple[date, date]) -> EngagementData:
        """Get client engagement analytics."""
        # Mock implementation
        return EngagementData(
            gallery_views=1247,
            unique_visitors=892,
            avg_session_duration=425,  # seconds
            bounce_rate=23.5,
            download_count=3456,
            favorite_count=891,
            share_count=234,
            comment_count=67,
            top_performing_galleries=[
                {"name": "Wedding - Smith & Johnson", "views": 245, "engagement": 89.2},
                {"name": "Portrait Session - Davis Family", "views": 198, "engagement": 76.8},
                {"name": "Corporate Event - Tech Summit", "views": 167, "engagement": 71.3},
            ],
            device_breakdown={
                "mobile": 52.3,
                "desktop": 38.7,
                "tablet": 9.0
            },
            geographic_data=[
                {"country": "United States", "sessions": 756, "percentage": 67.2},
                {"country": "Canada", "sessions": 134, "percentage": 11.9},
                {"country": "United Kingdom", "sessions": 89, "percentage": 7.9},
                {"country": "Australia", "sessions": 67, "percentage": 6.0},
                {"country": "Others", "sessions": 79, "percentage": 7.0},
            ]
        )
    
    def _get_performance_metrics(self, studio_id: str, date_range: tuple[date, date]) -> PerformanceMetrics:
        """Get system and business performance metrics."""
        # Mock implementation
        return PerformanceMetrics(
            avg_upload_time=2.3,  # seconds
            avg_gallery_load_time=1.8,  # seconds
            system_uptime=99.8,  # percentage
            storage_usage=67.5,  # percentage
            bandwidth_usage=2.1,  # GB
            error_rate=0.12,  # percentage
            client_satisfaction=4.7,  # out of 5
            project_completion_rate=93.3,  # percentage
            on_time_delivery_rate=96.7,  # percentage
            monthly_trends=[
                {"month": "2024-01", "projects": 12, "revenue": 28500, "satisfaction": 4.6},
                {"month": "2024-02", "projects": 15, "revenue": 34200, "satisfaction": 4.8},
                {"month": "2024-03", "projects": 18, "revenue": 41600, "satisfaction": 4.7},
                {"month": "2024-04", "projects": 14, "revenue": 32100, "satisfaction": 4.9},
            ]
        )
    
    def _generate_insights(self, studio_id: str, date_range: tuple[date, date]) -> List[InsightRecommendation]:
        """Generate AI-powered insights and recommendations."""
        # Mock insights - in production, these would be generated based on actual data analysis
        return [
            InsightRecommendation(
                title="Peak Booking Opportunity",
                description="Your booking rate increases by 34% during weekend inquiries. Consider highlighting weekend availability in your marketing.",
                impact="high",
                action_items=[
                    "Update website to emphasize weekend slots",
                    "Create weekend-specific marketing campaigns",
                    "Adjust pricing strategy for weekend bookings"
                ],
                estimated_revenue_impact=5600.00,
                confidence=0.87
            ),
            InsightRecommendation(
                title="Client Retention Optimization",
                description="Clients who receive galleries within 48 hours have a 67% higher rebooking rate.",
                impact="medium", 
                action_items=[
                    "Set up automated delivery workflows",
                    "Create rush delivery service offering",
                    "Implement delivery time tracking"
                ],
                estimated_revenue_impact=3200.00,
                confidence=0.92
            ),
            InsightRecommendation(
                title="Mobile Experience Enhancement",
                description="52% of your gallery views are on mobile, but mobile conversion is 15% lower than desktop.",
                impact="medium",
                action_items=[
                    "Optimize gallery layouts for mobile",
                    "Implement mobile-first design improvements",
                    "Test mobile checkout process"
                ],
                estimated_revenue_impact=2800.00,
                confidence=0.78
            )
        ]
    
    def get_heatmap_data(
        self, 
        studio_id: str, 
        metric: str,
        date_range: Optional[tuple[date, date]] = None
    ) -> List[HeatmapData]:
        """Get heatmap data for visualization."""
        if not date_range:
            end_date = date.today()
            start_date = end_date - timedelta(days=90)
            date_range = (start_date, end_date)
        
        # Mock heatmap data
        heatmap_data = []
        current_date = date_range[0]
        
        while current_date <= date_range[1]:
            # Generate mock activity data
            import random
            activity_level = random.randint(0, 100)
            
            heatmap_data.append(HeatmapData(
                date=current_date,
                value=activity_level,
                metric=metric,
                details={
                    "gallery_views": random.randint(0, 50),
                    "downloads": random.randint(0, 20),
                    "bookings": random.randint(0, 5)
                }
            ))
            current_date += timedelta(days=1)
        
        return heatmap_data
    
    def get_custom_report(
        self,
        studio_id: str,
        metrics: List[str],
        date_range: tuple[date, date],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate custom analytics report."""
        # Mock implementation for custom reporting
        report_data = {
            "report_id": f"custom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "studio_id": studio_id,
            "date_range": {
                "start": date_range[0].isoformat(),
                "end": date_range[1].isoformat()
            },
            "metrics": {},
            "filters_applied": filters or {},
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Generate mock data for requested metrics
        for metric in metrics:
            if metric == "revenue":
                report_data["metrics"][metric] = {
                    "total": 45680.50,
                    "average": 2534.47,
                    "trend": "increasing",
                    "growth_rate": 12.5
                }
            elif metric == "clients":
                report_data["metrics"][metric] = {
                    "new_clients": 12,
                    "returning_clients": 8,
                    "total_active": 45,
                    "retention_rate": 94.2
                }
            elif metric == "projects":
                report_data["metrics"][metric] = {
                    "total_projects": 28,
                    "completed": 25,
                    "in_progress": 3,
                    "avg_duration": 14.5  # days
                }
            elif metric == "engagement":
                report_data["metrics"][metric] = {
                    "gallery_views": 1847,
                    "downloads": 3456,
                    "shares": 234,
                    "avg_session_duration": 425
                }
        
        return report_data
    
    def export_analytics(
        self,
        studio_id: str,
        format: str,
        date_range: tuple[date, date],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Export analytics data in specified format."""
        # Mock export functionality
        export_data = {
            "export_id": f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "format": format,
            "status": "completed",
            "download_url": f"/exports/analytics_{studio_id}_{format}.{format.lower()}",
            "file_size": "2.4 MB",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        return export_data