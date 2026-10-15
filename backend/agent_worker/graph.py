import json
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from backend.agent_worker.prompts import (
    SYSTEM_PROMPT_TEMPLATE,
    PROMPT_DISCLOSURE,
    ESCALATION_SUMMARY_PROMPT,
)
from backend.agent_worker.llm_client import llm_client
from backend.agent_worker.rag import retrieve_kb_context
from backend.app.db.session import AsyncSessionLocal
from backend.app.api.endpoints.verification import MOCK_ORDERS

logger = logging.getLogger("asistline.graph")

class AgentState(TypedDict):
    call_id: str
    tenant_id: str
    tenant_name: str
    language: str
    script_config: Dict[str, Any]
    escalation_rules: Dict[str, Any]
    transcript_turns: List[Dict[str, str]]
    user_input: str
    intent: str
    is_angry: bool
    wants_human: bool
    kb_context: str
    kb_chunks: List[Dict[str, Any]]
    confidence_score: float
    has_grounding: bool
    verification_step: str
    order_id: Optional[str]
    phone_last4: Optional[str]
    verified_data: Optional[Dict[str, Any]]
    repeat_failures: int
    escalation_needed: bool
    escalation_reason: str
    escalation_summary: str
    ai_response: str
    status: str

# 1. Greet Node
async def greet_node(state: AgentState) -> Dict[str, Any]:
    lang = state.get("language") or "en"
    script_cfg = state.get("script_config") or {}
    welcome_dict = script_cfg.get("welcome_message") or PROMPT_DISCLOSURE
    welcome_text = welcome_dict.get(lang, welcome_dict.get("en", PROMPT_DISCLOSURE["en"]))

    # Ensure California recording disclosure is present
    if "recorded" not in welcome_text.lower() and "ai" not in welcome_text.lower():
        welcome_text = f"This call may be recorded and answered by an AI assistant. {welcome_text}"

    return {
        "ai_response": welcome_text,
        "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": welcome_text}],
        "status": "active",
    }

# 2. Analyze Node
async def analyze_node(state: AgentState) -> Dict[str, Any]:
    user_text = state.get("user_input", "").strip()
    user_lower = user_text.lower().strip()
    import re

    order_id = state.get("order_id")
    phone_last4 = state.get("phone_last4")
    num_5 = re.findall(r'\b\d{5}\b', user_text)
    num_4 = re.findall(r'\b\d{4}\b', user_text)
    if num_5:
        order_id = num_5[0]
    if num_4:
        phone_last4 = num_4[-1]

    # Fast-Path Heuristics: Saves Gemini API quota (15 RPM Free Tier limit)
    audio_check_keywords = [
        "audible", "hear me", "you hear", "you listening", "are you there",
        "can you hear", "am i speaking", "am i clear"
    ]
    greeting_keywords = ["hello", "hi", "hey", "hallo", "good morning", "good afternoon", "good evening", "namaste"]
    gratitude_keywords = ["thank you", "thanks", "appreciate it", "bye", "goodbye", "that's all", "that is all", "have a good day"]
    human_keywords = ["human", "agent", "person", "representative", "specialist", "supervisor", "transfer me"]
    order_keywords = ["track order", "order status", "where is my order", "my package", "shipment"]

    wants_human = any(w in user_lower for w in human_keywords)
    is_angry = any(w in user_lower for w in ["terrible", "angry", "furious", "ridiculous", "worst", "unacceptable"])

    if wants_human:
        intent = "escalate"
    elif any(k in user_lower for k in audio_check_keywords):
        intent = "audio_check"
    elif any(k in user_lower for k in gratitude_keywords):
        intent = "gratitude"
    elif any(user_lower == k or user_lower.startswith(k + " ") or user_lower.endswith(" " + k) for k in greeting_keywords):
        intent = "greeting"
    elif (num_5 or num_4 or any(k in user_lower for k in order_keywords)) and state.get("verification_step") != "verified":
        intent = "verify" if state.get("verification_step") == "requested" else "order_status"
    else:
        # Only invoke Gemini Intent Analyzer when fast-path heuristics are inconclusive
        analysis = await llm_client.analyze_intent_json(user_text)
        intent = analysis.get("intent", "faq")
        if not order_id:
            order_id = analysis.get("order_id")
        if not phone_last4:
            phone_last4 = analysis.get("phone_last4")
        if analysis.get("wants_human"):
            wants_human = True
        if analysis.get("is_angry"):
            is_angry = True

    return {
        "intent": intent,
        "is_angry": is_angry,
        "wants_human": wants_human,
        "order_id": order_id,
        "phone_last4": phone_last4,
        "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "customer", "text": user_text}],
    }

