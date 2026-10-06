import json
import re
import asyncio
from typing import Dict, Any, Tuple
import google.generativeai as genai
from apps.api.app.core.config import settings
from apps.worker.graph.state import CallState
from apps.worker.tools.adapter import MockRestTenantToolAdapter
from apps.worker.grounding import evaluate_grounded_answer
from apps.api.app.services.kb_search import KBSearchService


async def node_greet(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Greeting node delivering initial tenant script."""
    lang = state.language
    greeting_text = tenant_config.get("script", {}).get("greeting", {}).get(
        lang,
        "Thank you for calling. How can I assist you today?"
    )
    state.ai_response = greeting_text
    state.turn_count += 1
    return state


async def node_detect_language(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Language detection node checking caller utterances for language switches."""
    if not state.transcript:
        return state

    last_utterance = state.transcript[-1].get("text", "").lower()

    if any(h in last_utterance for h in ["नमस्ते", "हिंदी", "हिंदी में", "hindi"]):
        state.language = "hi"
    elif any(s in last_utterance for s in ["hola", "español", "spanish"]):
        state.language = "es"
    elif any(e in last_utterance for e in ["english", "hello", "hi"]):
        state.language = "en"

    return state


async def node_classify_intent(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Classify caller intent using Gemini or deterministic intent rules engine."""
    if not state.transcript:
        state.intent = "faq"
        state.intent_confidence = 0.90
        return state

    last_text = state.transcript[-1].get("text", "").lower()

    # Rule-based fast classifier fallback (checking specific intents before generic tokens)
    if any(k in last_text for k in ["person", "human", "agent", "representative", "specialist", "speak to someone", "operator"]):
        state.intent = "human_request"
        state.intent_confidence = 0.99
    elif any(k in last_text for k in ["callback", "call me back", "schedule call", "phone me"]):
        state.intent = "callback"
        state.intent_confidence = 0.95
    elif any(k in last_text for k in ["account", "balance", "plan details", "subscription"]):
        state.intent = "account_inquiry"
        state.intent_confidence = 0.95
    elif any(k in last_text for k in ["complaint", "damaged", "broken", "issue", "problem", "frustrated", "wrong"]):
        state.intent = "complaint"
        state.intent_confidence = 0.90
    elif any(k in last_text for k in ["order", "status", "tracking", "package", "delivery", "where is my"]):
        state.intent = "order_status"
        state.intent_confidence = 0.95
    elif any(k in last_text for k in ["bye", "goodbye", "that's all", "nothing else", "done", "end call"]):
        state.intent = "goodbye"
        state.intent_confidence = 0.95
    elif any(k in last_text for k in ["thanks", "thank you", "appreciate"]):
        state.intent = "thanks"
        state.intent_confidence = 0.90
    elif any(k in last_text for k in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you", "how can you help", "what can you do", "help me"]):
        state.intent = "greeting"
        state.intent_confidence = 0.95
    else:
        state.intent = "faq"
        state.intent_confidence = 0.85

    # Sentiment detection
    if any(s in last_text for s in ["angry", "upset", "terrible", "worst", "unacceptable", "fraud", "legal"]):
        state.sentiment = "frustrated"
    elif any(s in last_text for s in ["thanks", "thank you", "great", "helpful"]):
        state.sentiment = "positive"

    return state


async def node_verify_caller(state: CallState, tenant_config: Dict[str, Any], db_session=None) -> CallState:
    """Caller verification node handling factor collection and 3-attempt lock out."""
    if state.verified:
        return state

    last_text = state.transcript[-1].get("text", "") if state.transcript else ""
    
    # Extract order_id and phone_last4 from utterance using regex
    order_match = re.search(r'\b\d{5}\b', last_text)
    phone_match = re.search(r'\b\d{4}\b', last_text)

    if order_match:
        state.caller_profile["order_id"] = order_match.group(0)
    if phone_match:
        state.caller_profile["phone_last4"] = phone_match.group(0)

    order_id = state.caller_profile.get("order_id", "48213")
    phone_last4 = state.caller_profile.get("phone_last4", "1234")

    adapter = MockRestTenantToolAdapter()
    res = await adapter.verify_caller(state.tenant_id, {"order_id": order_id, "phone_last4": phone_last4})

    if res.get("verified"):
        state.verified = True
        state.caller_profile["account_id"] = res.get("account_id")
        state.ai_response = f"Thank you. Your account identity has been verified."
    else:
        state.verify_attempts += 1
        if state.verify_attempts >= tenant_config.get("verification", {}).get("max_attempts", 3):
            state.escalation_reason = "verification_failed_3_times"
            state.status = "escalated"
            state.ai_response = "I was unable to verify your identity after 3 attempts. I am transferring you to a live representative."
        else:
            state.ai_response = f"I could not verify those details. Please provide your 5-digit order number and 4-digit phone PIN. (Attempt {state.verify_attempts}/3)"

    return state


async def node_kb_answer(state: CallState, tenant_config: Dict[str, Any], db_session=None) -> CallState:
    """Knowledge base grounded answer node."""
    if not state.transcript:
        return state

    query = state.transcript[-1].get("text", "")
    hits = []
    if db_session:
        hits = await KBSearchService.hybrid_search(db_session, state.tenant_id, query, top_k=4)

    answer_obj = await evaluate_grounded_answer(query, hits, tenant_config, state.language)

    state.ai_response = answer_obj.answer
    state.used_chunk_ids = answer_obj.used_chunk_ids
    if not answer_obj.is_grounded:
        state.kb_hits.append({"query": query, "status": "miss"})
    else:
        state.kb_hits.append({"query": query, "status": "hit", "chunk_ids": answer_obj.used_chunk_ids})

    return state


async def node_run_action(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Execute tenant tool operations (order status, account info, ticket, callback)."""
    adapter = MockRestTenantToolAdapter()
    intent = state.intent

    if intent == "order_status":
        order_id = state.caller_profile.get("order_id", "48213")
        res = await adapter.get_order_status(state.tenant_id, order_id)
        state.tool_results.append(res)
        state.ai_response = f"Order {res['order_id']} for {res['item']} is currently {res['status']}, scheduled for delivery {res['delivery_date']}."

    elif intent == "account_inquiry":
        acc_id = state.caller_profile.get("account_id", "ACC-1042")
        res = await adapter.get_account_info(state.tenant_id, acc_id)
        state.tool_results.append(res)
        state.ai_response = f"Your account status is {res['status']} under the {res['plan']} plan with a current balance of ${res['balance_usd']}."

    elif intent == "complaint":
        if not state.awaiting_confirmation:
            state.pending_action = {"type": "create_ticket", "subject": f"Customer Complaint - {state.tenant_id}"}
            state.awaiting_confirmation = True
            state.ai_response = f"I can create a support ticket for your complaint regarding this issue. Should I go ahead and file ticket '{state.pending_action['subject']}'?"
        else:
            # Executing write action upon spoken confirmation
            res = await adapter.create_ticket(state.tenant_id, state.pending_action)
            state.tool_results.append(res)
            state.awaiting_confirmation = False
            state.pending_action = None
            state.ai_response = f"Your complaint ticket {res['ticket_id']} has been successfully created. A support specialist will review it within 24 hours."

    elif intent == "callback":
        if not state.awaiting_confirmation:
            state.pending_action = {"type": "schedule_callback", "phone_number": "555-0199", "preferred_time": "Today 4 PM"}
            state.awaiting_confirmation = True
            state.ai_response = f"I can schedule a callback for you at {state.pending_action['preferred_time']} to 555-0199. Should I confirm this booking?"
        else:
            res = await adapter.schedule_callback(state.tenant_id, state.pending_action)
            state.tool_results.append(res)
            state.awaiting_confirmation = False
            state.pending_action = None
            state.ai_response = f"Your callback request {res['callback_id']} has been scheduled for {res['preferred_time']}. Our team will reach out to you then."

    return state


async def node_check_escalation(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Rules engine checking all escalation triggers."""
    rules = tenant_config.get("escalation_rules", {})
    
    # 1. Explicit human request
    if state.intent == "human_request":
        state.escalation_reason = "caller_requested_human"
        state.status = "escalated"

    # 2. Verification failure 3 times
    elif state.verify_attempts >= tenant_config.get("verification", {}).get("max_attempts", 3):
        state.escalation_reason = "verification_failed_3_times"
        state.status = "escalated"

    # 3. KB miss twice in a row
    elif len([h for h in state.kb_hits if h.get("status") == "miss"]) >= rules.get("max_kb_misses", 2):
        state.escalation_reason = "kb_miss_twice"
        state.status = "escalated"

    # 4. Negative sentiment / keyword match
    elif state.sentiment == "frustrated":
        state.escalation_reason = "negative_sentiment"
        state.status = "escalated"

    if state.status == "escalated" and not state.ai_response.startswith("I'm connecting you"):
        lang = state.language
        state.ai_response = "I'm connecting you to a specialist. I'll share what we've discussed so you don't have to repeat it."

    return state


async def node_summarize_close(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Summarize conversation and close call gracefully."""
    lang = state.language
    closing_text = tenant_config.get("script", {}).get("closing", {}).get(
        lang,
        "Thank you for reaching out. Have a wonderful day!"
    )
    state.status = "resolved"
    state.ai_response = closing_text
    return state


async def node_greeting_response(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Handle conversational greetings and 'how can you help' type queries with Gemini or script."""
    lang = state.language
    tenant_id = tenant_config.get("tenant_id", "")
    display_name = tenant_config.get("display_name", "our company")

    # Try Gemini for a natural conversational response
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL_ID)

            last_text = state.transcript[-1].get("text", "") if state.transcript else "hello"

            prompt = (
                f"You are a friendly tier-1 customer support voice agent for {display_name}. "
                f"The caller just said: \"{last_text}\"\n"
                f"Respond naturally in 1-2 short spoken sentences in language '{lang}'. "
                f"Greet them warmly and briefly list 2-3 things you can help with "
                f"(like checking order status, answering questions about plans/products, "
                f"or connecting them with a specialist). "
                f"Do NOT use markdown, bullet points, or any formatting. "
                f"Speak as if on a phone call."
            )

            response = await asyncio.to_thread(model.generate_content, prompt)
            if response.text:
                state.ai_response = response.text.strip()
                return state
        except Exception:
            pass

    # Fallback scripted response
    if lang == "hi":
        state.ai_response = (
            f"नमस्ते! {display_name} में आपका स्वागत है। "
            "मैं आपके ऑर्डर की स्थिति जांच सकता हूँ, हमारे प्लान और सेवाओं के बारे में बता सकता हूँ, "
            "या आपको किसी विशेषज्ञ से जोड़ सकता हूँ। आप किस बारे में जानना चाहेंगे?"
        )
    else:
        state.ai_response = (
            f"Hello! Welcome to {display_name}. "
            "I can help you check your order status, answer questions about our plans and services, "
            "or connect you with a specialist. What would you like help with today?"
        )
    return state


async def node_thanks_response(state: CallState, tenant_config: Dict[str, Any]) -> CallState:
    """Handle 'thank you' type responses gracefully."""
    lang = state.language
    if lang == "hi":
        state.ai_response = "आपका स्वागत है! क्या कुछ और है जिसमें मैं आपकी मदद कर सकता हूँ?"
    else:
        state.ai_response = "You're welcome! Is there anything else I can help you with?"
    return state
