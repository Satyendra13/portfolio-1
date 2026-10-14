import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.models.tenant import Tenant
from backend.app.models.kb import KBDocument, KBChunk
from backend.app.schemas.kb import (
    KBDocumentUpload,
    KBDocumentResponse,
    KBChunkResponse,
    KBSearchResponse,
    KBSearchResultItem,
)
from backend.app.services.embedding import generate_embedding, cosine_similarity

router = APIRouter(prefix="/tenants/{tenant_id}/kb", tags=["Knowledge Base"])

def split_text_into_chunks(text: str, max_chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text by paragraphs or sentences with optional overlap.
    """
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks = []
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > max_chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_len = para_len
        else:
            current_chunk.append(para)
            current_len += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks or [text]

@router.post("/upload", response_model=KBDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    tenant_id: str,
    payload: KBDocumentUpload,
    db: AsyncSession = Depends(get_db),
):
    # Verify tenant exists
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Create document
    doc = KBDocument(
        tenant_id=tenant_id,
        title=payload.title,
        content=payload.content,
        source_url=payload.source_url,
    )
    db.add(doc)
    await db.flush()  # to get doc.id

    # Split and embed chunks
    chunk_texts = split_text_into_chunks(payload.content)
    chunk_objects = []

    for idx, text in enumerate(chunk_texts):
        emb = await generate_embedding(text)
        chunk = KBChunk(
            document_id=doc.id,
            tenant_id=tenant_id,
            chunk_text=text,
            chunk_index=idx,
            embedding=emb,
        )
        chunk_objects.append(chunk)
        db.add(chunk)

    await db.commit()
    await db.refresh(doc)

    return KBDocumentResponse(
        id=doc.id,
        tenant_id=doc.tenant_id,
        title=doc.title,
        content=doc.content,
        source_url=doc.source_url,
        created_at=doc.created_at,
        chunks=[
            KBChunkResponse(
                id=c.id,
                chunk_text=c.chunk_text,
                chunk_index=c.chunk_index,
                created_at=c.created_at,
            )
            for c in chunk_objects
        ],
    )

@router.get("/documents", response_model=List[KBDocumentResponse])
async def list_documents(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KBDocument).where(KBDocument.tenant_id == tenant_id).order_by(KBDocument.created_at.desc())
    )
    docs = result.scalars().all()
    return docs

@router.get("/search", response_model=KBSearchResponse)
async def search_kb(
    tenant_id: str,
    q: str = Query(..., description="User question or query"),
    top_k: int = Query(4, description="Maximum number of chunks to return"),
    min_score: float = Query(settings.DEFAULT_KB_MIN_SCORE, description="Minimum cosine similarity threshold"),
    db: AsyncSession = Depends(get_db),
):
    query_emb = await generate_embedding(q)

    # Fetch chunks for this tenant
    # Check if we are running on postgres with pgvector
    if "postgres" in settings.DATABASE_URL:
        # Native pgvector cosine distance
        query = (
            select(KBChunk, KBDocument.title)
            .join(KBDocument, KBChunk.document_id == KBDocument.id)
            .where(KBChunk.tenant_id == tenant_id)
            .order_by(KBChunk.embedding.cosine_distance(query_emb))
            .limit(top_k)
        )
        result = await db.execute(query)
        items = []
        for chunk, title in result.all():
            score = 1.0 - chunk.embedding.cosine_distance(query_emb)
            if score >= min_score:
                items.append(
                    KBSearchResultItem(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        title=title,
                        chunk_text=chunk.chunk_text,
                        score=round(float(score), 4),
                    )
                )
        return KBSearchResponse(query=q, results=items)
    else:
        # SQLite / in-memory cosine similarity fallback
        query = (
            select(KBChunk, KBDocument.title)
            .join(KBDocument, KBChunk.document_id == KBDocument.id)
            .where(KBChunk.tenant_id == tenant_id)
        )
        result = await db.execute(query)
        scored_chunks = []
        for chunk, title in result.all():
            if chunk.embedding:
                score = cosine_similarity(query_emb, chunk.embedding)
                if score >= min_score:
                    scored_chunks.append((score, chunk, title))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        items = [
            KBSearchResultItem(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                title=title,
                chunk_text=chunk.chunk_text,
                score=round(float(score), 4),
            )
            for score, chunk, title in scored_chunks[:top_k]
        ]
        return KBSearchResponse(query=q, results=items)

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(tenant_id: str, doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KBDocument).where(KBDocument.tenant_id == tenant_id, KBDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    return None
