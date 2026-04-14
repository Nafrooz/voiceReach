from __future__ import annotations


class EmbeddingService:
    """
    Placeholder embedding service.

    Replace with a real embedding provider (local model, hosted model, etc.).
    """

    def __init__(self, model: str):
        self.model = model

    async def embed(self, text: str) -> list[float]:
        _ = text
        # Return a deterministic placeholder vector shape.
        return [0.0] * 8
