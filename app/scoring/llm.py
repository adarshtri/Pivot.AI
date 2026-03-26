import httpx
import logging
import json
import asyncio
import time
from collections import deque
from typing import Protocol

logger = logging.getLogger(__name__)

def build_sieve_prompt(job: dict, goals: list[dict]) -> str:
    """Helper to logically group goals and structure the explicit JSON constraint prompt."""
    categories = {}
    for g in goals:
        cat = g.get('category', 'Goal')
        text = g.get('text', '')
        weight = g.get('weight', 1.0)
        if text:
            categories.setdefault(cat, []).append(f"'{text}' (Priority {weight}x)")
    
    cat_strings = []
    for cat, items in categories.items():
        cat_strings.append(f"{cat}: Wants ANY of [{', '.join(items)}]")
        
    goals_str = "\n".join(cat_strings)
    
    return f"""Analyze this job against the candidate's priorities.

Job Title: {job.get('role', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}

Candidate Priorities:
{goals_str}

Is there a fundamental mismatch between the Job Title/Location and the Candidate Priorities? 
For example, if the Priority is "Engineering" but the Job Title is "Human Resources" or "Sales", that is a strong mismatch.

Respond STRICTLY in valid JSON format with exactly two keys:
1. "verdict": Must be strictly one of: "Strong Match", "Moderate Match", or "Weak Match".
2. "reasoning": Exactly two sentences. First sentence state clearly if there is a mismatch or if it's a good fit. Second sentence explain why based ONLY on the Title, Location, and Priorities.

JSON Response:"""

class LLMProvider(Protocol):
    """Protocol defining the explicitly formalized JSON Inference abstraction."""
    async def generate_rationale(self, job: dict, goals: list[dict]) -> dict: ...
    async def close(self): ...

class OllamaClient(LLMProvider):
    """Async wrapper for the local Ollama LLM REST API."""
    def __init__(self, host="http://localhost:11434", model="phi4-mini"):
        self.host = host
        self.model = model
        self.client = httpx.AsyncClient(timeout=300.0)

    async def generate_rationale(self, job: dict, goals: list[dict]) -> dict:
        prompt = build_sieve_prompt(job, goals)
        try:
            response = await self.client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.2}
                }
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "{}").strip()
            
            try:
                parsed = json.loads(response_text)
                return {
                    "verdict": parsed.get("verdict", "Moderate Match"),
                    "reasoning": parsed.get("reasoning", "Failed to extract reasoning.")
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse Ollama JSON: %s", response_text)
                return {"verdict": "Moderate Match", "reasoning": response_text}
                
        except httpx.ConnectError:
            logger.warning("Ollama daemon is offline at %s.", self.host)
            return {"verdict": "Moderate Match", "reasoning": "Local LLM reasoning offline."}
        except Exception as e:
            logger.error("Ollama generation failed: %s", e)
            return {"verdict": "Moderate Match", "reasoning": "Local LLM reasoning unavailable."}

    async def close(self):
        await self.client.aclose()


class GroqClient(LLMProvider):
    """Async wrapper for the Groq Cloud LPU inference engine with built-in rate limiter."""
    def __init__(
        self,
        api_key: str,
        model: str = "llama3-8b-8192",
        min_delay_seconds: float = 6.0,
        calls_per_minute: int = 10,
    ):
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Rate limiting state
        self._min_delay = min_delay_seconds
        self._calls_per_minute = calls_per_minute
        self._call_timestamps: deque = deque()  # sliding window of recent call times
        self._last_call_time: float = 0.0
        
    async def _enforce_rate_limit(self):
        """Block until both rate limit constraints are satisfied."""
        now = time.monotonic()
        
        # 1. Minimum delay between individual calls
        elapsed = now - self._last_call_time
        if elapsed < self._min_delay:
            await asyncio.sleep(self._min_delay - elapsed)
            now = time.monotonic()
        
        # 2. Sliding window: drop timestamps older than 60 seconds
        window_start = now - 60.0
        while self._call_timestamps and self._call_timestamps[0] < window_start:
            self._call_timestamps.popleft()
        
        # 3. If at the per-minute cap, sleep until the oldest call exits the window
        if len(self._call_timestamps) >= self._calls_per_minute:
            sleep_until = self._call_timestamps[0] + 60.0
            wait = sleep_until - time.monotonic()
            if wait > 0:
                logger.info("Groq rate limit: waiting %.1fs (per-minute cap reached)", wait)
                await asyncio.sleep(wait)
                now = time.monotonic()
                # Prune again after sleep
                window_start = now - 60.0
                while self._call_timestamps and self._call_timestamps[0] < window_start:
                    self._call_timestamps.popleft()
        
        # Record this call
        self._call_timestamps.append(time.monotonic())
        self._last_call_time = time.monotonic()

    async def generate_rationale(self, job: dict, goals: list[dict]) -> dict:
        if not self.api_key or self.api_key == "********":
            return {"verdict": "Moderate Match", "reasoning": "Groq API key is not configured or invalid."}
            
        await self._enforce_rate_limit()
        prompt = build_sieve_prompt(job, goals)
        try:
            response = await self.client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Follows the standard OpenAI Completion JSON Schema
            choices = data.get("choices", [])
            if not choices:
                return {"verdict": "Moderate Match", "reasoning": "Empty completion array from Groq."}
                
            response_text = choices[0].get("message", {}).get("content", "{}").strip()
            
            try:
                parsed = json.loads(response_text)
                return {
                    "verdict": parsed.get("verdict", "Moderate Match"),
                    "reasoning": parsed.get("reasoning", "Failed to extract reasoning.")
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse Groq JSON: %s", response_text)
                return {"verdict": "Moderate Match", "reasoning": response_text}
                
        except Exception as e:
            logger.error("Groq generation failed: %s", e)
            return {"verdict": "Moderate Match", "reasoning": "Cloud inference unavailable."}

    async def close(self):
        await self.client.aclose()
