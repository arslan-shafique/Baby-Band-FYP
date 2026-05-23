"""
Firebase Auth Middleware
Verifies the Firebase ID token sent by the Flutter app.

HOW IT WORKS (for beginners):
1. User logs in via Firebase Auth in Flutter → gets an ID token
2. Flutter sends this token in the Authorization header: "Bearer <token>"
3. This middleware extracts the token and verifies it with Firebase
4. If valid, the decoded user info (uid, email) is passed to the route handler
5. If invalid/missing, returns 401 Unauthorized

USAGE IN ROUTES:
    @router.get("/protected-endpoint")
    async def my_endpoint(current_user: dict = Depends(get_current_user)):
        uid = current_user["uid"]
        email = current_user["email"]
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

# This creates the "Bearer token" extractor
# It looks for "Authorization: Bearer <token>" in request headers
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency that verifies the Firebase ID token and returns user info.

    Returns:
        dict with keys: uid, email, name, email_verified, etc.

    Raises:
        HTTPException 401 if token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Verify the token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)

        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email", ""),
            "name": decoded_token.get("name", ""),
            "email_verified": decoded_token.get("email_verified", False),
        }

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
