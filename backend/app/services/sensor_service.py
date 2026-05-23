"""
Sensor Service — Business logic for sensor data queries.

Sensor data is WRITTEN by AWS Lambda (from MQTT → IoT Core → Lambda → Firestore).
This service handles READING and aggregation.
"""

from datetime import datetime, timedelta
from typing import Optional
from app.firebase_client import get_firestore_client


class SensorService:
    """Service for querying and aggregating sensor data."""

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = "sensor_data"

    async def get_latest_reading(self, baby_id: str) -> Optional[dict]:
        """Get the most recent sensor reading for a baby."""
        docs = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(1)
            .stream()
        )

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            return data

        return None

    async def get_history(
        self,
        baby_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        data_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        Get sensor data history with filtering and pagination.

        Args:
            baby_id: Baby's profile ID
            start_date: Start of date range filter
            end_date: End of date range filter
            data_type: Optional filter (heart_rate, temperature, humidity)
            page: Page number (1-indexed)
            page_size: Number of results per page
        """
        query = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
        )

        if start_date:
            query = query.where("timestamp", ">=", start_date)
        if end_date:
            query = query.where("timestamp", "<=", end_date)

        query = query.order_by("timestamp", direction="DESCENDING")

        # Get all matching docs for count (Firestore doesn't have COUNT)
        all_docs = list(query.stream())
        total = len(all_docs)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_docs = all_docs[start_idx:end_idx]

        data = []
        for doc in page_docs:
            item = doc.to_dict()
            item["id"] = doc.id
            data.append(item)

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_stats(self, baby_id: str, hours: int = 24) -> dict:
        """
        Get aggregated sensor statistics for the last N hours.
        Returns min, max, and average for each sensor type.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        docs = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
            .where("timestamp", ">=", cutoff)
            .stream()
        )

        heart_rates = []
        temperatures = []
        humidities = []
        spo2_values = []

        for doc in docs:
            data = doc.to_dict()
            if data.get("heart_rate") is not None:
                heart_rates.append(data["heart_rate"])
            if data.get("temperature") is not None:
                temperatures.append(data["temperature"])
            if data.get("humidity") is not None:
                humidities.append(data["humidity"])
            if data.get("spo2") is not None:
                spo2_values.append(data["spo2"])

        def calc_stats(values: list) -> dict:
            if not values:
                return {"min": None, "max": None, "avg": None, "count": 0}
            return {
                "min": round(min(values), 1),
                "max": round(max(values), 1),
                "avg": round(sum(values) / len(values), 1),
                "count": len(values),
            }

        return {
            "period_hours": hours,
            "heart_rate": calc_stats(heart_rates),
            "temperature": calc_stats(temperatures),
            "humidity": calc_stats(humidities),
            "spo2": calc_stats(spo2_values),
        }
