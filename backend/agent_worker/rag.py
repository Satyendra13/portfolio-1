import logging
from typing import Dict, Any, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.kb import KBChunk, KBDocument
from backend.app.services.embedding import generate_embedding, cosine_similarity
from backend.app.core.config import settings

logger = logging.getLogger("asistline.rag")

async def retrieve_kb_context(
    tenant_id: str,
    query: str,
    db: AsyncSession,
    top_k: int = 3,
    min_score: float = settings.DEFAULT_KB_MIN_SCORE,
) -> Tuple[str, List[Dict[str, Any]], float, bool]:
    """
    Perform semantic vector search against tenant KB chunks.
    Returns:
    (formatted_context_text, list_of_chunk_items, max_similarity_score, has_relevant_grounding)
    """
    if not query.strip():
        return "", [], 0.0, False

    query_emb = await generate_embedding(query)

    # Postgres pgvector path
    if "postgres" in settings.DATABASE_URL:
        stmt = (
            select(KBChunk, KBDocument.title)
            .join(KBDocument, KBChunk.document_id == KBDocument.id)
            .where(KBChunk.tenant_id == tenant_id)
            .order_by(KBChunk.embedding.cosine_distance(query_emb))
            .limit(top_k)
        )
        result = await db.execute(stmt)
        chunks = []
        max_score = 0.0
        for chunk, title in result.all():
            score = 1.0 - chunk.embedding.cosine_distance(query_emb)
            if score >= min_score:
                chunks.append({
                    "chunk_id": chunk.id,
                    "title": title,
                    "text": chunk.chunk_text,
                    "score": round(float(score), 4),
                })
                max_score = max(max_score, score)

        has_grounding = len(chunks) > 0
        context_str = "\n\n".join(f"[{c['title']}]: {c['text']}" for c in chunks)
        return context_str, chunks, max_score, has_grounding

    # SQLite fallback path
    stmt = (
        select(KBChunk, KBDocument.title)
        .join(KBDocument, KBChunk.document_id == KBDocument.id)
        .where(KBChunk.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    scored_items = []
    for chunk, title in result.all():
        if chunk.embedding:
            sim = cosine_similarity(query_emb, chunk.embedding)
            if sim >= min_score:
                scored_items.append({
                    "chunk_id": chunk.id,
                    "title": title,
                    "text": chunk.chunk_text,
                    "score": round(float(sim), 4),
                })

    scored_items.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored_items[:top_k]
    max_score = top_chunks[0]["score"] if top_chunks else 0.0
    has_grounding = len(top_chunks) > 0
    context_str = "\n\n".join(f"[{c['title']}]: {c['text']}" for c in top_chunks)

    return context_str, top_chunks, max_score, has_grounding
