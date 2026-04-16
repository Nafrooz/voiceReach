from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.embedding_service import get_embedding_service
from app.services.qdrant_service import get_qdrant_service
from app.utils.text_processor import chunk_text

router = APIRouter(prefix="/ingest", tags=["ingest"])


class TextIngestRequest(BaseModel):
    text: str
    source: str
    domain: str
    language: str = "en"
    # healthcare | government | finance | education


class UrlIngestRequest(BaseModel):
    url: str
    domain: str


@router.post("/text")
async def ingest_text(
    req: TextIngestRequest,
    embed_svc=Depends(get_embedding_service),
    qdrant_svc=Depends(get_qdrant_service),
):
    chunks = chunk_text(req.text, chunk_size=300, overlap=50)
    vectors = await embed_svc.embed_batch(chunks)
    docs = [
        {
            "vector": v,
            "text": c,
            "source": req.source,
            "domain": req.domain,
            "language": req.language,
        }
        for c, v in zip(chunks, vectors)
    ]
    n = await qdrant_svc.upsert_documents(docs)
    return {"chunks_ingested": n}


@router.post("/url")
async def ingest_url(
    req: UrlIngestRequest,
    embed_svc=Depends(get_embedding_service),
    qdrant_svc=Depends(get_qdrant_service),
):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(req.url)
        r.raise_for_status()

    text = re.sub(r"<[^>]+>", "", r.text)  # strip HTML tags
    from langdetect import detect

    lang = detect(text[:500])
    chunks = chunk_text(text)
    vectors = await embed_svc.embed_batch(chunks)
    docs = [
        {
            "vector": v,
            "text": c,
            "source": req.url,
            "domain": req.domain,
            "language": lang,
        }
        for c, v in zip(chunks, vectors)
    ]
    n = await qdrant_svc.upsert_documents(docs)
    return {"chunks_ingested": n, "language_detected": lang}


@router.post("/deduplicate")
async def deduplicate_knowledge_base(
    qdrant_svc=Depends(get_qdrant_service),
):
    """Remove duplicate chunks that have identical text content."""
    results, _ = await qdrant_svc._client.scroll(
        collection_name=qdrant_svc._settings.COLLECTION_KNOWLEDGE,
        limit=2000,
        with_payload=True,
        with_vectors=False,
    )
    seen: dict[str, str] = {}  # text_hash -> first point id
    duplicates: list[str] = []
    for point in results:
        text = (point.payload or {}).get("text", "")
        h = str(hash(text))
        if h in seen:
            duplicates.append(str(point.id))
        else:
            seen[h] = str(point.id)

    if duplicates:
        await qdrant_svc._client.delete(
            collection_name=qdrant_svc._settings.COLLECTION_KNOWLEDGE,
            points_selector=duplicates,
        )

    return {"duplicates_removed": len(duplicates), "unique_chunks_remaining": len(seen)}


@router.post("/seed")
async def seed_knowledge_base(
    embed_svc=Depends(get_embedding_service),
    qdrant_svc=Depends(get_qdrant_service),
):
    try:
        seed_path = Path(__file__).resolve().parents[4] / "data" / "knowledge_base" / "seed_data.json"
        items = json.loads(seed_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    # Support either a list of docs OR {"documents":[...]}.
    if isinstance(items, dict) and isinstance(items.get("documents"), list):
        items = items["documents"]

    total = 0
    for item in items:
        chunks = chunk_text(item["text"])
        vectors = await embed_svc.embed_batch(chunks)
        docs = [
            {
                "vector": v,
                "text": c,
                "source": item["source"],
                "domain": item["domain"],
                "language": item.get("language", "en"),
            }
            for c, v in zip(chunks, vectors)
        ]
        total += await qdrant_svc.upsert_documents(docs)
    return {"total_chunks_ingested": total, "documents_processed": len(items)}
