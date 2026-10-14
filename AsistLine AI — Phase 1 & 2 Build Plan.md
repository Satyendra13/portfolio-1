# AsistLine AI — End-to-End Build Plan

### Phase 1 (build now, in Antigravity) + Phase 2 (roadmap only)

**Build tool:** Antigravity, model Gemini 3.8 Flash (Medium) **Scope for Antigravity:** Phase 1 only — two web portals: (1) Customer Calling Portal, (2) Human Agent Handoff Portal.

> Note: if "Gemini 3.8 Flash" isn't resolvable inside Antigravity's model picker, the closest available fast Gemini tier (e.g. Flash-class) is a drop-in swap — the LLM is abstracted behind one service in this architecture, so nothing else changes.

---

## 1. What Phase 1 Actually Delivers

Two connected web apps sharing one LiveKit room and one backend:

| Portal | Who uses it | What it does |
| --- | --- | --- |
| **Customer Calling Portal** | End customer, in browser | Clicks "Call Support," talks to the AI over WebRTC, gets answers grounded in the KB, can be transferred to a human |
| **Human Agent Portal** | Support agent, in browser | Sees incoming AI-escalated calls, full transcript + context, one-click accept, joins the same LiveKit room, finishes the call |

No SIP, no real phone numbers, no outbound calling in Phase 1 — that's Phase 2.

---

## 2. Tech Stack (Phase 1)

| Layer | Choice | Why |
| --- | --- | --- |
| Backend API | FastAPI (Python 3.12) | async-native, fast to iterate, plays well with LangGraph |
| Real-time audio | LiveKit (WebRTC) | handles room/track management, lets customer + AI + human share one room |
| VAD | Silero VAD | detects speech start/stop for turn-taking and barge-in |
| STT | ElevenLabs Scribe (or Deepgram as fallback) | low-latency streaming transcription |
| LLM orchestration | LangGraph + Gemini 3.8 Flash (Medium) | state machine keeps the agent on-script, prevents open-ended hallucination |
| TTS | ElevenLabs streaming voice | natural, low-latency, interruptible |
| KB / RAG | PostgreSQL 16 + pgvector | one DB for transcripts, tenant config, and embeddings |
| Frontend (both portals) | React + Tailwind CSS | fast to build, matches your existing stack |
| Realtime signaling (agent notifications) | WebSocket (FastAPI native) | push "incoming escalation" events to the agent portal instantly |
| Auth | JWT (customer: anonymous/session token; agent: login) | simplest viable for a POC |

---

## 3. Architecture at a Glance

```
┌─────────────────────┐        ┌─────────────────────┐
│ Customer Portal (web)│        │ Agent Portal (web)   │
│  - Mic button         │       │  - Incoming call list │
│  - LiveKit client     │       │  - Transcript view    │
│  - Live captions       │      │  - Accept/Join button │
└──────────┬───────────┘        └──────────┬───────────┘
           │ WebRTC (LiveKit)               │ WebRTC (join same room)
           ▼                                ▼
      ┌─────────────────────────────────────────┐
      │              LiveKit Room                │
      │   (customer track + AI agent track +     │
      │    human agent track, same room)         │
      └───────────────┬───────────────────────────┘
                       │ audio frames
                       ▼
      ┌─────────────────────────────────────────┐
      │      AI Voice Agent Worker (Python)       │
      │  Silero VAD → STT → LangGraph → TTS       │
      │  - RAG lookup against pgvector KB         │
      │  - Verification step (order ID + phone)   │
      │  - Escalation decision                    │
      └───────────────┬───────────────────────────┘
                       │
                       ▼
      ┌─────────────────────────────────────────┐
      │           FastAPI Backend                 │
      │  - Tenant config / KB management           │
      │  - Call session + transcript store          │
      │  - Escalation queue + WebSocket push        │
      │  - LiveKit room/token issuing API           │
      └───────────────┬───────────────────────────┘
                       │
                       ▼
            ┌───────────────────────┐
            │ PostgreSQL 16 + pgvector│
            │ (tenants, KB, calls,    │
            │  transcripts, embeddings)│
            └───────────────────────┘
```

---

## 4. Data Model (PostgreSQL)

Core tables to create first — everything else depends on these:

