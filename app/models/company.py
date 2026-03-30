"""Company data model."""

from datetime import datetime

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company record for intelligence and watchlists."""

    name: str
    source: str = Field("", description="ATS platform: greenhouse, lever")
    domain: str | None = ""
    stage: str | None = Field("", description="e.g. Series A, B, C, Public")
    size: str | None = Field("", description="Number of employees")
    description: str | None = ""
    priority_tag: str = ""
    discovered_via: str = Field("", description="How discovered: manual, brave_search")


class CompanyResponse(BaseModel):
    """Company data returned to API consumers."""

    name: str
    source: str = ""
    domain: str | None = ""
    stage: str | None = ""
    size: str | None = ""
    description: str | None = ""
    priority_tag: str = ""
    discovered_via: str = ""
    open_jobs_count: int = 0
    closed_jobs_count: int = 0
    
    # Per-user matching fields
    user_match_score: float | None = None
    user_match_verdict: str | None = None
    user_match_rationale: str | None = None
