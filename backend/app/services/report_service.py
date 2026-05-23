"""
Report Service — Business logic for generating health reports.

Aggregates data from multiple Firestore collections to produce
weekly/monthly reports and dashboard summaries.
"""

from datetime import datetime, timedelta
from app.firebase_client import get_firestore_client
from app.services.sensor_service import SensorService
from app.services.cry_service import CryService
from app.services.sleep_service import SleepService


class ReportService:
    """Service for generating health reports and dashboard summaries."""

    def __init__(self):
        self.db = get_firestore_client()
        self.sensor_service = SensorService()
        self.cry_service = CryService()
        self.sleep_service = SleepService()

    async def get_dashboard_summary(self, baby_id: str) -> dict:
        """
        Aggregates latest data from all sources into a single response.
        This powers the Flutter Dashboard in one API call.
        """
        # Get latest sensor data
        latest_sensor = await self.sensor_service.get_latest_reading(baby_id)

        # Get latest cry event
        latest_cry = await self.cry_service.get_latest_event(baby_id)

        # Get current sleep status
        latest_sleep = await self.sleep_service.get_latest_session(baby_id)

        # Get 24-hour sensor stats
        sensor_stats = await self.sensor_service.get_stats(baby_id, hours=24)

        # Get 24-hour sleep summary
        sleep_summary = await self.sleep_service.get_summary(baby_id, hours=24)

        return {
            "baby_id": baby_id,
            "latest_sensor": latest_sensor,
            "latest_cry": latest_cry,
            "latest_sleep": latest_sleep,
            "sensor_stats_24h": sensor_stats,
            "sleep_summary_24h": sleep_summary,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def generate_weekly_report(self, baby_id: str) -> dict:
        """
        Generate a weekly health report.

        TODO (Phase 6): Implement full report with:
        - Average heart rate, temperature trends
        - Cry frequency by type
        - Sleep pattern analysis
        - Anomaly highlights
        """
        sensor_stats = await self.sensor_service.get_stats(baby_id, hours=168)  # 7 days
        sleep_summary = await self.sleep_service.get_summary(baby_id, hours=168)
        cry_history = await self.cry_service.get_history(baby_id, limit=200)

        # Count cries by type
        cry_counts = {}
        for event in cry_history.get("data", []):
            cry_type = event.get("cry_type", "unknown")
            cry_counts[cry_type] = cry_counts.get(cry_type, 0) + 1

        return {
            "baby_id": baby_id,
            "period": "weekly",
            "period_days": 7,
            "sensor_stats": sensor_stats,
            "sleep_summary": sleep_summary,
            "cry_counts": cry_counts,
            "total_cry_events": cry_history.get("total", 0),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def generate_monthly_report(self, baby_id: str) -> dict:
        """
        Generate a monthly health report.

        TODO (Phase 6): Implement comprehensive monthly analysis.
        """
        return {
            "baby_id": baby_id,
            "period": "monthly",
            "message": "Monthly reports will be available in Phase 6",
            "generated_at": datetime.utcnow().isoformat(),
        }
