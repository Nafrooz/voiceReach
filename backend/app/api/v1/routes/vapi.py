from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()


@router.post("/webhook/vapi")
async def vapi_webhook(
    request: Request,
    x_vapi_signature: str | None = Header(default=None, alias="X-Vapi-Signature"),
):
    """
    Vapi webhook receiver.

    Signature verification is a placeholder; wire it to `Settings.vapi_webhook_secret`.
    """
    payload = await request.json()

    if x_vapi_signature is None:
        # Placeholder behavior; you may want to accept unsigned in dev.
        raise HTTPException(status_code=400, detail="Missing X-Vapi-Signature header")

    return {"ok": True, "received": True, "payload": payload}

