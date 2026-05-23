"""
Notification Schemas — Pydantic models for notification API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Request Schemas ───────────────────────────────────────────

class NotificationCreate(BaseModel):
    """Schema for creating a notification (used internally by services)."""
    user_id: str
    baby_id: str
    type: str = Field("info", pattern="^(info|warning|critical)$")
    title: str
    message: str


# ── Response Schemas ──────────────────────────────────────────

class NotificationResponse(BaseModel):
    """A single notification in API responses."""
    id: str
    user_id: str
    baby_id: str
    type: str
    title: str
    message: str
    is_read: bool
    created_at: Optional[datetime] = None


class NotificationListResponse(BaseModel):
    """List of notifications with unread count."""
    data: List[NotificationResponse]
    total: int
    unread_count: int
