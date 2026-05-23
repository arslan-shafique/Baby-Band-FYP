"""
Sleep Tracking Routes
Endpoints for sleep session history and sleep quality analysis.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import datetime
from app.middleware.firebase_auth import get_current_user
from app.schemas.sleep_session import (
    SleepSessionResponse,
    SleepHistoryResponse,
    SleepSummaryResponse,
)
from app.services.sleep_service import SleepService
from pydantic import BaseModel
from collections import deque
from app.firebase_client import get_firestore_client

# --- SLEEP CLASSIFICATION CONSTANTS ---
DEEP_SLEEP_HR_VAR_MAX = 5.0
DEEP_SLEEP_MAG_VAR_MAX = 0.005
DEEP_SLEEP_SPIKES_MAX = 1

LIGHT_SLEEP_HR_VAR_MAX = 15.0
LIGHT_SLEEP_MAG_VAR_MAX = 0.05
LIGHT_SLEEP_SPIKES_MAX = 4

# In-memory buffer per device: { "device_id": deque(maxlen=3) }
_sleep_buffers = {}

class HeartData(BaseModel):
    bpm: float
    varianceBpm: float
    fingerDetected: bool
    valid: bool

class MotionData(BaseModel):
    meanMag: float
    varianceMag: float
    spikeCount: int
    detected: bool

class EnvironmentData(BaseModel):
    temperature: float
    humidity: float
    valid: bool

class SleepPayload(BaseModel):
    device_id: str
    timestamp: int
    heart: HeartData
    motion: MotionData
    environment: EnvironmentData

router = APIRouter()


@router.get("/history/{baby_id}", response_model=SleepHistoryResponse)
async def get_sleep_history(
    baby_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """
    Get sleep session history for a baby.
    Used by the Flutter Sleep History page.
    """
    service = SleepService()
    result = await service.get_history(
        baby_id=baby_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return result


@router.get("/summary/{baby_id}", response_model=SleepSummaryResponse)
async def get_sleep_summary(
    baby_id: str,
    hours: int = Query(24, ge=1, le=168, description="Summary for last N hours"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get aggregated sleep statistics.
    Shows total sleep, deep/light/awake breakdown, quality scores.
    """
    service = SleepService()
    summary = await service.get_summary(baby_id, hours)
    return summary


@router.get("/latest/{baby_id}", response_model=SleepSessionResponse)
async def get_current_sleep_status(
    baby_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the baby's current sleep status (or most recent session).
    Used by the Dashboard to show current sleep state.
    """
    service = SleepService()
    session = await service.get_latest_session(baby_id)

    if not session:
        raise HTTPException(status_code=404, detail="No sleep data found")

    return session


@router.post("/")
async def classify_sleep(payload: SleepPayload):
    """
    Receive sensor payload, buffer it, and classify sleep state.
    Requires 3 consecutive payloads (30s window) for classification.
    """
    device_id = payload.device_id
    
    # 1. Early validation: if data is bad, clear buffer and return early
    if not payload.heart.valid or not payload.heart.fingerDetected:
        if device_id in _sleep_buffers:
            _sleep_buffers[device_id].clear()
        return {
            "device_id": device_id,
            "sleep_state": "insufficient_data",
            "features": None,
            "buffered_payloads": 0
        }

    # 2. Append to buffer
    if device_id not in _sleep_buffers:
        _sleep_buffers[device_id] = deque(maxlen=3)
        
    _sleep_buffers[device_id].append(payload)
    
    # 3. Check if we have enough data (exactly 3 valid contiguous payloads)
    if len(_sleep_buffers[device_id]) < 3:
        return {
            "device_id": device_id,
            "sleep_state": "insufficient_data",
            "features": None,
            "buffered_payloads": len(_sleep_buffers[device_id])
        }

    # Extract features from the 3-entry window
    window = _sleep_buffers[device_id]
    mean_hr = sum(p.heart.bpm for p in window) / 3.0
    hr_variance = sum(p.heart.varianceBpm for p in window) / 3.0
    mean_mag_variance = sum(p.motion.varianceMag for p in window) / 3.0
    total_spikes = sum(p.motion.spikeCount for p in window)

    # Rule-based classification
    state = "awake"
    if hr_variance < DEEP_SLEEP_HR_VAR_MAX and mean_mag_variance < DEEP_SLEEP_MAG_VAR_MAX and total_spikes <= DEEP_SLEEP_SPIKES_MAX:
        state = "deep"
    elif hr_variance < LIGHT_SLEEP_HR_VAR_MAX and mean_mag_variance < LIGHT_SLEEP_MAG_VAR_MAX and total_spikes <= LIGHT_SLEEP_SPIKES_MAX:
        state = "light"

    features = {
        "mean_hr": mean_hr,
        "hr_variance": hr_variance,
        "mean_mag_variance": mean_mag_variance,
        "total_spikes": total_spikes
    }

    # Write to Firestore
    db = get_firestore_client()
    doc_data = {
        "device_id": device_id,
        "timestamp": payload.timestamp,
        "sleep_state": state,
        "mean_hr": mean_hr,
        "hr_variance": hr_variance,
        "mean_mag_variance": mean_mag_variance,
        "total_spikes": total_spikes
    }
    db.collection("sleep_sessions").add(doc_data)

    return {
        "device_id": device_id,
        "sleep_state": state,
        "features": features,
        "buffered_payloads": 3
    }

