import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId

from app.database import get_db
from app.auth import get_current_user
from app.scoring.insights import InsightsEngine
from app.models.insights import InsightsResponse, InsightItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/insights", tags=["Insights"])

@router.get("", response_model=InsightsResponse)
async def get_insights(user_id: str = Depends(get_current_user)) -> InsightsResponse:
    """Fetch all generated insights for the current user, sorted by created_at descending."""
    db = get_db()
    cursor = db.insights.find({"user_id": user_id}).sort("created_at", -1)
    insights = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        insights.append(InsightItem(**doc))
    
    # Get the latest update time from the most recent insight, or now
    updated_at = insights[0].created_at if insights else datetime.now(timezone.utc)
    
    return InsightsResponse(insights=insights, updated_at=updated_at)

@router.post("/run", status_code=202)
async def trigger_insights_generation(user_id: str = Depends(get_current_user)) -> dict:
    """Manually trigger the Insights Engine for the current user in the background."""
    db = get_db()
    engine = InsightsEngine(db)

    async def _run():
        try:
            summary = await engine.run(user_id)
            logger.info("Background insights generation complete for %s: %s", user_id, summary)
        except Exception:
            logger.exception("Background insights generation failed for %s", user_id)
        finally:
            await engine.cleanup()

    import asyncio
    asyncio.create_task(_run())
    
    return {"status": "accepted", "message": "Insights generation started in background"}

@router.delete("/{insight_id}", status_code=204)
async def delete_insight(insight_id: str, user_id: str = Depends(get_current_user)):
    """Delete a specific insight for the current user."""
    db = get_db()
    try:
        result = await db.insights.delete_one({"_id": ObjectId(insight_id), "user_id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Insight not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid insight ID")
