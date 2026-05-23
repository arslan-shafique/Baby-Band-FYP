"""
Sensor Data Schemas — Pydantic models for sensor reading API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Sub-schemas ───────────────────────────────────────────────

class MotionDataSchema(BaseModel):
    """3-axis accelerometer reading."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


# ── Request Schemas ───────────────────────────────────────────

class SensorDataCreate(BaseModel):
    """
    Schema for receiving sensor data from ESP32 (via Lambda).
    This matches the MQTT payload structure from the hardware.
    """
    baby_id: str
    device_id: str
    heart_rate: Optional[float] = Field(None, ge=0, le=300)
    spo2: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=-10, le=60)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    motion: Optional[MotionDataSchema] = None
    timestamp: Optional[datetime] = None


# ── Response Schemas ──────────────────────────────────────────

class SensorDataResponse(BaseModel):
    """A single sensor reading in API responses."""
    id: str
    baby_id: str
    device_id: str
    heart_rate: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    motion: Optional[MotionDataSchema] = None
    timestamp: Optional[datetime] = None


class SensorHistoryResponse(BaseModel):
    """Paginated list of sensor readings."""
    data: List[SensorDataResponse]
    total: int
    page: int
    page_size: int


# ── Query Parameters ──────────────────────────────────────────

class SensorHistoryQuery(BaseModel):
    """Query parameters for filtering sensor history."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
