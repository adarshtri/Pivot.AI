"""User profile and goals models."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


# ── Profile ──────────────────────────────────────────────────────────────────


class ProfilePayload(BaseModel):
    """Request body for creating/updating a user profile."""

    user_id: str
    skills: list[str] = Field(default_factory=list)
    experience_level: str = ""
    current_role: str = ""
    is_admin: bool = False


class ProfileResponse(BaseModel):
    """Profile data returned to API consumers."""

    user_id: str
    skills: list[str]
    experience_level: str
    current_role: str
    is_admin: bool = False
    updated_at: datetime


# ── Goals ────────────────────────────────────────────────────────────────────


class GoalsPayload(BaseModel):
    """Request body for creating/updating user goals."""

    user_id: str
    target_roles: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    career_direction: str = ""


class GoalsResponse(BaseModel):
    """Goals data returned to API consumers."""

    user_id: str
    target_roles: list[str]
    domains: list[str]
    locations: list[str]
    career_direction: str
    updated_at: datetime
