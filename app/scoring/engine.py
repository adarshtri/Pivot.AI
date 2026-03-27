"""AI Scoring Engine for evaluating job fit against user profiles."""

import logging
import hashlib
import json
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.scoring.embeddings import EmbeddingsService
from app.scoring.llm import LLMProvider, OllamaClient, GroqClient
from app.telegram_utils import send_telegram_message


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
        skills = user.get("skills", [])
        
        # Compute a content fingerprint of the current goals AND skills.
        # If it matches what's stored on a pipeline item, skip re-scoring.
        state_payload = {"goals": goals, "skills": skills}
        state_fingerprint = hashlib.md5(
            json.dumps(state_payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        
        logger.info("Scoring run for user %s | state fingerprint: %s", user_id, state_fingerprint)
        
        embed_svc = self._get_embeddings_service()

        # Pre-compute User Skills Vector
        skills_text = ", ".join(skills)
        skills_vector = await embed_svc.embed_text(skills_text) if skills else None

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
            # Skip if ignored or goals/skills haven't changed since last scoring
            existing = pipeline_lookup.get(job["job_id"])
            if existing:
                if existing.get("status") == "ignored":
                    skipped_count += 1
                    continue
                    
                if existing.get("goals_fingerprint") == state_fingerprint:
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
                
            # 3. Compute Goal Score
            total_weight = 0.0
            weighted_goal_sum = 0.0
            goal_scores = {}
            
            for goal in goals:
                g_text = goal.get("text", "")
                g_weight = float(goal.get("weight", 1.0))
                
                if not g_text:
                    continue
                    
                total_weight += g_weight
                g_vector = await embed_svc.embed_text(g_text)
                
                if job_vector and g_vector:
                    sim = embed_svc.compute_similarity(g_vector, job_vector)
                    clamped_score = min(100.0, max(0.0, sim * 100.0))
                    goal_scores[g_text] = {
                        "score": round(clamped_score, 1),
                        "weight": g_weight
                    }
                    weighted_goal_sum += clamped_score * g_weight
            
            goal_avg = (weighted_goal_sum / total_weight) if total_weight > 0 else 0.0

            # 4. Compute Skill Match Score
            skill_score = 0.0
            if skills_vector and job_vector:
                skill_sim = embed_svc.compute_similarity(skills_vector, job_vector)
                skill_score = min(100.0, max(0.0, skill_sim * 100.0))

            # 5. Blend Final Score (70% Goals, 30% Skills)
            final_score = (goal_avg * 0.7) + (skill_score * 0.3)
            
            # 6. Sieve and Scalpel Logic
            if round(final_score) >= 50:
                rationale = "Pending LLM Reasoning"
            else:
                rationale = "Mathematically filtered by priority & skill match."

            # 7. Determine status and upsert to pipeline
            existing = pipeline_lookup.get(job["job_id"])
            current_status = existing.get("status", "recommended") if existing else "recommended"

            now = datetime.now(timezone.utc)
            
            await self._db.pipeline.update_one(
                {"user_id": user_id, "job_id": job["job_id"]},
                {
                    "$set": {
                        "score": round(final_score, 1),
                        "goal_scores": goal_scores,
                        "skill_score": round(skill_score, 1),
                        "status": current_status,
                        "rationale": rationale,
                        "goals_fingerprint": state_fingerprint,
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
        
        strong_matches = []

        async for p in candidate_cursor:
            # Skip if already inferred with the current goals state
            if p.get("llm_goals_fingerprint") == llm_fingerprint:
                skipped_count += 1
                continue

            job = await self._db.jobs.find_one({"job_id": p["job_id"]})
            if not job:
                continue
                
            result = await llm.generate_rationale(job, goals)
            verdict = result.get("verdict", "Moderate Match")
            
            await self._db.pipeline.update_one(
                {"user_id": user_id, "job_id": job["job_id"]},
                {"$set": {
                    "rationale": result.get("reasoning", ""),
                    "llm_verdict": verdict,
                    "llm_goals_fingerprint": llm_fingerprint,
                }}
            )
            
            # Add to summary candidates (all inferred jobs are score >= 50)
            strong_matches.append({
                "role": job.get("role", "Unknown Role"),
                "company": job.get("company", "Unknown Company"),
                "score": p.get("score", 0.0),
                "url": job.get("url", ""),
                "verdict": verdict
            })

            inferred_count += 1

            
            total_processed = inferred_count + skipped_count
            if total_processed % 10 == 0:
                elapsed = time.monotonic() - _start
                logger.info(
                    "LLM inference progress: %d inferred, %d skipped (%.1fs elapsed)",
                    inferred_count, skipped_count, elapsed
                )

        # Send Telegram Summary for jobs inferred in this run
        if strong_matches and user.get("telegram_token") and user.get("telegram_chat_id"):
            # Sort by score descending and take top 5
            strong_matches.sort(key=lambda x: x["score"], reverse=True)
            top_matches = strong_matches[:5]
            
            summary_lines = [
                "<b>🚀 Top Career Matches Found!</b>",
                f"\nWe analyzed your pipeline and found {len(strong_matches)} strong matches for your goals.\n"
            ]
            
            for i, match in enumerate(top_matches, 1):
                v_icon = "🔥" if match["verdict"] == "Strong Match" else "✨"
                summary_lines.append(
                    f"{i}. {v_icon} <b>{match['role']}</b> at {match['company']}\n"
                    f"   🎯 Score: {match['score']:.0f}/100 | <a href='{match['url']}'>View Job</a>\n"
                )
            
            summary_lines.append(f"\nVisit your dashboard to see all matches: http://localhost:3000/jobs")
            
            await send_telegram_message(
                user["telegram_token"], 
                user["telegram_chat_id"], 
                "\n".join(summary_lines)
            )



        if self._llm_client:

            await self._llm_client.close()

        summary = {"status": "completed", "inferred_jobs": inferred_count, "skipped_jobs": skipped_count}
        logger.info("LLM inference complete for user %s: %s", user_id, summary)
        return summary
