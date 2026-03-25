"""Goals API — create/update and retrieve user career goals."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.user import GoalsPayload, GoalsResponse

router = APIRouter(prefix="/api/v1/goals", tags=["Goals"])


@router.post("", response_model=GoalsResponse, status_code=200)
async def upsert_goals(payload: GoalsPayload) -> GoalsResponse:
    """Create or update user goals."""
    db = get_db()
    now = datetime.now(timezone.utc)

    doc = payload.model_dump()
    doc["updated_at"] = now

    await db.users.update_one(
        {"user_id": payload.user_id},
        {"$set": {f"goals.{k}": v for k, v in doc.items() if k != "user_id"}},
        upsert=True,
    )

    # Return the full goals record
    user = await db.users.find_one({"user_id": payload.user_id}, {"_id": 0})
    goals_data = user.get("goals", {})
    return GoalsResponse(
        user_id=payload.user_id,
        target_roles=goals_data.get("target_roles", []),
        domains=goals_data.get("domains", []),
        locations=goals_data.get("locations", []),
        career_direction=goals_data.get("career_direction", ""),
        updated_at=goals_data.get("updated_at", now),
    )


@router.get("/{user_id}", response_model=GoalsResponse)
async def get_goals(user_id: str) -> GoalsResponse:
    """Retrieve user goals by user_id."""
    db = get_db()
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: '{user_id}'")

    goals_data = user.get("goals", {})
    if not goals_data:
        raise HTTPException(status_code=404, detail=f"Goals not set for user '{user_id}'")

    return GoalsResponse(
        user_id=user_id,
        target_roles=goals_data.get("target_roles", []),
        domains=goals_data.get("domains", []),
        locations=goals_data.get("locations", []),
        career_direction=goals_data.get("career_direction", ""),
        updated_at=goals_data.get("updated_at", datetime.now(timezone.utc)),
    )
