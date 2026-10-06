# AsistLine AI — POC Build Plan (for Antigravity)

Real-time multilingual AI voice agent for BPOs. Automates tier-1 inbound calls, answers strictly from each client's knowledge base, performs backend actions, and hands off to a human agent with full context.

**Phase 1 scope: browser-based calling only. No SIP or phone numbers yet.**

---

## 1. Interpretation of the requirements (read first)

1. **KB-grounded speech.** The AI agent may only speak facts that come from (a) the tenant's knowledge base or (b) a backend API result. If neither supports an answer, it says so and offers escalation or a callback. It never answers from general model knowledge on policy or account topics.
2. **Two voice agents on a call.**
   - **Agent 1 — AI Voice Agent** (Gemini + ElevenLabs): handles the call first.
   - **Agent 2 — Human Voice Agent**: a live BPO agent using a browser softphone, who joins the same call on escalation.
   - The caller is also in a browser tab, so every party is a browser participant.
   - *If you meant two AI agents (for example a customer simulator calling the support agent), the same media layer supports it. See section 14, "Optional: AI caller simulator".*
3. **Phase 1 = browser calling.** The caller clicks "Call Support" on a demo web page. Audio runs over WebRTC. SIP is a Phase 2 adapter behind the same interface.

---

## 2. Architecture

```
 Caller browser (React)          Human agent browser (React)        Supervisor browser (React)
        │ WebRTC                        │ WebRTC                            │ HTTPS + WS
        ▼                               ▼                                   ▼
 ┌────────────────────────── LiveKit server (self-hosted, Docker) ──────────────────────────┐
 │  Room per call:  caller  +  ai-agent (Python worker)  +  human-agent (joins on escalation) │
 └───────────────────────────────────────────┬──────────────────────────────────────────────┘
                                             │
                          Python voice worker (livekit-agents)
                          VAD → STT → LangGraph → TTS   (barge-in aware)
                                             │
                     ┌───────────────────────┼────────────────────────┐
                     ▼                       ▼                        ▼
             FastAPI backend         Tenant tool adapters      PostgreSQL + pgvector
        (REST + WS, auth, tenants,   (CRM / OMS / ticketing    (tenants, KB chunks, calls,
         dashboard, escalation)       — mock servers in POC)    turns, tickets, callbacks)
```

**Why LiveKit:** it is standard WebRTC, it lets the AI worker join as a normal participant, and a warm transfer becomes "add the human to the room". SIP is later added via LiveKit SIP without touching the agent logic. It is self-hostable in one Docker container.

**Fallback if LiveKit is blocked:** browser mic → WebSocket (PCM16, 16 kHz) → FastAPI → same pipeline. Human handoff then needs a second WebSocket audio bridge. Keep the `MediaTransport` interface (section 5) so either can be swapped.

---

## 3. Tech stack (final)

| Layer | Choice | Notes |
|---|---|---|
| Backend API | Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, Pydantic v2 | Async everywhere |
| Voice worker | `livekit-agents` (Python) | Handles VAD, turn detection, interruptions |
| STT | ElevenLabs realtime STT (Scribe), configurable | Streaming, multilingual, language auto-detect |
| LLM | Gemini Flash-class model | Model ID in env var; function calling and structured output |
| TTS | ElevenLabs multilingual low-latency model | Voice ID per tenant per language |
| Orchestration | LangGraph | Explicit state machine, checkpointed per call |
| DB | PostgreSQL 16 + pgvector | One DB for relational data and vectors; no separate vector store in POC |
| Embeddings | Gemini embedding model | Dimension in env var |
| Frontend | React + Vite + TypeScript + Tailwind, `livekit-client` | Three apps in one workspace |
| Infra | Docker Compose | `livekit`, `postgres`, `api`, `worker`, `web`, `mock-backends` |

All model names, voice IDs and thresholds live in `.env` and per-tenant config, never hard-coded.

---

## 4. Repository layout

