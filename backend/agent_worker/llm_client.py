import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from backend.app.core.config import settings

logger = logging.getLogger("asistline.llm_client")

class GeminiLLMClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.primary_model = settings.GEMINI_MODEL_ID or "gemini-flash-lite-latest"
        self.fallback_models = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
        ]
        self.working_model: Optional[str] = self.primary_model
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _get_candidate_models(self) -> List[str]:
        candidates = []
        if self.working_model:
            candidates.append(self.working_model)
        for m in [self.primary_model] + self.fallback_models:
            if m not in candidates:
                candidates.append(m)
        return candidates

    async def generate_text(self, contents: str, system_instruction: Optional[str] = None) -> str:
        client = self._get_client()
        models_to_try = self._get_candidate_models()

        last_error = None
        for model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=350,
                    system_instruction=system_instruction if system_instruction else None,
                )
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=config,
                )
                if response and response.text:
                    self.working_model = model
                    return response.text.strip()
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {e}")
                if self.working_model == model:
                    self.working_model = None

        # If all API calls fail, raise to trigger escalation handler
        raise RuntimeError(f"All Gemini models exhausted. Last error: {last_error}")

    async def analyze_intent_json(self, user_text: str) -> Dict[str, Any]:
        from backend.agent_worker.prompts import INTENT_DETECTION_SYSTEM_PROMPT
        client = self._get_client()
        prompt = f"Customer statement: '{user_text}'"

        models_to_try = self._get_candidate_models()
        for model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    system_instruction=INTENT_DETECTION_SYSTEM_PROMPT,
                )
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    self.working_model = model
                    return json.loads(response.text.strip())
            except Exception as e:
                logger.warning(f"Intent analysis on {model} failed: {e}")
                if self.working_model == model:
                    self.working_model = None

        # Basic fallback heuristic if LLM analysis fails
        lower = user_text.lower()
        wants_human = any(w in lower for w in ["human", "agent", "person", "representative", "specialist"])
        is_angry = any(w in lower for w in ["terrible", "angry", "furious", "ridiculous", "worst", "unacceptable"])
        return {
            "intent": "escalate" if wants_human else "faq",
            "is_angry": is_angry,
            "wants_human": wants_human,
            "order_id": None,
            "phone_last4": None,
        }

llm_client = GeminiLLMClient()
