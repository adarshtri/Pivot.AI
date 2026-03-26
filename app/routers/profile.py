"""Profile API — create/update and retrieve user profiles."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.user import ProfilePayload, ProfileResponse

router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


@router.post("", response_model=ProfileResponse, status_code=200)
async def upsert_profile(payload: ProfilePayload) -> ProfileResponse:
    """Create or update a user profile."""
    db = get_db()
    now = datetime.now(timezone.utc)

    doc = payload.model_dump(exclude_unset=True)
    doc["updated_at"] = now

    await db.users.update_one(
        {"user_id": payload.user_id},
        {"$set": doc},
        upsert=True,
    )


    return ProfileResponse(**doc)


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str) -> ProfileResponse:
    """Retrieve a user profile by user_id."""
    db = get_db()
    doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Profile not found for user '{user_id}'")
    return ProfileResponse(**doc)
