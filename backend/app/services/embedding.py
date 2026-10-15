import math
import numpy as np
from typing import List, Optional
from google import genai
from google.genai import types
from backend.app.core.config import settings

_client: Optional[genai.Client] = None

def get_genai_client() -> Optional[genai.Client]:
    global _client
    if _client is None and settings.GEMINI_API_KEY:
        try:
            _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize Google GenAI Client: {e}")
            _client = None
    return _client

def _fallback_embedding(text: str, dim: int = 768) -> List[float]:
    """
    Deterministic pseudo-embedding fallback in case Gemini API is unavailable or offline.
    Ensures identical texts have high similarity and tests can run reliably.
    """
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vec
    for word in words:
        h = hash(word)
        idx = abs(h) % dim
        vec[idx] += 1.0
    # Normalize L2
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

_embedding_cache: dict[str, List[float]] = {}

async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using Gemini model with in-memory caching to save API quota.
    """
    clean_text = text.strip().lower()
    if clean_text in _embedding_cache:
        return _embedding_cache[clean_text]

    client = get_genai_client()
    if client:
        try:
            import asyncio
            response = await asyncio.to_thread(
                client.models.embed_content,
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=text,
            )
            if response and response.embeddings:
                emb = list(response.embeddings[0].values)
                _embedding_cache[clean_text] = emb
                return emb
        except Exception as e:
            print(f"Gemini embedding API error: {e}, falling back to local embedding.")
    
    fallback = _fallback_embedding(text, dim=settings.EMBEDDING_DIMENSION)
    _embedding_cache[clean_text] = fallback
    return fallback

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts.
    """
    results = []
    for text in texts:
        emb = await generate_embedding(text)
        results.append(emb)
    return results

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Compute cosine similarity between two float vectors.
    """
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
