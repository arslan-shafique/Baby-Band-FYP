"""
Cry Event Schemas — Pydantic models for cry classification API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Request Schemas ───────────────────────────────────────────

class CryClassifyRequest(BaseModel):
    """
    Schema for sending audio features to the ML model for classification.
    The ESP32 extracts MFCC features and sends them here.
    """
    baby_id: str
    audio_features: List[float] = Field(..., description="MFCC feature vector from ESP32")
    duration_seconds: Optional[int] = Field(None, ge=0)


class CryEventCreate(BaseModel):
    """Schema for manually creating a cry event (e.g., from Lambda)."""
    baby_id: str
    cry_type: str = Field(..., pattern="^(hungry|tired|discomfort|diaper|unknown)$")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    duration_seconds: Optional[int] = None


# ── Response Schemas ──────────────────────────────────────────

class CryClassifyResponse(BaseModel):
    """Response from the ML classification endpoint."""
    cry_type: str
    confidence: float
    all_predictions: Optional[dict] = None  # All class probabilities


class CryEventResponse(BaseModel):
    """A single cry event in API responses."""
    id: str
    baby_id: str
    cry_type: str
    confidence: float
    duration_seconds: Optional[int] = None
    timestamp: Optional[datetime] = None


class CryHistoryResponse(BaseModel):
    """Paginated list of cry events."""
    data: List[CryEventResponse]
    total: int