- **tenants** — `id, name, script_config (jsonb), escalation_rules (jsonb), created_at`
- **kb_documents** — `id, tenant_id, title, content, source_url, created_at`
- **kb_chunks** — `id, document_id, chunk_text, embedding (vector), created_at` — the pgvector RAG table
- **calls** — `id, tenant_id, livekit_room_name, customer_session_id, status (ai_active/escalated/human_active/ended), started_at, ended_at`
- **call_turns** — `id, call_id, speaker (customer/ai/human), text, timestamp` — full transcript, append-only
- **escalations** — `id, call_id, reason, summary, status (pending/accepted/resolved), created_at, accepted_by_agent_id`
- **agents** — `id, tenant_id, name, email, status (available/busy/offline)`
- **verifications** — `id, call_id, order_id, phone_last4, verified_bool, verified_at`

---

## 5. Core Components — Build Order

### 5.1 Foundation (build first)

1. FastAPI skeleton: health check, tenant CRUD, Postgres connection, migrations (Alembic)
2. pgvector extension enabled; embedding function (use Gemini embeddings or a small open embedding model)
3. KB ingestion endpoint: upload text/FAQ → chunk → embed → store in `kb_chunks`
4. LiveKit server connection (LiveKit Cloud or self-hosted) + token-issuing endpoint (`POST /livekit/token`)

### 5.2 Customer Calling Portal

1. Landing page with one big "Call Support" button
2. On click: request LiveKit token from backend → join room as `customer`
3. Mic permission + audio track publish
4. Live caption display (subscribe to a data channel the AI worker publishes transcript events to)
5. "Call ended" / "Transferring you to a specialist…" states
6. Language toggle (English / Hindi) — tenant-configurable welcome message

### 5.3 AI Voice Agent Worker (the brain)

This is a standalone Python process (LiveKit Agent) that joins each room as a participant:

1. Subscribes to customer audio track
2. Silero VAD → detects utterance boundaries
3. STT (ElevenLabs Scribe) → text
4. LangGraph state machine:
   - **Greet** node → plays tenant's welcome message
   - **Listen** node → waits for input
   - **Retrieve** node → pgvector similarity search against `kb_chunks`, filtered by `tenant_id`
   - **Answer** node → Gemini 3.8 Flash generates a reply **constrained to only use retrieved KB text** (system prompt enforces "if not in context, say you don't know")
   - **Verify** node → triggered for account-specific questions; asks for Order ID + last 4 phone digits, checks against tenant's backend/API or mock data
   - **Escalate** node → triggered on: explicit request, repeated failure to resolve, sentiment/anger detection, or KB has no answer
5. TTS (ElevenLabs) streams the answer back as an audio track, with interrupt-on-barge-in (stop generation/playback within \~300ms of detected customer speech)
6. Every turn written to `call_turns` in real time

### 5.4 Escalation + Human Handoff

1. When the agent worker hits the **Escalate** node:
   - Writes a row to `escalations` with a generated summary (one more Gemini call: "summarize this call for a human agent in 2-3 lines")
   - Publishes a WebSocket event to all available agents of that tenant: `new_escalation`
   - AI tells the customer: "Let me connect you to a specialist, one moment."
2. **Agent Portal** receives the WebSocket push → shows a card: customer issue, summary, full transcript so far, "Accept" button
3. On Accept:
   - Backend issues the agent a LiveKit token for the **same room**
   - Agent joins as a new participant; the AI worker either leaves the room or mutes itself and stays silent (configurable — staying lets it keep logging the transcript)
   - Customer sees "You've been connected to \[Agent Name\]" — never has to repeat their issue because the agent already has the summary + transcript on screen
4. Call ends → both leave room → `calls.status = ended`, `ended_at` set

### 5.5 Human Agent Portal

1. Login (simple JWT auth)
2. Dashboard: queue of pending escalations (real-time via WebSocket), sorted oldest-first
3. Call detail view: customer summary, live transcript scroll, "Accept Call" button
4. In-call view: audio controls (mute/unmute), live transcript continuing to update, "End Call" button
5. Status toggle: available/busy/offline

---

## 6. Key API Endpoints (FastAPI)

| Endpoint | Purpose |
| --- | --- |
| `POST /livekit/token` | Issue a LiveKit room token (customer or agent) |
| `POST /tenants/{id}/kb/upload` | Ingest a KB document (chunk + embed) |
| `GET /tenants/{id}/kb/search?q=` | Debug endpoint — test RAG retrieval directly |
| `POST /calls/start` | Create a call session row, return room name |
| `GET /calls/{id}/transcript` | Full transcript for a call |
| `WS /ws/agent/{tenant_id}` | Agent portal subscribes here for `new_escalation` events |
| `POST /escalations/{id}/accept` | Agent accepts → returns LiveKit token for that room |
| `POST /verify` | Verification check (order ID + phone digits) against tenant data source |

