from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

from app.api.v1.router import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load embedding model + create Qdrant collections."""
    _ = app
    logger.info("Starting VoiceReach backend...")
    t0 = time.time()

    # Pre-load embedding model (downloads once, then cached)
    from app.services.embedding_service import get_embedding_service

    get_embedding_service()
    logger.info("Embedding model loaded in %.1fs", time.time() - t0)

    # Create Qdrant collections if they don't exist
    from app.services.qdrant_service import get_qdrant_service

    await get_qdrant_service().create_collections()
    logger.info("Qdrant collections ready")

    yield
    logger.info("VoiceReach backend shutdown")


app = FastAPI(title="VoiceReach API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    _ = get_settings()
    return {"status": "ok", "version": "1.0.0", "stack": "Groq+Qdrant+Vapi"}

