from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from apps.api.app.core.db import get_db
from apps.api.app.models.models import KBDocument, KBChunk
from apps.api.app.schemas.kb import KBDocumentResponse, KBSearchRequest, KBSearchResponse
from apps.api.app.services.kb_ingest import KBIngestService
from apps.api.app.services.kb_search import KBSearchService

router = APIRouter(prefix="/v1/tenants/{tenant_id}/kb", tags=["Knowledge Base"])


@router.post("/documents", response_model=KBDocumentResponse)
async def upload_kb_document(
    tenant_id: str,
    file: UploadFile = File(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    content_bytes = await file.read()
    filename = title or file.filename or "uploaded_doc.txt"
    file_type = filename.split(".")[-1] if "." in filename else "txt"

    doc = await KBIngestService.ingest_document(
        session=db,
        tenant_id=tenant_id,
        title=filename,
        content_bytes=content_bytes,
        file_type=file_type
    )

    # Count chunks
    chunk_stmt = select(KBChunk).where(KBChunk.document_id == doc.id)
    c_res = await db.execute(chunk_stmt)
    chunk_count = len(list(c_res.scalars().all()))

    return KBDocumentResponse(
        id=doc.id,
        tenant_id=doc.tenant_id,
        title=doc.title,
        file_type=doc.file_type,
        content_hash=doc.content_hash,
        created_at=doc.created_at,
        chunk_count=chunk_count
    )


@router.get("/documents", response_model=List[KBDocumentResponse])
async def list_kb_documents(tenant_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(KBDocument).options(selectinload(KBDocument.chunks)).where(KBDocument.tenant_id == tenant_id)
    res = await db.execute(stmt)
    docs = list(res.scalars().all())

    return [
        KBDocumentResponse(
            id=d.id,
            tenant_id=d.tenant_id,
            title=d.title,
            file_type=d.file_type,
            content_hash=d.content_hash,
            created_at=d.created_at,
            chunk_count=len(d.chunks)
        )
        for d in docs
    ]


@router.delete("/documents/{doc_id}")
async def delete_kb_document(tenant_id: str, doc_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(KBDocument).where(KBDocument.id == doc_id, KBDocument.tenant_id == tenant_id)
    res = await db.execute(stmt)
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="KB Document not found")

    await db.delete(doc)
    await db.commit()
    return {"status": "deleted", "document_id": doc_id}


@router.post("/search", response_model=KBSearchResponse)
async def search_kb(tenant_id: str, req: KBSearchRequest, db: AsyncSession = Depends(get_db)):
    hits = await KBSearchService.hybrid_search(
        session=db,
        tenant_id=tenant_id,
        query=req.query,
        top_k=req.top_k
    )
    return KBSearchResponse(query=req.query, hits=hits)
