from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.core.db import engine, Base, AsyncSessionLocal
from apps.api.app.routers import health, calls, kb, escalations
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.kb_ingest import KBIngestService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed tenants and default KB documents
    async with AsyncSessionLocal() as session:
        await TenantService.seed_tenants_from_files(session)
        await KBIngestService.seed_tenant_kbs(session)

    yield


app = FastAPI(
    title="AsistLine AI API",
    description="Multi-tenant, real-time multilingual AI voice agent backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(calls.router)
app.include_router(kb.router)
app.include_router(escalations.router)


@app.get("/")
async def root():
    return {"message": "Welcome to AsistLine AI API Platform"}
