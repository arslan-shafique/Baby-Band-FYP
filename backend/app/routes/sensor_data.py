"""
Sensor Data Routes
Endpoints for querying sensor data stored in Firestore.

NOTE: Sensor data is WRITTEN by AWS Lambda (from MQTT/IoT Core), not by this API.
These endpoints are for READING data — used by the Flutter app.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import datetime
from app.middleware.firebase_auth import get_current_user
from app.services.sensor_service import SensorService
from app.services.notification_service import NotificationService
from app.firebase_client import get_firestore_client
from pydantic import BaseModel

TEMP_IDEAL_MIN = 20.0
TEMP_IDEAL_MAX = 22.0
TEMP_ACCEPTABLE_MAX = 26.0
TEMP_WARNING_MAX = 28.0

HUM_MIN = 40.0
HUM_MAX = 60.0

class EnvironmentData(BaseModel):
    temperature: float
    humidity: float
    valid: bool

class SensorPayload(BaseModel):
    device_id: str
    timestamp: int
    environment: EnvironmentData

def classify_environment(temp: float, hum: float):
    if temp < TEMP_IDEAL_MIN:
        t_stat = "too_cold"
    elif temp <= TEMP_IDEAL_MAX:
        t_stat = "ideal"
    elif temp <= TEMP_ACCEPTABLE_MAX:
        t_stat = "acceptable"
    elif temp <= TEMP_WARNING_MAX:
        t_stat = "warning"
    else:
        t_stat = "danger"

    if hum < HUM_MIN:
        h_stat = "too_dry"
    elif hum <= HUM_MAX:
        h_stat = "safe"
    else:
        h_stat = "too_humid"

    if t_stat in ["danger", "too_cold"]:
        overall = "danger"
    elif t_stat in ["ideal", "acceptable"] and h_stat == "safe":
        overall = "safe"
    else:
        overall = "warning"

    return t_stat, h_stat, overall

router = APIRouter()


@router.get("/latest/{baby_id}")
async def get_latest_sensor_data(
    baby_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the most recent sensor reading for a baby.
    Used by the Flutter Dashboard to show current vitals.
    """
    service = SensorService()
    data = await service.get_latest_reading(baby_id)

    if not data:
        raise HTTPException(status_code=404, detail="No sensor data found")

    return data


@router.get("/history/{baby_id}")
async def get_sensor_history(
    baby_id: str,
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    data_type: Optional[str] = Query(None, description="Filter by type: heart_rate, temperature, humidity"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """
    Get sensor reading history for a baby with optional date filtering.
    Used by Flutter History pages (Heart Rate, Temperature).
    """
    service = SensorService()
    result = await service.get_history(
        baby_id=baby_id,
        start_date=start_date,
        end_date=end_date,
        data_type=data_type,
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/stats/{baby_id}")
async def get_sensor_stats(
    baby_id: str,
    hours: int = Query(24, ge=1, le=168, description="Stats for last N hours"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get aggregated statistics (min, max, avg) for sensor data.
    Useful for health reports and dashboard summaries.
    """
    service = SensorService()
    stats = await service.get_stats(baby_id, hours)
    return stats

@router.post("/")
async def process_sensor_data(payload: SensorPayload):
    """
    Receive sensor payload and perform environment classification.
    """
    if not payload.environment.valid:
        return {"status": "skipped", "reason": "environment data not valid"}
        
    t_stat, h_stat, overall = classify_environment(
        payload.environment.temperature, 
        payload.environment.humidity
    )
    
    db = get_firestore_client()
    
    doc_data = {
        "device_id": payload.device_id,
        "timestamp": payload.timestamp,
        "temperature": payload.environment.temperature,
        "humidity": payload.environment.humidity,
        "temperature_status": t_stat,
        "humidity_status": h_stat,
        "overall": overall
    }
    
    # Save to Firestore
    db.collection("environment_logs").add(doc_data)
    
    # Alert mechanism
    if overall == "danger":
        # We need the user_id for the notification
        # The baby profile document ID is typically the device_id
        doc = db.collection("baby_profiles").document(payload.device_id).get()
        if doc.exists:
            user_id = doc.to_dict().get("user_id")
            if user_id:
                notif_service = NotificationService()
                await notif_service.create_notification(
                    user_id=user_id,
                    baby_id=payload.device_id,
                    title="Environment Danger",
                    message=f"Alert: The environment is dangerous (Temp: {t_stat}, Humidity: {h_stat}).",
                    notif_type="environment_danger"
                )
                
    return {
        "environment": doc_data
    }
