"""AI Scoring Engine for evaluating job fit against user profiles."""

import logging
import hashlib
import json
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.scoring.embeddings import EmbeddingsService
from app.scoring.llm import LLMProvider, OllamaClient, GroqClient

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Evaluates jobs against a user's profile using semantic AI and heuristics."""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        # Lazy initialization of the embeddings model
        self._embeddings_service: EmbeddingsService | None = None
        self._llm_client: LLMProvider | None = None

    def _get_embeddings_service(self) -> EmbeddingsService:
        if self._embeddings_service is None:
            self._embeddings_service = EmbeddingsService()
        return self._embeddings_service

    async def _get_llm_client(self) -> LLMProvider:
        if self._llm_client is None:
            settings = await self._db.admin_settings.find_one({"_id": "settings"}) or {}
            provider = settings.get("model_provider", "ollama")
            model_name = settings.get("model_name", "phi4-mini")
            
            if provider == "groq":
                self._llm_client = GroqClient(
                    api_key=settings.get("llm_api_key", ""),
                    model=model_name
                )
            else:
                self._llm_client = OllamaClient(model=model_name)
                
        return self._llm_client

    async def run(self, user_id: str) -> dict:
        """Score all unscored (or updated) jobs for the given user."""
        # 1. Fetch user data
        user = await self._db.users.find_one({"user_id": user_id})
        if not user:
            logger.warning("Scoring failed: User '%s' not found.", user_id)
            return {"status": "skipped", "reason": "User not found"}
            
        goals = user.get("goals", [])
        
        # Compute a content fingerprint of the current goals.
        # If it matches what's stored on a pipeline item, skip re-scoring.
        goals_fingerprint = hashlib.md5(
            json.dumps(goals, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        logger.info("Scoring run for user %s | goals fingerprint: %s", user_id, goals_fingerprint)
        
        embed_svc = self._get_embeddings_service()

        # 2. Iterate through jobs
        total_jobs = await self._db.jobs.count_documents({})
        cursor = self._db.jobs.find({})
        scored_count = 0
        skipped_count = 0
        updated_count = 0
        import time
        _start = time.monotonic()
        
        # Pre-fetch existing pipeline to avoid overwriting user statuses (like "saved")
        pipeline_lookup = {}
        async for p in self._db.pipeline.find({"user_id": user_id}):
            pipeline_lookup[p["job_id"]] = p

        async for job in cursor:
            # Skip if ignored or goals haven't changed since last scoring
            existing = pipeline_lookup.get(job["job_id"])
            if existing:
                if existing.get("status") == "ignored":
                    skipped_count += 1
                    continue
                    
                if existing.get("goals_fingerprint") == goals_fingerprint:
                    skipped_count += 1
                    if (skipped_count + scored_count) % 50 == 0:
                        elapsed = time.monotonic() - _start
                        logger.info(
                            "Scoring progress: %d scored, %d skipped / %d total (%.1fs)",
                            scored_count, skipped_count, total_jobs, elapsed
                        )
                    continue

            job_vector = job.get("vector")
            if not job_vector:
                # Generate and cache job embedding
                job_text = f"Title: {job.get('role', '')}. "
                job_text += f"Company: {job.get('company', '')}. "
                job_text += f"Location: {job.get('location', '')}. "
                desc = job.get('description', '')[:2000]
                job_text += f"Description: {desc}"
                
                job_vector = await embed_svc.embed_text(job_text)
                if job_vector:
                    await self._db.jobs.update_one(
                        {"job_id": job["job_id"]}, 
                        {"$set": {"vector": job_vector}}
                    )
            
            if not job_vector:
                continue
                
            # 3. Compute score per goal
            goal_scores = {}
            total_weight = 0.0
            weighted_score_sum = 0.0
            
            for goal in goals:
                g_id = goal.get("id", "")
                g_type = goal.get("type", "Unknown")
                g_text = goal.get("text", "")
                g_weight = float(goal.get("weight", 1.0))
                
                if not g_text or not g_id:
                    continue
                    
                total_weight += g_weight
                g_vector = await embed_svc.embed_text(g_text)
                
                if job_vector and g_vector:
                    sim = embed_svc.compute_similarity(g_vector, job_vector)
                    # Normalize BGE Cosine Similarity (~0.3 to 1.0) into a 0-100 rubric scale
                    base_score = max(0.0, sim * 100.0)
                    clamped_score = min(100.0, base_score)
                    
                    goal_scores[g_text] = {
                        "score": round(clamped_score, 1),
                        "weight": g_weight,
                        "category": g_type
                    }
                    weighted_score_sum += clamped_score * g_weight
            
            if total_weight > 0:
                final_score = weighted_score_sum / total_weight
            else:
                final_score = 0.0
            
            # 4. Sieve and Scalpel Logic
            if round(final_score) >= 50:
                rationale = "Pending LLM Reasoning"
            else:
                rationale = "Mathematically filtered by priority rubric."

            # 5. Determine status and upsert to pipeline
            existing = pipeline_lookup.get(job["job_id"])
            current_status = existing.get("status", "recommended") if existing else "recommended"

            now = datetime.now(timezone.utc)
            
            # When rescoring, always reset the LLM fields so stale verdicts
            # don't show alongside a "Pending LLM Reasoning" rationale.
            llm_verdict_reset = None
            
            await self._db.pipeline.update_one(
                {"user_id": user_id, "job_id": job["job_id"]},
                {
                    "$set": {
                        "score": round(final_score, 1),
                        "goal_scores": goal_scores,
                        "status": current_status,
                        "rationale": rationale,
                        "llm_verdict": llm_verdict_reset,
                        "goals_fingerprint": goals_fingerprint,
                        "updated_at": now
                    }
                },
                upsert=True
            )
            scored_count += 1
            if existing:
                updated_count += 1
            
            if scored_count % 50 == 0:
                elapsed = time.monotonic() - _start
                logger.info(
                    "Scoring progress: %d scored, %d skipped / %d total (%.1fs elapsed)",
                    scored_count, skipped_count, total_jobs, elapsed
                )

        summary = {
            "status": "completed", 
            "total_scored": scored_count,
            "total_skipped": skipped_count,
            "new_pipeline_items": scored_count - updated_count
        }
        logger.info("Scoring Engine completed for user %s: %s", user_id, summary)
        
        # Cleanup
        if self._llm_client:
            await self._llm_client.close()
            
        return summary

    async def run_inference(self, user_id: str) -> dict:
        """Run the LLM Scalpel on jobs whose LLM fingerprint is stale or missing."""
        user = await self._db.users.find_one({"user_id": user_id})
        if not user:
            return {"status": "skipped", "reason": "User not found"}
        
        goals = user.get("goals", [])
        
        # Compute the LLM's own independent goals fingerprint.
        # This lets inference run and skip correctly regardless of whether
        # math scoring was run first.
        llm_fingerprint = hashlib.md5(
            json.dumps(goals, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        logger.info("LLM inference run for user %s | fingerprint: %s", user_id, llm_fingerprint)

        # Query high-scoring jobs that haven't been ignored or applied yet.
        candidate_cursor = self._db.pipeline.find({
            "user_id": user_id,
            "score": {"$gte": 49.5},
            "status": {"$in": ["recommended", "saved"]}
        }).sort("score", -1).limit(50)

        
        inferred_count = 0
        skipped_count = 0
        import time
        _start = time.monotonic()
        llm = await self._get_llm_client()
        
        async for p in candidate_cursor:
            # Skip if already inferred with the current goals state
            if p.get("llm_goals_fingerprint") == llm_fingerprint:
                skipped_count += 1
                continue

            job = await self._db.jobs.find_one({"job_id": p["job_id"]})
            if not job:
                continue
                
            result = await llm.generate_rationale(job, goals)
            
            await self._db.pipeline.update_one(
                {"user_id": user_id, "job_id": job["job_id"]},
                {"$set": {
                    "rationale": result.get("reasoning", ""),
                    "llm_verdict": result.get("verdict", "Moderate Match"),
                    "llm_goals_fingerprint": llm_fingerprint,
                }}
            )
            inferred_count += 1
            
            total_processed = inferred_count + skipped_count
            if total_processed % 10 == 0:
                elapsed = time.monotonic() - _start
                logger.info(
                    "LLM inference progress: %d inferred, %d skipped (%.1fs elapsed)",
                    inferred_count, skipped_count, elapsed
                )
            
        if self._llm_client:
            await self._llm_client.close()

        summary = {"status": "completed", "inferred_jobs": inferred_count, "skipped_jobs": skipped_count}
        logger.info("LLM inference complete for user %s: %s", user_id, summary)
        return summary
