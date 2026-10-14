import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String(36), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(64), nullable=False)
    phone_last4 = Column(String(8), nullable=False)
    verified_bool = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    details = Column(JSON, nullable=True)

    # Relationships
    call = relationship("Call", back_populates="verifications")
