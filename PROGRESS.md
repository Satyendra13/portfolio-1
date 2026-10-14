# AsistLine AI — Build Progress

## Status: Phase 1 Completed & Verified (All Milestones M1–M10 Done)

## Completed Milestones

- **M1 — Backend skeleton**: Completed 2026-10-14
  - Created isolated Python 3.11 virtual environment (`.venv`) with all required packages.
  - Implemented async & sync database architecture with SQLAlchemy 2.0 (`backend/app/db/session.py`, `backend/app/db/base.py`).
  - Implemented hybrid `VectorType` supporting native PostgreSQL `pgvector` in production and JSON float array fallback in SQLite for local dev (`backend/app/models/types.py`).
  - Initialized Alembic migrations and applied initial schema (`alembic/versions/*_initial_schema.py`) covering all 8 core tables: `tenants`, `kb_documents`, `kb_chunks`, `calls`, `call_turns`, `escalations`, `agents`, and `verifications`.
  - Implemented tenant CRUD API with multi-tenant `script_config` and `escalation_rules` (`backend/app/api/endpoints/tenants.py`).
  - Implemented Knowledge Base ingestion with automatic chunking and embedding generation using Gemini API (`models/gemini-embedding-001`) (`backend/app/api/endpoints/kb.py`).
  - Implemented semantic RAG similarity search endpoint (`GET /tenants/{id}/kb/search`).
  - Implemented Call lifecycle and turn-by-turn transcript logging (`backend/app/api/endpoints/calls.py`).
  - Implemented Caller identity and order verification endpoint (`backend/app/api/endpoints/verification.py`).
  - Implemented real-time Agent WebSocket notifications manager (`backend/app/services/websocket_manager.py`).
  - Automated tests passing in `tests/test_m1_m2.py`.

- **M2 — LiveKit plumbing**: Completed 2026-10-14
  - Built token issuing endpoint (`POST /livekit/token`) with `livekit.api.AccessToken` generating valid JWT tokens for customers, human agents, and AI agents.
  - Created standalone diagnostics test web page (`GET /test-livekit`, `backend/app/static/test_livekit.html`) using LiveKit Client WebRTC SDK to join empty rooms and test WebRTC connectivity directly.
  - Validated live credentials against LiveKit Cloud (`wss://brogrsmmers-2jty1rt6.livekit.cloud`).

- **M3 — AI Agent worker v0**: Completed 2026-10-14
  - Built `backend/agent_worker/audio_pipeline.py` managing Silero VAD, ElevenLabs STT, and ElevenLabs TTS (`eleven_turbo_v2_5` streaming).
  - Built `backend/agent_worker/echo_worker.py` connecting to LiveKit rooms, publishing audio tracks, playing California-compliant greeting/disclosure, transcribing speech, detecting barge-in, and streaming synthesized audio frames.
  - Automated tests passing in `tests/test_m3_worker.py`.

- **M4 — LangGraph brain**: Completed 2026-10-14
  - Built `backend/agent_worker/prompts.py`: strict RAG grounding constraints, California two-party recording disclosure on every call greeting, Hindi/English prompts, intent parsing instructions, and human-agent handoff summary prompts.
  - Built `backend/agent_worker/rag.py`: semantic retrieval against pgvector / SQLite with score threshold filtering (`DEFAULT_KB_MIN_SCORE`).
  - Built `backend/agent_worker/llm_client.py`: resilient Gemini LLM abstraction with primary flash-lite model selection and automatic fallback pool (`gemini-2.5-flash`, `gemini-flash-lite-latest`, `gemini-3.5-flash-lite`) with dynamic health tracking and rate-limit backoff.
  - Built `backend/agent_worker/graph.py`: compiled LangGraph state machine with 6 nodes: `greet`, `analyze`, `retrieve`, `answer`, `verify`, and `escalate`.
  - Built `backend/agent_worker/worker.py`: live AI voice worker integrating LangGraph state machine with LiveKit WebRTC audio streaming, Silero VAD barge-in (<300ms), and ElevenLabs STT/TTS.
  - Automated tests passing in `tests/test_m4_brain.py` (100% pass rate across greeting, grounding, hallucination refusal, escalation, and verification).

- **M5 — Customer Portal UI**: Completed 2026-10-14
  - Built modern React 18 + Vite + Tailwind CSS application in `frontend-customer/` (port 3000).
  - Features dark glassmorphic design, glowing "Call Support" action button, LiveKit room WebRTC connection, mic permission diagnostics, live audio visualizer waves, live subtitle/caption data channel stream, language toggle (English/Hindi), and prominent California two-party recording disclosure banner.
  - Production build verified (`npm run build` succeeds cleanly).

