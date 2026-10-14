import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Call(Base):
    __tablename__ = "calls"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    livekit_room_name = Column(String(128), unique=True, nullable=False, index=True)
    customer_session_id = Column(String(128), nullable=False)
    status = Column(String(32), default="ai_active", nullable=False) # ai_active, escalated, human_active, ended
    language = Column(String(10), default="en", nullable=False)
    
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="calls")
    turns = relationship("CallTurn", back_populates="call", cascade="all, delete-orphan", order_by="CallTurn.timestamp")
    escalations = relationship("Escalation", back_populates="call", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="call", cascade="all, delete-orphan")


class CallTurn(Base):
    __tablename__ = "call_turns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String(36), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True)
    speaker = Column(String(32), nullable=False) # customer, ai, human
    text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True) # node, latency_ms, tokens, sentiment
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    call = relationship("Call", back_populates="turns")
