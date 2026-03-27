from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class LearningStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"

class LearningItem(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    skill_name: str
    status: LearningStatus = LearningStatus.PLANNED
    origin_insight_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class LearningHubResponse(BaseModel):
    items: List[LearningItem]
    updated_at: datetime