# 3. Retrieve Node
async def retrieve_node(state: AgentState) -> Dict[str, Any]:
    query = state.get("user_input", "")
    tenant_id = state.get("tenant_id", "")

    async with AsyncSessionLocal() as db:
        context_str, chunks, max_score, has_grounding = await retrieve_kb_context(
            tenant_id=tenant_id,
            query=query,
            db=db,
            top_k=3,
        )

    repeat_failures = state.get("repeat_failures", 0)
    if not has_grounding:
        repeat_failures += 1

    return {
        "kb_context": context_str,
        "kb_chunks": chunks,
        "confidence_score": max_score,
        "has_grounding": has_grounding,
        "repeat_failures": repeat_failures,
    }

# 4. Verify Node (Order ID + phone last-4 check)
async def verify_node(state: AgentState) -> Dict[str, Any]:
    order_id = state.get("order_id")
    phone_last4 = state.get("phone_last4")

    # If only order_id is provided
    if order_id and not phone_last4:
        msg = f"Thank you for providing Order ID {order_id}. To access your order details securely, could you please confirm the last 4 digits of your phone number?"
        return {
            "ai_response": msg,
            "verification_step": "requested",
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": msg}],
        }
    # If only phone_last4 is provided
    elif phone_last4 and not order_id:
        msg = "Thank you. Could you please also provide your 5-digit Order ID so I can pull up your delivery status?"
        return {
            "ai_response": msg,
            "verification_step": "requested",
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": msg}],
        }
    # If neither is provided
    elif not order_id and not phone_last4:
        msg = (
            "To check your order status securely, could you please provide your "
            "5-digit Order ID and the last 4 digits of your phone number?"
        )
        return {
            "ai_response": msg,
            "verification_step": "requested",
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": msg}],
        }

    # Verify against mock database
    order_data = MOCK_ORDERS.get(str(order_id).strip())
    if order_data and order_data.get("phone_last4") == str(phone_last4).strip():
        cust_name = order_data["customer_name"]
        status = order_data["order_status"]
        eta = order_data["delivery_date"]
        resp = (
            f"Thank you for verifying, {cust_name}. Your order {order_id} is currently "
            f"{status}, with expected delivery {eta}."
        )
        return {
            "ai_response": resp,
            "verification_step": "verified",
            "verified_data": order_data,
            "repeat_failures": 0,
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": resp}],
        }
    else:
        repeat_failures = state.get("repeat_failures", 0) + 1
        resp = (
            "I wasn't able to locate an order matching that Order ID and phone number. "
            "Please double check the digits, or I can connect you to a human agent."
        )
        return {
            "ai_response": resp,
            "verification_step": "failed",
            "repeat_failures": repeat_failures,
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": resp}],
        }

# 5. Answer Node (Grounded Gemini generation with context awareness)
async def answer_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("intent")
    lang = state.get("language", "en")
    user_query = state.get("user_input", "")

    # Direct conversational response for audio/presence checks
    if intent == "audio_check":
        if lang == "hi":
            reply = "हाँ, मैं आपको स्पष्ट रूप से सुन पा रहा हूँ! कृपया बताएं, मैं आपकी किस प्रकार सहायता कर सकता हूँ?"
        else:
            reply = "Yes, I can hear you loud and clear! How can I help you today?"
        return {
            "ai_response": reply,
            "repeat_failures": 0,
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": reply}],
        }

    # Direct conversational response for greetings
    if intent == "greeting":
        if lang == "hi":
            reply = "नमस्ते! आज मैं आपकी क्या सहायता कर सकता हूँ?"
        else:
            reply = "Hello! How can I assist you with your inquiry or order today?"
        return {
            "ai_response": reply,
            "repeat_failures": 0,
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": reply}],
        }

    # Direct conversational response for gratitude and call wrapping
    if intent == "gratitude":
        if lang == "hi":
            reply = "आपका बहुत-बहुत धन्यवाद! यदि आपको कोई अन्य सहायता चाहिए तो अवश्य बताएं। आपका दिन शुभ हो!"
        else:
            reply = "You are very welcome! Please let me know if there is anything else I can help you with. Have a great day!"
        return {
            "ai_response": reply,
            "repeat_failures": 0,
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": reply}],
        }

    has_grounding = state.get("has_grounding", False)
    kb_context = state.get("kb_context", "")
    tenant_name = state.get("tenant_name", "Support")

    # Non-negotiable grounding enforcement for ungrounded queries
    if not has_grounding or not kb_context.strip():
        if lang == "hi":
            refusal_text = (
                "क्षमा करें, मेरे नॉलेज बेस में इस विषय की जानकारी उपलब्ध नहीं है। "
                "क्या आप चाहते हैं कि मैं आपकी बात किसी विशेषज्ञ प्रतिनिधि से कराऊँ?"
            )
        else:
            refusal_text = (
                "I apologize, but I do not have that information in my verified knowledge base. "
                "Would you like me to connect you with a support specialist who can assist?"
            )
        return {
            "ai_response": refusal_text,
            "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": refusal_text}],
        }

    # Build verified order context if caller was already verified
    verified_data = state.get("verified_data")
    if verified_data:
        verified_context = (
            f"\nVERIFIED CUSTOMER ORDER DATA:\n"
            f"- Customer Name: {verified_data.get('customer_name')}\n"
            f"- Order ID: {state.get('order_id')}\n"
            f"- Order Status: {verified_data.get('order_status')}\n"
            f"- Delivery Date: {verified_data.get('delivery_date')}\n"
            f"- Items Count: {verified_data.get('items_count')}\n"
            f"- Total Amount: {verified_data.get('total_amount')}\n"
        )
    else:
        verified_context = ""

    # Build dialogue context from transcript turns so the agent has full conversational memory
    turns = state.get("transcript_turns", [])
    dialogue_lines = []
    for t in turns[-6:]:
        spk = "Customer" if t.get("speaker") == "customer" else "Agent"
        txt = t.get("text", "")
        if txt:
            dialogue_lines.append(f"{spk}: {txt}")
    if not dialogue_lines or dialogue_lines[-1] != f"Customer: {user_query}":
        dialogue_lines.append(f"Customer: {user_query}")
    dialogue_context = "\n".join(dialogue_lines)

    # Prompt injection
    sys_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        tenant_name=tenant_name,
        language="Hindi" if lang == "hi" else "English",
        kb_context=kb_context,
        verified_context=verified_context,
    )

    try:
        reply = await llm_client.generate_text(
            contents=f"Conversation History:\n{dialogue_context}\n\nAgent Response:",
            system_instruction=sys_prompt,
        )
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        # Failure recovery: trigger escalation per brief requirement
        return {
            "escalation_needed": True,
            "escalation_reason": "llm_failure",
            "ai_response": "I'm having trouble retrieving that right now. Let me connect you directly to a specialist.",
        }

    return {
        "ai_response": reply,
        "transcript_turns": state.get("transcript_turns", []) + [{"speaker": "ai", "text": reply}],
    }

