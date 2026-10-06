from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class KBDocumentResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    file_type: str
    content_hash: str
    created_at: datetime
    chunk_count: int = 0


class KBSearchRequest(BaseModel):
    query: str
    top_k: int = 4


class KBSearchHit(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class KBSearchResponse(BaseModel):
    query: str
    hits: List[KBSearchHit]
