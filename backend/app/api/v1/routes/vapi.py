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
    # Vapi may send signature as plain hex or with "sha256=" prefix
    sig = signature.removeprefix("sha256=")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


@router.post("/vapi")
async def vapi_webhook(
    request: Request,
    settings=Depends(get_settings),
    query_svc=Depends(get_query_service),
):
    body = await request.body()
    secret = request.headers.get("x-vapi-secret", "")
    if secret and settings.VAPI_SECRET:
        if secret != settings.VAPI_SECRET:
            logger.warning("Vapi secret mismatch — check VAPI_SECRET in .env.")
    _ = HTTPException  # kept for import

    payload = await request.json()
    msg = payload.get("message", {})
    msg_type = msg.get("type", "")
    logger.info("vapi_webhook type=%s", msg_type)

    # Vapi sends "tool-calls" when assistant uses toolIds
    if msg_type == "tool-calls":
        tool_call_list = msg.get("toolCallList", [])
        results = []
        call_id = msg.get("call", {}).get("id", "anon")

        for tool_call in tool_call_list:
            tool_call_id = tool_call.get("id", "")
            fn = tool_call.get("function", {})
            fn_name = fn.get("name", "")

            if fn_name != "query_knowledge_base":
                results.append({"toolCallId": tool_call_id, "result": FALLBACK})
                continue

            import json as _json
            raw_args = fn.get("arguments", "{}")
            params = _json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            query = params.get("query", "")
            user_id = params.get("user_id", call_id)

            try:
                logger.info("vapi_query query=%r user=%s", query, user_id)
                res = await query_svc.query_knowledge_base(QueryRequest(user_id=user_id, query=query))
                logger.info("vapi_query domain=%s lang=%s answered=%s answer=%r", res.domain, res.language, res.answered, res.answer[:80])
                results.append({"toolCallId": tool_call_id, "result": res.answer})
            except Exception as exc:
                logger.error("vapi_webhook error: %s", exc, exc_info=True)
                results.append({"toolCallId": tool_call_id, "result": FALLBACK})

        return {"results": results}

    # Legacy function-call format
    if msg_type == "function-call":
        fn = msg.get("functionCall", {})
        if fn.get("name") != "query_knowledge_base":
            return {"result": FALLBACK}

        params = fn.get("parameters", {})
        query = params.get("query", "")
        user_id = params.get("user_id", msg.get("call", {}).get("id", "anon"))

        try:
            res = await query_svc.query_knowledge_base(QueryRequest(user_id=user_id, query=query))
            return {"result": res.answer}
        except Exception as exc:
            logger.error("vapi_webhook error: %s", exc, exc_info=True)
            return {"result": FALLBACK}

    if msg_type == "end-of-call-report":
        logger.info("call_ended call_id=%s", msg.get("call", {}).get("id"))
        return {"status": "logged"}

    return {"status": "ignored"}