```
asistline-ai/
├─ AGENTS.md                     # rules for Antigravity agents (section 15)
├─ docker-compose.yml
├─ .env.example
├─ apps/
│  ├─ api/                       # FastAPI
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ core/                # config, db, auth, tenancy middleware
│  │  │  ├─ models/              # SQLAlchemy
│  │  │  ├─ schemas/
│  │  │  ├─ routers/             # tenants, kb, calls, tokens, escalations, tickets, callbacks, analytics
│  │  │  ├─ services/            # kb_ingest, kb_search, summary, metrics
│  │  │  └─ ws/                  # live call events for dashboard/agent console
│  │  ├─ alembic/
│  │  └─ tests/
│  ├─ worker/                    # voice agent
│  │  ├─ main.py                 # livekit worker entrypoint
│  │  ├─ pipeline.py             # VAD/STT/LLM/TTS wiring
│  │  ├─ graph/
│  │  │  ├─ state.py
│  │  │  ├─ nodes/               # greet, language, intent, verify, kb_answer, action, escalate, close
│  │  │  └─ build.py
│  │  ├─ tools/                  # tenant-aware tool functions
│  │  ├─ grounding.py            # KB-only answer guard
│  │  └─ tests/
│  ├─ mock-backends/             # fake CRM/OMS/ticketing per tenant
│  └─ web/
│     ├─ caller/                 # demo "Call Support" page
│     ├─ agent-console/          # human agent softphone + screen pop
│     └─ supervisor/             # dashboard
├─ data/
│  ├─ tenants/                   # seed configs (YAML)
│  └─ kb/                        # sample KB docs per tenant
├─ eval/                         # scripted test calls + metrics
└─ docs/
```

---

## 5. Core interfaces

```python
class MediaTransport(Protocol):        # LiveKit today, SIP later
    async def join(self, call_id: str) -> None: ...
    async def audio_in(self) -> AsyncIterator[bytes]: ...
    async def audio_out(self, chunks: AsyncIterator[bytes]) -> None: ...
    async def interrupt(self) -> None: ...          # cancel TTS playback (barge-in)
    async def add_participant(self, role: str, identity: str) -> None: ...
    async def leave(self) -> None: ...

class TenantToolAdapter(Protocol):     # one implementation per client system
    async def verify_caller(self, factors: dict) -> VerifyResult: ...
    async def get_order_status(self, order_id: str) -> OrderStatus: ...
    async def get_account_info(self, account_id: str) -> AccountInfo: ...
    async def create_ticket(self, payload: TicketIn) -> Ticket: ...
    async def schedule_callback(self, payload: CallbackIn) -> Callback: ...
```

Tenant adapters are selected by `tenant.adapter_type` (`mock_rest`, later `salesforce`, `zendesk`, etc.).

---

## 6. Voice pipeline requirements

1. **Latency target:** caller stops speaking → first AI audio ≤ 1.5 s median, ≤ 2.5 s p95. Stream everything: STT partials, LLM tokens, TTS chunks.
2. **Barge-in:** if VAD detects caller speech while the AI is speaking, stop TTS within 300 ms, flush the audio queue, and mark the AI turn as `interrupted` with the text actually spoken so far. The next LLM turn must know what was and wasn't said.
3. **Turn detection:** use VAD plus end-of-utterance detection. Ignore back-channel noise ("hmm", "ok") under a minimum duration while the AI is speaking.
4. **Multilingual:**
   - Tenant config lists `supported_languages` (POC: English, Hindi, plus one more, for example Spanish).
   - Detect the language from the first caller utterance, and re-check each turn. If the caller switches, the AI follows.
   - TTS voice comes from `tenant.voices[language]`.
   - KB retrieval is cross-lingual: embed the query as is, and answer in the caller's language from chunks in any language.
5. **Filler and dead-air handling:** if a tool call takes more than 1.2 s, speak a short filler ("Let me check that for you"). After 6 s of caller silence, prompt once, then again, then close politely.
6. **Spoken-style output:** short sentences, no markdown, numbers and IDs read digit by digit, dates spoken naturally.
7. **Recording and transcripts:** store per-turn text with timestamps and language. Audio recording is optional and off by default in POC.

---

## 7. Knowledge-base grounding (key requirement)

### Ingestion (per tenant)
- Upload endpoint accepts PDF, DOCX, TXT, MD and FAQ CSV (`question,answer`).
- Parse → chunk (about 400 tokens, 60 overlap, split on headings/FAQ boundaries) → embed → store in `kb_chunks` with `tenant_id`, `document_id`, `title`, `language`, `embedding vector`, `metadata jsonb`.
- FAQ CSV rows become one chunk each, with the question included in the chunk text.
- Re-ingest is idempotent (hash per document).

### Retrieval
- Every retrieval is filtered by `tenant_id` at the SQL level. This is a hard multi-tenant safety rule.
- Hybrid search: pgvector cosine top-8 plus Postgres full-text rank, merged by reciprocal rank fusion, then top-4 to the LLM.
- Retrieval runs as a LangGraph node on each caller question, and also as a tool the LLM can call for follow-ups.

