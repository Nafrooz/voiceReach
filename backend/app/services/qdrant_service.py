from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchText,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    ScoredPoint,
    TextIndexParams,
    TokenizerType,
    VectorParams,
)

_log = logging.getLogger(__name__)

from app.config import get_settings

class QdrantService:
    def __init__(self, settings):
        self._client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        self._settings = settings

    async def create_collections(self) -> None:
        """Call at app startup via lifespan."""
        for name in [self._settings.COLLECTION_KNOWLEDGE, self._settings.COLLECTION_SESSIONS]:
            exists = await self._client.collection_exists(name)
            if not exists:
                await self._client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=self._settings.VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
        # Keyword index on domain for filtered semantic search
        await self._client.create_payload_index(
            collection_name=self._settings.COLLECTION_KNOWLEDGE,
            field_name="domain",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        # Full-text index on text field for hybrid search
        await self._client.create_payload_index(
            collection_name=self._settings.COLLECTION_KNOWLEDGE,
            field_name="text",
            field_schema=TextIndexParams(
                type="text",
                tokenizer=TokenizerType.WORD,
                min_token_len=2,
                max_token_len=20,
                lowercase=True,
            ),
        )
        # Keyword index on user_id for session history filters
        await self._client.create_payload_index(
            collection_name=self._settings.COLLECTION_SESSIONS,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )

    async def upsert_documents(self, docs: list[dict]) -> int:
        """docs: [{vector, text, source, domain, language}]"""
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=d["vector"],
                payload={k: v for k, v in d.items() if k != "vector"},
            )
            for d in docs
        ]

        # Batch in 100s
        for i in range(0, len(points), 100):
            await self._client.upsert(
                collection_name=self._settings.COLLECTION_KNOWLEDGE,
                points=points[i : i + 100],
            )

        return len(points)

    async def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        domain: str | None = None,
        top_k: int = 5,
    ) -> list[ScoredPoint]:
        """Hybrid search: semantic + full-text, reranked with Reciprocal Rank Fusion."""
        domain_filter = (
            Filter(must=[FieldCondition(key="domain", match=MatchValue(value=domain))])
            if domain
            else None
        )
        # Extract keywords (words > 3 chars) for better full-text matching
        keywords = " ".join(w for w in query_text.split() if len(w) > 3)
        ft_query = keywords if keywords else query_text
        text_filters = [FieldCondition(key="text", match=MatchText(text=ft_query))]
        if domain:
            text_filters.append(FieldCondition(key="domain", match=MatchValue(value=domain)))

        # Run semantic and full-text searches in parallel
        semantic_results, ft_results = await asyncio.gather(
            self._client.search(
                collection_name=self._settings.COLLECTION_KNOWLEDGE,
                query_vector=query_vector,
                limit=top_k * 3,
                query_filter=domain_filter,
                with_payload=True,
            ),
            self._client.scroll(
                collection_name=self._settings.COLLECTION_KNOWLEDGE,
                scroll_filter=Filter(must=text_filters),
                limit=top_k * 3,
                with_payload=True,
                with_vectors=False,
            ),
        )

        ft_points = ft_results[0]  # scroll returns (points, next_offset)

        _log.info(
            "hybrid_search domain=%s semantic_hits=%d ft_hits=%d",
            domain, len(semantic_results), len(ft_points),
        )

        # Reciprocal Rank Fusion — K=10 tuned for small domain-specific KB (~200 chunks)
        K = 10
        rrf: dict[str, float] = {}
        id_to_payload: dict[str, dict] = {}
        id_to_cosine: dict[str, float] = {}

        for rank, point in enumerate(semantic_results):
            pid = str(point.id)
            rrf[pid] = rrf.get(pid, 0.0) + 1.0 / (K + rank + 1)
            id_to_payload[pid] = point.payload or {}
            id_to_cosine[pid] = point.score  # store cosine similarity score

        for rank, point in enumerate(ft_points):
            pid = str(point.id)
            rrf[pid] = rrf.get(pid, 0.0) + 1.0 / (K + rank + 1)
            if pid not in id_to_payload:
                id_to_payload[pid] = point.payload or {}

        # Sort by RRF score
        sorted_ids = sorted(rrf, key=lambda x: rrf[x], reverse=True)[:top_k]

        # Log RRF scores and cosine scores for each candidate
        for rank, pid in enumerate(sorted_ids):
            cosine = id_to_cosine.get(pid, None)
            _log.info(
                "  [%d] rrf=%.4f cosine=%s text_preview=%r",
                rank + 1,
                rrf[pid],
                f"{cosine:.4f}" if cosine is not None else "ft-only",
                (id_to_payload.get(pid, {}).get("text", "") or "")[:60],
            )

        # Apply cosine similarity threshold as quality gate after RRF ranking
        COSINE_THRESHOLD = 0.45
        filtered_ids = [
            pid for pid in sorted_ids
            if id_to_cosine.get(pid, 0.0) >= COSINE_THRESHOLD
        ]

        cosine_scores = [id_to_cosine.get(pid, 0.0) for pid in sorted_ids]
        min_needed = min(cosine_scores) if cosine_scores else 0.0
        max_score = max(cosine_scores) if cosine_scores else 0.0
        _log.info(
            "hybrid_search rrf_candidates=%d after_threshold=%d | "
            "cosine range=[%.4f, %.4f] threshold=%.2f | %s",
            len(sorted_ids),
            len(filtered_ids),
            min_needed,
            max_score,
            COSINE_THRESHOLD,
            "WILL ANSWER" if filtered_ids else "NO ANSWER — raise threshold or lower it",
        )

        from qdrant_client.models import ScoredPoint as SP
        return [
            SP(
                id=pid,
                score=round(id_to_cosine[pid], 4),
                payload=id_to_payload[pid],
                version=0,
            )
            for pid in filtered_ids
            if id_to_payload.get(pid)
        ]

    async def store_session(self, user_id, query, response, vector, domain, language, latency_ms: int = 0, answered: bool = True):
        from datetime import datetime, timezone

        point = PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload={
                "user_id": user_id,
                "query": query,
                "response": response,
                "domain": domain,
                "language": language,
                "latency_ms": latency_ms,
                "answered": answered,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        await self._client.upsert(
            collection_name=self._settings.COLLECTION_SESSIONS,
            points=[point],
        )

    async def get_user_history(self, user_id: str, limit: int = 3) -> list[dict]:
        results, _ = await self._client.scroll(
            collection_name=self._settings.COLLECTION_SESSIONS,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=limit,
            with_payload=True,
        )
        return [r.payload for r in results]

    async def get_knowledge_sources(self) -> list[dict]:
        """Return unique sources with chunk counts and metadata."""
        results, _ = await self._client.scroll(
            collection_name=self._settings.COLLECTION_KNOWLEDGE,
            limit=1000,
            with_payload=True,
        )
        # Aggregate by source
        sources: dict[str, dict] = {}
        for r in results:
            if not r.payload:
                continue
            src = r.payload.get("source", "unknown")
            if src not in sources:
                sources[src] = {
                    "source": src,
                    "domain": r.payload.get("domain", "general"),
                    "language": r.payload.get("language", "en"),
                    "chunk_count": 0,
                }
            sources[src]["chunk_count"] += 1
        return sorted(sources.values(), key=lambda x: x["domain"])

    async def get_all_sessions(self, limit: int = 100) -> list[dict]:
        results, _ = await self._client.scroll(
            collection_name=self._settings.COLLECTION_SESSIONS,
            limit=limit,
            with_payload=True,
        )
        return [r.payload for r in results if r.payload]


_service: QdrantService | None = None


def get_qdrant_service() -> QdrantService:
    """
    FastAPI dependency that returns a cached service instance.
    """
    global _service
    if _service is None:
        _service = QdrantService(get_settings())
    return _service
