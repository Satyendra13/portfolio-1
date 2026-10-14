# AsistLine AI — Phase 1: Real-Time Multilingual Voice Agent Platform

AsistLine AI is an enterprise-grade, real-time AI voice agent platform engineered for BPO Tier-1 inbound call center support. It bridges browser-based customers with AI agents and human support specialists across a shared LiveKit WebRTC room, powered by FastAPI, LangGraph, Google Gemini, and ElevenLabs.

---

## 🌟 Key Features

1. **Two Connected Portals in a Single Shared Room**:
   - **Customer Calling Portal** (`http://localhost:3000`): Dark glassmorphic browser calling UI with live audio waveform visualizer, real-time subtitles via LiveKit Data Channel, language toggle (English/Hindi), and microphone diagnostic checks.
   - **Human Agent Portal** (`http://localhost:3001`): Call center dashboard receiving real-time WebSocket alerts, AI-generated call summaries, full scrollable conversation transcripts, one-click "Accept & Join Call", in-call audio controls, and resolution tracking.

2. **Compliance & Grounded Intelligence**:
   - **Mandatory California Two-Party Consent Disclosure**: Automatically delivered on the initial greeting turn before any customer inquiry is processed.
   - **Strict Zero-Hallucination RAG Grounding**: Powered by Gemini embeddings (`models/gemini-embedding-001`) and vector search. If an answer cannot be grounded in retrieved knowledge base chunks, the agent politely refuses to speculate and offers a human transfer.
   - **Resilient Multi-Model LLM Pool**: Uses `gemini-2.5-flash`, `gemini-flash-lite-latest`, and `gemini-3.5-flash-lite` with automatic fallback and rate-limit backoff.

3. **Sub-300ms Barge-In Interruption & Speech Pipeline**:
   - **Silero VAD**: Continuously monitors incoming customer audio frames; interrupts AI voice playback in under 300ms upon customer speaking.
   - **ElevenLabs Streaming STT & TTS**: High-fidelity speech synthesis (`eleven_turbo_v2_5` streaming at 24kHz) and speech-to-text.
   - **Dynamic Audio Resampler**: LiveKit `AudioResampler` guarantees format synchronization between TTS output and WebRTC audio sources.

4. **Multi-Turn Verification Flow**:
   - Interactive identity verification (Order ID + last 4 digits of phone number) against mock backend records before disclosing sensitive account details.

5. **Zero-Repeat Human Escalation**:
   - Triggered on explicit request, persistent customer frustration/anger, verification failure, or knowledge base misses.
   - Pushes structured summary and full transcript to human agents via WebSockets so the customer never repeats their issue.

---

## 🏗️ Architecture & Tech Stack

```mermaid
graph TD
    CustomerPortal[Customer Portal (React 3000)] <-->|WebRTC Audio + Captions| LiveKit[LiveKit Cloud WebRTC Room]
    AgentPortal[Agent Portal (React 3001)] <-->|WebRTC Audio| LiveKit
    AgentPortal <-->|WebSocket Escalation Alerts| FastAPI[FastAPI Backend (Port 8000)]
    CustomerPortal <-->|REST API| FastAPI
    
    FastAPI <--> SQLite[(SQLite / pgvector DB)]
    
    FastAPI -.->|Launches on Call Start| VoiceWorker[Voice Worker (audio_pipeline.py)]
    VoiceWorker <-->|Audio Publish / Subscribe| LiveKit
    VoiceWorker <-->|State Machine Execution| LangGraph[LangGraph State Machine]
    LangGraph <-->|Semantic Vector Search| SQLite
    LangGraph <-->|Intent & Grounded Answer| Gemini[Google Gemini Flash]
    VoiceWorker <-->|VAD Interruption <300ms| Silero[Silero VAD]
    VoiceWorker <-->|Speech-to-Text & TTS| ElevenLabs[ElevenLabs AI Audio]
```

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (asyncio + aiosqlite / asyncpg), Alembic, Pydantic v2.
- **AI Brain**: LangGraph state machine, Google GenAI SDK (`models/gemini-embedding-001`, `gemini-2.5-flash`).
- **WebRTC & Audio**: LiveKit Python Agents SDK, Silero VAD, ElevenLabs Streaming STT/TTS.
- **Frontends**: React 18, Vite 6, Tailwind CSS, Lucide Icons, LiveKit Client SDK.

---

