import numpy as np
import pytest

import app.services.embedding_service as es


class _FakeModel:
    def encode(self, texts, normalize_embeddings=True, batch_size=32):
        _ = (normalize_embeddings, batch_size)
        if isinstance(texts, str):
            return np.ones(768, dtype=np.float32) / np.sqrt(768)
        arr = np.ones((len(texts), 768), dtype=np.float32) / np.sqrt(768)
        return arr


@pytest.mark.asyncio
async def test_embed_text_returns_list_of_floats():
    monkey = pytest.MonkeyPatch()
    monkey.setattr(es, "SentenceTransformer", lambda *_args, **_kwargs: _FakeModel(), raising=False)
    svc = es.EmbeddingService()
    vec = await svc.embed_text("hello world")
    assert isinstance(vec, list)
    assert vec
    assert all(isinstance(x, float) for x in vec)
    monkey.undo()


@pytest.mark.asyncio
async def test_vector_dimension_is_768():
    monkey = pytest.MonkeyPatch()
    monkey.setattr(es, "SentenceTransformer", lambda *_args, **_kwargs: _FakeModel(), raising=False)
    svc = es.EmbeddingService()
    vec = await svc.embed_text("dimension check")
    assert len(vec) == 768
    monkey.undo()


@pytest.mark.asyncio
async def test_embed_hindi_text_returns_valid_vector():
    monkey = pytest.MonkeyPatch()
    monkey.setattr(es, "SentenceTransformer", lambda *_args, **_kwargs: _FakeModel(), raising=False)
    svc = es.EmbeddingService()
    text = "■■■■■■■■■ ■■■■ ■■■■■ ■■■■ ■■?"
    vec = await svc.embed_text(text)
    assert isinstance(vec, list)
    assert len(vec) == 768
    assert all(isinstance(x, float) for x in vec)
    monkey.undo()


@pytest.mark.asyncio
async def test_embed_batch_count_matches_input():
    monkey = pytest.MonkeyPatch()
    monkey.setattr(es, "SentenceTransformer", lambda *_args, **_kwargs: _FakeModel(), raising=False)
    svc = es.EmbeddingService()
    texts = ["one", "two", "three"]
    vecs = await svc.embed_batch(texts)
    assert isinstance(vecs, list)
    assert len(vecs) == len(texts)
    assert all(len(v) == 768 for v in vecs)
    monkey.undo()


@pytest.mark.asyncio
async def test_normalized_vectors_have_unit_magnitude():
    monkey = pytest.MonkeyPatch()
    monkey.setattr(es, "SentenceTransformer", lambda *_args, **_kwargs: _FakeModel(), raising=False)
    svc = es.EmbeddingService()
    vec = await svc.embed_text("normalize me")
    assert abs(np.linalg.norm(vec) - 1.0) < 0.01
    monkey.undo()