# 6. Escalate Node
async def escalate_node(state: AgentState) -> Dict[str, Any]:
    reason = state.get("escalation_reason") or "Customer requested specialist or issue unresolved."
    turns = state.get("transcript_turns", [])

    transcript_text = "\n".join(f"{t.get('speaker', 'user')}: {t.get('text', '')}" for t in turns[-6:])

    try:
        summary_prompt = ESCALATION_SUMMARY_PROMPT.format(transcript=transcript_text)
        summary = await llm_client.generate_text(contents=summary_prompt)
    except Exception:
        summary = f"Escalated due to {reason}. Customer statement: {state.get('user_input', '')}"

    escalate_message = "Let me connect you to a specialist who can help you with this right away. Please hold one moment."

    return {
        "escalation_needed": True,
        "escalation_reason": reason,
        "escalation_summary": summary.strip(),
        "status": "escalated",
        "ai_response": escalate_message,
        "transcript_turns": turns + [{"speaker": "ai", "text": escalate_message}],
    }

# Routing logic
def route_after_analyze(state: AgentState) -> str:
    if state.get("wants_human"):
        state["escalation_reason"] = "Customer explicitly requested human agent"
        return "escalate"
    if state.get("is_angry"):
        state["escalation_reason"] = "Detected customer frustration / angry sentiment"
        return "escalate"
    if state.get("intent") in ["audio_check", "greeting", "gratitude"]:
        return "answer"
    # If caller is already verified, allow answering follow-up questions with verified order context
    if state.get("verification_step") == "verified":
        return "retrieve"
    if state.get("intent") in ["order_status", "verify"] or state.get("verification_step") == "requested":
        return "verify"
    return "retrieve"

def route_after_retrieve(state: AgentState) -> str:
    rules = state.get("escalation_rules") or {}
    max_retries = rules.get("max_retries_before_escalate", 1)
    if not state.get("has_grounding") and state.get("repeat_failures", 0) > max_retries:
        state["escalation_reason"] = "No matching knowledge base document found after retries"
        return "escalate"
    return "answer"

def route_after_verify(state: AgentState) -> str:
    if state.get("repeat_failures", 0) >= 2:
        state["escalation_reason"] = "Verification failed multiple times"
        return "escalate"
    return END

def route_initial(state: AgentState) -> str:
    # If no user input has been provided yet, greet the caller
    if not state.get("user_input"):
        return "greet"
    return "analyze"

# Graph Construction
def build_agent_graph():
    builder = StateGraph(AgentState)

    builder.add_node("greet", greet_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("verify", verify_node)
    builder.add_node("answer", answer_node)
    builder.add_node("escalate", escalate_node)

    # Entry point from START
    builder.add_conditional_edges(
        START,
        route_initial,
        {
            "greet": "greet",
            "analyze": "analyze",
        }
    )

    builder.add_edge("greet", END)

    builder.add_conditional_edges(
        "analyze",
        route_after_analyze,
        {
            "escalate": "escalate",
            "verify": "verify",
            "retrieve": "retrieve",
            "answer": "answer",
        }
    )

    builder.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "answer": "answer",
            "escalate": "escalate",
        }
    )

    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "escalate": "escalate",
            END: END,
        }
    )

    builder.add_edge("answer", END)
    builder.add_edge("escalate", END)

    return builder.compile()

agent_graph = build_agent_graph()
