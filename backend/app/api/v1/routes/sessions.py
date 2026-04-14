from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import SessionListResponse

router = APIRouter()


@router.get("/sessions/{user_id}", response_model=SessionListResponse)
async def get_sessions(user_id: str) -> SessionListResponse:
    """
    List sessions for a user (placeholder).
    """
    return SessionListResponse(user_id=user_id, sessions=[])
