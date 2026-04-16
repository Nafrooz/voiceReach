from __future__ import annotations

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

# System prompt — kept short because voice responses must be brief
VOICE_SYSTEM_PROMPT = """
You are VoiceReach, a compassionate voice assistant helping people
with limited digital access understand government schemes and healthcare.
STRICT RULES:
1. Respond in the EXACT SAME LANGUAGE as the user's question
2. Maximum 80 words — this answer will be spoken aloud
3. Use simple, everyday language — no jargon or technical terms
4. Start directly with the answer — no preambles like "Sure!" or "Great question!"
5. If context does not contain the answer, say: "I don't have that information right now.
Please visit your nearest Common Service Centre for help."
6. End with ONE simple follow-up question to help the user further
""".strip()

CLASSIFY_PROMPT = (
    "Classify this query into exactly one word — healthcare, government, finance, or education:\n{query}"
)

DETECT_LANG_PROMPT = (
    "Detect the PRIMARY language of this text. "
    "The text may mix Indian language words with English (code-switching is common in Indian speech). "
    "If ANY Telugu words are present (nenu, naku, ela, cheyali, account, undi, ledha, okka, anni, cheppandi, cheyandi, open, meeru, mee, memu, manam, oka), reply: te\n"
    "If ANY Hindi words are present (mujhe, kaise, kya, karein, chahiye, aur, bhi, yojana, karo, iska, uska, hai, hoga, mera, apna), reply: hi\n"
    "If ANY Tamil words are present (enakku, eppadi, enna, pannanum, venum, irukku, solla, uதவி), reply: ta\n"
    "If the text is purely English with no Indic words, reply: en\n"
    "Reply with ONLY one of: en, hi, te, ta — no explanation.\n"
    "Text: {query}"
)

TRANSLATE_PROMPT = (
    "Translate the following text to English. Output only the translation, nothing else.\nText: {query}"
)


class GroqService:
    def __init__(self, settings):
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self._settings = settings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def generate_rag_response(
        self,
        query: str,
        context_chunks: list[str],
        history: list[dict],
        language: str,
    ) -> str:
        lang = (language or "en").lower().strip()
        lang_name = {"en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil"}.get(lang, "English")
        lang_rule = (
            f"OUTPUT LANGUAGE OVERRIDE: Respond ONLY in {lang_name}.\n"
            + (
                "Use Telugu script (తెలుగు లిపి) only."
                if lang == "te"
                else "Use Tamil script (தமிழ் எழுத்து) only."
                if lang == "ta"
                else "Use Devanagari script (देवनागरी) only."
                if lang == "hi"
                else "Use standard English."
            )
        )

        context = "\n---\n".join(context_chunks[:5])
        messages: list[dict[str, str]] = [
            {"role": "system", "content": VOICE_SYSTEM_PROMPT},
            {"role": "system", "content": lang_rule},
        ]

        # Add last 2 history turns
        for h in history[-2:]:
            messages.append({"role": "user", "content": str(h.get("query", ""))})
            messages.append({"role": "assistant", "content": str(h.get("response", ""))})

        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"})

        resp = self._client.chat.completions.create(
            model=self._settings.GROQ_MODEL,  # llama-3.3-70b-versatile
            messages=messages,
            max_tokens=self._settings.MAX_RESPONSE_TOKENS,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    async def detect_language_llm(self, text: str) -> str:
        """Use LLM to detect language — handles romanized Indic text that script detection misses."""
        resp = self._client.chat.completions.create(
            model=self._settings.GROQ_FAST_MODEL,
            messages=[{"role": "user", "content": DETECT_LANG_PROMPT.format(query=text[:300])}],
            max_tokens=5,
            temperature=0,
        )
        lang = resp.choices[0].message.content.strip().lower()
        return lang if lang in {"en", "hi", "te", "ta"} else "en"

    async def translate_to_english(self, text: str) -> str:
        """Translate query to English for better embedding retrieval against English KB."""
        resp = self._client.chat.completions.create(
            model=self._settings.GROQ_FAST_MODEL,
            messages=[{"role": "user", "content": TRANSLATE_PROMPT.format(query=text)}],
            max_tokens=100,
            temperature=0,
        )
        return resp.choices[0].message.content.strip()

    async def classify_domain(self, query: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._settings.GROQ_FAST_MODEL,  # llama-3.1-8b-instant (fast!)
            messages=[
                {"role": "user", "content": CLASSIFY_PROMPT.format(query=query)},
            ],
            max_tokens=5,
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip().lower()
        return raw if raw in {"healthcare", "government", "finance", "education"} else "general"


_service: GroqService | None = None


def get_groq_service() -> GroqService:
    """
    FastAPI dependency that returns a cached service instance.
    """
    from app.config import get_settings

    global _service
    if _service is None:
        _service = GroqService(get_settings())
    return _service

