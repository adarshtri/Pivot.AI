"""LLM Factory — Singleton provider for shared, rate-limited LLM clients."""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.scoring.llm import LLMProvider, OllamaClient, GroqClient

logger = logging.getLogger(__name__)

class LLMFactory:
    """Manager for a shared LLM client to ensure global rate limiting."""
    
    _instance: LLMProvider | None = None
    _current_config: dict | None = None

    @classmethod
    async def get_provider(cls, db: AsyncIOMotorDatabase) -> LLMProvider:
        """Get (or create) the shared LLM provider instance based on current settings."""
        settings = await db.admin_settings.find_one({"_id": "settings"}) or {}
        provider_type = settings.get("model_provider", "ollama")
        model_name = settings.get("model_name", "phi4-mini")
        api_key = settings.get("llm_api_key", "")
        
        # Rate limit settings
        calls_per_minute = settings.get("llm_max_calls_per_minute", 15)
        min_delay = settings.get("llm_min_delay_seconds", 4.0)

        # Config fingerprint to detect changes
        config = {
            "type": provider_type,
            "model": model_name,
            "api_key_hash": hash(api_key),
            "cpm": calls_per_minute,
            "delay": min_delay
        }

        # If instance exists and config hasn't changed, return existing
        if cls._instance and cls._current_config == config:
            return cls._instance

        # Otherwise, recreate
        if cls._instance:
            logger.info("Configuration changed. Recreating LLM provider.")
            await cls._instance.close()

        logger.info("Initializing new LLM provider for %s: %s (Limit: %d cpm)", provider_type, model_name, calls_per_minute)
        
        if provider_type == "groq":
            cls._instance = GroqClient(
                api_key=api_key,
                model=model_name,
                min_delay_seconds=min_delay,
                calls_per_minute=calls_per_minute
            )
        else:
            cls._instance = OllamaClient(model=model_name)
            
        cls._current_config = config
        return cls._instance

    @classmethod
    async def close_all(cls):
        """Shutdown the shared client."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            cls._current_config = None
