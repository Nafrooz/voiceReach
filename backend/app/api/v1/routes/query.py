from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_kb(body: QueryRequest) -> QueryResponse:
    """
    Query endpoint (placeholder).

    Intended flow:
    - detect language
    - embed query
    - retrieve context from Qdrant
    - call Groq with context
    """
    _ = body
    return QueryResponse(answer="placeholder-answer", sources=[])
