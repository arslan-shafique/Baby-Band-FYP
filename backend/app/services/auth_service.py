"""
Auth Service — Handles user profile management with Firebase.

NOTE: Actual authentication (sign up, sign in) is done by Firebase Auth SDK
in the Flutter app. This service manages the Firestore user document.
"""

from app.firebase_client import get_firestore_client
from app.schemas.user import UserProfileUpdate, UserSettingsUpdate
from app.models.user import User, UserSettings


class AuthService:
    """Service for user profile and settings management."""

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = "users"

    async def get_or_create_user(self, firebase_user: dict) -> dict:
        """
        Get user profile from Firestore, or create one if it's their first login.

        Args:
            firebase_user: Decoded Firebase token data (uid, email, etc.)
        """
        uid = firebase_user["uid"]
        doc_ref = self.db.collection(self.collection).document(uid)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()

        # First-time user — create profile in Firestore
        new_user = User(
            uid=uid,
            email=firebase_user.get("email", ""),
            display_name=firebase_user.get("name", ""),
        )
        doc_ref.set(new_user.to_dict())
        return new_user.to_dict()

    async def update_user_profile(self, uid: str, update_data: UserProfileUpdate) -> dict:
        """Update user's profile fields."""
        doc_ref = self.db.collection(self.collection).document(uid)
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        if update_dict:
            doc_ref.update(update_dict)

        return doc_ref.get().to_dict()

    async def get_user_settings(self, uid: str) -> dict:
        """Get user's app settings."""
        doc = self.db.collection(self.collection).document(uid).get()
        if not doc.exists:
            return UserSettings().__dict__

        data = doc.to_dict()
        return data.get("settings", UserSettings().__dict__)

    async def update_user_settings(self, uid: str, settings: UserSettingsUpdate) -> dict:
        """Update user's app settings. Only updates non-None fields."""
        doc_ref = self.db.collection(self.collection).document(uid)

        # Build nested update dictionary
        updates = {}
        for key, value in settings.model_dump().items():
            if value is not None:
                updates[f"settings.{key}"] = value

        if updates:
            doc_ref.update(updates)

        return doc_ref.get().to_dict().get("settings", {})
