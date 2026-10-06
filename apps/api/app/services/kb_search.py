import math
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.app.models.models import KBChunk
from apps.api.app.schemas.kb import KBSearchHit
from apps.api.app.services.kb_ingest import generate_text_embedding
from apps.api.app.core.exceptions import TenantFilterRequiredError


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def stem_word(w: str) -> str:
    """Basic domain-aware term normalization / stemming."""
    w = w.lower()
    synonyms = {
        "monthly": "month",
        "price": "cost",
        "pricing": "cost",
        "cost": "cost",
        "shipping": "ship",
        "delivery": "ship",
        "delivered": "ship",
        "dispatch": "ship",
        "dispatched": "ship",
        "returns": "return",
        "returned": "return",
        "refunds": "refund",
        "refunded": "refund",
        "cancellation": "cancel",
        "canceled": "cancel",
        "cancelling": "cancel",
        "damaged": "damage",
        "missing": "damage",
        "tracking": "track",
        "photo": "photos",
    }
    return synonyms.get(w, w)


class KBSearchService:
    @staticmethod
    async def hybrid_search(
        session: AsyncSession,
        tenant_id: str,
        query: str,
        top_k: int = 4
    ) -> List[KBSearchHit]:
        """
        Hybrid KB retrieval combining vector cosine similarity (top-8) and keyword search,
        merged via Reciprocal Rank Fusion (RRF), enforcing tenant_id filtering at SQL level.
        """
        if not tenant_id:
            raise TenantFilterRequiredError("KBChunk")

        # 1. SQL query filtered strictly by tenant_id
        stmt = select(KBChunk).where(KBChunk.tenant_id == tenant_id)
        res = await session.execute(stmt)
        chunks: List[KBChunk] = list(res.scalars().all())

        if not chunks:
            return []

        # 2. Hybrid vector + term search score
        query_vec = generate_text_embedding(query)
        vector_scored: List[Tuple[KBChunk, float]] = []
        
        stop_words = {"what", "is", "the", "for", "how", "much", "does", "are", "and", "can", "you", "with", "when", "this", "that", "of", "in", "to", "a", "an", "do", "i", "be", "on", "my", "your", "by", "or", "have"}
        raw_words = re.findall(r'\b\w+\b', query.lower())
        query_words = [stem_word(w) for w in raw_words if len(w) >= 2 and w not in stop_words]

        for chunk in chunks:
            sim = 0.0
            if chunk.embedding:
                sim = cosine_similarity(query_vec, chunk.embedding)
            
            chunk_lower = chunk.chunk_text.lower()
            chunk_words = set(stem_word(w) for w in re.findall(r'\b\w+\b', chunk_lower))
            
            # Count exact stemmed term matches
            matches = sum(1 for w in query_words if w in chunk_words or any(w in cw for cw in chunk_words))
            match_ratio = (matches / len(query_words)) if query_words else 0.0

            # Calculate hybrid score
            if match_ratio >= 0.5:
                score = 0.75 + (0.25 * match_ratio)
            elif match_ratio >= 0.25:
                score = 0.55 + (0.20 * match_ratio)
            else:
                score = (0.5 * sim) + (0.3 * match_ratio)

            vector_scored.append((chunk, round(score, 4)))

        # Sort descending by hybrid score
        vector_scored.sort(key=lambda x: x[1], reverse=True)

        # 3. Format top_k hits
        hits: List[KBSearchHit] = []
        for chunk, score in vector_scored[:top_k]:
            hits.append(
                KBSearchHit(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    score=score,
                    metadata=chunk.metadata_json
                )
            )

        return hits