## 📋 Prerequisites

- **Python**: Version 3.11 (`.venv` virtual environment included in repository).
- **Node.js**: Version 18+ and `npm`.
- **API Keys**: Configured in `.env` (LiveKit Cloud, Google Gemini, ElevenLabs).

---

## ⚙️ Environment Configuration

Ensure your `.env` file at the root of the project contains:

```ini
ENV=development
LOG_LEVEL=INFO

# Backend API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=asistline-secret-key-12345

# Database (SQLite with vector fallback for local dev; PostgreSQL 16 + pgvector in prod)
DATABASE_URL=sqlite+aiosqlite:///./asistline.db
DATABASE_URL_SYNC=sqlite:///./asistline.db

# LiveKit WebRTC
LIVEKIT_URL=wss://brogrsmmers-2jty1rt6.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# AI Models
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_ID=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001

# ElevenLabs Speech
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_STT_MODEL=scribe_v2_realtime
ELEVENLABS_TTS_MODEL=eleven_multilingual_v2
```

---

## 🚀 How to Run the Application

You can run the full system in 3 or 4 terminal tabs:

### 1. Database Setup & Seeding (First-time only)

Run database migrations and seed the demo data (Apex Logistics, Pacific Electronics, CalCoast Health with 9 embedded KB documents and verification orders):

```powershell
# Run Alembic migrations
.venv\Scripts\python.exe -m alembic upgrade head

# Seed demo tenants, knowledge base chunks, and mock verification records
.venv\Scripts\python.exe -m backend.app.db.seed_demo
```

### 2. Start the FastAPI Backend (Port 8000)

```powershell
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000 --reload
```
- API Docs & Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- LiveKit diagnostics page: `http://localhost:8000/test-livekit`

### 3. Start the Customer Calling Portal (Port 3000)

```powershell
cd frontend-customer
npm.cmd run dev
```
Open `http://localhost:3000` in your web browser.

### 4. Start the Human Agent Portal (Port 3001)

```powershell
cd frontend-agent
npm.cmd run dev
```
Open `http://localhost:3001` in your web browser.

### 5. (Optional) Run the Standalone Voice Worker Service

> **Note**: The FastAPI backend **automatically spawns** the voice agent worker in the background whenever a customer clicks "Call Support".  
> However, if you prefer to run the worker in an independent terminal window or attach to a custom room directly, use:

```powershell
# Run in dispatcher daemon mode (monitors and attaches to new calls automatically)
.venv\Scripts\python.exe -m backend.agent_worker.worker

# Or connect directly to a specific LiveKit room
.venv\Scripts\python.exe -m backend.agent_worker.worker --room <room-name> --tenant apex-logistics
```

---

## 🧪 How to Test & Interactive Demo Walkthrough

### Scenario A: Full Voice Call with AI Agent
1. Open the **Customer Portal** at `http://localhost:3000`.
2. Select a tenant from the dropdown (e.g. **Apex Logistics Support**).
3. Click the glowing **"Call Support"** button and grant microphone permission when prompted.
4. **Listen to the Greeting**: The AI agent immediately joins the room and speaks:
   > *"Thank you for calling Apex Logistics Support. Please note that this call is recorded for quality and compliance purposes. How can I help you today?"*
5. **Ask a Grounded Question**:
   - Ask: *"How many days does standard shipping take?"*
   - AI answers strictly from the KB: *"Standard ground shipping takes 3 to 5 business days..."*
6. **Test Barge-In (<300ms interruption)**:
   - While the AI is speaking, begin talking: *"Wait, what about overnight shipping?"*
   - The AI voice immediately cuts off and answers your new question.

### Scenario B: Order Verification Flow
1. While connected on the call, say: *"I want to check the status of my order."*
2. The AI prompts: *"I can certainly help you with that. Could you please provide your Order ID?"*
3. Say: *"10492"*
4. The AI prompts: *"Thank you. For security, could you please provide the last four digits of the phone number on the account?"*
5. Say: *"4821"*
6. The AI verifies the record and provides the tracking details (e.g., in transit, out for delivery).

### Scenario C: Zero-Repeat Human Agent Escalation
1. Open the **Human Agent Portal** at `http://localhost:3001` in another browser window (or side-by-side).
2. On the Customer Portal call, say: *"I need to speak with a human specialist right now, this is urgent!"*
3. The AI replies: *"I completely understand. Let me transfer you directly to a human specialist. Please hold on."*
4. **Agent Portal Alert**:
   - An audible alert sounds on `http://localhost:3001` and a new escalation card appears in the queue.
   - Shows Reason: *"Customer requested human agent"*, AI-generated summary, and the complete transcript history.
