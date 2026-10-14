from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class KBDocumentUpload(BaseModel):
    title: str
    content: str
    source_url: Optional[str] = None

class KBChunkResponse(BaseModel):
    id: str
    chunk_text: str
    chunk_index: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KBDocumentResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    content: str
    source_url: Optional[str] = None
    created_at: datetime
    chunks: Optional[List[KBChunkResponse]] = None

    model_config = ConfigDict(from_attributes=True)

class KBSearchRequest(BaseModel):
    query: str
    top_k: int = 4
    min_score: float = 0.55

class KBSearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    chunk_text: str
    score: float

class KBSearchResponse(BaseModel):
    query: str
    results: List[KBSearchResultItem]
