import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    
    # Configuration JSONB/JSON
    # Example:
    # {
    #   "welcome_message": {"en": "Thank you for calling. This call may be recorded...", "hi": "..."},
    #   "languages": ["en", "hi"],
    #   "escalation_triggers": ["angry_sentiment", "repeat_failure", "explicit_request"],
    #   "verification_required_for": ["order_status", "refund"],
    #   "voice_id": "elevenlabs-voice-id"
    # }
    script_config = Column(JSON, nullable=False, default=dict)
    escalation_rules = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    documents = relationship("KBDocument", back_populates="tenant", cascade="all, delete-orphan")
    chunks = relationship("KBChunk", back_populates="tenant", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="tenant", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
