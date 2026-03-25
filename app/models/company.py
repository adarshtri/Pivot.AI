"""Company data model."""

from datetime import datetime

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company record for intelligence and watchlists."""

    name: str
    source: str = Field("", description="ATS platform: greenhouse, lever")
    domain: str = ""
    stage: str = Field("", description="e.g. Series A, B, C, Public")
    priority_tag: str = ""
    discovered_via: str = Field("", description="How discovered: manual, brave_search")


class CompanyResponse(BaseModel):
    """Company data returned to API consumers."""

    name: str
    source: str = ""
    domain: str = ""
    stage: str = ""
    priority_tag: str = ""
    discovered_via: str = ""
