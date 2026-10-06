import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.core.db import Base


class TenantScopedMixin:
    """Mixin for models that belong to a specific tenant and require tenant filtering."""
    is_tenant_scoped: bool = True


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    config: Mapped[Optional["TenantConfig"]] = relationship("TenantConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")


class TenantConfig(Base, TenantScopedMixin):
    __tablename__ = "tenant_configs"

    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    config_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="config")


class User(Base, TenantScopedMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # bpo_admin | supervisor | human_agent
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KBDocument(Base, TenantScopedMixin):
    __tablename__ = "kb_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chunks: Mapped[List["KBChunk"]] = relationship("KBChunk", back_populates="document", cascade="all, delete-orphan")


class KBChunk(Base, TenantScopedMixin):
    __tablename__ = "kb_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)  # Store JSON embedding vector
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["KBDocument"] = relationship("KBDocument", back_populates="chunks")


class Call(Base, TenantScopedMixin):
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    room_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    primary_intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verify_attempts: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[str] = mapped_column(String(32), default="active")  # active | resolved_by_ai | escalated | abandoned | callback_scheduled
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    human_agent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ai_talk_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    human_talk_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    turns: Mapped[List["CallTurn"]] = relationship("CallTurn", back_populates="call", cascade="all, delete-orphan", order_by="CallTurn.seq")
    events: Mapped[List["CallEvent"]] = relationship("CallEvent", back_populates="call", cascade="all, delete-orphan")


class CallTurn(Base):
    __tablename__ = "call_turns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id: Mapped[str] = mapped_column(String(64), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String(16), nullable=False)  # caller | ai | human
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    interrupted: Mapped[bool] = mapped_column(Boolean, default=False)
    used_chunk_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    call: Mapped["Call"] = relationship("Call", back_populates="turns")


class CallEvent(Base):
    __tablename__ = "call_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id: Mapped[str] = mapped_column(String(64), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    call: Mapped["Call"] = relationship("Call", back_populates="events")


class Escalation(Base, TenantScopedMixin):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id: Mapped[str] = mapped_column(String(64), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued | accepted | resolved | callback_offered
    summary_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    human_agent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class Ticket(Base, TenantScopedMixin):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    call_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("calls.id", ondelete="SET NULL"), nullable=True)
    ticket_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open")
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Callback(Base, TenantScopedMixin):
    __tablename__ = "callbacks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    call_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("calls.id", ondelete="SET NULL"), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    preferred_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CallSummary(Base):
    __tablename__ = "call_summaries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id: Mapped[str] = mapped_column(String(64), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    actions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    follow_ups: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CallMetric(Base, TenantScopedMixin):
    __tablename__ = "call_metrics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id: Mapped[str] = mapped_column(String(64), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    latency_p50: Mapped[float] = mapped_column(Float, default=0.0)
    latency_p95: Mapped[float] = mapped_column(Float, default=0.0)
    total_duration: Mapped[float] = mapped_column(Float, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EscalationFeedback(Base, TenantScopedMixin):
    __tablename__ = "escalation_feedback"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    escalation_id: Mapped[str] = mapped_column(String(64), ForeignKey("escalations.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(32), nullable=False)  # appropriate | could_have_been_automated | wrong_queue
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
