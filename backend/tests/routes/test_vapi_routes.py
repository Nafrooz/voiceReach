import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.services.embedding_service import get_embedding_service
from app.services.groq_service import get_groq_service
from app.services.qdrant_service import get_qdrant_service


class _DummyEmbedding:
    async def embed_text(self, text: str):
        _ = text
        return [0.0] * 768

    async def embed_batch(self, texts):
        return [[0.0] * 768 for _ in texts]


class _DummyQdrant:
    async def create_collections(self) -> None:
        return None

    async def semantic_search(self, query_vector, domain=None, top_k=5, score_threshold=0.55):
        _ = (query_vector, domain, top_k, score_threshold)

        class _Pt:
            payload = {"text": "retrieved chunk"}

        return [_Pt()]

    async def get_user_history(self, user_id: str, limit: int = 3):
        _ = (user_id, limit)
        return [{"query": "old q", "response": "old a"}]

    async def store_session(self, user_id, query, response, vector, domain, language):
        _ = (user_id, query, response, vector, domain, language)
        return None

    async def upsert_documents(self, docs):
        return len(docs)


class _DummyGroq:
    async def classify_domain(self, query: str) -> str:
        _ = query
        return "healthcare"

    async def generate_rag_response(self, query, context_chunks, history, language):
        _ = (query, context_chunks, history, language)
        return "final answer"


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    # Lifespan calls these directly; patch to avoid real downloads/network.
    monkeypatch.setattr("app.services.embedding_service.get_embedding_service", lambda: _DummyEmbedding())
    monkeypatch.setattr("app.services.qdrant_service.get_qdrant_service", lambda: _DummyQdrant())

    from app.main import app
    # Default overrides for the whole test module
    app.dependency_overrides[get_settings] = lambda: Settings(
        QDRANT_URL="http://localhost:6333",
        QDRANT_API_KEY="test",
        GROQ_API_KEY="test",
        VAPI_SECRET="test-secret",
    )
    app.dependency_overrides[get_embedding_service] = lambda: _DummyEmbedding()
    app.dependency_overrides[get_qdrant_service] = lambda: _DummyQdrant()
    app.dependency_overrides[get_groq_service] = lambda: _DummyGroq()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_webhook_invalid_signature_returns_403(client: TestClient):
    body = b'{"message":{"type":"function-call"}}'
    r = client.post(
        "/api/v1/webhook/vapi",
        data=body,
        headers={"content-type": "application/json", "x-vapi-signature": "bad"},
    )
    assert r.status_code == 403


def test_webhook_valid_function_call_returns_result_key(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    settings = Settings(
        QDRANT_URL="http://localhost:6333",
        QDRANT_API_KEY="test",
        GROQ_API_KEY="test",
        VAPI_SECRET="test-secret",
    )

    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {"name": "query_knowledge_base", "parameters": {"query": "What is PM-JAY?", "user_id": "u1"}},
            "call": {"id": "call-1"},
        }
    }
    import json

    body = json.dumps(payload).encode("utf-8")
    sig = _sign(body, settings.VAPI_SECRET)
    r = client.post(
        "/api/v1/webhook/vapi",
        data=body,
        headers={"content-type": "application/json", "x-vapi-signature": sig},
    )
    assert r.status_code == 200
    data = r.json()
    assert "result" in data


def test_webhook_end_of_call_returns_logged(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    settings = Settings(
        QDRANT_URL="http://localhost:6333",
        QDRANT_API_KEY="test",
        GROQ_API_KEY="test",
        VAPI_SECRET="test-secret",
    )

    payload = {"message": {"type": "end-of-call-report", "call": {"id": "call-xyz"}}}
    import json

    body = json.dumps(payload).encode("utf-8")
    sig = _sign(body, settings.VAPI_SECRET)
    r = client.post(
        "/api/v1/webhook/vapi",
        data=body,
        headers={"content-type": "application/json", "x-vapi-signature": sig},
    )
    assert r.status_code == 200
    assert r.json() == {"status": "logged"}


def test_ingest_seed_endpoint_returns_count(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    r = client.post("/api/v1/ingest/seed", json={})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("total_chunks_ingested"), int)
    assert isinstance(data.get("documents_processed"), int)

