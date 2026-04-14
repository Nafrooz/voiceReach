from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QdrantMatch:
    id: str
    score: float
    payload: dict[str, object]


class QdrantService:
    """
    Placeholder Qdrant integration.

    Wire this to an actual Qdrant client (e.g. `qdrant-client`) when ready.
    """

    def __init__(self, url: str, collection: str):
        self.url = url
        self.collection = collection

    async def upsert_texts(self, texts: list[str], metadatas: list[dict[str, object]] | None = None) -> int:
        _ = (texts, metadatas)
        return 0

    async def search(self, vector: list[float], top_k: int = 5) -> list[QdrantMatch]:
        _ = (vector, top_k)
        return []

    async def reset_collection(self) -> None:
        return None
