from __future__ import annotations


def detect_language(text: str) -> str:
    """
    Lightweight language detection using `langdetect`.

    Returns an ISO-ish language code used by the app (en/hi/te/ta). If detection fails
    or returns an unsupported language, defaults to "en".
    """
    sample = (text or "").strip()
    if not sample:
        return "en"

    # Script-based fast path for short Indic queries (more reliable than statistical
    # detection on very small inputs).
    if any("\u0C00" <= ch <= "\u0C7F" for ch in sample):  # Telugu
        return "te"
    if any("\u0B80" <= ch <= "\u0BFF" for ch in sample):  # Tamil
        return "ta"
    if any("\u0900" <= ch <= "\u097F" for ch in sample):  # Devanagari (Hindi)
        return "hi"

    from langdetect import DetectorFactory, LangDetectException, detect

    # Ensure deterministic results across runs/processes.
    DetectorFactory.seed = 0

    try:
        lang = detect(sample[:500]).lower()
    except LangDetectException:
        return "en"

    # Normalize to the languages we support in the demo.
    supported = {"en", "hi", "te", "ta"}
    return lang if lang in supported else "en"

