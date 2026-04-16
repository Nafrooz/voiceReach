from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import get_settings
from app.models.schemas import QueryRequest
from app.services.query_service import get_query_service

router = APIRouter(prefix="/webhook", tags=["vapi"])
logger = logging.getLogger(__name__)

FALLBACK = (
    "I'm sorry, I couldn't find that information right now. "
    "Please visit your nearest Common Service Centre or call 1800-11-0001 for help."
)


def verify_vapi_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/vapi")
async def vapi_webhook(
    request: Request,
    settings=Depends(get_settings),
    query_svc=Depends(get_query_service),
):
    body = await request.body()
    sig = request.headers.get("x-vapi-signature", "")
    if not verify_vapi_signature(body, sig, settings.VAPI_SECRET):
        raise HTTPException(403, "Invalid signature")

    payload = await request.json()
    msg_type = payload.get("message", {}).get("type", "")

    if msg_type == "function-call":
        fn = payload["message"]["functionCall"]
        if fn["name"] != "query_knowledge_base":
            return {"result": FALLBACK}

        params = fn["parameters"]
        query = params.get("query", "")
        user_id = params.get("user_id", payload["message"].get("call", {}).get("id", "anon"))

        try:
            res = await query_svc.query_knowledge_base(QueryRequest(user_id=user_id, query=query))
            logger.info("vapi_query user=%s domain=%s lang=%s answered=%s", user_id, res.domain, res.language, res.answered)
            return {"result": res.answer}
        except Exception as exc:
            logger.error("vapi_webhook error: %s", exc, exc_info=True)
            return {"result": FALLBACK}

    if msg_type == "end-of-call-report":
        logger.info(
            "call_ended call_id=%s",
            payload.get("message", {}).get("call", {}).get("id"),
        )
        return {"status": "logged"}

    return {"status": "ignored"}

