"""
Sleep Session Schemas — Pydantic models for sleep tracking API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Request Schemas ───────────────────────────────────────────

class SleepSessionCreate(BaseModel):
    """Schema for recording a new sleep session."""
    baby_id: str
    stage: str = Field(..., pattern="^(awake|light|deep)$")
    start_time: datetime
    end_time: Optional[datetime] = None
    quality_score: Optional[int] = Field(None, ge=0, le=100)


# ── Response Schemas ──────────────────────────────────────────

class SleepSessionResponse(BaseModel):
    """A single sleep session in API responses."""
    id: str
    baby_id: str
    stage: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    quality_score: Optional[int] = None


class SleepSummaryResponse(BaseModel):
    """Aggregated sleep statistics."""
    total_sleep_minutes: int
    deep_sleep_minutes: int
    light_sleep_minutes: int
    awake_minutes: int
    average_quality_score: Optional[float] = None
    session_count: int


class SleepHistoryResponse(BaseModel):
    """List of sleep sessions."""
    data: List[SleepSessionResponse]
    summary: Optional[SleepSummaryResponse] = None
    total: int
