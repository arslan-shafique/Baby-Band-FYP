"""
Firebase Admin SDK Client
Initializes the Firebase connection and provides the Firestore database client.

HOW IT WORKS (for beginners):
1. Firebase Admin SDK lets your Python backend talk to Firebase services
2. You need a "service account key" JSON file from Firebase Console
3. This file initializes the connection ONCE when the app starts
4. Other files import `get_firestore_client()` to read/write data
"""

import firebase_admin
from firebase_admin import credentials, firestore
from app.config import get_settings

# Global variable to hold the Firestore client
_firestore_client = None


def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK.
    Called once at app startup from main.py.

    Steps to get your service account key:
    1. Go to Firebase Console → Your Project → Project Settings
    2. Click "Service Accounts" tab
    3. Click "Generate New Private Key"
    4. Save the JSON file as 'firebase-service-account.json' in backend/
    """
    settings = get_settings()

    # Only initialize if not already done (prevents errors on hot reload)
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': settings.FIREBASE_RTDB_URL
        })
        print("✅ Firebase Admin SDK initialized successfully")


def get_firestore_client():
    """
    Returns the Firestore database client.
    Usage:
        db = get_firestore_client()
        doc = db.collection('users').document('user123').get()
    """
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.client()
    return _firestore_client
