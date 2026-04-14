from __future__ import annotations


class GroqService:
    """
    Groq LLM integration (placeholder).

    Important: This is intentionally Groq-focused (not OpenAI/Anthropic).
    """

    def __init__(self, api_key: str | None, model: str):
        self.api_key = api_key
        self.model = model

    async def chat(self, *, system: str | None, user: str, context: str | None = None) -> str:
        _ = (system, user, context)
        return "placeholder-groq-response"