---

## 7. Multi-Tenant Config

Each tenant's `script_config` JSONB holds:

```json
{
  "welcome_message": {"en": "...", "hi": "..."},
  "languages": ["en", "hi"],
  "escalation_triggers": ["angry_sentiment", "repeat_failure", "explicit_request"],
  "verification_required_for": ["order_status", "refund"],
  "voice_id": "elevenlabs-voice-xyz"
}
```

This keeps one codebase serving many clients without forking.

---

## 8. Build Sequence for Antigravity (Milestones)

1. **M1 — Backend skeleton**: FastAPI + Postgres + pgvector + Alembic migrations + tenant/KB CRUD
2. **M2 — LiveKit plumbing**: token endpoint, a working "join empty room" test page
3. **M3 — AI Agent worker v0**: joins room, echoes STT→TTS with no LLM (proves the audio pipeline works end-to-end)
4. **M4 — LangGraph brain**: wire in Gemini 3.8 Flash + RAG retrieval + grounded answering
5. **M5 — Customer Portal UI**: real landing page, captions, call states
6. **M6 — Verification flow**: order ID + phone digit check node
7. **M7 — Escalation + WebSocket push**: backend logic + summary generation
8. **M8 — Agent Portal UI**: queue, accept, in-call view, transcript handoff
9. **M9 — Barge-in tuning**: get interruption latency under 300ms
10. **M10 — End-to-end test pass**: full call → escalate → human accepts → resolves, with 2-3 seeded tenants and sample KBs

Build in that order — each milestone is independently demoable, which matters for a POC.

---

## 9. Success Metrics to Track from Day 1

- Containment rate (% calls AI resolves without escalation)
- Average handle time (AI-only vs. AI+human)
- Escalation-to-accept latency (target: under 2 seconds)
- Barge-in response latency (target: under 300ms)
- Answer latency (customer stops talking → AI starts replying, target: under 1.5s)
- Verification success rate

---

## 10. Phase 2 — Roadmap (not built by Antigravity now)

Phase 2 extends Phase 1 without re-architecting it — the LiveKit room + AI worker + backend stay the same; only the "how does the customer get into the room" layer changes.

1. **Real phone number support (SIP)**
   - Integrate Twilio or Telnyx SIP trunking → LiveKit SIP bridge
   - Inbound calls land in a LiveKit room exactly like a browser call does today
   - No changes needed to the AI worker or agent portal — they don't know or care if the customer is on a browser or a phone line
2. **Caller voice verification**
   - Voiceprint enrollment + matching (e.g. via ElevenLabs or a dedicated voice-biometrics provider) as an alternative/addition to the order-ID + phone-digits flow
3. **Outbound calling** (callback scheduling fulfillment, proactive notifications)
4. **Supervisor analytics dashboard** — containment rate, AHT, cost-per-call, live call monitoring, QA scoring
5. **CRM/backend system integrations** (real order systems, ticketing, refund APIs) replacing Phase 1's mock verification
6. **Multi-language expansion** beyond English/Hindi, with automatic language detection

Phase 2 is a connectivity + integrations project, not a rebuild — that's the payoff of getting the Phase 1 architecture right.

---

## 11. Pre-Build Checklist & Risk Items (handle before/during M1–M10)

**Legal & compliance (California-specific)**

- California is a two-party consent state for call recording. The **Greet node must disclose recording/AI use** before any other interaction ("This call may be recorded for quality and training purposes, and you're speaking with an AI assistant."). This is not optional — bake it into every tenant's `welcome_message`.
- Decide a transcript/PII retention window now (e.g. auto-purge `call_turns` after 30–90 days) — a POC pitched to real call centers will get asked this.

**Failure handling (the plan above assumes happy-path only — add these)**

- STT/LLM/TTS call fails or times out mid-turn → retry once, then auto-escalate with "I'm having trouble — let me connect you to someone."
- Customer goes silent for N seconds → one "Are you still there?" prompt, then end the call or escalate.
- Escalation fires but no agent is available/online → fallback path needed (queue with wait estimate, or "leave a callback request" flow). Without this, `escalations` can pile up with nothing picking them up.

