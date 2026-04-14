from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import get_settings
from app.services.embedding_service import get_embedding_service
from app.services.groq_service import get_groq_service
from app.services.qdrant_service import get_qdrant_service

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
    embed_svc=Depends(get_embedding_service),
    qdrant_svc=Depends(get_qdrant_service),
    groq_svc=Depends(get_groq_service),
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
            from app.utils.language_detector import detect_language

            language = detect_language(query)
            domain = await groq_svc.classify_domain(query)
            q_vec = await embed_svc.embed_text(query)
            results = await qdrant_svc.semantic_search(q_vec, domain=domain)
            chunks = [r.payload["text"] for r in results]
            history = await qdrant_svc.get_user_history(user_id)
            response = await groq_svc.generate_rag_response(query, chunks, history, language)
            r_vec = await embed_svc.embed_text(response)
            await qdrant_svc.store_session(user_id, query, response, r_vec, domain, language)
            logger.info("vapi_query user=%s domain=%s lang=%s", user_id, domain, language)
            return {"result": response}
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

