from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import ingest, query, sessions, vapi

api_router = APIRouter()

api_router.include_router(vapi.router, tags=["vapi"])
api_router.include_router(query.router, tags=["query"])
api_router.include_router(ingest.router, tags=["ingest"])
api_router.include_router(sessions.router, tags=["sessions"])
