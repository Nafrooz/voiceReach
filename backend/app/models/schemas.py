from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str | None = None
    text: str | None = None
    score: float | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    user_id: str | None = None
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)


class IngestDocument(BaseModel):
    id: str | None = None
    text: str
    metadata: dict[str, object] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    documents: list[IngestDocument] = Field(default_factory=list)


class IngestResponse(BaseModel):
    ok: bool
    ingested: int = 0


class SessionSummary(BaseModel):
    session_id: str
    created_at: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class SessionListResponse(BaseModel):
    user_id: str
    sessions: list[SessionSummary] = Field(default_factory=list)
