"""Pipeline models for tracking job match scores and user actions."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PipelineItem(BaseModel):
    """A tracked job in a user's pipeline."""
    
    user_id: str
    job_id: str
    score: float = 0.0
    status: str = "recommended"  # recommended, saved, applied, ignored
    rationale: str = ""
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
    pipeline_status: str
    pipeline_rationale: str
    pipeline_updated_at: datetime
