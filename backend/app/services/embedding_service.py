from __future__ import annotations

import logging
import time

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Loads multilingual-mpnet locally — no API cost, supports 50+ languages.
    """

    def __init__(self):
        t0 = time.perf_counter()
        # Load once at startup — model cached on disk after first run
        self._model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
        dt = time.perf_counter() - t0
        _log.info("Embedding model loaded in %.3fs", dt)

    # This model: 768-dim, supports Hindi/Telugu/Tamil/English etc.
    async def embed_text(self, text: str) -> list[float]:
        """Embed single text. Returns 768-dim normalized vector."""
        text = text.lower().strip()
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()  # type: ignore[no-any-return]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed for ingestion. Much faster than one-by-one."""
        vectors = self._model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [v.tolist() for v in vectors]  # type: ignore[no-any-return]


_log = logging.getLogger(__name__)

# Module-level singleton — NEVER reinitialize per request
_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """
    FastAPI dependency that returns a cached service instance.
    """
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service