### Grounded-answer guard (`grounding.py`)
1. If the best retrieval score is below `tenant.kb_min_score`, skip generation. Respond with the tenant's "not found" line, then offer a callback or a human agent.
2. Otherwise prompt Gemini with: *"Answer ONLY using the CONTEXT below. If the context does not contain the answer, reply exactly `NO_ANSWER`. Do not use outside knowledge. Keep it under 3 sentences, spoken style."*
3. The model returns structured output: `{answer, used_chunk_ids[], confidence}`.
4. If the output is `NO_ANSWER`, `used_chunk_ids` is empty, or confidence is low, treat it as not found. Never speak an ungrounded answer.
5. Log `used_chunk_ids` on every AI turn so a supervisor can see the source of any statement.

### Persona rule
The AI may use general knowledge only for conversation glue (greetings, confirmations, clarifying questions). It must not use it for policies, prices, timelines, eligibility, or account facts.

---

## 8. LangGraph design

**State (`CallState`)**: `call_id, tenant_id, language, transcript[], intent, intent_confidence, verified (bool), verify_attempts, caller_profile, pending_action, kb_hits[], tool_results[], escalation_reason, sentiment, turn_count, status`.

**Nodes**

| Node | Responsibility |
|---|---|
| `greet` | Tenant greeting from script, in the detected language |
| `detect_language` | Set or update language |
| `classify_intent` | Structured Gemini call: `order_status, account_inquiry, complaint, faq, callback, human_request, other` with confidence |
| `verify_caller` | Ask for the tenant's verification factors (for example order ID plus phone last 4 or DOB), call `verify_caller`, allow 3 attempts, then escalate |
| `kb_answer` | Retrieval plus grounding guard |
| `run_action` | Tenant tools: order status, account info, create ticket, schedule callback. Read back and confirm any write action before executing |
| `check_escalation` | Rules engine (section 9), runs after every turn |
| `escalate` | Build handoff packet, request human, hold the caller with a script line |
| `summarize_close` | Ask if anything else is needed, close, generate post-call summary |

**Routing rules:** account-specific intents need `verified == True`. FAQ does not. Any explicit human request goes straight to `check_escalation`.

Use the LangGraph Postgres checkpointer keyed by `call_id`.

---

## 9. Escalation and human handoff

**Triggers (tenant-configurable in `escalation_rules`):**
- Caller explicitly asks for a human
- Verification failed 3 times
- Intent confidence below threshold twice in a row
- KB "not found" twice in a row
- Negative sentiment above threshold, or keywords (legal, fraud, chargeback, cancel account)
- Intent outside the tenant's automatable set
- Tool or API failure after retry

**Handoff flow (warm transfer inside the same room):**
1. AI tells the caller in their language: "I'm connecting you to a specialist. I'll share what we've discussed so you don't have to repeat it."
2. API creates an `escalations` row (`status=queued`) with the **handoff packet**:
   ```json
   {
     "call_id": "...", "tenant": "...", "language": "hi",
     "intent": "complaint", "verified": true,
     "caller": {"name": "...", "account_id": "..."},
     "summary": "3–5 lines, generated by Gemini",
     "reason": "caller_requested_human",
     "kb_answers_given": [{"q": "...", "chunk_ids": []}],
     "actions_taken": [{"type": "ticket_created", "id": "T-1042"}],
     "transcript": [ ... ],
     "sentiment": "frustrated"
   }
   ```
3. The agent console receives a WebSocket event, showing a ringing card with the summary. The agent clicks **Accept**.
4. API issues a LiveKit token for role `human_agent`. The agent joins the room, and the screen pop shows the packet and a live transcript.
5. The AI says a one-line introduction ("Connecting you to Priya"), then **mutes itself and stays as a silent listener** (still transcribing) or leaves, depending on `tenant.ai_after_handoff` (`leave` by default).
6. If no agent accepts within `queue_timeout` (default 45 s), the AI offers a callback and creates one.
7. Record `transfer_accuracy` inputs: after the call, the agent marks the escalation as *Appropriate / Could have been automated / Wrong queue*.

---

## 10. Multi-tenancy