5. Click **"Accept & Join Call"** on the Agent Portal.
   - The human agent connects to the **exact same LiveKit room** via WebRTC.
   - Customer and Agent can speak to each other with zero repetition required.
6. Click **"Resolve & End Call"** to complete the handoff.

---

## 🧪 Automated Testing & Evaluation Benchmark

Run the automated test suite across all milestones:

```powershell
# Run the complete test suite
.venv\Scripts\pytest.exe -v tests/

# Run individual test modules
.venv\Scripts\pytest.exe -v tests/test_m1_m2.py      # Backend CRUD, migrations, LiveKit token issuance
.venv\Scripts\pytest.exe -v tests/test_m3_worker.py   # Echo worker & track publishing
.venv\Scripts\pytest.exe -v tests/test_m4_brain.py    # LangGraph nodes, greeting disclosure, verification
.venv\Scripts\pytest.exe -v tests/test_m10_e2e_eval.py # End-to-end call lifecycle & 15-question evaluation
```

### 15-Question Grounding & Hallucination Benchmark Results:
- **Grounded Questions Accuracy**: **100.0%** (9/9 correct answers matching knowledge base facts)
- **Zero-Hallucination Refusal Accuracy**: **100.0%** (6/6 ungrounded queries correctly refused)

---

## 📁 Repository Directory Structure

```text
stitch/
├── alembic/                       # Database migration scripts & environments
│   └── versions/                  # Schema revisions (tenants, calls, escalations, etc.)
├── backend/
│   ├── agent_worker/              # Real-time voice agent worker
│   │   ├── audio_pipeline.py      # Silero VAD, ElevenLabs STT/TTS, 24kHz AudioResampler
│   │   ├── graph.py               # LangGraph compiled state machine (6 nodes)
│   │   ├── llm_client.py          # Gemini Flash client with auto-fallbacks
│   │   ├── prompts.py             # System prompts & California disclosure rules
│   │   ├── rag.py                 # Vector similarity search retriever
│   │   └── worker.py              # LiveKit WebRTC voice worker & dispatcher CLI
│   └── app/
│       ├── api/endpoints/         # REST & WebSocket endpoints (calls, escalations, kb, tenants)
│       ├── core/config.py         # Application settings & environment parsing
│       ├── db/                    # SQLAlchemy async engine, session, & seed scripts
│       ├── models/                # SQLAlchemy models (hybrid VectorType)
│       ├── schemas/               # Pydantic validation schemas
│       └── services/              # LiveKit token generator & WebSocket broadcast manager
├── frontend-customer/             # React 18 + Vite Customer Calling Portal (Port 3000)
│   └── src/                       # LiveKit WebRTC client, audio visualizer, captions
├── frontend-agent/                # React 18 + Vite Human Agent Portal (Port 3001)
│   └── src/                       # Real-time queue, WebSockets, in-call audio controls
├── tests/                         # Pytest test suite covering Milestones M1 through M10
├── PROGRESS.md                    # Persistent development progress tracking
└── README.md                      # Project documentation and run guide
```

---

## 🔧 Troubleshooting & Common Questions

1. **Why did `python -m backend.agent_worker.worker` exit immediately?**
   - *Cause*: The worker script previously lacked a `__main__` entrypoint.
   - *Fix*: A standalone CLI and dispatcher daemon was added. You can now run `python -m backend.agent_worker.worker` to watch for calls or pass `--room <name>` to join directly.

2. **Why was the AI voice agent not speaking initially?**
   - *Cause*: LiveKit's `AudioSource` expects 24,000 Hz, while the default ElevenLabs output stream delivered 22,050 Hz MP3 frames, causing an `RtcError: sample_rate and num_channels don't match`.
   - *Fix*: Configured ElevenLabs TTS with `encoding="mp3_24000_48"` and added an `rtc.AudioResampler` in `audio_pipeline.py` to guarantee seamless audio delivery.

3. **Browser Microphone Permissions**:
   - Ensure you click "Allow" when the browser requests microphone access on `http://localhost:3000` and `http://localhost:3001`. If blocked, click the lock/settings icon in the URL bar to enable it.
