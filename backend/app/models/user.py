"""
User Model — Defines the structure of a user document in Firestore.

Firestore Collection: 'users'
Document ID: Firebase Auth UID (e.g., 'abc123xyz')

This is NOT a database ORM model (like SQLAlchemy).
Firestore is schemaless — these are TYPE HINTS to help you
understand what fields a user document should have.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserSettings:
    """User's app preferences (stored as a nested object in Firestore)."""
    notifications: bool = True
    sound_alerts: bool = True
    vibration: bool = True
    auto_sync: bool = True
    temperature_unit: str = "°C"
    language: str = "English"
    alert_volume: float = 0.8
    hr_alert_threshold: int = 150
    temp_alert_threshold: float = 37.5


@dataclass
class User:
    """
    Represents a parent user in the system.

    Firestore path: users/{uid}
    """
    uid: str                          # Firebase Auth UID
    email: str                        # User's email
    display_name: str = ""            # e.g., "John & Sarah"
    settings: UserSettings = field(default_factory=UserSettings)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for Firestore storage."""
        return {
            "uid": self.uid,
            "email": self.email,
            "display_name": self.display_name,
            "settings": {
                "notifications": self.settings.notifications,
                "sound_alerts": self.settings.sound_alerts,
                "vibration": self.settings.vibration,
                "auto_sync": self.settings.auto_sync,
                "temperature_unit": self.settings.temperature_unit,
                "language": self.settings.language,
                "alert_volume": self.settings.alert_volume,
                "hr_alert_threshold": self.settings.hr_alert_threshold,
                "temp_alert_threshold": self.settings.temp_alert_threshold,
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "User":
        """Create User instance from Firestore document data."""
        settings_data = data.get("settings", {})
        return User(
            uid=data.get("uid", ""),
            email=data.get("email", ""),
            display_name=data.get("display_name", ""),
            settings=UserSettings(**settings_data) if settings_data else UserSettings(),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at"),
        )