- `tenant_id` on every table, and enforced in every query through a repository layer plus FastAPI dependency. Add a test that fails if a query on a tenant table lacks a tenant filter.
- Tenant config (YAML seed → DB JSONB):
  ```yaml
  tenant_id: acme_telecom
  display_name: Acme Telecom
  supported_languages: [en, hi]
  voices: {en: "<eleven_voice_id>", hi: "<eleven_voice_id>"}
  script:
    greeting: {en: "...", hi: "..."}
    not_found: {en: "...", hi: "..."}
    closing: {en: "...", hi: "..."}
  verification: {factors: [order_id, phone_last4], max_attempts: 3}
  automatable_intents: [order_status, faq, complaint, callback]
  escalation_rules: {sentiment_threshold: -0.6, keywords: [legal, fraud], max_kb_misses: 2}
  kb_min_score: 0.55
  adapter: {type: mock_rest, base_url: http://mock-backends:9000/acme_telecom}
  ```
- Seed **two tenants** with different scripts, KBs, verification factors and escalation rules, so the demo can prove isolation:
  1. **Acme Telecom**: plans, billing, complaint tickets
  2. **QuickCart**: order status, returns policy, callbacks
- Supervisor dashboard is scoped per tenant, with a tenant switcher for BPO admins.

---

## 11. Data model (PostgreSQL)

`tenants`, `tenant_configs`, `users` (role: `bpo_admin | supervisor | human_agent`), `kb_documents`, `kb_chunks` (vector), `calls`, `call_turns`, `call_events`, `escalations`, `tickets`, `callbacks`, `call_summaries`, `call_metrics`, `escalation_feedback`.

Key columns:
- `calls`: `id, tenant_id, room_name, started_at, ended_at, language, primary_intent, verified, outcome (resolved_by_ai | escalated | abandoned | callback_scheduled), escalated_at, human_agent_id, ai_talk_seconds, human_talk_seconds`
- `call_turns`: `call_id, seq, speaker (caller|ai|human), text, language, started_at, ended_at, interrupted bool, used_chunk_ids uuid[], latency_ms`
- `call_summaries`: `call_id, intent, resolution, actions jsonb, sentiment, follow_ups jsonb, summary_text`

---

## 12. API surface (FastAPI)

```
POST /v1/calls/start              {tenant_id} → {call_id, room, caller_token}
POST /v1/calls/{id}/end
GET  /v1/calls?tenant=&filters    GET /v1/calls/{id} (turns, events, summary)
WS   /v1/ws/calls/live            live call list + transcript stream (supervisor)

POST /v1/tenants/{t}/kb/documents (multipart)   GET/DELETE  .../kb/documents
POST /v1/tenants/{t}/kb/search    {query} → chunks + scores   (debug tool)

GET  /v1/escalations/queue        WS /v1/ws/agent (ringing events)
POST /v1/escalations/{id}/accept  → {agent_token}
POST /v1/escalations/{id}/feedback

GET  /v1/analytics/overview?tenant=&from=&to=
GET  /v1/analytics/calls-timeseries, /intents, /escalation-reasons
```

Worker-only internal routes (service token): create ticket, schedule callback, save summary, log turn.

---

## 13. Frontends

**Caller page (`web/caller`)**
- Tenant selector (demo only), language hint (optional), big "Call Support" button, mute, hang up, live captions of both sides, visual "AI speaking / listening" indicator.

**Agent console (`web/agent-console`)**
- Login, availability toggle, incoming-escalation ringer, screen pop (summary, intent, reason, actions taken, transcript, KB sources), in-call controls, disposition form (outcome plus escalation feedback).

**Supervisor dashboard (`web/supervisor`)**
- KPI cards: **Containment rate, AHT (AI-handled vs escalated), Transfer accuracy, Cost per call, Calls today**
- Charts: calls over time, intent mix, escalation reasons, language mix
- Live calls table with a live transcript drawer
- Call detail: transcript with per-turn KB sources, tool calls, summary, timeline
- KB manager: upload, list, delete, "test a question" box

### Metric definitions (implement exactly)
- **Containment rate** = calls with `outcome = resolved_by_ai` ÷ all completed calls in the tenant's automatable intents
- **AHT reduction** = baseline AHT (tenant config, for example 360 s) − mean AHT of calls handled fully by AI, shown as seconds and %
- **Transfer accuracy** = escalations marked *Appropriate* ÷ escalations with feedback
- **Cost per call** = `(ai_minutes × ai_cost_per_min) + (human_minutes × human_cost_per_min)` ÷ calls, vs the baseline of `baseline_human_cost_per_call`. Rates are tenant config values, and are clearly labelled assumptions in the UI.

