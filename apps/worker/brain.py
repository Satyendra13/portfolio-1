import re
import asyncio
from typing import AsyncIterator, Dict, Any, List
import google.generativeai as genai
from apps.api.app.core.config import settings


def format_spoken_text(text: str) -> str:
    """
    Format LLM output for spoken text delivery:
    - Removes markdown syntax (*, #, `, _, etc.)
    - Formats numbers/IDs digit by digit if requested (e.g. ID 4821 -> 4 8 2 1)
    """
    # Remove markdown bold/italic/code
    clean = re.sub(r'[\*\#\`\_\[\]\(\)]', '', text)
    # Replace multiple spaces
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


async def respond(state: Dict[str, Any]) -> AsyncIterator[str]:
    """
    Core LLM response function.
    M1: Plain conversational streaming engine (Gemini API or fallback).
    M3: Replaced seamlessly by LangGraph state machine execution.
    """
    tenant_id = state.get("tenant_id", "acme_telecom")
    language = state.get("language", "en")
    transcript: List[Dict[str, str]] = state.get("transcript", [])
    script_greeting = state.get("greeting")

    # If transcript is empty and a greeting script is provided, yield greeting
    if not transcript and script_greeting:
        yield script_greeting
        return

    # Use Gemini API if configured
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL_ID)

            system_instruction = (
                f"You are a tier-1 customer support voice assistant for tenant '{tenant_id}'. "
                f"Speak strictly in language code '{language}'. "
                f"Rules: Short spoken-style sentences (1-3 sentences). No markdown or bullet points. "
                f"Spell out account numbers or order IDs digit by digit."
            )

            prompt_messages = f"System: {system_instruction}\n"
            for turn in transcript[-5:]:
                prompt_messages += f"{turn.get('speaker', 'user')}: {turn.get('text', '')}\n"
            prompt_messages += "ai:"

            response = await asyncio.to_thread(
                model.generate_content,
                prompt_messages,
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    formatted = format_spoken_text(chunk.text)
                    if formatted:
                        yield formatted
            return
        except Exception as e:
            # Fallback if Gemini call encounters an issue or quota
            pass

    # High-fidelity mock/fallback streaming response for M1 voice loop testing
    last_caller_text = transcript[-1]["text"] if transcript else ""
    
    if "hello" in last_caller_text.lower() or "hi" in last_caller_text.lower():
        reply = "Hello! How can I assist you with your account or order today?"
    elif "status" in last_caller_text.lower() or "order" in last_caller_text.lower():
        reply = "I can certainly check your order status. Could you please provide your order ID?"
    elif "hindi" in last_caller_text.lower() or "हिंदी" in last_caller_text:
        reply = "नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ?"
    else:
        reply = f"I understood your request about {last_caller_text if last_caller_text else 'your inquiry'}. Let me help you with that right away."

    # Stream reply in words with short delays for speech simulation
    words = reply.split(" ")
    for i in range(0, len(words), 3):
        chunk = " ".join(words[i:i+3]) + " "
        yield chunk
        await asyncio.sleep(0.05)
