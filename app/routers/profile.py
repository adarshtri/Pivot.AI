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

@router.post("/{user_id}/resume/tailor/{job_id}", status_code=202)
async def tailor_resume(user_id: str, job_id: str) -> dict:
    """Trigger LLM resume tailoring in the background."""
    db = get_db()
    from app.scoring.resume import ResumeEngine
    engine = ResumeEngine(db)

    import asyncio
    import logging
    logger = logging.getLogger(__name__)

    async def _run():
        try:
            result = await engine.tailor(user_id, job_id)
            logger.info("Resume tailoring complete for %s (job: %s)", user_id, job_id)
        except Exception:
            logger.exception("Resume tailoring failed for %s", user_id)

    asyncio.create_task(_run())
    return {"status": "accepted", "message": "Resume tailoring started in background"}

@router.get("/{user_id}/resume/tailored/{job_id}")
async def get_tailored_resume(user_id: str, job_id: str) -> dict:
    """Retrieve a previously generated tailored resume."""
    db = get_db()
    doc = await db.tailored_resumes.find_one({"user_id": user_id, "job_id": job_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    return doc