---

## 14. Build phases and milestones

Each milestone ends with a demo and acceptance checks. Do not start one until the previous is green.

### M0 — Scaffold (Day 1)
- Monorepo, Docker Compose (LiveKit, Postgres+pgvector, api, worker, web), `.env.example`, Alembic baseline, CI-style `make test`.
- **Accept:** `docker compose up` starts all services. `/health` is OK. The caller page loads.

### M1 — Two-way browser voice loop (Days 2–4)
- Caller page joins a LiveKit room. Worker joins, greets, and holds a plain Gemini conversation via STT→LLM→TTS.
- Barge-in and turn detection working.
- **Accept:** speak to the AI in a browser. Median response latency ≤ 1.5 s. Interrupting mid-sentence stops the AI within 300 ms.

### M2 — KB grounding (Days 4–7)
- KB ingest and hybrid search, grounded-answer guard, "not found" behavior, supervisor KB upload UI (minimal).
- **Accept:** ≥ 90% of a 30-question in-KB test set is answered correctly with correct chunk IDs. 100% of a 15-question out-of-KB set returns the "not found" line and never an invented answer.

### M3 — LangGraph orchestration and tools (Days 7–11)
- Intent classification, caller verification, mock backends, order status, account info, ticket creation, callback scheduling, confirmations before writes, multilingual (English + Hindi first).
- **Accept:** each of the five use cases works end to end for both tenants. Wrong verification three times triggers escalation.

### M4 — Human agent (Agent 2) and warm handoff (Days 11–15)
- Agent console, escalation queue, handoff packet, accept → join room, screen pop, AI leaves or goes silent, timeout → callback.
- **Accept:** from a browser call, say "I want to talk to a person". A second browser (agent) rings, sees the summary and transcript within 2 s, accepts, and speaks to the caller with the AI no longer talking.

### M5 — Supervisor dashboard and analytics (Days 15–18)
- KPIs, charts, live calls, call detail, post-call structured summary, escalation feedback, tenant switcher.
- **Accept:** all four success metrics appear and update after a call. Numbers match a hand calculation on 10 seeded calls.

### M6 — Multi-tenant proof and polish (Days 18–20)
- Second tenant end to end, isolation tests, third language, error and reconnect handling, demo seed data, demo script.
- **Accept:** cross-tenant isolation test suite passes. A caller to QuickCart never receives Acme KB content.

### M7 — Evaluation run (Days 20–22)
- `eval/` runner: 40 scripted scenarios (text-driven through the pipeline, plus 10 live voice runs) → containment, transfer accuracy, latency and grounding report saved as `docs/poc-results.md`.

### Optional: AI caller simulator (only if "two voice agents" meant two AIs)
- A second worker `caller_sim` joins the same LiveKit room with a persona prompt ("angry customer, order delayed") and speaks via TTS. Useful for automated regression of the support agent. Build after M4.

### Phase 2 (out of scope now, design for it)
SIP trunk through LiveKit SIP (Twilio, Exotel or Plivo), DTMF, call recording and compliance redaction, real CRM adapters, auth and SSO, load test, outbound calls.

---

## 15. Instructions for Antigravity

### `AGENTS.md` (create this at repo root in M0)
```
- Read docs/AsistLine-build-plan.md fully before any task.
- Never hard-code model names, voice IDs, API keys, thresholds. Use env or tenant config.
- Every DB query on tenant data must filter by tenant_id via the repository layer.
- The voice agent must never speak policy/account facts that are not from KB chunks or tool results.
- Async everywhere in the API and worker. No blocking calls in the audio path.
- Every milestone ships with tests and a short docs/ note. Run `make test` before marking done.
- Prefer small typed modules; Pydantic schemas for every API and LLM structured output.
- If a requirement is ambiguous, write the assumption in docs/assumptions.md and continue.
```

### Suggested parallel workstreams (Manager view)
| Agent | Owns | Starts at |
|---|---|---|
| A — Infra/API | Compose, FastAPI, DB models, migrations, tokens, analytics endpoints | M0 |
| B — Voice/Media | LiveKit worker, STT/TTS wiring, barge-in, latency instrumentation | M1 |
| C — KB/Grounding | Ingest, hybrid search, grounding guard, eval set | M2 (can prep during M1) |
| D — Orchestration | LangGraph nodes, tenant tool adapters, mock backends | M3 |
| E — Frontend | Caller page, agent console, supervisor dashboard | Caller page in M1, rest M4–M5 |

