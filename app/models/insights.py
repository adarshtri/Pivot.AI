from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class InsightAction(BaseModel):
    label: str
    action_type: str  # e.g., "update_goal", "learn_skill", "view_jobs"
    payload: Optional[dict] = None

class InsightItem(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    type: str  # "skill_gap", "goal_conflict", "market_trend", "trajectory"
    title: str
    content: str  # Detailed explanation (optional markdown)
    structured_items: List[dict] = []  # [{ "label": "K8s", "status": "Highly Recommended", "priority": "urgent" }]
    priority: int = 1  # 1 (High) to 3 (Low)
    recommendations: List[str] = []
    actions: List[InsightAction] = []
    created_at: datetime
    metadata: Optional[dict] = {}

    class Config:
        populate_by_name = True

class InsightsResponse(BaseModel):
    insights: List[InsightItem]
    updated_at: datetime
