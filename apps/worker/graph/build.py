from typing import Dict, Any, AsyncIterator
from apps.worker.graph.state import CallState
from apps.worker.graph.nodes.nodes import (
    node_greet,
    node_detect_language,
    node_classify_intent,
    node_verify_caller,
    node_kb_answer,
    node_run_action,
    node_check_escalation,
    node_summarize_close,
    node_greeting_response,
    node_thanks_response
)


class CallGraphOrchestrator:
    """
    LangGraph state machine orchestrator for AsistLine AI calls.
    Manages state transitions across language detection, intent classification,
    caller verification, KB grounding, tool execution, and escalation rules.
    """
    def __init__(self, tenant_config: Dict[str, Any]):
        self.tenant_config = tenant_config

    async def run_turn(self, state: CallState, caller_utterance: str, db_session=None) -> CallState:
        """Execute a full state transition turn for a caller utterance."""
        state.turn_count += 1
        
        # 1. Update transcript
        if caller_utterance:
            state.transcript.append({"speaker": "caller", "text": caller_utterance, "language": state.language})

        # 2. Check if answering spoken confirmation for write action
        if state.awaiting_confirmation:
            if any(yes in caller_utterance.lower() for yes in ["yes", "yeah", "sure", "proceed", "go ahead", "confirm", "ok", "okay"]):
                state = await node_run_action(state, self.tenant_config)
                state.transcript.append({"speaker": "ai", "text": state.ai_response, "language": state.language})
                return state
            else:
                state.awaiting_confirmation = False
                state.pending_action = None
                state.ai_response = "Understood. I have canceled that request. Is there anything else I can assist you with?"
                state.transcript.append({"speaker": "ai", "text": state.ai_response, "language": state.language})
                return state

        # 3. Detect language
        state = await node_detect_language(state, self.tenant_config)

        # 4. Classify intent
        state = await node_classify_intent(state, self.tenant_config)

        # 5. Check escalation rules
        state = await node_check_escalation(state, self.tenant_config)
        if state.status == "escalated":
            state.transcript.append({"speaker": "ai", "text": state.ai_response, "language": state.language})
            return state

        # 6. Route based on intent & verification status
        intent = state.intent

        # Account-specific intents require caller verification
        if intent in ["order_status", "account_inquiry", "complaint"] and not state.verified:
            state = await node_verify_caller(state, self.tenant_config, db_session)
            # Re-check escalation if verification failed 3 times
            state = await node_check_escalation(state, self.tenant_config)
            
            # If verification succeeded, proceed directly to run action
            if state.verified and state.status != "escalated":
                state = await node_run_action(state, self.tenant_config)

        elif intent == "faq":
            state = await node_kb_answer(state, self.tenant_config, db_session)

        elif intent == "greeting":
            state = await node_greeting_response(state, self.tenant_config)

        elif intent == "thanks":
            state = await node_thanks_response(state, self.tenant_config)

        elif intent == "goodbye":
            state = await node_summarize_close(state, self.tenant_config)

        elif intent in ["order_status", "account_inquiry", "complaint", "callback"]:
            state = await node_run_action(state, self.tenant_config)

        else:
            state = await node_kb_answer(state, self.tenant_config, db_session)

        # Append AI turn response to transcript
        state.transcript.append({"speaker": "ai", "text": state.ai_response, "language": state.language})
        return state


async def respond_graph(state_dict: Dict[str, Any]) -> AsyncIterator[str]:
    """
    Voice Worker LLM Brain entry point integrating LangGraph state machine execution.
    """
    tenant_config = state_dict.get("tenant_config", {})
    call_id = state_dict.get("call_id", "call_demo")
    tenant_id = state_dict.get("tenant_id", "acme_telecom")
    language = state_dict.get("language", "en")
    transcript = state_dict.get("transcript", [])
    
    # Initialize CallState
    call_state = CallState(
        call_id=call_id,
        tenant_id=tenant_id,
        language=language,
        transcript=transcript,
        verified=state_dict.get("verified", False)
    )

    last_caller_text = transcript[-1]["text"] if transcript else ""

    orchestrator = CallGraphOrchestrator(tenant_config)
    updated_state = await orchestrator.run_turn(call_state, last_caller_text)

    # Stream out AI response text
    response_text = updated_state.ai_response
    words = response_text.split(" ")
    for i in range(0, len(words), 3):
        chunk = " ".join(words[i:i+3]) + " "
        yield chunk