Agents B, C and E can run in parallel once A has published the DB schema and API contracts (M0). Ask each agent to produce a verification artifact (test output or a screen recording) at each milestone.

### Master prompt (paste into Antigravity to start)
```
You are building "AsistLine AI", a multi-tenant, real-time multilingual AI voice agent POC for BPO tier-1 inbound support.

Read docs/AsistLine-build-plan.md end to end. It is the source of truth.

Phase 1 constraints:
- Browser-based calling only (WebRTC via a self-hosted LiveKit). No SIP yet, but keep the MediaTransport interface so SIP can be added.
- Two voice agents on a call: the AI Voice Agent (Gemini + ElevenLabs, Python livekit-agents worker) and a Human Voice Agent (browser softphone in React) who joins the same room on escalation with a full context handoff.
- The AI agent must speak ONLY from the tenant knowledge base (pgvector hybrid search + grounded-answer guard) or from backend tool results. If unsupported, it says it doesn't have that information and offers callback/human transfer.
- Orchestrate with LangGraph. Multi-tenant from day one (2 seeded tenants).

Work milestone by milestone (M0 → M7 in the plan). For each milestone: implement, write tests, run them, and give me a verification artifact before moving on. Start with M0 and M1 now. Split the work across parallel agents using the workstream table in section 15, and create AGENTS.md first.
```

---

## 16. Risks and decisions to confirm

| Item | Default in this plan | Change if |
|---|---|---|
| Media layer | LiveKit | You must use raw WebSocket only |
| STT | ElevenLabs realtime STT | You prefer Gemini Live for lower latency |
| Vector store | pgvector | Corpus grows beyond ~1M chunks |
| Hindi voice quality | Verify with ElevenLabs voices in M1 | Voice sounds unnatural → test other voices |
| Human agent audio | Same LiveKit room | — |
| API keys needed | Gemini, ElevenLabs | Get these before M1 |
| Cost figures in dashboard | Tenant-config assumptions | You have real BPO rates |

**Hard risks:** end-to-end latency (mitigate by streaming everything and measuring from M1), hallucinated policy answers (grounding guard plus out-of-KB test set), tenant data leakage (repository-level tenant filter plus isolation tests).

---

# PART 2 — Antigravity Prompts (copy-paste, one per milestone)

Use **Prompt 0** once at the start. Then run the milestone prompts in order. Each prompt assumes the plan is saved at `docs/AsistLine-build-plan.md`.

## Prompt 0 — Master prompt (start of project)

```
You are building "AsistLine AI", a multi-tenant, real-time multilingual AI voice agent POC for BPO tier-1 inbound support.

Read docs/AsistLine-build-plan.md end to end. It is the source of truth.

Phase 1 constraints:
- Browser-based calling only (WebRTC via a self-hosted LiveKit). No SIP yet, but keep the MediaTransport interface so SIP can be added later.
- Two voice agents on a call: the AI Voice Agent (Gemini + ElevenLabs, Python livekit-agents worker) and a Human Voice Agent (browser softphone in React) who joins the same room on escalation with a full context handoff.
- The AI agent must speak ONLY from the tenant knowledge base (pgvector hybrid search + grounded-answer guard) or from backend tool results. If unsupported, it says it doesn't have that information and offers a callback or human transfer.
- Orchestrate with LangGraph. Multi-tenant from day one (2 seeded tenants: Acme Telecom, QuickCart).

Working rules:
- Create AGENTS.md first (content in section 15 of the plan).
- Work milestone by milestone (M0 to M7). For each: implement, write tests, run them, and give me a verification artifact (test output or screen recording) before moving on.
- Use parallel agents per the workstream table in section 15.
- Write ambiguities and assumptions to docs/assumptions.md and continue.

Start with M0 and M1 now.
```

## Prompt M0 — Scaffold

```
Implement Milestone M0 from docs/AsistLine-build-plan.md.

- Create the monorepo layout from section 4.
- docker-compose.yml with: livekit (self-hosted), postgres 16 with pgvector, api (FastAPI), worker (livekit-agents), web (Vite dev), mock-backends.
- .env.example with GEMINI_API_KEY, ELEVENLABS_API_KEY, model IDs, voice IDs, LIVEKIT_URL/API_KEY/API_SECRET, DATABASE_URL, thresholds.
- FastAPI app with /health, config loading, async SQLAlchemy 2, Alembic baseline migration with all tables from section 11 (tenant_id on every tenant table).
- Repository layer that enforces tenant_id filtering, plus a test that fails if a tenant-table query lacks a tenant filter.
- Makefile: `make up`, `make test`, `make lint`.
- Create AGENTS.md exactly as in section 15.

Acceptance: `docker compose up` starts everything, /health returns OK, caller page loads, `make test` passes.
```

