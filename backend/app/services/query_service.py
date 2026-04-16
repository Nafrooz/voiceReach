from __future__ import annotations

import logging
import time

from app.models.schemas import QueryRequest, QueryResponse, Source
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.groq_service import GroqService, get_groq_service
from app.services.qdrant_service import QdrantService, get_qdrant_service
from app.utils.language_detector import detect_language

_log = logging.getLogger(__name__)

FALLBACK_MESSAGE = (
    "I don't have that information right now. Please visit your nearest Common Service Centre for help."
)


class QueryService:
    def __init__(
        self,
        *,
        embed_svc: EmbeddingService,
        qdrant_svc: QdrantService,
        groq_svc: GroqService,
    ) -> None:
        self._embed = embed_svc
        self._qdrant = qdrant_svc
        self._groq = groq_svc

    async def query_knowledge_base(self, body: QueryRequest) -> QueryResponse:
        t_start = time.perf_counter()
        query = body.query.strip()
        language = detect_language(query)
        user_id = body.user_id or "anonymous"

        # Use fast model for coarse domain routing. If it returns "general",
        # we avoid filtering by domain to maximize retrieval recall.
        domain = await self._groq.classify_domain(query)

        q_vec = await self._embed.embed_text(query)
        history = await self._qdrant.get_user_history(user_id) if user_id else []

        results = await self._qdrant.hybrid_search(
            query_vector=q_vec,
            query_text=query,
            domain=None if domain == "general" else domain,
            top_k=body.top_k,
        )

        chunks: list[str] = []
        sources: list[Source] = []
        for r in results:
            payload = getattr(r, "payload", None) or {}
            text = payload.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text)
            sources.append(
                Source(
                    id=str(getattr(r, "id", "")) or None,
                    text=text if isinstance(text, str) else None,
                    score=float(getattr(r, "score", 0.0)) if getattr(r, "score", None) is not None else None,
                    metadata={k: v for k, v in payload.items() if k != "text"},
                )
            )

        # If retrieval returns no chunks, do NOT call Groq (avoid hallucinations).
        if not chunks:
            latency_ms = int((time.perf_counter() - t_start) * 1000)
            try:
                await self._qdrant.store_session(
                    user_id=user_id,
                    query=query,
                    response="",
                    vector=q_vec,
                    domain=domain,
                    language=language,
                    latency_ms=latency_ms,
                    answered=False,
                )
            except Exception:
                _log.exception("Failed to store session (no-context); continuing")

            return QueryResponse(
                answer=FALLBACK_MESSAGE,
                sources=[],
                language=language,
                domain=domain,
                answered=False,
            )

        answer = await self._groq.generate_rag_response(query=query, context_chunks=chunks, history=history, language=language)

        # Store session memory for follow-up questions.
        try:
            latency_ms = int((time.perf_counter() - t_start) * 1000)
            await self._qdrant.store_session(
                user_id=user_id,
                query=query,
                response=answer,
                vector=q_vec,
                domain=domain,
                language=language,
                latency_ms=latency_ms,
                answered=True,
            )
        except Exception:
            _log.exception("Failed to store session; continuing")

        return QueryResponse(answer=answer, sources=sources, language=language, domain=domain, answered=True)


_service: QueryService | None = None


def get_query_service() -> QueryService:
    global _service
    if _service is None:
        _service = QueryService(
            embed_svc=get_embedding_service(),
            qdrant_svc=get_qdrant_service(),
            groq_svc=get_groq_service(),
        )
    return _service