**Quality validation (so Slide 2–6 claims are measured, not assumed)**

- Build a small eval set: 15–20 seeded KB Q&A pairs, run against the Answer node to check grounding accuracy / hallucination rate before calling Phase 1 "done."
- Log per-call cost and latency (STT/TTS seconds, LLM tokens in/out, barge-in response time) from day 1 — this is what turns your cost-comparison slides from estimates into real numbers.

**Seed data (needed before M4 is testable)**

- One demo tenant, 5–10 sample KB documents (FAQ-style), and a mock order-lookup dataset for the verification node. Without this, nothing from M4 onward has real data to run against.

---

## 12. Suggested Folder Structure

```
asistline-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/ (routers: tenants, calls, kb, livekit, escalations)
│   │   ├── models/ (SQLAlchemy models)
│   │   ├── db/ (session, migrations)
│   │   └── core/ (config, auth)
│   └── agent_worker/
│       ├── worker.py (LiveKit agent entrypoint)
│       ├── graph.py (LangGraph state machine)
│       ├── rag.py (pgvector retrieval)
│       └── prompts.py
├── frontend-customer/ (React + Tailwind — Customer Calling Portal)
├── frontend-agent/ (React + Tailwind — Human Agent Portal)
└── docker-compose.yml (postgres, backend, both frontends)
```

---

## 13. Environment Variables Needed

```
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
GEMINI_API_KEY=
ELEVENLABS_API_KEY=
DATABASE_URL=
JWT_SECRET=
```

---

## 14. Master Build Prompt (paste this into Antigravity to start the build)

This is written so the agent treats it as a standing brief for the *entire* build, not a one-off task — and so it never loses track of what's already built across sessions, context resets, or compaction.

