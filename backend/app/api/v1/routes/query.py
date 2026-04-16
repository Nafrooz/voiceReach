from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import QueryRequest, QueryResponse
from app.services.query_service import get_query_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_kb(
    body: QueryRequest,
    query_svc=Depends(get_query_service),
) -> QueryResponse:
    return await query_svc.query_knowledge_base(body)