## Prompt M1 — Two-way browser voice loop

```
Implement Milestone M1 from docs/AsistLine-build-plan.md: a browser voice call where I speak to the AI and it speaks back.

1. apps/web/caller: React + Vite + TypeScript page with "Call Support", mute, hang up, live captions of both sides, and an "AI speaking / listening" indicator. Use livekit-client.
2. POST /v1/calls/start in FastAPI: creates a call row and LiveKit room, returns room name and caller token.
3. apps/worker: livekit-agents worker that joins the room and runs VAD -> ElevenLabs realtime STT -> Gemini -> ElevenLabs TTS, fully streaming.
4. The AI greets first, then converses in short spoken-style sentences (no markdown, IDs read digit by digit).
5. Barge-in: when I speak during AI speech, stop TTS within ~300 ms, flush audio, store the text actually spoken, mark the turn interrupted.
6. Detect English or Hindi and reply in the same language, with a per-language voice ID from config.
7. Log every turn to call_turns with latency_ms (end of speech to first audio).
8. Put the "brain" behind a function `respond(state) -> stream[str]` so LangGraph replaces it in M3.

Acceptance: docker compose up, open the caller page, talk to the AI by voice. Median response latency <= 1.5 s, barge-in <= 300 ms. Provide a latency report and a short recording. README with setup steps.
Do not build KB, LangGraph, escalation or dashboards yet.
```

## Prompt M2 — KB grounding

```
Implement Milestone M2 from docs/AsistLine-build-plan.md (section 7).

- Endpoints: upload/list/delete KB documents per tenant, plus POST /v1/tenants/{t}/kb/search for debugging.
- Ingestion: parse PDF, DOCX, TXT, MD and FAQ CSV; chunk ~400 tokens with 60 overlap on heading/FAQ boundaries; Gemini embeddings; store in kb_chunks (pgvector) with tenant_id; idempotent by content hash.
- Retrieval: tenant-filtered hybrid search (pgvector cosine top 8 + Postgres full-text, reciprocal rank fusion), top 4 to the LLM.
- apps/worker/grounding.py: score threshold from tenant config; strict prompt "answer ONLY from CONTEXT, else NO_ANSWER"; structured output {answer, used_chunk_ids, confidence}; treat NO_ANSWER, empty chunk IDs or low confidence as not found and speak the tenant's not_found line, then offer callback or human.
- Log used_chunk_ids on every AI turn.
- Wire it into the M1 voice loop so the AI answers only from the KB.
- Create sample KBs in data/kb for Acme Telecom and QuickCart, a 30-question in-KB set and a 15-question out-of-KB set in eval/.
- Minimal KB upload UI in the supervisor app.

Acceptance: >= 90% correct on the in-KB set with correct chunk IDs; 100% of out-of-KB questions get the not-found response with no invented answer. Show the eval report.
```

## Prompt M3 — LangGraph orchestration and tools

```
Implement Milestone M3 from docs/AsistLine-build-plan.md (sections 5, 8, 10).

- LangGraph graph with nodes: greet, detect_language, classify_intent, verify_caller, kb_answer, run_action, check_escalation, escalate (stub for now), summarize_close. CallState per section 8, Postgres checkpointer keyed by call_id.
- Intents: order_status, account_inquiry, complaint, faq, callback, human_request, other. Structured Gemini output with confidence.
- Account-specific intents require verified == True. Verification factors, max attempts and messages come from tenant config; 3 failures set an escalation flag.
- TenantToolAdapter interface plus mock_rest adapter, and apps/mock-backends (FastAPI) with fake data per tenant: verify_caller, get_order_status, get_account_info, create_ticket, schedule_callback.
- Read back and get spoken confirmation before any write action (ticket, callback).
- Filler phrase if a tool takes > 1.2 s; silence prompts at 6 s.
- Seed both tenants from data/tenants/*.yaml with different scripts, verification factors and rules.
- Replace the M1 brain function with the graph. English + Hindi.
- Tests: node unit tests, and scripted end-to-end conversations for all five use cases on both tenants.

Acceptance: every use case works end to end for both tenants; failed verification 3 times sets the escalation flag; no tool fact is spoken that did not come from a tool result.
```

