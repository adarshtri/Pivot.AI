"""Job Scoring Tools for Pivot.AI (Playbook-Compatible)."""

import logging
from app.scoring.engine import ScoringEngine
from app.repository import FileRepository

logger = logging.getLogger("mcp.tools.scoring")

async def score_job(job_id: str) -> str:
    """
    Run AI scoring and reasoning for a specific job (JSON-backed).
    :param job_id: The ID of the job to score.
    """
    logger.info(f"Scoring job: {job_id}")
    repo = FileRepository()
    engine = ScoringEngine(repo)
    result = await engine.score_job(job_id)
    return f"🎯 Scoring complete for {job_id}: {result}"

async def list_matches(min_score: int = 70) -> str:
    """
    List high-scoring job matches from local JSON history.
    :param min_score: Minimum matching score to include.
    """
    repo = FileRepository()
    engine = ScoringEngine(repo)
    matches = await engine.list_matches(min_score)
    top_matches = matches[:5]
    if not top_matches:
        return f"No matches found with score >= {min_score}."
    matches_text = "\n".join([
        f"- {m.get('company')} | {m.get('role')} | Score: {m.get('score')}" 
        for m in top_matches
    ])
    return f"🏆 Top Matches (from local history):\n{matches_text}"
