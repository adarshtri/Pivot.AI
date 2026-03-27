import logging
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timezone
from bson import ObjectId

from app.database import get_db
from app.models.learning import LearningItem, LearningHubResponse, LearningStatus
from app.scoring.engine import ScoringEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/learning", tags=["Learning Hub"])

@router.get("", response_model=LearningHubResponse)
async def get_learning_hub(user_id: str = "user1") -> LearningHubResponse:
    db = get_db()
    cursor = db.learning_hub.find({"user_id": user_id}).sort("created_at", -1)
    items = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(LearningItem(**doc))
    
    updated_at = items[0].updated_at if items else datetime.now(timezone.utc)
    return LearningHubResponse(items=items, updated_at=updated_at)

@router.post("", response_model=LearningItem)
async def add_learning_item(skill_name: str, origin_insight_id: str = None, user_id: str = "user1"):
    db = get_db()
    
    # Check if already tracking
    existing = await db.learning_hub.find_one({"user_id": user_id, "skill_name": skill_name})
    if existing:
        return LearningItem(**{**existing, "_id": str(existing["_id"])})

    now = datetime.now(timezone.utc)
    item = {
        "user_id": user_id,
        "skill_name": skill_name,
        "status": LearningStatus.PLANNED,
        "origin_insight_id": origin_insight_id,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.learning_hub.insert_one(item)
    item["_id"] = str(result.inserted_id)
    return LearningItem(**item)

@router.patch("/{item_id}", response_model=LearningItem)
async def update_learning_status(item_id: str, status: LearningStatus, user_id: str = "user1"):
    db = get_db()
    now = datetime.now(timezone.utc)
    
    result = await db.learning_hub.find_one_and_update(
        {"_id": ObjectId(item_id), "user_id": user_id},
        {"$set": {"status": status, "updated_at": now}},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
        
    result["_id"] = str(result["_id"])
    return LearningItem(**result)

@router.post("/{item_id}/promote")
async def promote_to_profile(item_id: str, background_tasks: BackgroundTasks, user_id: str = "user1"):
    """Move mastered skill to user profile and trigger re-scoring."""
    db = get_db()
    
    item = await db.learning_hub.find_one({"_id": ObjectId(item_id), "user_id": user_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    skill_name = item["skill_name"]
    
    # 1. Update User Profile
    await db.users.update_one(
        {"user_id": user_id},
        {"$addToSet": {"skills": skill_name}}
    )
    
    # 2. Mark as Mastered in Hub
    await db.learning_hub.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {"status": LearningStatus.MASTERED, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # 3. Trigger Re-Scoring in background
    engine = ScoringEngine(db)
    background_tasks.add_task(engine.run, user_id)
    
    return {"status": "success", "message": f"Skill '{skill_name}' added to profile. Re-scoring started."}

@router.delete("/{item_id}", status_code=204)
async def delete_learning_item(item_id: str, user_id: str = "user1"):
    db = get_db()
    await db.learning_hub.delete_one({"_id": ObjectId(item_id), "user_id": user_id})
