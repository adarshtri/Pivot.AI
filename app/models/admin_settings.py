"""Admin settings model — singleton stored in MongoDB."""

from pydantic import BaseModel, Field


class AdminSettings(BaseModel):
    """System-wide settings managed by the admin."""

    brave_search_api_key: str = ""
    model_provider: str = "ollama"  # "ollama" or "groq"
    model_name: str = "phi4-mini"
    llm_api_key: str = ""
    ingestion_interval_hours: int = 6
    discovery_interval_hours: int = 24


class AdminSettingsResponse(AdminSettings):
    """Response model (hides the API key partially)."""

    brave_search_api_key_set: bool = False
    llm_api_key_set: bool = False

    @classmethod
    def from_settings(cls, s: AdminSettings) -> "AdminSettingsResponse":
        return cls(
            brave_search_api_key="",  # never expose the key
            llm_api_key="",           # never expose the key
            brave_search_api_key_set=bool(s.brave_search_api_key),
            llm_api_key_set=bool(s.llm_api_key),
            model_provider=s.model_provider,
            model_name=s.model_name,
            ingestion_interval_hours=s.ingestion_interval_hours,
            discovery_interval_hours=s.discovery_interval_hours,
        )
