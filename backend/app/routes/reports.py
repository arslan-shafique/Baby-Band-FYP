"""
Reports Routes
Endpoints for generating health reports and analytics.
"""

from fastapi import APIRouter, Depends, Query
from app.middleware.firebase_auth import get_current_user
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/weekly/{baby_id}")
async def get_weekly_report(
    baby_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a weekly health report for a baby.
    Includes: average vitals, cry frequency, sleep patterns.
    """
    service = ReportService()
    report = await service.generate_weekly_report(baby_id)
    return report


@router.get("/monthly/{baby_id}")
async def get_monthly_report(
    baby_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a monthly health report for a baby.
    More comprehensive — includes trends and anomaly highlights.
    """
    service = ReportService()
    report = await service.generate_monthly_report(baby_id)
    return report


@router.get("/dashboard/{baby_id}")
async def get_dashboard_summary(
    baby_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a real-time dashboard summary for a baby.
    Aggregates latest data from all collections into one response.
    Used to populate the Flutter Dashboard in a single API call.
    """
    service = ReportService()
    summary = await service.get_dashboard_summary(baby_id)
    return summary
