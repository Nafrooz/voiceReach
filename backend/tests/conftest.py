from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _test_env_and_clear_settings(monkeypatch: pytest.MonkeyPatch):
    """
    Required env for Settings; clear LRU cache so each test sees fresh config.
    """
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "test-qdrant-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("VAPI_SECRET", "test-vapi-secret")

    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
