from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.services.qdrant_service import get_qdrant_service

router = APIRouter()


@router.get("/sessions/all")
async def get_all_sessions(qdrant_svc=Depends(get_qdrant_service)):
    sessions = await qdrant_svc.get_all_sessions(limit=200)

    # Sort newest first
    sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)

    # Compute stats
    today = datetime.now(timezone.utc).date().isoformat()
    today_sessions = [s for s in sessions if s.get("timestamp", "").startswith(today)]

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
