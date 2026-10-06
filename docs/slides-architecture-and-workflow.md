# AsistLine AI — 10-Slide Presentation Deck
## Executive, Architectural, Operational & Economic Blueprint

---

### Slide Directory
1. [Slide 1: Executive Overview & Problem Statement](#slide-1-executive-overview--problem-statement)
2. [Slide 2: Cost Breakdown: AI vs. Human Agents (US/California)](#slide-2-cost-breakdown-ai-vs-human-agents-uscalifornia)
3. [Slide 3: Operational Scalability & The Hybrid Deployment Model](#slide-3-operational-scalability--the-hybrid-deployment-model)
4. [Slide 4: End-to-End Conversational Workflow](#slide-4-end-to-end-conversational-workflow)
5. [Slide 5: Enterprise System Architecture & Topology](#slide-5-enterprise-system-architecture--topology)
6. [Slide 6: Ultra-Low Latency Voice Pipeline & Barge-In](#slide-6-ultra-low-latency-voice-pipeline--barge-in)
7. [Slide 7: Knowledge Base Grounding & Anti-Hallucination Guard](#slide-7-knowledge-base-grounding--anti-hallucination-guard)
8. [Slide 8: LangGraph Dialogue Orchestration & Backend Tools](#slide-8-langgraph-dialogue-orchestration--backend-tools)
9. [Slide 9: Technology Stack (What & Why)](#slide-9-technology-stack-what--why)
10. [Slide 10: Key Metrics, ROI & Phased Roadmap](#slide-10-key-metrics-roi--phased-roadmap)

---

## Slide 1: Executive Overview & Problem Statement
### Next-Gen BPO Tier-1 Inbound Voice Automation

#### Key Presentation Points:
- **The Contact Center Crisis**:
  - **High Turnover**: 30%–45% annual agent attrition drives non-stop hiring and training overhead.
  - **High Handle Times**: Tier-1 AHT averages 5–8 minutes, largely spent on repetitive queries (order status, FAQs, refunds).
  - **IVR Drop-Off**: Legacy touch-tone systems frustrate callers and yield poor customer satisfaction.
- **The GenAI Challenge**: Uncontrolled LLMs hallucinate policies, pricing, and refund terms—a catastrophic legal and brand risk.
- **The AsistLine Solution**:
  - **Real-Time Voice Agent**: Speaks strictly from verified client knowledge bases and live CRM/OMS APIs.
  - **Sub-1.5s Voice Loop**: Natural conversational turn-taking with instant barge-in support.
  - **Warm Human Handoff**: Transfers complex issues to human agents in the same room with full context in < 2 seconds.

> **Speaker Note**: *"Contact centers are bleeding money on repetitive calls, while traditional IVRs frustrate customers. AsistLine AI delivers human-quality, zero-hallucination voice automation that frees human agents to focus on high-value conversations."*

---

## Slide 2: Cost Breakdown: AI vs. Human Agents (US/California)
### 75% to 85% Reduction in Cost Per Productive Minute

#### Cost Comparison Table:
| Metric / Call Type | Human Call Center Agent (US / CA) | AsistLine AI Voice Agent | Net Savings per Call |
|:---|:---|:---|:---|
| **Billing Basis** | Hourly ($35–$50+ loaded wage with idle time) | Per active call minute only | **Pay only when speaking** |
| **Effective Cost / Min** | **$1.00 – $1.70 / min** (at 50-60% occupancy) | **$0.08 – $0.25 / min** | **75% – 85% cheaper** |
| **Quick Call (1.5 min)** | $1.50 – $2.55 | $0.15 – $0.25 | **~$2.00 saved** |
| **Standard Call (3.5 min)** | $3.50 – $5.95 | $0.35 – $0.60 | **~$4.00 saved** |
| **Long Call (7.0 min)** | $7.00 – $11.90 | $0.80 – $1.40 | **~$8.00 saved** |

#### AI Per-Minute Pipeline Stack:
- **STT (Speech-to-Text)**: $0.004 – $0.024/min (Real-time stream transcription)
- **LLM Reasoning**: $0.003 – $0.040/min (Context window + generated tokens)
- **TTS (Voice Synthesis)**: $0.020 – $0.120/min (High-fidelity natural voice)
- **Telephony & Media**: $0.008 – $0.022/min (WebRTC / SIP audio transport)
- **Total All-In Cost**: **$0.085 – $0.25 / active minute**

> **Speaker Note**: *"In California, fully loaded human agents cost $35 to $50 an hour. Factoring in breaks and idle time, that's $1.00 to $1.70 per productive minute. An AI voice call costs $0.08 to $0.25 all-in—generating 75% to 85% instant savings."*

---

## Slide 3: Operational Scalability & The Hybrid Deployment Model
### Tiered Routing: Combining AI Efficiency with Human Empathy

#### 1. Operational Capability Matrix:
| Capability | Human Agent | AsistLine AI Agent |
|:---|:---|:---|
| **Concurrency** | 1 call at a time per agent | **Infinite concurrent calls** (instant scale from 0 to 1,000+) |
| **Queue Time** | Callers wait on hold during surges | **Zero queueing**; answers on the 1st ring 24/7/365 |
| **Data & CRM Entry** | Manual post-call wrap-up; risk of errors | **100% structured JSON logs** synced to CRM immediately |
| **Turnover & Training** | Continuous retraining; 30%+ turnover | **Zero turnover**; prompt & KB updates take effect instantly |

#### 2. The Tiered Hybrid Strategy:
```
Caller Dials In
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ TIER 1: AsistLine AI Voice Agent (70% - 80% of Volume) │
│ • Instant pickup, 24/7 availability                    │
│ • Handles FAQs, order status, scheduling, simple claims│
│ • Validates caller identity & captures intake data     │
└──────────────────────────┬─────────────────────────────┘
                           │ Complex Issue / Sentiment Spike / Human Request
                           ▼
┌────────────────────────────────────────────────────────┐
│ TIER 2: Human Specialists (20% - 30% of Volume)        │
│ • Warm transfer inside the SAME WebRTC room            │
│ • Screen-pop displays AI summary, verified data, and KB│
│ • High-empathy negotiation & nuanced problem-solving   │
└────────────────────────────────────────────────────────┘
```

> **Speaker Note**: *"We don't eliminate human agents; we empower them. AI deflects 70% to 80% of routine volume on Tier 1. When an issue is complex or sensitive, it warm-transfers to a human specialist with full context in under two seconds."*

---

## Slide 4: End-to-End Conversational Workflow
### Frictionless Flow: From Inbound Click to Resolution or Warm Transfer

```mermaid
sequenceDiagram
    autonumber
    actor Caller as Caller Browser (WebRTC)
    participant LK as LiveKit SFU (WebRTC)
    participant Worker as Voice Worker (Python)
    participant LG as LangGraph Orchestration
    participant KB as pgvector Hybrid KB
    actor Human as Human Agent (Softphone)

    Caller->>LK: 1. Join Call Room (WebRTC)
    Worker->>LK: 2. Worker Joins & Speaks Tenant Greeting
    Caller->>Worker: 3. Spoken Utterance (Streaming Audio)
    Worker->>Worker: 4. VAD + ElevenLabs STT Transcription
    Worker->>LG: 5. Route to LangGraph Engine
    alt Routine FAQ / Policy Query
        LG->>KB: 6a. Hybrid Search (pgvector + FTS)
        KB-->>LG: 6b. Top Grounded Chunks
        LG->>LG: 6c. Verify Strict Grounding Guard
    else Transactional Request (e.g., Order Status)
        LG->>LG: 7a. 2-Factor Caller Verification
        LG->>LG: 7b. Execute Tenant Tool & Spoken Confirmation
    end
    LG-->>Worker: 8. Grounded Stream $\rightarrow$ ElevenLabs TTS
    Worker->>Caller: 9. Audio Response (< 1.5s Median Latency)

    opt Human Escalation Triggered
        LG->>Human: 10. Screen Pop with AI Summary & Live Transcript
        Human->>LK: 11. Human Joins Room; AI Steps Aside
        Human->>Caller: 12. Human Resolves Call without Asking Caller to Repeat
    end
```

> **Speaker Note**: *"The caller joins via WebRTC. Our worker greets them immediately. In under 1.5 seconds, their speech is transcribed, verified against the KB or CRM, and synthesized back. If human intervention is needed, the transfer happens seamlessly in the same room."*

---

## Slide 5: Enterprise System Architecture & Topology
### Decoupled, Microservice-Driven Infrastructure

```
┌────────────────────────────────────────────────────────────────────────┐
│                              CLIENT TIER                               │
│  Caller Web App (React)   Human Softphone (React)   Supervisor Portal  │
│  • WebRTC Audio Track     • Screen Pop & Context    • Live Audio Drawer│
│  • Live Captions Stream   • Call Disposition Form   • Analytics & KPIs │
└───────────────────┬───────────────────┬───────────────────┬────────────┘
                    │ WebRTC            │ WebRTC            │ REST / WS
┌───────────────────┴───────────────────┴───────────────────┼────────────┐
│ MEDIA TRANSPORT: LiveKit Server (WebRTC SFU, Self-Hosted) │            │
│ Room per Call: [ Caller ] ◄──► [ Voice Worker ] ◄──► [ Human Agent ]   │
└───────────────────────────────────────┬────────────────────────────────┘
                                        │ Streaming Audio (PCM16)
┌───────────────────────────────────────┴────────────────────────────────┐
│ VOICE WORKER: Python Service (`livekit-agents`)                        │
│ ┌──────────────┐   ┌────────────────┐   ┌──────────────┐   ┌─────────┐ │
│ │  Silero VAD  ├──►│ ElevenLabs STT ├──►│  LangGraph   ├──►│ElevenLabs││
│ │  Turn Engine │   │ Realtime Stream│   │ State Engine │   │   TTS   │ │
│ └──────────────┘   └────────────────┘   └───────┬──────┘   └─────────┘ │
└─────────────────────────────────────────────────┼──────────────────────┘
                                                  │ Async Queries & APIs
┌─────────────────────────────────────────────────┴──────────────────────┐
│ CONTROL PLANE & PERSISTENCE                                            │
│ FastAPI Backend        Tenant Tool Adapters     PostgreSQL 16+pgvector │
│ • Token Management     • CRM / OMS Mock APIs    • Tenant Isolation     │
│ • Escalation Queuing   • Order / Ticket Actions • Vectors & Transcripts│
└────────────────────────────────────────────────────────────────────────┘
```

> **Speaker Note**: *"Our topology separates media from control logic. LiveKit handles WebRTC audio mixing. Our Python worker streams audio directly to ElevenLabs and Gemini. The FastAPI backend and PostgreSQL with pgvector manage state, tenant isolation, and CRM tools."*

---

## Slide 6: Ultra-Low Latency Voice Pipeline & Barge-In
### Engineering Natural, Interruption-Aware Spoken Dialogue

#### 1. Latency Budget Breakdown:
```
Caller Stops Speaking ────────────────────────► First AI Audio Packet (≤ 1.5s Median)
├──── 150ms ────┼───── 350ms ─────┼────── 450ms ──────┼───── 350ms ─────┤
│ Silero VAD    │ ElevenLabs STT  │ Gemini Flash LLM  │ ElevenLabs TTS  │
│ Turn Detected │ Streaming Scribe│ First Token Emit  │ First PCM Chunk │
└───────────────┴─────────────────┴───────────────────┴─────────────────┘
```

#### 2. Conversational Voice Engineering:
- **Instant Barge-In (< 300 ms)**: When caller speaks while AI is talking, VAD triggers an immediate cancellation packet, purges audio buffers, and marks the turn `interrupted: true` with the exact words spoken.
- **Dead-Air Management**:
  - If a backend tool lookup takes **> 1.2s**, the AI speaks an empathetic filler: *"Let me check that for you..."*
  - If the caller is silent for **6.0s**, the agent prompts gently before gracefully ending the call.
- **Spoken Text Optimization**: Output is stripped of markdown and lists; numbers and order IDs are pronounced digit-by-digit (`"4-8-2-1-3"`).

> **Speaker Note**: *"Voice latency over 2 seconds feels robotic and awkward. By streaming tokens from Gemini Flash straight into ElevenLabs TTS, we hit under 1.5 seconds median latency. If the caller interrupts, audio cuts off in less than 300 milliseconds."*

---

## Slide 7: Knowledge Base Grounding & Anti-Hallucination Guard
### Zero Generative Invention on Policies, Pricing, and Rules

#### 1. Ingestion & Hybrid Retrieval:
- **Document Chunking**: 400-token chunks with 60-token overlap across PDF, DOCX, TXT, and FAQ CSV files.
- **Hybrid Search**: Merges dense semantic vectors (pgvector Cosine Top-8) with sparse keyword queries (PostgreSQL Full-Text Top-8) using **Reciprocal Rank Fusion (RRF)**.

#### 2. Grounding Guard Architecture (`grounding.py`):
```
Hybrid Retrieval Score Check
 ├── Below tenant.kb_min_score ────────► Refusal: "I don't have that information.
 │                                                 Let me connect you to an agent."
 └── Meets Threshold
       │
       ▼
 Prompt Gemini with Strict Context & Schema
       │
       ▼
 Pydantic Output: { answer, used_chunk_ids, confidence }
       ├── If NO_ANSWER or empty chunk_ids ─► Refusal / Escalate
       └── If Valid & Grounded ─────────────► Synthesize Speech Output
```

- **Traceable Auditing**: Every spoken answer logs its exact `used_chunk_ids` in `call_turns`, enabling instant supervisor verification.

> **Speaker Note**: *"This is our anti-hallucination moat. If a question isn't in the knowledge base, the AI refuses to guess. It returns a pre-configured tenant script and offers a human transfer or callback. Every factual statement is backed by verifiable document chunk IDs."*

---

## Slide 8: LangGraph Dialogue Orchestration & Backend Tools
### State Machine Control & Secure CRM Execution

#### 1. Deterministic Dialogue State Machine:
- **State Schema (`CallState`)**: Tracks `call_id`, `tenant_id`, `verified: bool`, `intent`, `verify_attempts`, `tool_results`, and `sentiment`.
- **Core Nodes**:
  - `greet` $\rightarrow$ Tenant-branded greeting in caller's language.
  - `detect_language` $\rightarrow$ Dynamic language switching (EN/HI/ES).
  - `classify_intent` $\rightarrow$ High-speed intent extraction.
  - `verify_caller` $\rightarrow$ 2-Factor verification (e.g., Order ID + Phone Last-4); **locks after 3 failed attempts**.
  - `run_action` $\rightarrow$ Executes backend transactions via `TenantToolAdapter`.
  - `check_escalation` $\rightarrow$ Evaluates sentiment, keywords, and retries after every turn.

#### 2. Two-Way Confirmation on Writes:
- High-risk operations (ticket submission, address updates, cancellations) require **explicit spoken read-back confirmation**:
  - *"I have created a return request for item 4-8-2-1. Shall I confirm this now?"*

> **Speaker Note**: *"LangGraph replaces unpredictable LLM loops with an explicit, checkpointed state machine. Account-sensitive actions require two-factor verification, and any transactional write requires verbal confirmation before firing."*

---

## Slide 9: Technology Stack (What & Why)
### Enterprise Cloud-Native Components

| Layer | Component | What It Does | Why We Selected It |
|:---|:---|:---|:---|
| **API Control Plane** | **FastAPI** (Python 3.12) | REST & WebSocket server for auth, tokens, analytics | High async throughput, native Pydantic v2 validation |
| **Media Transport** | **LiveKit Server** (Self-Hosted) | WebRTC SFU managing audio streams | Native room routing for human handoff; clean SIP migration path |
| **Voice Worker** | **`livekit-agents`** | Async Python daemon bridging audio & LLM | Production VAD, turn detection, and instant buffer flushing |
| **Speech-to-Text** | **ElevenLabs Scribe** | Streaming real-time transcription | Industry-leading latency, robust multilingual detection |
| **LLM Reasoning** | **Gemini 2.5 Flash** | Intent routing, KB answers, and summarization | Sub-second TTFT (Time-To-First-Token), native JSON schema output |
| **Text-to-Speech** | **ElevenLabs Multilingual** | Streaming PCM voice synthesis | Ultra-realistic voice quality with tenant voice customization |
| **Orchestration** | **LangGraph** | Dialogue state machine and checkpoints | Deterministic routing, turn-by-turn PostgreSQL checkpointing |
| **Database & Vectors**| **PostgreSQL 16 + pgvector** | Unified store for relational data and embeddings | Zero need for external vector DB; strict SQL tenant isolation |
| **Frontend Web** | **React + Vite + Tailwind** | Caller app, agent softphone, supervisor portal | Shared LiveKit client SDK, responsive ergonomics |

> **Speaker Note**: *"Every piece of our stack was chosen for latency, reliability, and security. We run FastAPI and LiveKit for real-time audio routing, Gemini Flash and ElevenLabs for sub-second speech streaming, and PostgreSQL with pgvector for unified storage."*

---

## Slide 10: Key Metrics, ROI & Phased Roadmap
### Business Impact & Continuous Delivery

#### 1. Core Contact Center KPIs:
- **Containment Rate**: Target **$\ge$ 70%** of Tier-1 automatable calls resolved end-to-end by AI.
- **AHT Reduction**: Lowers average handle time from **360s human baseline to < 180s** on AI calls.
- **Transfer Accuracy**: Target **$\ge$ 90%** of escalations validated as appropriate by human agents.
- **Blended Cost Per Call**: Drops average call expense from **$4.50+ to < $0.75**.

#### 2. Phased Milestone Roadmap:
```
M0: Scaffold & Multi-Tenant DB ──► M1: Two-Way WebRTC Voice Loop ──► M2: Knowledge Base Grounding
                                                                           │
M5: Supervisor Analytics ◄── M4: Warm Human Handoff ◄── M3: LangGraph & Backend Tools
       │
M6: Multi-Tenant Hardening ──► M7: 50-Scenario Eval Benchmark ──► Phase 2: SIP / Telephony
```

- **Phase 2 Expansion**: LiveKit SIP trunking (Twilio/Telnyx), biometric speaker ID, and native Salesforce/Zendesk CRM integrations.

> **Speaker Note**: *"AsistLine AI delivers measurable ROI from day one: 70%+ containment, 50% handle time reduction, and an 80% decrease in call costs. Our modular architecture is built to scale from browser WebRTC directly into enterprise SIP telephony."*