## Prompt M4 — Human agent and warm handoff

```
Implement Milestone M4 from docs/AsistLine-build-plan.md (section 9).

- Escalation triggers from tenant escalation_rules (explicit human request, failed verification, low intent confidence twice, KB miss twice, negative sentiment/keywords, non-automatable intent, tool failure).
- On escalate: AI says the handoff line in the caller's language, API creates an escalations row with the full handoff packet (Gemini 3-5 line summary, intent, reason, verified caller, actions taken, KB answers given, transcript, sentiment).
- apps/web/agent-console: login, availability toggle, WebSocket ringer for queued escalations, screen pop with summary and live transcript, Accept button, in-call controls (mute, hang up), disposition form with escalation feedback (Appropriate / Could have been automated / Wrong queue).
- POST /v1/escalations/{id}/accept returns a LiveKit token for role human_agent; the human joins the same room.
- After the human joins, the AI says a one-line introduction, then leaves (tenant.ai_after_handoff = leave, or silent listener).
- If nobody accepts within queue_timeout (45 s default), the AI offers a callback and creates it.

Acceptance: in the caller page say "I want to talk to a person". A second browser (agent console) rings, shows summary and transcript within 2 s, accepts, and speaks to the caller with the AI no longer talking. Provide a recording.
```

## Prompt M5 — Supervisor dashboard and analytics

```
Implement Milestone M5 from docs/AsistLine-build-plan.md (section 13).

- apps/web/supervisor: login, tenant switcher for BPO admins, KPI cards (Containment rate, AHT reduction, Transfer accuracy, Cost per call, Calls today), charts (calls over time, intent mix, escalation reasons, language mix), live calls table with WebSocket transcript drawer, call detail page (transcript with per-turn KB sources, tool calls, summary, timeline), KB manager.
- Implement the metric formulas exactly as defined in section 13. Rates and baselines (baseline AHT, ai_cost_per_min, human_cost_per_min, baseline_human_cost_per_call) come from tenant config and are labelled as assumptions in the UI.
- Post-call structured summary via Gemini saved to call_summaries: intent, resolution, actions, sentiment, follow-ups, summary_text.
- Analytics endpoints from section 12, scoped by tenant.
- Seed 10 historical calls to validate numbers.

Acceptance: all four success metrics render and update after a new call; values match a hand calculation on the 10 seeded calls.
```

## Prompt M6 — Multi-tenant proof and polish

```
Implement Milestone M6 from docs/AsistLine-build-plan.md.

- Complete the second tenant end to end (own scripts, KB, verification, escalation rules, voices, adapter URL).
- Add isolation tests: a caller to QuickCart never receives Acme KB content, tickets, callbacks or calls; API calls with the wrong tenant return 403/404; the dashboard never shows other tenants' data.
- Add a third language (Spanish or another the ElevenLabs model supports well).
- Error handling: reconnect on network drop, LLM/STT/TTS failure fallbacks (apologise, offer callback or human), graceful call end.
- Demo seed data and docs/demo-script.md walking through: FAQ, order status, complaint, callback, verification failure, human handoff, both tenants.

Acceptance: isolation test suite passes; the full demo script runs without manual fixes.
```

## Prompt M7 — Evaluation run

```
Implement Milestone M7 from docs/AsistLine-build-plan.md.

- eval/ runner with 40 scripted scenarios across both tenants and all intents (text-driven through the full pipeline) and a checklist for 10 live voice runs.
- Report: containment rate, AHT vs baseline, transfer accuracy, cost per call vs baseline, latency median/p95, grounding accuracy (in-KB correct, out-of-KB refusal rate), language-switch success.
- Save the results to docs/poc-results.md with a summary, limitations and Phase 2 recommendations (SIP via LiveKit SIP, recording and redaction, real CRM adapters, auth/SSO, load test).
```

## Optional prompt — AI caller simulator (only if "two voice agents" means two AIs)

```
Add a second worker, caller_sim, that joins a LiveKit room as a simulated customer with a persona prompt (for example: "angry customer, order is late, order ID 48213") and speaks via ElevenLabs TTS with its own STT. It calls the support agent automatically, and logs the full conversation and outcome. Use it for regression tests in eval/. Build after M4.
```
