"""Goals API — create/update and retrieve user career goals."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.auth import get_current_user
from app.models.user import GoalsPayload, GoalsResponse

router = APIRouter(prefix="/api/v1/goals", tags=["Goals"])


@router.post("", response_model=GoalsResponse, status_code=200)
async def upsert_goals(payload: GoalsPayload, user_id: str = Depends(get_current_user)) -> GoalsResponse:
    """Create or update career goals for the current user."""
    db = get_db()
    now = datetime.now(timezone.utc)

    # Use the user_id from the token, ignore payload.user_id
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"goals": [g.model_dump() for g in payload.goals], "goals_updated_at": now}},
        upsert=True,
    )

    # Return the full goals record
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return GoalsResponse(
        user_id=user_id,
        goals=user.get("goals", []),
        updated_at=user.get("goals_updated_at", now),
    )


@router.get("", response_model=GoalsResponse)
async def get_goals(user_id: str = Depends(get_current_user)) -> GoalsResponse:
    """Retrieve career goals for the current user."""
    db = get_db()
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: '{user_id}'")

    return GoalsResponse(
        user_id=user_id,
        goals=user.get("goals", []),
        updated_at=user.get("goals_updated_at", datetime.now(timezone.utc)),
    )

@router.get("/{user_id}", response_model=GoalsResponse, include_in_schema=False)
async def get_goals_legacy(user_id: str) -> GoalsResponse:
    """Legacy support - fallback for unmigrated frontend calls."""
    return await get_goals(user_id=user_id)
