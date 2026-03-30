"""Company Scoring Engine — evaluates companies against user profiles/goals."""

import logging
import json
import re
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.scoring.llm import LLMProvider, OllamaClient, GroqClient

logger = logging.getLogger(__name__)

class CompanyScoringEngine:
    """Layer 6 AI Engine: Evaluates companies for personalized user fit."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._llm_client: LLMProvider | None = None

    async def _get_llm_client(self) -> LLMProvider:
        from app.scoring.llm_factory import LLMFactory
        return await LLMFactory.get_provider(self._db)

    async def score_all_for_user(self, user_id: str, force: bool = False) -> dict:
        """Score all companies for a specific user using batching."""
        logger.info("Starting batch scoring for user: %s (force=%s)", user_id, force)
        
        user = await self._db.users.find_one({"user_id": user_id})
        goals_doc = await self._db.goals.find_one({"user_id": user_id})
        if not user:
            logger.error("User %s not found for scoring", user_id)
            return {"status": "error", "message": "User not found"}

        user_context = {
            "role": user.get("current_role", ""),
            "skills": user.get("skills", []),
            "experience_level": user.get("experience_level", ""),
            "goals": [g["text"] for g in goals_doc.get("goals", [])] if goals_doc else []
        }

        # 1. Fetch only companies not yet scored for this user (unless forced)
        if not force:
            scored_names = await self._db.company_matches.distinct(
                "company_name", 
                {"user_id": user_id}
            )
            query = {
                "description": {"$ne": ""},
                "name": {"$nin": scored_names}
            }
        else:
            query = {"description": {"$ne": ""}}

        companies = await self._db.companies.find(query).to_list(length=1000)
        
        total_companies = len(companies)
        if total_companies == 0:
            logger.info("No new companies to score for %s", user_id)
            return {"status": "completed", "scored_count": 0, "message": "No new companies to score"}

        logger.info("Found %d companies to score for %s", total_companies, user_id)
        
        scored_count = 0
        batch_size = 3
        
        for i in range(0, total_companies, batch_size):
            batch = companies[i : i + batch_size]
            logger.info("Scoring batch [%d/%d] for user %s", i + len(batch), total_companies, user_id)
            
            try:
                scores = await self._score_companies_batch(user_id, batch, user_context)
                scored_count += len(scores)
            except Exception:
                logger.exception("Batch scoring failed for companies: %s", [c["name"] for c in batch])
                # Fallback to individual scoring
                for comp in batch:
                    try:
                        await self.score_company_for_user(user_id, comp["name"], user_context)
                        scored_count += 1
                    except Exception:
                        logger.error("Fallback scoring also failed for %s", comp["name"])

        logger.info("Batch scoring complete: %d companies scored for %s", scored_count, user_id)
        return {"status": "completed", "scored_count": scored_count}

    async def _score_companies_batch(self, user_id: str, companies: list[dict], user_context: dict) -> list[dict]:
        """Score multiple companies in a single LLM call with job summarization."""
        if not companies: return []
        
        company_data = []
        for comp in companies:
            name = comp["name"]
            # Fetch jobs for this company
            jobs = await self._db.jobs.find(
                {"company": name},
                {"role": 1}
            ).sort("created_at", -1).limit(100).to_list(length=100)
            
            # Summarize jobs to save tokens: "Software Engineer (12), Product Manager (2)"
            role_counts = {}
            for j in jobs:
                role = j.get("role", "Unknown")
                role_counts[role] = role_counts.get(role, 0) + 1
            
            role_summary = ", ".join([f"{r} (x{c})" for r, c in role_counts.items()])
            
            company_data.append({
                "name": name,
                "description": comp.get("description", "N/A"),
                "stage": comp.get("stage", "N/A"),
                "size": comp.get("size", "N/A"),
                "hiring_for": role_summary or "No recent jobs found"
            })

        llm = await self._get_llm_client()
        prompt = f"""You are a Strategic Career Matchmaker. Evaluate these companies against the candidate profile.

### CANDIDATE PROFILE:
Current Role: {user_context['role']}
Level: {user_context['experience_level']}
Skills: {", ".join(user_context['skills'])}
Career Goals: {", ".join(user_context['goals'])}

### COMPANIES TO EVALUATE:
{json.dumps(company_data, indent=2)}

### TASK:
Analyze the alignment for EACH company. Provide a score, verdict, and rationale.
Consider both the company's description/stage and their current hiring activity (hiring_for).

Provide the following in JSON:
{{
  "matches": [
    {{
      "name": "company_name",
      "score": 0.0 to 1.0,
      "verdict": "Strong Match" | "Moderate Match" | "Weak Match",
      "rationale": "2-3 sentence explanation"
    }}
  ]
}}
Return ONLY the JSON object."""

        res_text = await llm.generate_text(prompt, temperature=0.0)
        match = re.search(r"\{.*\}", res_text, re.DOTALL)
        if not match:
            logger.error(
                "LLM returned no JSON for batch: %s. Raw Response (first 100 chars): %s", 
                [c["name"] for c in companies], 
                res_text[:100].replace("\n", " ")
            )
            return []
            
        try:
            data = json.loads(match.group(0))
            matches = data.get("matches", [])
            
            # Update DB for each match in batch
            now = datetime.now(timezone.utc)
            for m in matches:
                name = m.get("name")
                if not name: continue
                
                await self._db.company_matches.update_one(
                    {"user_id": user_id, "company_name": name},
                    {
                        "$set": {
                            "score": m.get("score", 0.0),
                            "verdict": m.get("verdict", "Weak Match"),
                            "rationale": m.get("rationale", ""),
                            "updated_at": now
                        }
                    },
                    upsert=True
                )
                logger.debug("Scored %s for user %s: %s (%.2f)", name, user_id, m.get("verdict"), m.get("score", 0.0))
            
            return matches
        except Exception:
            logger.exception("Failed to parse/store batch scoring result")
            return []

    async def score_company_for_user(self, user_id: str, company_name: str, user_context: dict = None) -> dict:
        """Score a specific company (individual fallback)."""
        logger.debug("Falling back to individual scoring for: %s", company_name)
        if not user_context:
            user = await self._db.users.find_one({"user_id": user_id})
            goals_doc = await self._db.goals.find_one({"user_id": user_id})
            user_context = {
                "role": user.get("current_role", ""),
                "skills": user.get("skills", []),
                "experience_level": user.get("experience_level", ""),
                "goals": [g["text"] for g in goals_doc.get("goals", [])] if goals_doc else []
            }

        company = await self._db.companies.find_one({"name": company_name})
        if not company:
            return {}
            
        results = await self._score_companies_batch(user_id, [company], user_context)
        return results[0] if results else {}
