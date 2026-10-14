import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from backend.app.models.types import VectorType
from backend.app.core.config import settings

class KBDocument(Base):
    __tablename__ = "kb_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    chunks = relationship("KBChunk", back_populates="document", cascade="all, delete-orphan")


class KBChunk(Base):
    __tablename__ = "kb_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0, nullable=False)
    
    # Adaptive vector column: pgvector in Postgres, JSON in SQLite
    embedding = Column(VectorType(dim=settings.EMBEDDING_DIMENSION), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("KBDocument", back_populates="chunks")
    tenant = relationship("Tenant", back_populates="chunks")
