from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import IngestRequest, IngestResponse

router = APIRouter()


@router.post("/ingest/documents", response_model=IngestResponse)
async def ingest_documents(body: IngestRequest) -> IngestResponse:
    """
    Ingest documents into the knowledge base (placeholder).
    """
    _ = body
    return IngestResponse(ok=True, ingested=0)


@router.post("/ingest/reset", response_model=IngestResponse)
async def reset_ingest_index() -> IngestResponse:
    """
    Reset/clear the knowledge base index (placeholder).
    """
    return IngestResponse(ok=True, ingested=0)