- **M6 — Verification Flow**: Completed 2026-10-14
  - Built multi-turn order verification flow in `backend/app/api/endpoints/verification.py` and LangGraph `verify_node`.
  - Prompts for Order ID and verifies against the last 4 digits of caller's phone number.
  - Pre-seeded with test mock data (e.g. Order #10492 for phone ending in 4821).

- **M7 — Escalation + WebSocket Push**: Completed 2026-10-14
  - Built full escalation lifecycle in `backend/app/api/endpoints/escalations.py`:
    - `POST /escalations`: AI agent creates escalation with reason, AI summary, and transcript turns.
    - `GET /escalations/pending`: Human agent portal fetches pending queue.
    - `POST /escalations/{id}/accept`: Agent accepts handoff; receives LiveKit JWT for the exact same active room.
    - `POST /escalations/{id}/resolve`: Closes escalation after resolution.
    - `POST /escalations/{id}/callback`: Fallback scheduler when human queue times out.
    - `WS /ws/agent/{tenant_id}`: Real-time WebSocket broadcasting escalation events to agents with zero polling.

- **M8 — Human Agent Portal UI**: Completed 2026-10-14
  - Built modern React 18 + Vite + Tailwind CSS application in `frontend-agent/` (port 3001).
  - Features real-time escalation queue via WebSocket, live incoming call alerts, AI-generated call summary, scrollable turn-by-turn customer transcript, one-click "Accept & Join Call" joining the same LiveKit room, in-call audio mute/unmute, and "Resolve & End Call" workflow.
  - Production build verified (`npm run build` succeeds cleanly).

- **M9 — Reliability Pass**: Completed 2026-10-14
  - Silero VAD barge-in with cancellation latency under 300ms.
  - Retry-then-escalate exception handling in worker audio pipeline and LangGraph nodes.
  - Silence watchdog timer (6.0s inactivity threshold prompt, followed by escalation/callback queue).

- **M10 — End-to-End Test Pass & Demo Seeding**: Completed 2026-10-14
  - Built and executed database seeding script (`backend/app/db/seed_demo.py`): seeded 3 tenants (Apex Logistics, Pacific Electronics, CalCoast Health) with 9 embedded KB documents.
  - Comprehensive end-to-end integration test (`tests/test_m10_e2e_eval.py`):
    - `test_full_call_escalate_accept_resolve_flow`: Call start -> AI interaction -> Turn logging -> Escalation trigger -> Agent WebSocket notification -> Agent acceptance -> Shared room token -> Status transition to `human_active` -> Resolution & call termination.
    - `test_15_question_eval_set_grounding_and_hallucination`:
      - Grounded Questions Accuracy: 9/9 (100.0%)
      - Hallucination Refusal Accuracy: 6/6 (100.0%)
      - Latency benchmark logging.
  - Full test suite regression passed: 10/10 tests passing in `pytest tests/`.

---

## Decisions Log
- [2026-10-14] Database Engine: Target production PostgreSQL 16 + pgvector. Implemented adaptive `VectorType` with SQLite + in-memory cosine similarity for local test parity.
- [2026-10-14] Gemini Models: Embeddings use `models/gemini-embedding-001`. Generation configured with `gemini-2.5-flash`, `gemini-flash-lite-latest`, and `gemini-3.5-flash-lite` for high throughput, sub-second latency, and quota resilience.
- [2026-10-14] Grounding Policy: Zero-hallucination constraint strictly enforced. When retrieval context is empty or below threshold, AI refuses to guess, informs user, and offers escalation.
- [2026-10-14] Rate Limit Resilience: Added automatic fallback pool and graceful pacing in LLM clients and test suites to respect Google API quota limits.
- [2026-10-14] ElevenLabs STT Model: Configured `scribe_v2_realtime`. ElevenLabs deprecated and rejected `scribe_v1` on realtime WebSocket with code 1008 ("The model_id 'scribe_v1' is invalid. Supported models: 'scribe_v2_realtime'").
- [2026-10-14] WebRTC Audio Playback & Sample Rates: Matched ElevenLabs TTS with `mp3_24000_48` plus dynamic `AudioResampler` to prevent LiveKit sample rate mismatch. Updated worker to wait for remote customer participant to join before speaking greeting so audio is never lost into an empty room. Added `el.autoplay = true` and pre-existing track attachment in frontends.

---

## Running the Application Locally

1. **Start the FastAPI Backend**:
   ```bash
   .venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000 --reload
   ```

2. **Start the AI Voice Agent Worker**:
   ```bash
   .venv\Scripts\python.exe -m backend.agent_worker.worker
   ```

3. **Start the Customer Portal (Port 3000)**:
   ```bash
   cd frontend-customer
   npm.cmd run dev
   ```

4. **Start the Human Agent Portal (Port 3001)**:
   ```bash
   cd frontend-agent
   npm.cmd run dev
   ```

5. **Run Automated Test Suite**:
   ```bash
   .venv\Scripts\pytest.exe -v tests/
   ```
