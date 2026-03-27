import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.scoring.llm import LLMProvider, OllamaClient, GroqClient
from app.models.insights import InsightItem, InsightAction

logger = logging.getLogger(__name__)

class InsightsEngine:
    """Layer 4 AI Engine: Generates strategic career insights by analyzing pipeline data and market trends."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._llm_client: LLMProvider | None = None

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
        """Run the full insights generation cycle for a user."""
        logger.info("Running Insights Engine for user: %s", user_id)
        
        # 1. Gather Data
        user = await self._db.users.find_one({"user_id": user_id})
        if not user:
            return {"status": "error", "message": "User not found"}

        # A. Top 20 Recommended Jobs (The "Perfect" Benchmark)
        recommended_pipeline = await self._db.pipeline.find(
            {"user_id": user_id, "status": "recommended"}
        ).sort("score", -1).limit(20).to_list(length=20)
        
        job_ids = [p["job_id"] for p in recommended_pipeline]
        recommended_jobs = await self._db.jobs.find({"job_id": {"$in": job_ids}}).to_list(length=20)

        # B. Behavioral Signals (Ignore Reasons)
        ignored_pipeline = await self._db.pipeline.find(
            {"user_id": user_id, "status": "ignored", "ignore_reason": {"$ne": None}}
        ).sort("updated_at", -1).limit(10).to_list(length=10)

        # 2. Prepare LLM Context
        context_str = json.dumps({
            "user_skills": user.get("skills", []),
            "target_goals": user.get("goals", []),
            "top_job_requirements": [
                {"role": j.get("role"), "company": j.get("company"), "desc": j.get("description", "")[:500]} 
                for j in recommended_jobs
            ],
            "recent_ignore_reasons": [p.get("ignore_reason") for p in ignored_pipeline if p.get("ignore_reason")]
        })

        # 3. Generate Insights (Calls to LLM)
        llm = await self._get_llm_client()
        
        # Combined Prompt to minimize LLM calls in this decoupled version
        prompt = f"""You are a Career Strategist AI. Analyze the following user context and job market data:
        
        CONTEXT: {context_str}
        
        Generate a list of exactly 2-4 actionable insights focused on:
        1. "skill_gap": Specific technical skills missing from user profile that many top jobs require.
        2. "goal_conflict": Identification of goals that are statistically fighting each other in the current job pool (e.g. high salary vs early stage).
        3. "trajectory": Suggestions on how to pivot profile to reach higher seniority roles.
        
        For each insight, provide:
        - title: Short catchy title.
        - type: One of ["skill_gap", "goal_conflict", "trajectory"].
        - content: A VERY CONCISE summary (max 2 sentences).
        - structured_items: (CRITICAL) For skill_gap, provide a list of objects with {{"label": "Skill Name", "status": "Highly Recommended" | "Optional" | "Nice to have"}}.
        - priority: 1 (High) to 3 (Low).
        - recommendations: List of 2-3 specific next actions or resources.
        
        RETURN ONLY A JSON OBJECT with an "insights" key containing the list of items.
        """
        
        raw_insights = await llm.generate_insights(prompt)
        
        # 4. Persistence
        now = datetime.now(timezone.utc)
        final_insights = []
        
        for i_data in raw_insights:
            # Add metadata and user context
            i_data["user_id"] = user_id
            i_data["created_at"] = now
            # Simple persistent ID for this run or use an upsert logic
            # For simplicity in this version, we'll just insert them.
            # In a real app we might want to deduplicate.
            
            result = await self._db.insights.insert_one(i_data)
            i_data["_id"] = str(result.inserted_id)
            final_insights.append(i_data)

        logger.info("Insights generation complete for user %s: %d items", user_id, len(final_insights))
        return {"status": "success", "count": len(final_insights), "insights": len(final_insights)}

    async def cleanup(self):
        if self._llm_client:
            await self._llm_client.close()