```
You are building AsistLine AI Phase 1 — a real-time AI voice agent system for
call centers, with two connected web portals sharing one LiveKit room and one
backend. You are the sole builder across this entire project. Treat this
prompt as your permanent brief for every session until Phase 1 is fully
built and tested — not a single task.

====================================================================
PROJECT CONTEXT (do not deviate from this without being told to)
====================================================================
Product: AsistLine AI — multilingual AI voice agent for BPO tier-1 inbound
support (order status, account inquiries, complaints, FAQ, callback
scheduling). Multi-tenant: each client has its own script, KB, escalation
rules. Target market: US/California call centers.

Phase 1 scope (build this, and ONLY this — Phase 2 is out of scope):
1. Customer Calling Portal (React + Tailwind) — browser-based WebRTC calling
2. Human Agent Portal (React + Tailwind) — receives AI escalations, agent
   joins the same call, sees full transcript + context, no repeat-yourself
3. FastAPI backend — tenant/KB management, call sessions, transcripts,
   escalation queue, LiveKit token issuing
4. AI Voice Agent Worker (Python, LiveKit Agent) — VAD → STT → LangGraph →
   TTS, RAG-grounded against pgvector KB, verification node, escalation node

Stack (do not substitute without discussing): FastAPI (Python 3.12), LiveKit
(WebRTC), Silero VAD, ElevenLabs Scribe (STT) + ElevenLabs TTS, Gemini
3.8 Flash (Medium) via LangGraph, PostgreSQL 16 + pgvector, React + Tailwind,
native FastAPI WebSocket for agent notifications, JWT auth.

Hard requirements, non-negotiable:
- Every call must open with a recording/AI disclosure (California is a
  two-party consent state) — this goes in every tenant's welcome_message
  and must play before anything else.
- The AI must NEVER answer outside what the KB retrieval returns. If
  retrieval has no relevant match, it says so and offers escalation — no
  invented answers, no guessing.
- Barge-in (customer interrupts AI) must stop AI audio within ~300ms.
- Escalation hand-off must give the human agent full transcript + a
  generated summary BEFORE the customer repeats anything.
- STT/LLM/TTS failures must retry once then auto-escalate, not hang silently.
- No agents available at escalation time must have a defined fallback
  (queue/callback), not an unhandled state.

====================================================================
PERSISTENT MEMORY — READ THIS EVERY SESSION, UPDATE IT EVERY SESSION
====================================================================
Maintain a file at the project root named PROGRESS.md. This file is your
memory across sessions, context resets, and compaction — treat it as the
single source of truth for "what already exists."

At the START of every session, before writing or changing any code:
1. Read PROGRESS.md in full.
2. Read the actual current state of the repo (list files, skim key modules)
   to confirm PROGRESS.md matches reality — if they disagree, trust the
   repo and correct PROGRESS.md first.
3. Identify the next incomplete milestone and resume from there. Do not
   re-build, re-scaffold, or rewrite anything already marked complete
   unless you are explicitly fixing a bug in it — if you need to change
   completed work, say why in PROGRESS.md before doing it.

At the END of every session (or after completing any milestone/sub-task),
update PROGRESS.md with:
- Which milestone(s) are now complete, and what was actually built
  (files/modules touched, key decisions made, any deviations from this
  brief and why)
- Any open issues, TODOs, or known gaps left for next session
- The exact next milestone to pick up

PROGRESS.md format to maintain:

  # AsistLine AI — Build Progress

  ## Status: [current milestone, e.g. "M4 in progress"]

  ## Completed
  - M1 — Backend skeleton: [done date/session] — details...
  - M2 — LiveKit plumbing: ...

  ## In Progress
  - M4 — LangGraph brain: [what's done so far, what's left]

  ## Not Started
  - M5, M6, M7, M8, M9, M10

  ## Decisions Log
  - [date] Chose X over Y because Z

  ## Known Issues / TODO
  - ...

  ## Next Session Should Start With
  - [specific next action]

Never skip updating this file. If you are ever unsure whether something was
already built, check PROGRESS.md and the repo before assuming — re-reading
is cheap, silently duplicating or overwriting work is expensive.

====================================================================
BUILD ORDER — build and fully verify each milestone before the next
====================================================================
M1 — Backend skeleton: FastAPI app, Postgres connection, pgvector
     extension enabled, Alembic migrations, tenant + KB CRUD endpoints.
M2 — LiveKit plumbing: token-issuing endpoint, a minimal test page that
     can join an empty LiveKit room (proves credentials/connectivity).
M3 — AI Agent worker v0: joins a room, does STT → TTS echo with NO LLM yet
     (proves the full audio pipeline works before adding intelligence).
M4 — LangGraph brain: wire in Gemini 3.8 Flash + pgvector RAG retrieval +
     grounded answering (refuses to answer outside KB context).
M5 — Customer Portal UI: real landing page, call button, live captions,
     call-state UI (connecting/active/transferring/ended), recording
     disclosure on greet.
M6 — Verification flow: order ID + phone-last-4 node, checked against a
     seeded mock dataset.
M7 — Escalation + WebSocket push: escalation trigger logic, summary
     generation, WebSocket push to available agents, no-agent-available
     fallback.
M8 — Agent Portal UI: escalation queue, call detail/summary view, accept
     flow, in-call view with live transcript, end-call flow.
M9 — Reliability pass: barge-in latency tuning (<300ms target), STT/LLM/TTS
     retry-then-escalate on failure, idle/silence timeout handling.
M10 — End-to-end test pass: seed 2-3 demo tenants with sample KBs + mock
     order data, run the 15-20 question eval set against the Answer node
     to check grounding/hallucination rate, run full call→escalate→accept→
     resolve flow manually, log per-call cost/latency.

Before declaring Phase 1 "complete," confirm every hard requirement above
is actually met, not just that the milestones are checked off.

====================================================================
WORKING STYLE
====================================================================
- Work through milestones in order. Don't jump ahead to later milestones
  before earlier ones are functional — each one should be demoable on
  its own.
- When a design decision isn't specified in this brief (e.g. exact pgvector
  index type, exact escalation sentiment-detection method), make a
  reasonable choice, implement it, and log it in the Decisions Log in
  PROGRESS.md rather than stalling.
- Keep tenant-specific config in the `script_config` JSONB structure
  described in this brief — do not hardcode any tenant's wording, voice,
  or rules into application code.
- If you hit a requirement conflict or something genuinely ambiguous that
  materially changes the architecture, stop and flag it rather than
  guessing silently.
```

---

## Quick-Reference: What Changed From the First Draft

- Added recording/AI disclosure as a hard requirement (California two-party consent)
- Added failure-handling requirements (STT/LLM/TTS retry logic, silence timeout, no-agent-available fallback)
- Added an eval-set validation step before declaring Phase 1 done
- Added per-call cost/latency logging as a build requirement, not an afterthought
- Added seed-data requirement so M4+ has something real to test against
- Added the Master Build Prompt with a persistent PROGRESS.md mechanism so Antigravity doesn't lose context across sessions