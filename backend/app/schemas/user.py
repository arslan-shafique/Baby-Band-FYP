"""
User Schemas — Pydantic models for user-related API requests and responses.

WHAT ARE SCHEMAS? (for beginners):
- Schemas define the SHAPE of data coming in (requests) and going out (responses)
- FastAPI uses them to automatically validate incoming data
- If a required field is missing, FastAPI returns a 422 error automatically
- They also generate the API documentation (Swagger UI)
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ── Request Schemas (data coming IN from Flutter) ─────────────

class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    notifications: Optional[bool] = None
    sound_alerts: Optional[bool] = None
    vibration: Optional[bool] = None
    auto_sync: Optional[bool] = None
    temperature_unit: Optional[str] = None
    language: Optional[str] = None
    alert_volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    hr_alert_threshold: Optional[int] = Field(None, ge=60, le=220)
    temp_alert_threshold: Optional[float] = Field(None, ge=35.0, le=42.0)


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile info."""
    display_name: Optional[str] = None


# ── Response Schemas (data going OUT to Flutter) ──────────────

class UserSettingsResponse(BaseModel):
    """User settings in API responses."""
    notifications: bool = True
    sound_alerts: bool = True
    vibration: bool = True
    auto_sync: bool = True
    temperature_unit: str = "°C"
    language: str = "English"
    alert_volume: float = 0.8
    hr_alert_threshold: int = 150
    temp_alert_threshold: float = 37.5


class UserResponse(BaseModel):
    """Full user profile in API responses."""
    uid: str
    email: str
    display_name: str
    settings: UserSettingsResponse
    created_at: Optional[datetime] = None
