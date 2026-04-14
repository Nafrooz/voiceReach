from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    """
    Normalize input text for indexing / querying (placeholder).
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def chunk_text(text: str, *, max_chars: int = 1200, overlap: int = 120) -> list[str]:
    """
    Naive chunker (placeholder).
    """
    if max_chars <= 0:
        return [text]
    if overlap >= max_chars:
        overlap = 0

    chunks: list[str] = []
    i = 0
    while i < len(text):
        end = min(len(text), i + max_chars)
        chunks.append(text[i:end])
        if end == len(text):
            break
        i = max(0, end - overlap)
    return chunks
