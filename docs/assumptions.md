# AsistLine AI — Assumptions & Environment Decisions

## Environment & Infrastructure Assumptions
1. **Local Execution & Verification**:
   - `docker` CLI is not directly accessible in this local Windows shell host environment; containerized execution config is provided via `docker-compose.yml`.
   - Automated test suite runs asynchronously using `pytest` and `pytest-asyncio` with SQLite + in-memory vector/pgvector emulation fallback for unit testing, and PostgreSQL 16 + pgvector support when deployed to Docker/production environments.
   - LiveKit WebRTC media transport uses the standard `MediaTransport` interface (`livekit-agents` worker in Python + `livekit-client` in JS/React). For standalone unit and integration testing without a running LiveKit server instance, a `MockMediaTransport` implementer is provided to verify STT/LLM/TTS streaming, turn logging, and barge-in handling.

2. **Multilingual & Models**:
   - Gemini Flash model (`gemini-2.5-flash` or configurable via `GEMINI_MODEL_ID`) is used for intent classification, KB grounded answer generation, call summary, and LLM turns.
   - ElevenLabs Scribe / Realtime STT and ElevenLabs Multilingual TTS are integrated via configurable environment keys and tenant voice mappings (`voices.en`, `voices.hi`, `voices.es`).
   - Grounded KB retrieval uses vector embeddings from Gemini (`models/text-embedding-004` or `GEMINI_EMBEDDING_MODEL`) combined with PostgreSQL full-text search / hybrid reciprocal rank fusion.

3. **Multi-tenancy Guarantee**:
   - All tenant-scoped database models enforce `tenant_id` at the SQLAlchemy repository query layer.
   - Multi-tenant verification unit tests enforce that any repository read/write on tenant entity models without explicit tenant context raises a `TenantFilterRequiredError`.

4. **Milestone Log**:
   - **M0 (Scaffold)**: Monorepo layout, Docker Compose setup, `.env.example`, Alembic database migrations, multi-tenant SQLAlchemy models, repository layer with tenant filter enforcement, unit tests, `/health` API, Makefile.
   - **M1 (Two-way Browser Voice Loop)**: `web/caller` React client app, FastAPI `/v1/calls/start`, `livekit-agents` worker voice pipeline (VAD -> STT -> LLM stream -> TTS stream), barge-in handling, turn logging, language detection (EN/HI), modular `respond(state)` LLM brain interface.
