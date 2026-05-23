"""
Cry Events Routes
Endpoints for cry classification (ML inference) and cry event history.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import Optional
from datetime import datetime
from app.middleware.firebase_auth import get_current_user
from app.schemas.cry_event import (
    CryClassifyRequest,
    CryClassifyResponse,
    CryEventResponse,
    CryHistoryResponse,
)
from app.services.cry_service import CryService

router = APIRouter()

import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

from ml_model.cry_detection.cloud_inference import CryDetector

_CLOUD_MODEL_PATH = os.path.join(WORKSPACE_ROOT, "ml_model/cry_detection/models/cloud_detection/cry_detection_cloud.h5")
cry_detector = CryDetector(model_path=_CLOUD_MODEL_PATH)

# Expected payload: 48000 int16 samples × 2 bytes each = 96000 bytes
EXPECTED_PCM_BYTES = 48000 * 2


@router.post("/classify", response_model=CryClassifyResponse)
async def classify_cry(
    request: CryClassifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Classify a baby's cry using the ML model.

    The ESP32 extracts MFCC features from audio and sends them here.
    The backend runs the TFLite model and returns the cry type.

    Flow: ESP32 → (MFCC features) → This Endpoint → TFLite Model → Cry Type
    """
    service = CryService()
    result = await service.classify_cry(request)
    return result


@router.post("/predict")
async def predict_cry_audio(request: Request):
    """
    Receives raw int16 PCM audio bytes from the ESP32 via
    Content-Type: application/octet-stream, extracts Mel Spectrogram
    features, runs the Keras classification model, and pushes results
    to Firebase RTDB.

    Expected payload: 96000 bytes (48000 int16 samples at 16kHz = 3 seconds).
    """
    # --- Validate content type ---
    content_type = request.headers.get("content-type", "")
    if "octet-stream" not in content_type:
        raise HTTPException(
            status_code=415,
            detail=f"Expected Content-Type: application/octet-stream, got: {content_type}"
        )

    # --- Read raw body ---
    audio_bytes = await request.body()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    if len(audio_bytes) != EXPECTED_PCM_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {EXPECTED_PCM_BYTES} bytes (48000 int16 samples), "
                   f"got {len(audio_bytes)} bytes"
        )

    # --- Binary Cry Detection Gate ---
    is_cry, confidence = cry_detector.is_cry(audio_bytes)
    if not is_cry:
        return {
            "cry_detected": False,
            "confidence": round(float(confidence), 4),
            "label": None,
            "message": "Audio classified as non-cry. Classification skipped."
        }

    service = CryService()

    try:
        result = await service.predict_audio(audio_bytes)
        result["cry_detected"] = True
        result["detection_confidence"] = round(float(confidence), 4)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{baby_id}", response_model=CryHistoryResponse)
async def get_cry_history(
    baby_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    cry_type: Optional[str] = Query(None, description="Filter by: hungry, tired, discomfort, diaper, unknown"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """
    Get cry event history for a baby.
    Used by the Flutter Cry History page.
    """
    service = CryService()
    result = await service.get_history(
        baby_id=baby_id,
        start_date=start_date,
        end_date=end_date,
        cry_type=cry_type,
        limit=limit,
    )
    return result


@router.get("/latest/{baby_id}", response_model=CryEventResponse)
async def get_latest_cry_event(
    baby_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the most recent cry classification for a baby.
    Used by the Flutter Dashboard's cry classification card.
    """
    service = CryService()
    event = await service.get_latest_event(baby_id)

    if not event:
        raise HTTPException(status_code=404, detail="No cry events found")

    return event
