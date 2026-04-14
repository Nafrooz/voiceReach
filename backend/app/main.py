from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifespan hook.

    Use this for initializing shared clients (Qdrant, Groq, etc.) and cleanup.
    """
    _ = app  # placeholder to avoid unused-arg linting in some setups
    yield


def create_app() -> FastAPI:
    # Settings are still loaded here so env validation happens on startup.
    _ = get_settings()
    app = FastAPI(title="voicereach", lifespan=lifespan)
    # Config no longer defines a version prefix; routes define full paths.
    app.include_router(api_router)
    return app


app = create_app()

