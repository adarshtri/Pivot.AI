"""Profile API — create/update and retrieve user profiles."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.auth import get_current_user
from app.models.user import ProfilePayload, ProfileResponse

router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


@router.post("", response_model=ProfileResponse, status_code=200)
async def upsert_profile(payload: ProfilePayload, user_id: str = Depends(get_current_user)) -> ProfileResponse:
    """Create or update a user profile (for the authenticated user)."""
    db = get_db()
    now = datetime.now(timezone.utc)

    doc = payload.model_dump(exclude_unset=True)
    doc["user_id"] = user_id # Force session-based user_id
    doc["updated_at"] = now

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": doc},
        upsert=True,
    )

    return ProfileResponse(**doc)


@router.get("", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user)) -> ProfileResponse:
    """Retrieve the current user's profile."""
    db = get_db()
    doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        # Should be auto-provisioned in auth.py, but safeguard here
        raise HTTPException(status_code=404, detail=f"Profile not found for user '{user_id}'")
    return ProfileResponse(**doc)

@router.get("/{user_id}", response_model=ProfileResponse, include_in_schema=False)
async def get_profile_by_id_legacy(user_id: str) -> ProfileResponse:
    """Legacy support - should be migrated on frontend."""
    return await get_profile(user_id=user_id)


@router.post("/resume/tailor/{job_id}", status_code=202)
async def tailor_resume(job_id: str, user_id: str = Depends(get_current_user)) -> dict:
    """Trigger LLM resume tailoring for the current user."""
    db = get_db()
    from app.scoring.resume import ResumeEngine
    engine = ResumeEngine(db)

    import asyncio
    import logging
    logger = logging.getLogger(__name__)

    async def _run():
        try:
            await engine.tailor(user_id, job_id)
            logger.info("Resume tailoring complete for %s (job: %s)", user_id, job_id)
        except Exception:
            logger.exception("Resume tailoring failed for %s", user_id)

    asyncio.create_task(_run())
    return {"status": "accepted", "message": "Resume tailoring started in background"}


@router.get("/resume/tailored/{job_id}")
async def get_tailored_resume(job_id: str, user_id: str = Depends(get_current_user)) -> dict:
    """Retrieve the current user's tailored resume for a job."""
    db = get_db()
    doc = await db.tailored_resumes.find_one({"user_id": user_id, "job_id": job_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    return doc
