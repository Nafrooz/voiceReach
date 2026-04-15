from __future__ import annotations

from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

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
        # Ensure keyword index on domain exists for filtered search
        await self._client.create_payload_index(
            collection_name=self._settings.COLLECTION_KNOWLEDGE,
            field_name="domain",
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

    async def semantic_search(
        self,
        query_vector: list[float],
        domain: str | None = None,
        top_k: int = 5,
        score_threshold: float = 0.55,
    ) -> list[ScoredPoint]:
        filt = (
            Filter(must=[FieldCondition(key="domain", match=MatchValue(value=domain))])
            if domain
            else None
        )
        return await self._client.search(
            collection_name=self._settings.COLLECTION_KNOWLEDGE,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=filt,
            with_payload=True,
        )

    async def store_session(self, user_id, query, response, vector, domain, language, latency_ms: int = 0):
        from datetime import datetime

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
                "timestamp": datetime.utcnow().isoformat(),
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
