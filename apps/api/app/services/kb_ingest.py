import os
import io
import csv
import hashlib
import re
import math
from typing import List, Dict, Any, Tuple, Optional
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from apps.api.app.core.config import settings
from apps.api.app.models.models import KBDocument, KBChunk


def generate_text_embedding(text: str) -> List[float]:
    """
    Generate embedding vector using Gemini API if configured,
    or a deterministic normalized TF-IDF / term-hashing vector for test/offline mode.
    """
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            result = genai.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception:
            pass

    # Deterministic 128-dim term-hashing vector fallback for offline testing
    dim = 128
    vec = [0.0] * dim
    words = re.findall(r'\w+', text.lower())
    for w in words:
        idx = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16) % dim
        vec[idx] += 1.0

    # Normalize vector to unit length
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def parse_and_chunk_document(
    filename: str,
    content_bytes: bytes,
    file_type: str
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Parse document content and split into semantic chunks on heading boundaries (Markdown/FAQ).
    """
    chunks: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    if file_type.lower() in ["csv", "faq"]:
        try:
            decoded = content_bytes.decode("utf-8")
            reader = csv.reader(io.StringIO(decoded))
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    q, a = row[0].strip(), row[1].strip()
                    if q and a:
                        chunk_text = f"FAQ Question: {q}\nAnswer: {a}"
                        chunks.append(chunk_text)
                        metadatas.append({"type": "faq", "question": q})
            if chunks:
                return chunks, metadatas
        except Exception:
            pass

    # Fallback to UTF-8 text parsing for TXT, MD, or plain text
    try:
        text_content = content_bytes.decode("utf-8", errors="ignore")
    except Exception:
        text_content = str(content_bytes)

    # Split strictly on Markdown headings (# Heading, ## Heading)
    raw_sections = re.split(r'\n(?=#{1,4}\s)', text_content)
    
    for section in raw_sections:
        cleaned_sec = section.strip()
        if not cleaned_sec:
            continue
        chunks.append(cleaned_sec)
        metadatas.append({"type": "document_section"})

    if not chunks and text_content.strip():
        chunks.append(text_content.strip())
        metadatas.append({"type": "document_section"})

    return chunks, metadatas


class KBIngestService:
    @staticmethod
    async def ingest_document(
        session: AsyncSession,
        tenant_id: str,
        title: str,
        content_bytes: bytes,
        file_type: str = "md"
    ) -> KBDocument:
        """
        Ingest a document into tenant's pgvector knowledge base. Idempotent by content hash.
        """
        content_hash = hashlib.sha256(content_bytes).hexdigest()

        # Check existing document by hash
        stmt = select(KBDocument).where(
            KBDocument.tenant_id == tenant_id,
            KBDocument.content_hash == content_hash
        )
        res = await session.execute(stmt)
        existing_doc = res.scalars().first()

        if existing_doc:
            return existing_doc

        # Parse & chunk
        chunks_text, metadatas = parse_and_chunk_document(title, content_bytes, file_type)

        # Create Document record
        doc = KBDocument(
            tenant_id=tenant_id,
            title=title,
            file_type=file_type,
            content_hash=content_hash
        )
        session.add(doc)
        await session.flush()

        # Generate embeddings & save chunks
        for idx, text in enumerate(chunks_text):
            vec = generate_text_embedding(text)
            meta = metadatas[idx] if idx < len(metadatas) else {}
            chunk_obj = KBChunk(
                tenant_id=tenant_id,
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=text,
                language="en",
                embedding=vec,
                metadata_json=meta
            )
            session.add(chunk_obj)

        await session.commit()
        await session.refresh(doc)
        return doc

    @staticmethod
    async def seed_tenant_kbs(session: AsyncSession, kb_dir: str = "data/kb") -> List[str]:
        """
        Seed tenant KBs from data/kb directory.
        """
        ingested_ids = []
        if not os.path.exists(kb_dir):
            return ingested_ids

        tenant_map = {
            "acme_telecom.md": "acme_telecom",
            "quickcart.md": "quickcart"
        }

        for fname, tenant_id in tenant_map.items():
            fpath = os.path.join(kb_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    content = f.read()
                doc = await KBIngestService.ingest_document(
                    session=session,
                    tenant_id=tenant_id,
                    title=fname,
                    content_bytes=content,
                    file_type="md"
                )
                ingested_ids.append(doc.id)

        return ingested_ids
