"""Admin settings model — singleton stored in MongoDB."""

from pydantic import BaseModel, Field


class AdminSettings(BaseModel):
    """System-wide settings managed by the admin."""

    brave_search_api_key: str = ""
    ingestion_interval_hours: int = 6
    discovery_interval_hours: int = 24


class AdminSettingsResponse(AdminSettings):
    """Response model (hides the API key partially)."""

    brave_search_api_key_set: bool = False

    @classmethod
    def from_settings(cls, s: AdminSettings) -> "AdminSettingsResponse":
        return cls(
            brave_search_api_key="",  # never expose the key
            brave_search_api_key_set=bool(s.brave_search_api_key),
            ingestion_interval_hours=s.ingestion_interval_hours,
            discovery_interval_hours=s.discovery_interval_hours,
        )
