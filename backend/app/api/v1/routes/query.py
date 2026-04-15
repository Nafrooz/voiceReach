from __future__ import annotations
import time

from fastapi import APIRouter, Depends

from app.models.schemas import QueryRequest, QueryResponse, Source
from app.services.embedding_service import get_embedding_service
from app.services.groq_service import get_groq_service
from app.services.qdrant_service import get_qdrant_service
from app.utils.language_detector import detect_language

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_kb(
    body: QueryRequest,
    embed_svc=Depends(get_embedding_service),
    qdrant_svc=Depends(get_qdrant_service),
    groq_svc=Depends(get_groq_service),
) -> QueryResponse:
    t_start = time.perf_counter()
    language = detect_language(body.query)

    query_vector = await embed_svc.embed_text(body.query)

    domain = await groq_svc.classify_domain(body.query)

    hits = await qdrant_svc.semantic_search(
        query_vector=query_vector,
        domain=domain if domain != "general" else None,
        top_k=body.top_k,
    )

    context_chunks = [h.payload.get("text", "") for h in hits if h.payload]

    if not context_chunks:
        latency_ms = int((time.perf_counter() - t_start) * 1000)
        await qdrant_svc.store_session(
            user_id=body.user_id or "anonymous",
            query=body.query,
            response="",
            vector=query_vector,
            domain=domain,
            language=language,
            latency_ms=latency_ms,
            answered=False,
        )
        return QueryResponse(
            answer="I don't have that information right now. Please visit your nearest Common Service Centre for help.",
            sources=[],
        )

    history: list[dict] = []
    if body.user_id:
        history = await qdrant_svc.get_user_history(body.user_id)

    answer = await groq_svc.generate_rag_response(
        query=body.query,
        context_chunks=context_chunks,
        history=history,
        language=language,
    )

    latency_ms = int((time.perf_counter() - t_start) * 1000)

    user_id = body.user_id or "anonymous"
    await qdrant_svc.store_session(
        user_id=user_id,
        query=body.query,
        response=answer,
        vector=query_vector,
        domain=domain,
        language=language,
        latency_ms=latency_ms,
        answered=True,
    )

    sources = [
        Source(
            id=str(h.id),
            text=h.payload.get("text", "") if h.payload else "",
            score=h.score,
            metadata={k: v for k, v in (h.payload or {}).items() if k != "text"},
        )
        for h in hits
    ]

    return QueryResponse(answer=answer, sources=sources)
