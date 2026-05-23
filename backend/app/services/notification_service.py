"""
Notification Service — Business logic for alerts and notifications.
"""

from datetime import datetime
from typing import Optional
from app.firebase_client import get_firestore_client


class NotificationService:
    """Service for managing parent notifications."""

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = "notifications"

    async def create_notification(
        self,
        user_id: str,
        baby_id: str,
        title: str,
        message: str,
        notif_type: str = "info",
    ) -> str:
        """
        Create a new notification in Firestore.
        Called by other services or Lambda when an alert condition is met.
        """
        data = {
            "user_id": user_id,
            "baby_id": baby_id,
            "type": notif_type,
            "title": title,
            "message": message,
            "is_read": False,
            "created_at": datetime.utcnow(),
        }

        _, doc_ref = self.db.collection(self.collection).add(data)
        
        # --- TRIGGER FCM PUSH NOTIFICATION ---
        try:
            from firebase_admin import messaging
            
            # Fetch the user's FCM token from their profile
            user_doc = self.db.collection("users").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                fcm_token = user_data.get("fcm_token")
                
                # If they have an active FCM token registered from the Flutter app
                if fcm_token:
                    # Construct the Push Notification payload
                    message_payload = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=message,
                        ),
                        data={
                            "type": notif_type,
                            "baby_id": baby_id,
                            "notification_id": doc_ref.id,
                        },
                        token=fcm_token,
                    )
                    
                    # Send the message!
                    response = messaging.send(message_payload)
                    print(f"Successfully sent FCM push notification: {response}")
                else:
                    print(f"User {user_id} does not have an FCM token. Could not send push notification.")
        except Exception as e:
            print(f"Error sending FCM push notification: {e}")

        return doc_ref.id

    async def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> dict:
        """Get notifications for a user."""
        query = (
            self.db.collection(self.collection)
            .where("user_id", "==", user_id)
        )

        if unread_only:
            query = query.where("is_read", "==", False)

        query = query.order_by("created_at", direction="DESCENDING").limit(limit)

        docs = list(query.stream())
        data = []
        unread_count = 0

        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            data.append(item)
            if not item.get("is_read", False):
                unread_count += 1

        return {
            "data": data,
            "total": len(data),
            "unread_count": unread_count,
        }

    async def mark_as_read(self, notification_id: str, user_id: str) -> None:
        """Mark a single notification as read."""
        doc_ref = self.db.collection(self.collection).document(notification_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError("Notification not found")

        if doc.to_dict().get("user_id") != user_id:
            raise PermissionError("Not your notification")

        doc_ref.update({"is_read": True})

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all of a user's notifications as read. Returns count updated."""
        docs = (
            self.db.collection(self.collection)
            .where("user_id", "==", user_id)
            .where("is_read", "==", False)
            .stream()
        )

        count = 0
        for doc in docs:
            doc.reference.update({"is_read": True})
            count += 1

        return count

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for nav badge."""
        docs = (
            self.db.collection(self.collection)
            .where("user_id", "==", user_id)
            .where("is_read", "==", False)
            .stream()
        )
        return sum(1 for _ in docs)
