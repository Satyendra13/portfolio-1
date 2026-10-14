from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.db.session import init_db
from backend.app.api.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database schema & vector extensions
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title="AsistLine AI - Backend API",
    description="Real-time multi-tenant AI voice agent backend for BPO tier-1 inbound support",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows browser WebRTC portals to communicate cleanly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.responses import HTMLResponse

# Register all API endpoints
app.include_router(api_router)

@app.get("/test-livekit", response_class=HTMLResponse, tags=["Diagnostics"])
async def get_test_livekit_page():
    html_path = Path(__file__).parent / "static" / "test_livekit.html"
    return html_path.read_text(encoding="utf-8")

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "asistline-backend",
        "env": settings.ENV,
        "database": "connected",
        "livekit_configured": bool(settings.LIVEKIT_API_KEY and settings.LIVEKIT_URL),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "elevenlabs_configured": bool(settings.ELEVENLABS_API_KEY),
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )
