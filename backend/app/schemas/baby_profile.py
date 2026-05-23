"""
Baby Profile Schemas — Pydantic models for baby profile API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Request Schemas ───────────────────────────────────────────

class BabyProfileCreate(BaseModel):
    """Schema for creating a new baby profile."""
    name: str = Field(..., min_length=1, max_length=100, examples=["Emma"])
    date_of_birth: Optional[str] = Field(None, examples=["2025-09-15"])
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    device_id: Optional[str] = Field(None, examples=["ESP32_001"])


class BabyProfileUpdate(BaseModel):
    """Schema for updating an existing baby profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[str] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    device_id: Optional[str] = None
    avatar_url: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────

class BabyProfileResponse(BaseModel):
    """Baby profile in API responses."""
    id: str                     # Firestore document ID
    user_id: str                # Parent's Firebase Auth UID
    name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    device_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
