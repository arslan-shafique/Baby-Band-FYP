"""
Quick script to get a Firebase ID Token for testing the API.
"""

import requests
import json

# ══════════════════════════════════════════════════════════════
# 🔧 CONFIGURE THESE VALUES
# ══════════════════════════════════════════════════════════════

FIREBASE_WEB_API_KEY = "AIzaSyAuZDeJsbHbrNBYw01C_O-JOptdeb63QzM"

TEST_EMAIL = "admin@gmail.com"
TEST_PASSWORD = "admin12345"

# ══════════════════════════════════════════════════════════════


def get_id_token():
    """
    Sign in using Firebase REST API and get an ID token.
    This is the same thing the Flutter app does behind the scenes.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "returnSecureToken": True,
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        token = data["idToken"]

        print("✅ Successfully signed in!")
        print(f"📧 Email: {data['email']}")
        print(f"🆔 UID: {data['localId']}")
        print(f"\n🔑 Your ID Token (copy this):\n")
        print(token)
        print(f"\n📋 Use this in Swagger UI:")
        print(f"   1. Open http://127.0.0.1:8000/docs")
        print(f"   2. Click the 🔓 'Authorize' button (top right)")
        print(f"   3. Paste the token above (without 'Bearer ' prefix)")
        print(f"   4. Click 'Authorize' → now all endpoints will work!")
        return token
    else:
        error = response.json().get("error", {})
        print(f"❌ Login failed: {error.get('message', 'Unknown error')}")
        print(f"   Status: {response.status_code}")
        print(f"\n💡 Common fixes:")
        print(f"   - Check your FIREBASE_WEB_API_KEY is correct")
        print(f"   - Make sure the user exists in Firebase Console → Authentication")
        print(f"   - Make sure Email/Password sign-in is enabled")
        return None


if __name__ == "__main__":
    get_id_token()
