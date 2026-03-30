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
        from app.scoring.llm_factory import LLMFactory
        return await LLMFactory.get_provider(self._db)

    async def tailor(self, user_id: str, job_id: str) -> dict:
        """Tailor a user's LaTeX resume for a specific job."""
        logger.info("Tailoring resume for user: %s, job: %s", user_id, job_id)
        
        user = await self._db.users.find_one({"user_id": user_id})
        job = await self._db.jobs.find_one({"job_id": job_id})
        goals_doc = await self._db.goals.find_one({"user_id": user_id})
        
        if not user or not job:
            return {"status": "error", "message": "User or Job not found"}

        base_resume = user.get("resume_latex", "")
        if not base_resume:
            return {"status": "error", "message": "No base resume found in profile"}

        job_desc = job.get("description", "")
        job_role = job.get("role", "")
        company = job.get("company", "")
        
        # Format goals for the prompt
        user_goals = []
        if goals_doc and "goals" in goals_doc:
            user_goals = [f"- {g['text']} (Priority: {g['weight']})" for g in goals_doc["goals"]]
        goals_str = "\n".join(user_goals) if user_goals else "None provided."

        llm = await self._get_llm_client()
        
        prompt = f"""You are a Precise Resume Tailoring Agent. Your goal is to rewrite a LaTeX resume to align with a job description while maintaining 100% factual accuracy.

### CORE PRINCIPLES:
1. **Source of Truth**: The BASE LATEX RESUME is your *only* source of experience, projects, dates, and titles. 
2. **Zero Hallucination**: NEVER invent a metric (e.g., "improved efficiency by 20%"), a tool, or a responsibility that is not explicitly in the BASE LATEX.
3. **Alignment vs. Invention**: Alignment means using the *existing* resume content but prioritizing and rephrasing it to use the keywords and focus areas of the TARGET JOB. Match the vocabulary, but DO NOT invent achievements.
4. **No Placeholders**: Never use placeholders like [Your Name] or [Job Title]. Use the data from the BASE LATEX.

### TARGET JOB:
Role: {job_role}
Company: {company}
Focus Areas: {job_desc[:1500]}

### CANDIDATE GOALS & PRIORITIES:
{goals_str}

### BASE LATEX RESUME:
{base_resume}

### EXECUTION STEPS:
1. **Identify Relevant Points**: Pick the bullet points and skills from the BASE LATEX that best match the TARGET JOB and the CANDIDATE GOALS.
2. **Re-order for Impact**: Put the most relevant experiences and bullet points at the top of their respective sections.
3. **Contextual Rephrasing**: Rewrite bullets to better use Job Description terminology (e.g., "developed" → "engineered") ONLY if it stays 100% true to the original meaning.
4. **LaTeX Fidelity**: Maintain the exact LaTeX structure, commands, and formatting. Do not add new packages.

### OUTPUT:
Return ONLY the raw LaTeX code. No intro, no meta-commentary, no markdown backticks.

MODIFIED LATEX:"""

        tailored_latex = await llm.generate_text(prompt, temperature=0.0)
        
        if not tailored_latex:
            return {"status": "error", "message": "LLM failed to generate tailored resume"}

        # Clean up any potential markdown backticks that the LLM might have ignored instructions on
        tailored_latex = tailored_latex.replace("```latex", "").replace("```", "").strip()

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
