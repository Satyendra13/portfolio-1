import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String(36), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(32), default="pending", nullable=False) # pending, accepted, resolved, callback_requested
    
    accepted_by_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    call = relationship("Call", back_populates="escalations")
    accepted_by = relationship("Agent", back_populates="accepted_escalations")
