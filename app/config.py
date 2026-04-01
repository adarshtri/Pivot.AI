"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "pivot_ai"

    # Brave Search    # Ingestion & Discovery
    brave_search_api_key: str = ""

    # Authentication (Clerk)
    clerk_issuer_url: str = ""
    clerk_audience: str = ""

    # Scheduler
    ingestion_interval_hours: int = 6
    discovery_interval_hours: int = 24

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
