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


from enum import Enum

class GoalType(str, Enum):
    LOCATION = "Location"
    CAREER_DIRECTION = "Career Direction"
    DOMAIN = "Domain"
    TARGET_ROLE = "Target Role"

class UserGoal(BaseModel):
    """A granular rubric goal with an explicit priority weight."""
    
    id: str
    type: GoalType = GoalType.TARGET_ROLE
    text: str
    weight: float = 1.0


class GoalsPayload(BaseModel):
    """Request body for creating/updating user goals."""

    user_id: str
    goals: list[UserGoal] = Field(default_factory=list)


class GoalsResponse(BaseModel):
    """Goals data returned to API consumers."""

    user_id: str
    goals: list[UserGoal]
    updated_at: datetime
