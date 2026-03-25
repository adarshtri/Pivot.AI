"""Job data model — normalized schema for all job sources."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Job(BaseModel):
    """Normalized job posting stored in MongoDB."""

    job_id: str = Field(..., description="Unique job identifier from the source")
    company: str
    role: str
    description: str = ""
    location: str = ""
    url: str = ""
    source: str = Field(..., description="Origin: greenhouse, lever, etc.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class JobCreate(BaseModel):
    """Schema for manually creating a job (admin/testing)."""

    job_id: str
    company: str
    role: str
    description: str = ""
    location: str = ""
    url: str = ""
    source: str = "manual"


class JobResponse(BaseModel):
    """Schema returned to API consumers."""

    job_id: str
    company: str
    role: str
    description: str
    location: str
    url: str
    source: str
    created_at: datetime
