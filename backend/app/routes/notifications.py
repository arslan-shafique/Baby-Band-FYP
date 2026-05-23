"""
Notification Routes
Endpoints for managing parent notifications and alerts.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from app.middleware.firebase_auth import get_current_user
from app.schemas.notification import NotificationListResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """
    Get notifications for the current user.
    Used by the Flutter Notifications page.
    """
    service = NotificationService()
    result = await service.get_notifications(
        user_id=current_user["uid"],
        unread_only=unread_only,
        limit=limit,
    )
    return result


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a single notification as read."""
    service = NotificationService()
    await service.mark_as_read(notification_id, current_user["uid"])
    return {"status": "ok", "message": "Notification marked as read"}


@router.put("/read-all")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user),
):
    """Mark all of the current user's notifications as read."""
    service = NotificationService()
    count = await service.mark_all_as_read(current_user["uid"])
    return {"status": "ok", "message": f"Marked {count} notifications as read"}


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
):
    """
    Get the count of unread notifications.
    Used by Flutter's bottom nav badge.
    """
    service = NotificationService()
    count = await service.get_unread_count(current_user["uid"])
    return {"unread_count": count}
