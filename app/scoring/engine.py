"""AI-powered job scoring engine — now works on Plain JSON files."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.repository import FileRepository

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Evaluates jobs against the user's profile and persists scores in JSON."""

    def __init__(self, repo: FileRepository):
        self._repo = repo

    async def score_job(self, job_id: str) -> dict[str, Any]:
        """Run AI scoring and reasoning for a specific job."""
        job = await self._repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        logger.info(f"Scoring job: {job_id} ({job.get('role')})")
        
        # Placeholder for LLM scoring logic
        # In the future, this would fetch from Ollama/Groq using the user profile
        job["score"] = 85 # Mock score for now
        job["rationale"] = "Role matches your background in Python/Rust."
        job["scored_at"] = datetime.now(timezone.utc).isoformat()
        
        await self._repo.upsert_job(job)
        
        return {
            "job_id": job_id,
            "score": job["score"],
            "rationale": job["rationale"]
        }

    async def list_matches(self, min_score: int = 70) -> list[dict[str, Any]]:
        """List high-scoring job matches from the local JSON file."""
        jobs = await self._repo.list_jobs()
        matches = [
            j for j in jobs 
            if j.get("score") and j.get("score") >= min_score
        ]
        
        # Sort by score descending
        matches.sort(key=lambda x: x.get("score", 0), reverse=True)
        return matches
