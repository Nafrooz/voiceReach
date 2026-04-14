from __future__ import annotations

import hmac
import hashlib


class VapiService:
    """
    Placeholder Vapi integration.
    """

    def __init__(self, api_key: str | None, webhook_secret: str | None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    def verify_webhook_signature(self, *, raw_body: bytes, signature: str | None) -> bool:
        """
        Placeholder signature verification.

        If you know Vapi's exact signing scheme, update this method accordingly.
        """
        if not self.webhook_secret or not signature:
            return False
        digest = hmac.new(self.webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)
