import pytest

from app.config import Settings
from app.services.groq_service import GroqService


class _FakeChoice:
    def __init__(self, content: str):
        self.message = type("msg", (), {"content": content})


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, create_impl):
        self._create_impl = create_impl

    def create(self, **kwargs):
        return self._create_impl(**kwargs)


class _FakeChat:
    def __init__(self, create_impl):
        self.completions = _FakeCompletions(create_impl)


class _FakeGroqClient:
    def __init__(self, create_impl):
        self.chat = _FakeChat(create_impl)


def _settings() -> Settings:
    return Settings(
        QDRANT_URL="http://localhost:6333",
        QDRANT_API_KEY="test",
        GROQ_API_KEY="test",
        VAPI_SECRET="test-secret",
    )


@pytest.mark.asyncio
async def test_classify_domain_returns_valid_domain():
    svc = GroqService(_settings())
    svc._client = _FakeGroqClient(lambda **kwargs: _FakeResponse("healthcare"))
    out = await svc.classify_domain("pmjay eligibility?")
    assert out == "healthcare"


@pytest.mark.asyncio
async def test_classify_domain_returns_general_for_unknown():
    svc = GroqService(_settings())
    svc._client = _FakeGroqClient(lambda **kwargs: _FakeResponse("foobar"))
    out = await svc.classify_domain("something weird")
    assert out == "general"


@pytest.mark.asyncio
async def test_generate_rag_response_under_150_tokens():
    seen = {}

    def create_impl(**kwargs):
        seen.update(kwargs)
        return _FakeResponse("ok")

    svc = GroqService(_settings())
    svc._client = _FakeGroqClient(create_impl)

    _ = await svc.generate_rag_response(
        query="What is PM-JAY?",
        context_chunks=["chunk1", "chunk2"],
        history=[{"query": "hi", "response": "hello"}],
        language="en",
    )

    assert seen.get("max_tokens") == 150


@pytest.mark.asyncio
async def test_fallback_on_groq_error():
    calls = {"n": 0}

    def create_impl(**kwargs):
        calls["n"] += 1
        raise RuntimeError("boom")

    svc = GroqService(_settings())
    svc._client = _FakeGroqClient(create_impl)

    with pytest.raises(Exception):
        await svc.generate_rag_response(
            query="hi",
            context_chunks=[],
            history=[],
            language="en",
        )

    # tenacity should retry 3x
    assert calls["n"] == 3

