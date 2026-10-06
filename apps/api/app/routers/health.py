from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "AsistLine AI API"}
