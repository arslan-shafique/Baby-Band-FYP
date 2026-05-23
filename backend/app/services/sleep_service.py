"""
Sleep Service — Business logic for sleep session analysis.
"""

from datetime import datetime, timedelta
from typing import Optional
from app.firebase_client import get_firestore_client


class SleepService:
    """Service for sleep session queries and analysis."""

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = "sleep_sessions"

    async def get_history(
        self,
        baby_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
    ) -> dict:
        """Get sleep session history with optional date filtering."""
        query = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
        )

        if start_date:
            query = query.where("start_time", ">=", start_date)
        if end_date:
            query = query.where("start_time", "<=", end_date)

        query = query.order_by("start_time", direction="DESCENDING").limit(limit)

        docs = list(query.stream())
        data = []
        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            data.append(item)

        # Calculate summary
        summary = self._calculate_summary(data)

        return {"data": data, "summary": summary, "total": len(data)}

    async def get_summary(self, baby_id: str, hours: int = 24) -> dict:
        """Get aggregated sleep statistics for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        docs = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
            .where("start_time", ">=", cutoff)
            .stream()
        )

        data = [doc.to_dict() for doc in docs]
        return self._calculate_summary(data)

    async def get_latest_session(self, baby_id: str) -> Optional[dict]:
        """Get the most recent sleep session."""
        docs = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
            .order_by("start_time", direction="DESCENDING")
            .limit(1)
            .stream()
        )

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            return data

        return None

    def _calculate_summary(self, sessions: list) -> dict:
        """Calculate aggregated sleep statistics from a list of sessions."""
        total_minutes = 0
        deep_minutes = 0
        light_minutes = 0
        awake_minutes = 0
        quality_scores = []

        for session in sessions:
            duration = session.get("duration_minutes", 0) or 0
            stage = session.get("stage", "awake")
            score = session.get("quality_score")

            total_minutes += duration

            if stage == "deep":
                deep_minutes += duration
            elif stage == "light":
                light_minutes += duration
            elif stage == "awake":
                awake_minutes += duration

            if score is not None:
                quality_scores.append(score)

        return {
            "total_sleep_minutes": total_minutes,
            "deep_sleep_minutes": deep_minutes,
            "light_sleep_minutes": light_minutes,
            "awake_minutes": awake_minutes,
            "average_quality_score": (
                round(sum(quality_scores) / len(quality_scores), 1)
                if quality_scores
                else None
            ),
            "session_count": len(sessions),
        }
