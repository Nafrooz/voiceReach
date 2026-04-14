from __future__ import annotations

import json
import os
from typing import Any

import httpx


async def configure_assistant(config_path: str) -> str:
    """
    Create a Vapi assistant from a local JSON config file.

    POST https://api.vapi.ai/assistant with Bearer token.
    Returns assistant_id.
    """
    api_key = os.environ.get("VAPI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing VAPI_API_KEY environment variable")

    with open(config_path, "r", encoding="utf-8") as f:
        config: dict[str, Any] = json.load(f)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.vapi.ai/assistant",
            json=config,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()

    assistant_id = data.get("id") or data.get("assistantId")
    if not assistant_id:
        raise RuntimeError("Vapi response missing assistant id")
    return str(assistant_id)


async def update_server_url(assistant_id: str, url: str) -> None:
    """
    Update an existing assistant's serverUrl after deployment.

    PATCH https://api.vapi.ai/assistant/{assistant_id}
    """
    api_key = os.environ.get("VAPI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing VAPI_API_KEY environment variable")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.patch(
            f"https://api.vapi.ai/assistant/{assistant_id}",
            json={"serverUrl": url},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()

