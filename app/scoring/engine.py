"""AI Scoring Engine for evaluating job fit against user profiles."""

import logging
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.scoring.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Evaluates jobs against a user's profile using semantic AI and heuristics."""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        # Lazy initialization of the embeddings model
        self._embeddings_service: EmbeddingsService | None = None

    def _get_embeddings_service(self) -> EmbeddingsService:
        if self._embeddings_service is None:
            self._embeddings_service = EmbeddingsService()
        return self._embeddings_service

    async def run(self, user_id: str) -> dict:
        """Score all unscored (or updated) jobs for the given user."""
        # 1. Fetch user data
        user = await self._db.users.find_one({"user_id": user_id})
        if not user:
            logger.warning("Scoring failed: User '%s' not found.", user_id)
            return {"status": "skipped", "reason": "User not found"}
            
        profile = user.get("skills", []) + [user.get("experience_level", ""), user.get("current_role", "")]
        goals = user.get("goals", {})
        
        # Build a dense user vector representation
        user_text = f"Role: {user.get('current_role', '')}. "
        user_text += f"Experience: {user.get('experience_level', '')}. "
        user_text += f"Skills: {', '.join(user.get('skills', []))}. "
        user_text += f"Target Roles: {', '.join(goals.get('target_roles', []))}. "
        user_text += f"Target Domains: {', '.join(goals.get('domains', []))}. "
        user_text += f"Preferred Locations: {', '.join(goals.get('locations', []))}. "
        user_text += f"Career Direction: {goals.get('career_direction', '')}."
        
        embed_svc = self._get_embeddings_service()
        user_vector = await embed_svc.embed_text(user_text)
        if not user_vector:
            logger.error("Failed to generate user vector for '%s'", user_id)
            return {"status": "failed", "reason": "User embedding failed"}

        # 2. Iterate through jobs
        cursor = self._db.jobs.find({})
        scored_count = 0
        updated_count = 0
        
        # Pre-fetch existing pipeline to avoid overwriting user statuses (like "saved")
        pipeline_lookup = {}
        async for p in self._db.pipeline.find({"user_id": user_id}):
            pipeline_lookup[p["job_id"]] = p

        async for job in cursor:
            # We cache the job vector in the jobs collection itself
            job_vector = job.get("vector")
            if not job_vector:
                # Generate and cache job embedding
                job_text = f"Title: {job.get('role', '')}. "
                job_text += f"Company: {job.get('company', '')}. "
                job_text += f"Location: {job.get('location', '')}. "
                # We truncate description to avoid massive context token lengths
                desc = job.get('description', '')[:2000]
                job_text += f"Description: {desc}"
                
                job_vector = await embed_svc.embed_text(job_text)
                if job_vector:
                    await self._db.jobs.update_one(
                        {"job_id": job["job_id"]}, 
                        {"$set": {"vector": job_vector}}
                    )
            
            if not job_vector:
                continue # Skip if embedding failed entirely
                
            # 3. Compute Semantic Score (0.0 to 1.0)
            cos_sim = embed_svc.compute_similarity(user_vector, job_vector)
            
            # Baseline semantic score out of 70
            semantic_score = cos_sim * 70.0
            
            # 4. Compute Heuristic Score (out of 30)
            heuristic_score = 0.0
            
            # Location bump or penalty (Semantic Match)
            job_loc = job.get("location", "").strip()
            user_locs = [loc.strip() for loc in goals.get("locations", []) if loc.strip()]
            
            is_loc_match = False
            
            # Check for remote explicitly first (often not semantically caught)
            job_loc_lower = job_loc.lower()
            user_locs_lower = [l.lower() for l in user_locs]
            if "remote" in job_loc_lower and "remote" in user_locs_lower:
                is_loc_match = True
            
            # If not explicitly remote, evaluate semantics
            elif user_locs and job_loc:
                # We can generate a quick vector for the job's location string
                job_loc_vector = await embed_svc.embed_text(job_loc)
                
                for user_loc in user_locs:
                    # Simple strict substring check just in case
                    if user_loc.lower() in job_loc_lower or job_loc_lower in user_loc.lower():
                        is_loc_match = True
                        break
                        
                    # Semantic check
                    # (In production, user_loc_vectors could be cached to save ms, but fastembed is fast enough)
                    user_loc_vector = await embed_svc.embed_text(user_loc)
                    if job_loc_vector and user_loc_vector:
                        loc_sim = embed_svc.compute_similarity(user_loc_vector, job_loc_vector)
                        # Threshold of 0.85 ensures we capture formatting differences ("San Jose, CA" vs "San Jose")
                        # but strictly exclude different cities ("San Jose" vs "San Francisco" ~0.78)
                        if loc_sim > 0.85:
                            is_loc_match = True
                            break
                            
            if user_locs and job_loc:
                if is_loc_match:
                    heuristic_score += 15.0
                else:
                    # Severe penalty for geographic mismatch
                    heuristic_score -= 40.0
            
            # Role match bump or penalty (Semantic Match against Job Title)
            job_role = job.get("role", "").strip()
            user_roles = [r.strip() for r in goals.get("target_roles", []) if r.strip()]
            
            if user_roles and job_role:
                job_role_vector = await embed_svc.embed_text(job_role)
                max_role_sim = 0.0
                
                for r in user_roles:
                    # Quick exact substring check
                    if r.lower() in job_role.lower() or job_role.lower() in r.lower():
                        max_role_sim = 1.0
                        break
                        
                    r_vector = await embed_svc.embed_text(r)
                    if job_role_vector and r_vector:
                        r_sim = embed_svc.compute_similarity(r_vector, job_role_vector)
                        max_role_sim = max(max_role_sim, r_sim)
                
                if max_role_sim > 0.70:
                    heuristic_score += 15.0  # Strong title match
                elif max_role_sim < 0.65:
                    # Severe penalty for fundamentally mismatched departments (e.g. Sales vs Engineering)
                    heuristic_score -= 50.0
                
            final_score = min(100.0, semantic_score + heuristic_score)
            
            # 5. Determine status and upsert to pipeline
            existing = pipeline_lookup.get(job["job_id"])
            current_status = existing.get("status", "recommended") if existing else "recommended"
            
            # Formulate a quick rationale
            rationale_parts = []
            if heuristic_score >= 15:
                rationale_parts.append("Location/Role match")
            if semantic_score > 45:
                rationale_parts.append("Strong semantic fit")
            elif semantic_score > 35:
                rationale_parts.append("Moderate semantic fit")
            rationale = " & ".join(rationale_parts) if rationale_parts else "Weak fit"

            now = datetime.now(timezone.utc)
            await self._db.pipeline.update_one(
                {"user_id": user_id, "job_id": job["job_id"]},
                {
                    "$set": {
                        "score": round(final_score, 1),
                        "status": current_status,
                        "rationale": rationale,
                        "updated_at": now
                    }
                },
                upsert=True
            )
            scored_count += 1
            if existing:
                updated_count += 1

        summary = {
            "status": "completed", 
            "total_scored": scored_count, 
            "new_pipeline_items": scored_count - updated_count
        }
        logger.info("Scoring Engine completed for user %s: %s", user_id, summary)
        return summary
