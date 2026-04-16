from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.services.qdrant_service import get_qdrant_service

router = APIRouter()

def _parse_iso(ts: str) -> datetime | None:
    """
    Parse ISO8601 timestamps from Qdrant payloads.
    Supports both timezone-aware and naive strings; naive is treated as UTC.
    """
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/knowledge/sources")
async def get_knowledge_sources(qdrant_svc=Depends(get_qdrant_service)):
    sources = await qdrant_svc.get_knowledge_sources()
    total_chunks = sum(s["chunk_count"] for s in sources)
    return {"sources": sources, "total_chunks": total_chunks}



@router.get("/sessions/all")
async def get_all_sessions(qdrant_svc=Depends(get_qdrant_service)):
    sessions = await qdrant_svc.get_all_sessions(limit=200)

    # Sort newest first
    sessions.sort(key=lambda s: _parse_iso(s.get("timestamp", "") or "") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # Compute stats
    today = datetime.now(timezone.utc).date()
    today_sessions = []
    for s in sessions:
        dt = _parse_iso(s.get("timestamp", "") or "")
        if dt and dt.date() == today:
            today_sessions.append(s)

    latencies = [s["latency_ms"] for s in sessions if "latency_ms" in s]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    languages = {s.get("language") for s in sessions if s.get("language")}
    domains = {s.get("domain") for s in sessions if s.get("domain")}

    return {
        "total_queries_today": len(today_sessions),
        "avg_response_time_ms": avg_latency,
        "languages_detected": len(languages),
        "domains_served": len(domains),
        "recent": sessions[:50],
    }
