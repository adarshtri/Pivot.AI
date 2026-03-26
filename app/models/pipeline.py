"""Pipeline models for tracking job match scores and user actions."""

from typing import Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PipelineItem(BaseModel):
    """A tracked job in a user's pipeline."""
    
    user_id: str
    job_id: str
    score: float = 0.0
    goal_scores: dict[str, Any] = Field(default_factory=dict)
    status: str = "recommended"  # recommended, saved, applied, ignored
    rationale: str = ""
    ignore_reason: str | None = None
    llm_verdict: str | None = None

    goals_fingerprint: str | None = None
    llm_goals_fingerprint: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PipelineResponse(BaseModel):
    """Response model combining Job details and Pipeline tracking info."""
    
    # We will merge the Job document and PipelineItem document
    job_id: str
    company: str
    role: str
    description: str
    location: str
    url: str
    source: str
    created_at: datetime
    
    pipeline_score: float
    pipeline_goal_scores: dict[str, Any]
    pipeline_status: str
    pipeline_rationale: str
    pipeline_ignore_reason: str | None = None
    pipeline_llm_verdict: str | None = None

    pipeline_updated_at: datetime


class PaginatedPipelineResponse(BaseModel):
    """Response model for a paginated list of pipeline items."""
    
    items: list[PipelineResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    counts: dict[str, int] = Field(default_factory=dict)


