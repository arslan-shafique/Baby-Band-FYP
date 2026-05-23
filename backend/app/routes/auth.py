"""
Authentication Routes
Handles Firebase Auth token verification and user profile management.

NOTE: User REGISTRATION and LOGIN happen in Flutter using Firebase Auth SDK directly.
This backend only VERIFIES the token and manages the Firestore user profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.middleware.firebase_auth import get_current_user
from app.schemas.user import UserResponse, UserProfileUpdate, UserSettingsUpdate
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get the current user's profile from Firestore.
    Requires: Firebase Auth token in Authorization header.
    """
    service = AuthService()
    user = await service.get_or_create_user(current_user)
    return user


@router.put("/profile")
async def update_user_profile(
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update the current user's profile (display name, etc.)."""
    service = AuthService()
    updated = await service.update_user_profile(current_user["uid"], update_data)
    return {"status": "ok", "message": "Profile updated", "data": updated}


@router.get("/settings")
async def get_user_settings(current_user: dict = Depends(get_current_user)):
    """Get the current user's app settings."""
    service = AuthService()
    settings = await service.get_user_settings(current_user["uid"])
    return settings


@router.put("/settings")
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update user's app settings (notifications, units, thresholds, etc.)."""
    service = AuthService()
    updated = await service.update_user_settings(current_user["uid"], settings)
    return {"status": "ok", "message": "Settings updated", "data": updated}
