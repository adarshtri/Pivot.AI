import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.scoring.llm import LLMProvider, OllamaClient, GroqClient

logger = logging.getLogger(__name__)

class ResumeEngine:
    """Layer 5 AI Engine: Handles LaTeX resume tailoring using LLM."""

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

    async def tailor(self, user_id: str, job_id: str) -> dict:
        """Tailor a user's LaTeX resume for a specific job."""
        logger.info("Tailoring resume for user: %s, job: %s", user_id, job_id)
        
        user = await self._db.users.find_one({"user_id": user_id})
        job = await self._db.jobs.find_one({"job_id": job_id})
        
        if not user or not job:
            return {"status": "error", "message": "User or Job not found"}

        base_resume = user.get("resume_latex", "")
        if not base_resume:
            return {"status": "error", "message": "No base resume found in profile"}

        job_desc = job.get("description", "")
        job_role = job.get("role", "")
        company = job.get("company", "")

        llm = await self._get_llm_client()
        
        prompt = f"""You are an expert Resume Tailoring AI. 
        Your task is to modify a candidate's base LaTeX resume to perfectly align with a target job description.

        TARGET JOB: {job_role} at {company}
        JOB DESCRIPTION:
        {job_desc[:2000]}

        BASE LATEX RESUME:
        {base_resume}

        INSTRUCTIONS:
        1. STRICKLY maintain the EXACT SAME LaTeX structure, preamble, and custom commands. 
        2. DO NOT introduce any new LaTeX packages, environments, or syntax that aren't already present in the BASE LATEX.
        3. NO MARKDOWN: Never use Markdown syntax like **bold** or *italics*. Use only LaTeX commands like \\textbf{{text}} or \\textit{{text}} as per the BASE LATEX.
        4. FOCUSED TAILORING: Rephrase and reorder "Experience" and "Skills" bullets to perfectly align with the TARGET JOB'S requirements.
        5. Match the tone and level of detail found in the JOB DESCRIPTION while keeping the BASE LATEX'S formatting style (e.g., if it uses \\item, keep \\item; if it uses \\cvitem, keep \\cvitem).
        6. Do NOT invent fake experience. Highlight existing relevant skills and projects.
        7. Return ONLY the final LaTeX code. No preamble, no explanation, no markdown backticks.

        MODIFIED LATEX:"""

        tailored_latex = await llm.generate_text(prompt, temperature=0.3)
        
        if not tailored_latex:
            return {"status": "error", "message": "LLM failed to generate tailored resume"}

        # Store the tailored version
        now = datetime.now(timezone.utc)
        result = await self._db.tailored_resumes.update_one(
            {"user_id": user_id, "job_id": job_id},
            {
                "$set": {
                    "latex": tailored_latex,
                    "created_at": now,
                    "base_resume_snapshot": base_resume[:100] # just for tracking
                }
            },
            upsert=True
        )

        return {
            "status": "success",
            "job_id": job_id,
            "latex": tailored_latex
        }

    async def cleanup(self):
        if self._llm_client:
            await self._llm_client.close()
