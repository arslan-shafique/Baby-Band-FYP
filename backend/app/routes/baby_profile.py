"""
Baby Profile Routes
CRUD operations for managing baby profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.middleware.firebase_auth import get_current_user
from app.schemas.baby_profile import (
    BabyProfileCreate,
    BabyProfileUpdate,
    BabyProfileResponse,
)
from app.firebase_client import get_firestore_client

router = APIRouter()


@router.get("/profile", response_model=List[BabyProfileResponse])
async def get_baby_profiles(current_user: dict = Depends(get_current_user)):
    """
    Get all baby profiles for the current user.
    A parent can have multiple babies registered.
    """
    db = get_firestore_client()
    docs = (
        db.collection("baby_profiles")
        .where("user_id", "==", current_user["uid"])
        .stream()
    )

    profiles = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        profiles.append(data)

    return profiles


@router.post("/profile", response_model=BabyProfileResponse, status_code=201)
async def create_baby_profile(
    profile: BabyProfileCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new baby profile linked to the current user."""
    db = get_firestore_client()

    profile_data = profile.model_dump()
    profile_data["user_id"] = current_user["uid"]
    profile_data["created_at"] = None  # Firestore server timestamp

    from google.cloud.firestore import SERVER_TIMESTAMP
    profile_data["created_at"] = SERVER_TIMESTAMP

    doc_ref = db.collection("baby_profiles").add(profile_data)
    doc_id = doc_ref[1].id

    profile_data["id"] = doc_id
    profile_data["created_at"] = None  # Will be set by Firestore
    return profile_data


@router.put("/profile/{profile_id}", response_model=BabyProfileResponse)
async def update_baby_profile(
    profile_id: str,
    update_data: BabyProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing baby profile."""
    db = get_firestore_client()
    doc_ref = db.collection("baby_profiles").document(profile_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Baby profile not found")

    # Verify ownership
    if doc.to_dict().get("user_id") != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Not your baby profile")

    # Only update non-None fields
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

    from google.cloud.firestore import SERVER_TIMESTAMP
    update_dict["updated_at"] = SERVER_TIMESTAMP

    doc_ref.update(update_dict)

    # Return updated document
    updated_doc = doc_ref.get().to_dict()
    updated_doc["id"] = profile_id
    return updated_doc


@router.delete("/profile/{profile_id}")
async def delete_baby_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a baby profile."""
    db = get_firestore_client()
    doc_ref = db.collection("baby_profiles").document(profile_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Baby profile not found")

    if doc.to_dict().get("user_id") != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Not your baby profile")

    doc_ref.delete()
    return {"status": "ok", "message": "Baby profile deleted"}
